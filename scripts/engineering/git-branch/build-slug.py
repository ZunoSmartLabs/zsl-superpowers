#!/usr/bin/env python3
"""
Build a canonical git branch name from a description.

Slug rules (from git-branch/SKILL.md):
  - Lowercase
  - Replace non-alphanumeric characters with hyphens
  - Collapse consecutive hyphens into one
  - Trim leading/trailing hyphens
  - Total branch name (prefix/[N-]slug) must not exceed 40 characters
    The slug is truncated so the FULL name (prefix + separators + slug) fits

Valid prefixes: feature/ fix/ chore/ refactor/ env/

Usage:
  # Build a name
  python scripts/engineering/git-branch/build-slug.py DESCRIPTION
  python scripts/engineering/git-branch/build-slug.py --prefix fix DESCRIPTION
  python scripts/engineering/git-branch/build-slug.py --prefix feature --issue-id 22 DESCRIPTION

  # Validate an existing branch name has a valid prefix
  python scripts/engineering/git-branch/build-slug.py --validate BRANCHNAME

Output: canonical branch name to stdout
Exit 0 = success
Exit 1 = error (message on stderr) or invalid name (--validate mode)
"""

import argparse
import re
import sys

VALID_PREFIXES = ("feature/", "fix/", "chore/", "refactor/", "env/")
MAX_LENGTH = 40


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = text.strip("-")
    return text


def build_name(description: str, prefix: str, issue_id: int | None = None) -> str:
    if not prefix.endswith("/"):
        prefix = prefix + "/"

    slug = slugify(description)
    if not slug:
        print("error: description produces an empty slug", file=sys.stderr)
        sys.exit(1)

    # Calculate the overhead: prefix + optional "N-" before slug
    overhead = len(prefix)
    if issue_id is not None:
        overhead += len(str(issue_id)) + 1  # "N-"

    max_slug_len = MAX_LENGTH - overhead
    if max_slug_len < 1:
        print(
            f"error: prefix '{prefix}' with issue-id leaves no room for a slug within {MAX_LENGTH} chars",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(slug) > max_slug_len:
        slug = slug[:max_slug_len].rstrip("-")

    if issue_id is not None:
        name = f"{prefix}{issue_id}-{slug}"
    else:
        name = f"{prefix}{slug}"

    return name


def validate_name(name: str) -> bool:
    return any(name.startswith(p) for p in VALID_PREFIXES)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build or validate a canonical git branch name."
    )
    parser.add_argument(
        "description",
        nargs="?",
        default="",
        help="Human-readable description to slugify (required unless --validate is used)",
    )
    parser.add_argument(
        "--prefix",
        default="feature",
        help="Branch prefix without slash: feature, fix, chore, refactor, env (default: feature)",
    )
    parser.add_argument(
        "--issue-id",
        type=int,
        default=None,
        metavar="N",
        help="GitHub/GitLab issue number to prepend to slug (e.g. --issue-id 22 → prefix/22-slug)",
    )
    parser.add_argument(
        "--validate",
        metavar="BRANCHNAME",
        default=None,
        help="Validate that BRANCHNAME has a recognised prefix; exit 0 if valid, 1 if not",
    )
    args = parser.parse_args()

    if args.validate is not None:
        if validate_name(args.validate):
            print(f"valid: {args.validate}")
            sys.exit(0)
        else:
            valid_list = ", ".join(p.rstrip("/") for p in VALID_PREFIXES)
            print(
                f"invalid: '{args.validate}' — must start with one of: {valid_list}",
                file=sys.stderr,
            )
            sys.exit(1)

    if not args.description:
        parser.error("description is required when not using --validate")

    # Normalise prefix: accept with or without trailing slash
    prefix = args.prefix.rstrip("/")
    if prefix + "/" not in VALID_PREFIXES:
        valid_list = ", ".join(p.rstrip("/") for p in VALID_PREFIXES)
        print(
            f"error: unknown prefix '{prefix}' — must be one of: {valid_list}",
            file=sys.stderr,
        )
        sys.exit(1)

    name = build_name(args.description, prefix, args.issue_id)
    print(name)


if __name__ == "__main__":
    main()
