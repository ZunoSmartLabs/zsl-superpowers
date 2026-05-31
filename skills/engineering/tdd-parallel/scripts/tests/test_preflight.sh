#!/usr/bin/env bash
# Tests for zsl-preflight.sh. Pure shell, no bats dependency. Builds throwaway git
# repos in temp dirs and asserts PASS/FAIL lines + exit codes — including inputs the
# old prose way gets wrong (a clean tree on a detached HEAD; a `.worktrees` line
# missing its trailing slash).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PREFLIGHT="$SCRIPT_DIR/zsl-preflight.sh"
fails=0

note() { printf '  %s\n' "$1"; }
ok() { printf 'ok   - %s\n' "$1"; }
bad() {
  printf 'FAIL - %s\n' "$1"
  fails=$((fails + 1))
}

assert_eq() {
  # assert_eq <desc> <expected> <actual>
  if [ "$2" = "$3" ]; then ok "$1"; else
    bad "$1"
    note "expected: $2"
    note "actual:   $3"
  fi
}
assert_contains() {
  # assert_contains <desc> <haystack> <needle>
  case "$2" in
    *"$3"*) ok "$1" ;;
    *)
      bad "$1"
      note "missing: $3"
      note "in:      $2"
      ;;
  esac
}

mkrepo() {
  local d
  d="$(mktemp -d)"
  git -C "$d" init -q
  git -C "$d" config user.email t@t.t
  git -C "$d" config user.name t
  echo init >"$d/f"
  git -C "$d" add f
  git -C "$d" commit -qm init
  echo "$d"
}

# --- 1. Golden: clean repo, on a branch, required file present, gitignore line present
repo="$(mkrepo)"
touch "$repo/docs-file"
printf '.worktrees/\n' >"$repo/.gitignore"
git -C "$repo" add -A && git -C "$repo" commit -qm files # commit so the tree is genuinely clean
out="$(cd "$repo" && bash "$PREFLIGHT" --clean-tree --not-detached --require-file docs-file --ensure-gitignore-line '.worktrees/' 2>&1)"
code=$?
assert_eq "golden: exit 0" 0 "$code"
assert_contains "golden: tree clean PASS" "$out" "PASS: working tree clean"
assert_contains "golden: not detached PASS" "$out" "PASS: HEAD on a branch (not detached)"
assert_contains "golden: file exists PASS" "$out" "PASS: file exists: docs-file"
assert_contains "golden: gitignore present PASS" "$out" "PASS: gitignore has line: .worktrees/"
rm -rf "$repo"

# --- 2. Fails-the-prose-way: detached HEAD on a CLEAN tree.
# `git status` still shows clean, so a model eyeballing it proceeds — the script refuses.
repo="$(mkrepo)"
git -C "$repo" checkout -q --detach HEAD
out="$(cd "$repo" && bash "$PREFLIGHT" --clean-tree --not-detached 2>&1)"
code=$?
assert_eq "detached: exit 1" 1 "$code"
assert_contains "detached: tree still PASSes clean" "$out" "PASS: working tree clean"
assert_contains "detached: detached FAILs" "$out" "FAIL: HEAD on a branch (not detached)"
rm -rf "$repo"

# --- 3. Fails-the-prose-way: gitignore has `.worktrees` WITHOUT the trailing slash.
# A model sees ".worktrees" and assumes it's covered; grep -qxF requires the exact
# line, so the script appends ".worktrees/" rather than double-relying on the bare name.
repo="$(mkrepo)"
printf '.worktrees\n' >"$repo/.gitignore"
out="$(cd "$repo" && bash "$PREFLIGHT" --ensure-gitignore-line '.worktrees/' 2>&1)"
code=$?
assert_eq "no-slash: exit 0 (append is not a failure)" 0 "$code"
assert_contains "no-slash: appended line" "$out" "PASS: gitignore line appended: .worktrees/"
gi="$(cat "$repo/.gitignore")"
assert_contains "no-slash: bare line still there" "$gi" ".worktrees"
assert_contains "no-slash: exact line now present" "$(grep -xF '.worktrees/' "$repo/.gitignore")" ".worktrees/"
# Idempotency: a second run must NOT append again.
out2="$(cd "$repo" && bash "$PREFLIGHT" --ensure-gitignore-line '.worktrees/' 2>&1)"
assert_contains "no-slash: second run sees it present" "$out2" "PASS: gitignore has line: .worktrees/"
count="$(grep -cxF '.worktrees/' "$repo/.gitignore")"
assert_eq "no-slash: exact line appears exactly once" 1 "$count"
rm -rf "$repo"

# --- 4. Missing required file → FAIL, exit 1.
repo="$(mkrepo)"
out="$(cd "$repo" && bash "$PREFLIGHT" --require-file docs/agents/issue-tracker.md 2>&1)"
code=$?
assert_eq "missing-file: exit 1" 1 "$code"
assert_contains "missing-file: FAIL line" "$out" "FAIL: file exists: docs/agents/issue-tracker.md"
rm -rf "$repo"

# --- 5. Dirty tree → FAIL.
repo="$(mkrepo)"
echo change >>"$repo/f"
out="$(cd "$repo" && bash "$PREFLIGHT" --clean-tree 2>&1)"
code=$?
assert_eq "dirty: exit 1" 1 "$code"
assert_contains "dirty: FAIL line" "$out" "FAIL: working tree clean"
rm -rf "$repo"

# --- 6. No flags → usage error, exit 2 (distinct from a check failure).
out="$(bash "$PREFLIGHT" 2>&1)"
code=$?
assert_eq "no-flags: exit 2" 2 "$code"

# --- 7. Not inside a git repo → --clean-tree FAILs cleanly (no crash).
tmp="$(mktemp -d)"
out="$(cd "$tmp" && bash "$PREFLIGHT" --clean-tree 2>&1)"
code=$?
assert_eq "no-repo: exit 1" 1 "$code"
assert_contains "no-repo: FAIL line" "$out" "FAIL: working tree clean (not inside a git repo)"
rm -rf "$tmp"

echo
if [ "$fails" -eq 0 ]; then
  echo "zsl-preflight.sh: all tests passed"
  exit 0
else
  echo "zsl-preflight.sh: $fails assertion(s) failed"
  exit 1
fi
