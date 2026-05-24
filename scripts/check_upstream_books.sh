#!/usr/bin/env bash
# Compare vendored agent-rules-books snapshot to upstream's latest tag.
# Prints the upstream/vendor version pair and a diff for any of the 10 embedded files.
# Exits 0 if vendor matches upstream's latest tag, 1 otherwise (so CI can flag drift).
#
# Run via `make check-upstream-books`.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$REPO_ROOT/vendor/agent-rules-books"
UPSTREAM_REPO="ciembor/agent-rules-books"

VENDORED=$(cat "$VENDOR/VERSION")
LATEST=$(curl -fsSL "https://api.github.com/repos/$UPSTREAM_REPO/releases/latest" \
  | grep -E '"tag_name"' | head -1 | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/')

if [ -z "$LATEST" ]; then
  echo "could not resolve upstream latest tag (network? rate limit?)" >&2
  exit 2
fi

echo "vendored: $VENDORED"
echo "upstream: $LATEST"

if [ "$VENDORED" = "$LATEST" ]; then
  echo "in sync."
  exit 0
fi

echo
echo "drift detected; diffs for embedded files (vendored vs upstream $LATEST):"
echo

FILES=(
  "refactoring/refactoring.mini.md"
  "refactoring/refactoring.nano.md"
  "working-effectively-with-legacy-code/working-effectively-with-legacy-code.mini.md"
  "working-effectively-with-legacy-code/working-effectively-with-legacy-code.nano.md"
  "a-philosophy-of-software-design/a-philosophy-of-software-design.mini.md"
  "clean-architecture/clean-architecture.mini.md"
  "release-it/release-it.mini.md"
  "domain-driven-design-distilled/domain-driven-design-distilled.mini.md"
  "implementing-domain-driven-design/implementing-domain-driven-design.mini.md"
  "clean-code/clean-code.mini.md"
  "the-pragmatic-programmer/the-pragmatic-programmer.mini.md"
)

BASE_URL="https://raw.githubusercontent.com/$UPSTREAM_REPO/$LATEST"

for f in "${FILES[@]}"; do
  remote=$(curl -fsSL "$BASE_URL/$f" || true)
  if [ -z "$remote" ]; then
    echo "MISSING UPSTREAM: $f"
    continue
  fi
  diff_out=$(diff -u "$VENDOR/$f" <(printf "%s" "$remote") || true)
  if [ -n "$diff_out" ]; then
    echo "=== $f ==="
    echo "$diff_out"
    echo
  fi
done

echo
echo "to adopt upstream: bump $VENDOR/VERSION, copy new files in, then run \`make sync-books\`."
exit 1
