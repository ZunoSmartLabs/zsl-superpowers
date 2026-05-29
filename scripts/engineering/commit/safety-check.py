#!/usr/bin/env python3
"""
Commit safety-check gate for /commit.

Reads `git status --porcelain`, inspects each dirty/untracked file, and blocks:
  - Secret-pattern files: .env*, *credentials*, *secret*, *.pem, *.key
  - Files that git would ignore (.gitignore members that are somehow dirty)
  - Large binaries > 10 MB
  - Committing directly to main/master when docs/agents/ship-style.md says "pull request"

Output: JSON to stdout
  { "blocked": [ {"file": "...", "reason": "..."}, ... ] }

Exit 0 = clean, safe to stage
Exit 1 = one or more files blocked (details in JSON on stdout)

Usage:
  python scripts/engineering/commit/safety-check.py
  python scripts/engineering/commit/safety-check.py --ship-style-file docs/agents/ship-style.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BLOCKED_PATTERNS = [
    (r"(^|[/\\])\.env", "secret — .env file"),
    (r"credentials", "secret — credentials file"),
    (r"secret", "secret — secret file"),
    (r"\.pem$", "secret — PEM certificate/key"),
    (r"\.key$", "secret — key file"),
]

SIZE_LIMIT_MB = 10


def run(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or os.getcwd())


def get_dirty_files():
    result = run(["git", "status", "--porcelain"])
    files = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        xy = line[:2]
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ")[1]
        files.append((xy, path))
    return files


def matches_secret_pattern(path):
    basename = os.path.basename(path)
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, basename, re.IGNORECASE) or re.search(
            pattern, path, re.IGNORECASE
        ):
            return reason
    return None


def is_gitignored(path):
    result = run(["git", "check-ignore", "-q", "--", path])
    return result.returncode == 0


def file_size_mb(path):
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except OSError:
        return 0.0


def current_branch():
    result = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return result.stdout.strip()


def ship_style_is_pr(ship_style_file="docs/agents/ship-style.md"):
    try:
        content = Path(ship_style_file).read_text().lower()
        # Match the generated template ("pull request") and natural hand-written phrasings
        return bool(
            re.search(
                r"pull.request|pr.style|ship.*via.*pr|use.*pr|requires?.*pr"
                r"|merge.*via.*pr|\bpr.required\b|\bprs?\s+required\b",
                content,
            )
        )
    except FileNotFoundError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Pre-commit safety gate: detect secrets, large files, and wrong-branch commits."
    )
    parser.add_argument(
        "--ship-style-file",
        default="docs/agents/ship-style.md",
        help="Path to ship-style.md (default: docs/agents/ship-style.md)",
    )
    args = parser.parse_args()

    blocked = []

    # Branch check: refuse to commit to main/master when ship-style is PR
    branch = current_branch()
    if branch in ("main", "master") and ship_style_is_pr(args.ship_style_file):
        blocked.append(
            {
                "file": f"(current branch: {branch})",
                "reason": (
                    f"on '{branch}' with PR ship-style — "
                    "commit to a feature branch instead and open a PR"
                ),
            }
        )

    # File-level checks
    for xy, path in get_dirty_files():
        # Skip any deletion (staged "D ", worktree " D", or both "DD") — nothing to inspect
        index_status, worktree_status = xy[0], xy[1]
        if index_status == "D" or worktree_status == "D":
            continue

        reason = matches_secret_pattern(path)
        if reason:
            blocked.append({"file": path, "reason": reason})
            continue

        # .gitignore check (only for untracked files — status "??")
        if xy == "??":
            if is_gitignored(path):
                blocked.append(
                    {
                        "file": path,
                        "reason": ".gitignore — file matches an ignore rule; likely shouldn't be committed",
                    }
                )
                continue

        size = file_size_mb(path)
        if size > SIZE_LIMIT_MB:
            blocked.append(
                {
                    "file": path,
                    "reason": f"large binary — {size:.1f} MB exceeds {SIZE_LIMIT_MB} MB limit",
                }
            )

    result = {"blocked": blocked}
    print(json.dumps(result, indent=2))
    sys.exit(1 if blocked else 0)


if __name__ == "__main__":
    main()
