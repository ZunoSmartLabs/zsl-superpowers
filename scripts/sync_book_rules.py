#!/usr/bin/env python3
"""Rewrite BEGIN/END fenced book rules in each skill's SKILL.md from vendor/agent-rules-books/.

Idempotent. If the fences don't exist yet, appends the full block at the bottom of SKILL.md.
If they exist, replaces only the content between the markers.

Run via `make sync-books`.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VENDOR = REPO / "vendor" / "agent-rules-books"


@dataclass(frozen=True)
class BookEmbed:
    book_dir: str
    filename: str
    title: str
    author: str


# Skill -> ordered list of book embeds.
MAPPING: dict[str, list[BookEmbed]] = {
    "engineering/tdd": [
        BookEmbed(
            "refactoring", "refactoring.nano.md",
            "Refactoring", "Martin Fowler",
        ),
        BookEmbed(
            "working-effectively-with-legacy-code", "working-effectively-with-legacy-code.nano.md",
            "Working Effectively with Legacy Code", "Michael Feathers",
        ),
    ],
    "engineering/improve-codebase-architecture": [
        BookEmbed(
            "a-philosophy-of-software-design", "a-philosophy-of-software-design.mini.md",
            "A Philosophy of Software Design", "John Ousterhout",
        ),
        BookEmbed(
            "clean-architecture", "clean-architecture.mini.md",
            "Clean Architecture", "Robert C. Martin",
        ),
    ],
    "engineering/diagnose": [
        BookEmbed(
            "release-it", "release-it.mini.md",
            "Release It!", "Michael T. Nygard",
        ),
    ],
    "engineering/domain-modeling": [
        BookEmbed(
            "domain-driven-design-distilled", "domain-driven-design-distilled.mini.md",
            "Domain-Driven Design Distilled", "Vaughn Vernon",
        ),
        BookEmbed(
            "implementing-domain-driven-design", "implementing-domain-driven-design.mini.md",
            "Implementing Domain-Driven Design", "Vaughn Vernon",
        ),
    ],
    "engineering/to-prd": [
        BookEmbed(
            "domain-driven-design-distilled", "domain-driven-design-distilled.mini.md",
            "Domain-Driven Design Distilled", "Vaughn Vernon",
        ),
    ],
    "engineering/code-review": [
        BookEmbed(
            "clean-code", "clean-code.mini.md",
            "Clean Code", "Robert C. Martin",
        ),
        BookEmbed(
            "refactoring", "refactoring.mini.md",
            "Refactoring", "Martin Fowler",
        ),
    ],
    "engineering/verify-coverage": [
        BookEmbed(
            "working-effectively-with-legacy-code", "working-effectively-with-legacy-code.mini.md",
            "Working Effectively with Legacy Code", "Michael Feathers",
        ),
    ],
    "engineering/prototype": [
        BookEmbed(
            "the-pragmatic-programmer", "the-pragmatic-programmer.mini.md",
            "The Pragmatic Programmer", "Andrew Hunt & David Thomas",
        ),
    ],
}

REGION_HEADER = "## Bundled book rules"
REGION_PREAMBLE = (
    "Do not hand-edit content between the `BEGIN`/`END` markers — "
    "`scripts/sync_book_rules.py` overwrites it from `vendor/agent-rules-books/`."
)
REGION_BEGIN = "<!-- BEGIN bundled-book-rules -->"
REGION_END = "<!-- END bundled-book-rules -->"


def vendor_version() -> str:
    return (VENDOR / "VERSION").read_text(encoding="utf-8").strip()


def render_book(embed: BookEmbed, version: str) -> str:
    body = (VENDOR / embed.book_dir / embed.filename).read_text(encoding="utf-8").rstrip()
    return (
        f'### Rules from "{embed.title}" by {embed.author}\n\n'
        f"<!-- BEGIN {embed.filename} {version} -->\n\n"
        f"{body}\n\n"
        f"<!-- END {embed.filename} -->\n"
    )


def render_region(skill_key: str, version: str) -> str:
    chunks = [REGION_BEGIN, "", REGION_HEADER, "", REGION_PREAMBLE, ""]
    for embed in MAPPING[skill_key]:
        chunks.append(render_book(embed, version))
    chunks.append(REGION_END)
    return "\n".join(chunks).rstrip() + "\n"


REGION_RE = re.compile(
    re.escape(REGION_BEGIN) + r".*?" + re.escape(REGION_END) + r"\n?",
    flags=re.DOTALL,
)


def write_skill(skill_key: str, version: str) -> tuple[Path, bool]:
    skill_md = REPO / "skills" / skill_key / "SKILL.md"
    original = skill_md.read_text(encoding="utf-8")
    region = render_region(skill_key, version)

    if REGION_RE.search(original):
        updated = REGION_RE.sub(region, original)
    else:
        sep = "" if original.endswith("\n\n") else ("\n" if original.endswith("\n") else "\n\n")
        updated = original + sep + region

    changed = updated != original
    if changed:
        skill_md.write_text(updated, encoding="utf-8")
    return skill_md, changed


def main() -> int:
    if not VENDOR.exists():
        print(f"vendor missing: {VENDOR}", file=sys.stderr)
        return 1
    version = vendor_version()
    print(f"Syncing book rules from {VENDOR} ({version})")
    any_changed = False
    for skill_key in MAPPING:
        path, changed = write_skill(skill_key, version)
        marker = "updated" if changed else "unchanged"
        any_changed |= changed
        print(f"  {marker}: {path.relative_to(REPO)}")
    if not any_changed:
        print("All SKILL.md files already in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
