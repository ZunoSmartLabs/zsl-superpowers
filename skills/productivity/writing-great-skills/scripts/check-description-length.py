#!/usr/bin/env python3
"""Hard character-count gate for a skill's `description` field.

The harness that surfaces skill descriptions in the system prompt truncates at
1024 characters — silently. A description over the cap loses its trailing
`Use when …` trigger clause, so the skill stops being selected for exactly the
cases the cut-off text described. Whether `len(description) <= 1024` has one
correct answer, so it is counted here rather than eyeballed.

Reads the description from a positional arg, from --file, or from stdin.
Exit 0 if within the cap; exit 1 (with the count) if over. Counts Unicode
characters, matching how the cap is specified.

Usage:
    check-description-length.py "the description text"
    check-description-length.py --file path/to/desc.txt
    printf '%s' "$DESC" | check-description-length.py
    check-description-length.py --max 1024 ...   # override the cap (default 1024)
"""

from __future__ import annotations

import argparse
import sys

DEFAULT_MAX = 1024


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("description", nargs="?", help="description text (else --file or stdin)")
    parser.add_argument("--file", help="read the description from this file")
    parser.add_argument(
        "--max", type=int, default=DEFAULT_MAX, help=f"max characters (default {DEFAULT_MAX})"
    )
    args = parser.parse_args()

    if args.file is not None:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
    elif args.description is not None:
        text = args.description
    else:
        text = sys.stdin.read()

    # A single trailing newline is an artifact of shell/file input, not the field.
    if text.endswith("\n"):
        text = text[:-1]

    n = len(text)
    if n <= args.max:
        print(f"PASS: description is {n} chars (<= {args.max})")
        return 0
    print(f"FAIL: description is {n} chars (> {args.max}) — trim {n - args.max} chars")
    return 1


if __name__ == "__main__":
    sys.exit(main())
