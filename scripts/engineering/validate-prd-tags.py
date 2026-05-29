#!/usr/bin/env python3
"""
Shared PRD user-story tag validator.

Reads a markdown document (stdin by default, or --file) and validates the
## User Stories section. Every story entry must have both:
  - Sub-bullet:  acceptance: automatable
  - Sub-bullet:  observable: <non-empty description>

Any story with a different acceptance value, or missing either sub-bullet,
is reported as invalid.

Output: JSON to stdout
  {
    "valid": true | false,
    "total_stories": N,
    "invalid_stories": [
      {
        "num": 1,
        "text": "<first 120 chars of the story line>",
        "missing": ["acceptance: automatable (sub-bullet missing)", ...]
      }
    ]
  }

Exit 0 = all stories valid (or --quiet and valid)
Exit 1 = validation failed

Used by: /triage (step 1 PRD tag check), /verify-coverage (pre-flight),
         /tdd-parallel (step 1d pre-flight).

Usage:
  gh issue view 42 --json body -q .body | python scripts/engineering/validate-prd-tags.py
  python scripts/engineering/validate-prd-tags.py --file prd-body.md
  python scripts/engineering/validate-prd-tags.py --file prd-body.md --quiet
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _find_user_stories_section(text: str) -> str | None:
    """Return the raw content that follows the first ## User Stories heading."""
    # Split on any markdown heading (# through ####)
    heading_re = re.compile(r"^#{1,4}\s+(.+)", re.MULTILINE)
    matches = list(heading_re.finditer(text))

    for i, m in enumerate(matches):
        if re.match(r"user\s+stories?", m.group(1).strip(), re.IGNORECASE):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[start:end]

    return None


def _parse_story_entries(section: str) -> list[tuple[int, str, list[str]]]:
    """
    Parse top-level list items and their immediate sub-bullets.

    Returns list of (story_num, story_text, sub_bullet_texts).
    """
    stories: list[tuple[int, str, list[str]]] = []
    current_story: str | None = None
    current_subs: list[str] = []
    story_num = 0

    top_level_re = re.compile(r"^[-*]\s+\S|^\d+\.\s+\S")
    sub_bullet_re = re.compile(r"^[ \t]{2,}[-*]\s*(.+)|^\t[-*]\s*(.+)")

    for line in section.splitlines():
        if top_level_re.match(line):
            if current_story is not None:
                stories.append((story_num, current_story, current_subs))
            story_num += 1
            current_story = re.sub(r"^[-*\d.]+\s+", "", line).strip()
            current_subs = []
        else:
            m = sub_bullet_re.match(line)
            if m and current_story is not None:
                sub_text = (m.group(1) or m.group(2) or "").strip()
                if sub_text:
                    current_subs.append(sub_text)

    if current_story is not None:
        stories.append((story_num, current_story, current_subs))

    return stories


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_stories(
    stories: list[tuple[int, str, list[str]]],
) -> list[dict]:
    invalid: list[dict] = []

    for num, text, sub_bullets in stories:
        missing: list[str] = []

        # --- acceptance check ---
        acceptance_bullets = [
            b for b in sub_bullets if re.match(r"^acceptance\s*:", b, re.IGNORECASE)
        ]
        if not acceptance_bullets:
            missing.append("acceptance: automatable (sub-bullet missing)")
        else:
            for ab in acceptance_bullets:
                val = re.sub(r"^acceptance\s*:\s*", "", ab, flags=re.IGNORECASE).strip()
                if val.lower() != "automatable":
                    missing.append(
                        f'acceptance: automatable (found: "{val}" — must be exactly "automatable")'
                    )

        # --- observable check ---
        obs_bullets = [
            b for b in sub_bullets if re.match(r"^observable\s*:", b, re.IGNORECASE)
        ]
        if not obs_bullets:
            missing.append("observable: <description> (sub-bullet missing)")
        else:
            for ob in obs_bullets:
                val = re.sub(r"^observable\s*:\s*", "", ob, flags=re.IGNORECASE).strip()
                if not val:
                    missing.append("observable: (value is empty — description required)")

        if missing:
            invalid.append({"num": num, "text": text[:120], "missing": missing})

    return invalid


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate PRD user-story acceptance: / observable: tags."
    )
    parser.add_argument(
        "--file",
        "-f",
        metavar="PATH",
        help="Markdown file to read (default: stdin)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress JSON output; only set exit code",
    )
    args = parser.parse_args()

    if args.file:
        try:
            text = Path(args.file).read_text()
        except FileNotFoundError:
            print(
                json.dumps(
                    {
                        "valid": False,
                        "total_stories": 0,
                        "invalid_stories": [],
                        "error": f"File not found: {args.file}",
                    },
                    indent=2,
                )
            )
            sys.exit(1)
    else:
        text = sys.stdin.read()

    section = _find_user_stories_section(text)
    if section is None:
        result = {
            "valid": False,
            "total_stories": 0,
            "invalid_stories": [],
            "error": "No '## User Stories' section found in the document",
        }
        if not args.quiet:
            print(json.dumps(result, indent=2))
        sys.exit(1)

    stories = _parse_story_entries(section)
    if not stories:
        result = {
            "valid": False,
            "total_stories": 0,
            "invalid_stories": [],
            "error": "'## User Stories' section found but no story entries could be parsed",
        }
        if not args.quiet:
            print(json.dumps(result, indent=2))
        sys.exit(1)

    invalid = _validate_stories(stories)
    result = {
        "valid": len(invalid) == 0,
        "total_stories": len(stories),
        "invalid_stories": invalid,
    }

    if not args.quiet:
        print(json.dumps(result, indent=2))

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
