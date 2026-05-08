#!/usr/bin/env python3
"""Digest Claude Code session histories into a timesheet summary.

Walks ~/.claude/projects/, opens every top-level session .jsonl (skipping
subagent files), filters events by ISO timestamp into the requested time
window, and renders Markdown bullets grouped by project (cwd). Use
`--format json` for the structured digest (intended for LLM synthesis).

Markdown signal priority:
1. git commit subjects (deduped) — the strongest "delivered" signal.
2. PR titles from `gh pr create --title "..."`.
3. Fallback: in-progress files / pre-window pushes / exploratory.

Active hours per project are estimated by counting distinct 5-minute
buckets that contain at least one event, summed across the project's
sessions.

Usage:
    digest_sessions.py [--hours N] [--format markdown|json]
                       [--include-noise] [--projects-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


SLASH_COMMAND_OUTPUT_MARKERS = (
    "<local-command-stdout>",
    "<local-command-stderr>",
    "<command-stdout>",
    "<command-stderr>",
)

# Paths we treat as noise unless --include-noise is passed. These directories
# accumulate health-check / probe sessions from menubar tools.
NOISE_PATH_FRAGMENTS = ("ClaudeProbe", "CodexBar")

ACTIVE_BUCKET_MINUTES = 5

COMMIT_SUBJECT_RE = re.compile(r"""git\s+commit\b[^"']*?-m\s+["']([^"'\n]+)["']""", re.S)
PR_TITLE_RE = re.compile(r"""--title\s+["']([^"'\n]+)["']""")


def parse_ts(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def is_subagent_file(path: Path) -> bool:
    return "subagents" in path.parts


def is_noise_path(cwd: str) -> bool:
    return any(frag in cwd for frag in NOISE_PATH_FRAGMENTS)


def decode_cwd_from_dir(name: str) -> str:
    if name.startswith("-"):
        return "/" + name[1:].replace("-", "/")
    return name


def extract_user_prompt(message: dict) -> str | None:
    content = message.get("content")
    if isinstance(content, str):
        text = content.strip()
        if not text:
            return None
        if any(m in text for m in SLASH_COMMAND_OUTPUT_MARKERS) and "<command-name>" not in text:
            return None
        return text
    return None


def summarize_tool_use(block: dict, summary: dict) -> None:
    name = block.get("name") or ""
    inp = block.get("input") or {}

    if name in ("Edit", "Write", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("notebook_path")
        if path:
            summary["files_touched"].setdefault(path, name)

    elif name == "Bash":
        cmd = (inp.get("command") or "").strip()
        if not cmd:
            return
        first = cmd.split("\n", 1)[0][:300]
        head = cmd.split("&&", 1)[0]
        low = head.lower().lstrip()
        if low.startswith("git commit"):
            summary["git_commits"].append(cmd)
        elif low.startswith("git push"):
            summary["git_pushes"].append(first)
        elif low.startswith("gh pr create"):
            summary["pr_creates"].append(cmd)
        elif low.startswith("gh pr merge"):
            summary["pr_merges"].append(first)
        elif low.startswith("git checkout -b") or low.startswith("git switch -c"):
            summary["branches_created"].append(first)


def bucket_id(ts: datetime) -> int:
    return int(ts.timestamp() // (ACTIVE_BUCKET_MINUTES * 60))


def process_session(path: Path, window_start: datetime, window_end: datetime) -> dict | None:
    user_prompts: list[str] = []
    summary = {
        "files_touched": {},
        "git_commits": [],
        "git_pushes": [],
        "pr_creates": [],
        "pr_merges": [],
        "branches_created": [],
    }
    buckets: set[int] = set()
    in_window_count = 0
    earliest: datetime | None = None
    latest: datetime | None = None
    cwd: str | None = None
    git_branch: str | None = None

    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = parse_ts(event.get("timestamp"))
                if ts is None or ts < window_start or ts > window_end:
                    continue

                in_window_count += 1
                buckets.add(bucket_id(ts))
                if earliest is None or ts < earliest:
                    earliest = ts
                if latest is None or ts > latest:
                    latest = ts

                if not cwd and event.get("cwd"):
                    cwd = event["cwd"]
                if not git_branch and event.get("gitBranch"):
                    git_branch = event["gitBranch"]

                etype = event.get("type")
                msg = event.get("message") or {}

                if etype == "user":
                    prompt = extract_user_prompt(msg)
                    if prompt:
                        user_prompts.append(prompt)
                elif etype == "assistant":
                    content = msg.get("content")
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                summarize_tool_use(block, summary)
    except OSError:
        return None

    if in_window_count == 0:
        return None

    return {
        "session_id": path.stem,
        "file": str(path),
        "cwd": cwd,
        "git_branch": git_branch,
        "started_at": earliest.isoformat() if earliest else None,
        "ended_at": latest.isoformat() if latest else None,
        "event_count": in_window_count,
        "active_minutes": len(buckets) * ACTIVE_BUCKET_MINUTES,
        "_buckets": buckets,
        "user_prompts": user_prompts,
        "files_touched": [
            {"path": p, "via": tool} for p, tool in summary["files_touched"].items()
        ],
        "git_commits": summary["git_commits"],
        "git_pushes": summary["git_pushes"],
        "pr_creates": summary["pr_creates"],
        "pr_merges": summary["pr_merges"],
        "branches_created": summary["branches_created"],
    }


def merge_nested_projects(project_records: list[dict]) -> list[dict]:
    """Collapse projects whose cwd is strictly nested under another project's cwd.

    Active minutes are recomputed as the union of buckets across all merged
    sessions — overlapping work does not double-count.
    """
    keepers: list[dict] = []
    for p in sorted(project_records, key=lambda r: len(r["cwd"].rstrip("/"))):
        cwd = p["cwd"].rstrip("/")
        parent = None
        for k in keepers:
            if cwd.startswith(k["cwd"].rstrip("/") + "/"):
                parent = k
                break
        if parent is None:
            keepers.append(p)
            continue
        parent["sessions"].extend(p["sessions"])
        all_buckets: set[int] = set()
        for s in parent["sessions"]:
            all_buckets |= s["_buckets"]
        parent["active_minutes"] = len(all_buckets) * ACTIVE_BUCKET_MINUTES
        parent["sessions"].sort(key=lambda s: s.get("started_at") or "")
    return keepers


def project_matches(cwd: str, patterns: list[str]) -> bool:
    """Bare patterns match basename; patterns containing '/' match full path. Case-insensitive."""
    if not patterns:
        return False
    name = os.path.basename(cwd.rstrip("/")) or cwd
    for raw in patterns:
        pat = raw.lower()
        if "/" in pat:
            if pat in cwd.lower():
                return True
        else:
            if pat in name.lower():
                return True
    return False


def collect(args: argparse.Namespace) -> dict:
    if not args.projects_dir.is_dir():
        print(f"projects dir not found: {args.projects_dir}", file=sys.stderr)
        sys.exit(1)

    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(hours=args.hours)
    mtime_floor = (window_start - timedelta(hours=2)).timestamp()

    # Explicit --only overrides the default noise filter; the user is being specific.
    apply_noise_filter = not args.include_noise and not args.only

    sessions: list[dict] = []
    for path in args.projects_dir.rglob("*.jsonl"):
        if is_subagent_file(path):
            continue
        try:
            if path.stat().st_mtime < mtime_floor:
                continue
        except OSError:
            continue
        digest = process_session(path, window_start, window_end)
        if not digest:
            continue
        if apply_noise_filter and digest["cwd"] and is_noise_path(digest["cwd"]):
            continue
        sessions.append(digest)

    projects: dict[str, list[dict]] = {}
    for s in sessions:
        key = s["cwd"] or decode_cwd_from_dir(Path(s["file"]).parent.name)
        projects.setdefault(key, []).append(s)

    project_records = []
    for cwd, sess_list in projects.items():
        sess_list.sort(key=lambda s: s.get("started_at") or "")
        merged_buckets: set[int] = set()
        for s in sess_list:
            merged_buckets |= s["_buckets"]
        project_records.append(
            {
                "cwd": cwd,
                "active_minutes": len(merged_buckets) * ACTIVE_BUCKET_MINUTES,
                "sessions": sess_list,
            }
        )

    if args.merge_nested:
        project_records = merge_nested_projects(project_records)

    project_records.sort(key=lambda p: -p["active_minutes"])

    if args.only:
        matched = [p for p in project_records if project_matches(p["cwd"], args.only)]
        if not matched:
            print("No projects matched --only patterns:", ", ".join(args.only), file=sys.stderr)
            if project_records:
                print("Available basenames:", file=sys.stderr)
                for p in project_records:
                    name = os.path.basename(p["cwd"].rstrip("/")) or p["cwd"]
                    print(f"  - {name}", file=sys.stderr)
            sys.exit(2)
        project_records = matched
    elif args.exclude:
        project_records = [p for p in project_records if not project_matches(p["cwd"], args.exclude)]

    return {
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "hours": args.hours,
        "session_count": sum(len(p["sessions"]) for p in project_records),
        "project_count": len(project_records),
        "projects": project_records,
    }


def strip_internal(digest: dict) -> dict:
    # _buckets is internal-only; strip before JSON serialization.
    out = dict(digest)
    out["projects"] = [
        {**p, "sessions": [{k: v for k, v in s.items() if k != "_buckets"} for s in p["sessions"]]}
        for p in digest["projects"]
    ]
    return out


def fmt_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes}m"
    h = minutes / 60
    return f"{int(h)}h" if h == int(h) else f"{h:.1f}h"


def fmt_window_phrase(hours: float) -> str:
    if hours == int(hours):
        n = int(hours)
        return f"last {n} hour{'s' if n != 1 else ''}"
    return f"last {hours} hours"


def commit_subject(cmd: str) -> str | None:
    m = COMMIT_SUBJECT_RE.search(cmd)
    if not m:
        return None
    subj = m.group(1).strip()
    return subj or None


def pr_title(cmd: str) -> str | None:
    m = PR_TITLE_RE.search(cmd)
    if not m:
        return None
    title = m.group(1).strip()
    return title or None


def project_outcome_bullets(project: dict) -> list[str]:
    """Real outcome bullets only — commit subjects and PR titles. No fallbacks, no merges."""
    bullets: list[str] = []
    for s in project["sessions"]:
        for c in s["git_commits"]:
            subj = commit_subject(c)
            if subj:
                bullets.append(subj)
        for p in s["pr_creates"]:
            title = pr_title(p)
            bullets.append(f"Opened PR: {title}" if title else "Opened pull request")

    seen: set[str] = set()
    deduped = []
    for b in bullets:
        if b not in seen:
            seen.add(b)
            deduped.append(b)
    return deduped


def render_list(digest: dict) -> str:
    lines: list[str] = []
    win_start = parse_ts(digest["window_start"]).astimezone()
    win_end = parse_ts(digest["window_end"]).astimezone()
    tz = win_end.strftime("%Z") or "local"

    lines.append(f"## Projects in {fmt_window_phrase(digest['hours'])}")
    lines.append(
        f"_{win_start.strftime('%Y-%m-%d %H:%M')} → {win_end.strftime('%H:%M')} {tz}_"
    )
    lines.append("")

    if not digest["projects"]:
        lines.append("_No sessions in this window._")
        return "\n".join(lines) + "\n"

    for project in digest["projects"]:
        cwd = project["cwd"]
        name = os.path.basename(cwd.rstrip("/")) or cwd
        duration = fmt_duration(project["active_minutes"])
        n = len(project["sessions"])
        lines.append(f"- **{name}** · {duration} · {n} session{'s' if n != 1 else ''}")
        lines.append(f"  `{cwd}`")

    return "\n".join(lines).rstrip() + "\n"


def render_markdown(digest: dict) -> str:
    lines: list[str] = []
    win_start = parse_ts(digest["window_start"]).astimezone()
    win_end = parse_ts(digest["window_end"]).astimezone()
    tz = win_end.strftime("%Z") or "local"

    lines.append(f"## Timesheet — {fmt_window_phrase(digest['hours'])}")
    lines.append(
        f"_{win_start.strftime('%Y-%m-%d %H:%M')} → {win_end.strftime('%H:%M')} {tz}_"
    )
    lines.append("")

    rendered_any = False
    for project in digest["projects"]:
        bullets = project_outcome_bullets(project)
        if not bullets:
            continue
        name = os.path.basename(project["cwd"].rstrip("/")) or project["cwd"]
        for bullet in bullets:
            lines.append(f"- {name} · {bullet}")
            rendered_any = True

    if not rendered_any:
        lines.append("_No outcomes in this window._")

    return "\n".join(lines).rstrip() + "\n"


def copy_to_clipboard(text: str) -> str | None:
    """Pipe text into the system clipboard. Returns the tool name used, or None if unavailable."""
    system = platform.system()
    if system == "Darwin":
        candidates = [["pbcopy"]]
    elif system == "Linux":
        candidates = [["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "-b", "-i"]]
    elif system == "Windows":
        candidates = [["clip"]]
    else:
        candidates = []

    for cmd in candidates:
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text, text=True, check=True)
                return cmd[0]
            except subprocess.CalledProcessError:
                continue
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=float, default=12.0, help="Window size in hours (default: 12)")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List projects only (no outcome bullets), then exit. Use to pick before generating the summary.",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Include only projects matching PATTERN (basename substring; full-path substring if PATTERN contains '/'). Repeatable.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Exclude projects matching PATTERN (same matching rules as --only). Repeatable. Ignored if --only is set.",
    )
    parser.add_argument(
        "--merge-nested",
        action="store_true",
        help="Collapse projects whose cwd is a subdirectory of another project's cwd into that parent (e.g. fold packages/api/foo into the parent monorepo).",
    )
    parser.add_argument(
        "--include-noise",
        action="store_true",
        help="Include health-check / probe paths normally filtered out",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Also copy the rendered output to the system clipboard (pbcopy / xclip / wl-copy / clip).",
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path.home() / ".claude" / "projects",
        help="Claude Code projects dir (default: ~/.claude/projects)",
    )
    args = parser.parse_args()

    digest = collect(args)

    if args.list:
        output = render_list(digest)
    elif args.format == "json":
        output = json.dumps(strip_internal(digest), indent=2) + "\n"
    else:
        output = render_markdown(digest)

    sys.stdout.write(output)

    if args.copy:
        tool = copy_to_clipboard(output)
        if tool:
            print(f"(copied to clipboard via {tool})", file=sys.stderr)
        else:
            print("(no clipboard tool found — install pbcopy / xclip / wl-copy / clip)", file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
