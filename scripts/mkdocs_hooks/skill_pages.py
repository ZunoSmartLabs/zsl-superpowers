"""Auto-generate one docs page per SKILL.md so the skills are first-class on the site.

The hook scans `skills/<bucket>/<name>/SKILL.md`, parses the YAML frontmatter, and
emits a virtual `docs/skills/<name>.md` page. Pages aren't written to disk — they're
attached to mkdocs's file collection via `File.generated` and served at build time.

Each generated page renders:
- Title and bucket
- The slash command (`/zsl:<name>`)
- A "When this skill activates" callout containing the full `description:` —
  Claude Code matches against this text when deciding whether to auto-invoke.
- An "Edit this skill" link to the SKILL.md on GitHub.
- The SKILL.md body (everything after the frontmatter, with the original H1 dropped
  so we don't end up with two H1s on one page).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from mkdocs.structure.files import File, Files

REPO_BLOB_BASE = "https://github.com/ZunoSmartLabs/zsl-superpowers/blob/main"

BUCKET_LABELS = {
    "engineering": "Engineering",
    "productivity": "Productivity",
    "misc": "Misc",
}


def _parse_skill_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    frontmatter = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta = yaml.safe_load(frontmatter) or {}
    return meta, body


def _strip_h1(body: str) -> str:
    """Drop the first top-level heading; keep everything else verbatim."""
    lines = body.splitlines()
    out: list[str] = []
    seen_h1 = False
    for line in lines:
        if not seen_h1 and re.match(r"^# \S", line):
            seen_h1 = True
            continue
        out.append(line)
    # Strip leading blank lines left behind by the dropped H1.
    while out and out[0].strip() == "":
        out.pop(0)
    return "\n".join(out) + "\n"


_LINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)\s]+?)(\s+\"[^\"]*\")?\)")
_INLINE_PATH_RE = re.compile(r"`([A-Za-z0-9_/-]+\.(?:md|sh|py|yml|yaml|toml))`")


def _rewrite_relative_links(body: str, bucket: str, name: str) -> str:
    """Resolve relative links inside a SKILL.md body to absolute GitHub URLs.

    SKILL.md files commonly link to sibling resource files (LANGUAGE.md,
    AGENT-BRIEF.md, scripts/foo.sh) that live in the skill's directory in the
    repo but aren't part of the docs site. Rewrite those to repo URLs so the
    docs page links don't 404 under `mkdocs build --strict`.
    """
    skill_base = f"{REPO_BLOB_BASE}/skills/{bucket}/{name}"

    def _is_relative(target: str) -> bool:
        if target.startswith(("http://", "https://", "mailto:", "#", "/")):
            return False
        return True

    def _rewrite_target(target: str) -> str:
        # Drop ./ prefix so we don't double up.
        if target.startswith("./"):
            target = target[2:]
        return f"{skill_base}/{target}"

    def _link_sub(match: re.Match) -> str:
        text, target, title = match.group(1), match.group(2), match.group(3) or ""
        if not _is_relative(target):
            return match.group(0)
        return f"[{text}]({_rewrite_target(target)}{title})"

    return _LINK_RE.sub(_link_sub, body)


def _render_page(meta: dict, body: str, bucket: str, repo_skill_path: str) -> str:
    name = meta.get("name", "unnamed")
    description = (meta.get("description") or "").strip()
    user_invocable = bool(meta.get("disable-model-invocation"))
    bucket_label = BUCKET_LABELS.get(bucket, bucket.capitalize())
    title = name.replace("-", " ").title().replace("Tdd", "TDD").replace("Prd", "PRD")

    parts: list[str] = [f"# {title}", ""]

    parts.append(f"**Bucket:** {bucket_label} · ")
    parts.append(f"**Slash command:** `/zsl:{name}` · ")
    parts.append(
        f"**Source:** [skills/{bucket}/{name}/SKILL.md]({REPO_BLOB_BASE}/{repo_skill_path})"
    )
    parts.append("")

    if user_invocable:
        parts.append("!!! info \"User-invocable only\"")
        parts.append(
            "    This skill is marked `disable-model-invocation: true` — Claude won't auto-trigger "
            "it, so you must invoke it explicitly with the slash command above."
        )
        parts.append("")
    else:
        parts.append("!!! tip \"When this skill activates\"")
        parts.append(
            "    Claude Code matches this skill against the trigger text below. You can also invoke"
            " it explicitly with the slash command."
        )
        parts.append("")
        parts.append("    " + description.replace("\n", "\n    "))
        parts.append("")

    if user_invocable and description:
        parts.append("## What it does")
        parts.append("")
        parts.append(description)
        parts.append("")

    body_clean = _strip_h1(_rewrite_relative_links(body, bucket, name)).rstrip()
    if body_clean:
        parts.append("---")
        parts.append("")
        parts.append(body_clean)
        parts.append("")

    return "\n".join(parts)


def on_files(files: Files, config, **kwargs) -> Files:
    repo_root = Path(config["config_file_path"]).parent
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        return files

    for skill_md in sorted(skills_root.glob("*/*/SKILL.md")):
        bucket = skill_md.parent.parent.name
        meta, body = _parse_skill_md(skill_md)
        name = meta.get("name") or skill_md.parent.name
        rel_skill_path = str(skill_md.relative_to(repo_root))
        content = _render_page(meta, body, bucket, rel_skill_path)
        files.append(
            File.generated(
                config=config,
                src_uri=f"skills/{name}.md",
                content=content,
            )
        )
    return files
