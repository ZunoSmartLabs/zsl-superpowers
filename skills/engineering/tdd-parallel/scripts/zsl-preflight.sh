#!/usr/bin/env bash
# zsl-preflight.sh — deterministic refuse-or-proceed gates for skills that must
# validate repo state before doing work. Each check has exactly one correct
# boolean answer derivable by a plain git/shell predicate, so it is scripted here
# rather than eyeballed by the model. Prints "PASS: <desc>" or "FAIL: <desc>" per
# check and exits 1 if ANY check failed (0 if all passed). A FAIL means refuse,
# per the invoking skill's prose.
#
# This script is intentionally generic and parameterized so one validator serves
# every preflight that reduces to these primitives. NON-deterministic reads — e.g.
# "ship-style.md says PR-style", which interprets free-form prose — are NOT here;
# they stay model-driven in the skill.
#
# Flags (at least one required):
#   --clean-tree                 git working tree has no changes (porcelain empty)
#   --not-detached               HEAD points at a branch, not a detached commit
#   --require-file PATH          PATH exists and is a regular file (repeatable)
#   --ensure-gitignore-line LINE root .gitignore contains LINE exactly; append if not
set -uo pipefail

status=0
did_check=0
pass() { echo "PASS: $1"; }
fail() {
  echo "FAIL: $1"
  status=1
}

usage() {
  cat >&2 <<'EOF'
usage: zsl-preflight.sh [--clean-tree] [--not-detached] \
                        [--require-file PATH]... [--ensure-gitignore-line LINE]...
At least one check flag is required. Exits 1 if any check fails, 2 on a usage error.
EOF
}

check_clean_tree() {
  did_check=1
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    fail "working tree clean (not inside a git repo)"
  elif [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    fail "working tree clean"
  else
    pass "working tree clean"
  fi
}

check_not_detached() {
  did_check=1
  if git symbolic-ref -q HEAD >/dev/null 2>&1; then
    pass "HEAD on a branch (not detached)"
  else
    fail "HEAD on a branch (not detached)"
  fi
}

check_require_file() {
  did_check=1
  if [ -f "$1" ]; then
    pass "file exists: $1"
  else
    fail "file exists: $1"
  fi
}

ensure_gitignore_line() {
  did_check=1
  local line="$1" gi=".gitignore"
  if [ -f "$gi" ] && grep -qxF "$line" "$gi"; then
    pass "gitignore has line: $line"
  else
    printf '%s\n' "$line" >>"$gi"
    pass "gitignore line appended: $line"
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --clean-tree)
      check_clean_tree
      shift
      ;;
    --not-detached)
      check_not_detached
      shift
      ;;
    --require-file)
      [ $# -ge 2 ] || {
        usage
        exit 2
      }
      check_require_file "$2"
      shift 2
      ;;
    --ensure-gitignore-line)
      [ $# -ge 2 ] || {
        usage
        exit 2
      }
      ensure_gitignore_line "$2"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [ "$did_check" -eq 0 ]; then
  usage
  exit 2
fi
exit "$status"
