#!/usr/bin/env bash
# Pre-flight gate for /verify-coverage.
#
# Checks (in order):
#   1. docs/agents/issue-tracker.md exists  → run /setup-zsl-superpowers if not
#   2. docs/agents/triage-labels.md exists  → same
#   3. Working tree is clean                → Tier B mutation reverts require a clean tree
#   4. (Optional) PRD tag validation        → delegates to validate-prd-tags.py
#
# Usage:
#   # Basic filesystem + clean-tree checks only:
#   scripts/engineering/verify-coverage/preflight.sh
#
#   # Also validate PRD tags (pass PRD markdown via --prd-file or stdin):
#   scripts/engineering/verify-coverage/preflight.sh --prd-file /tmp/prd-body.md
#   gh issue view 42 --json body -q .body | scripts/engineering/verify-coverage/preflight.sh --validate-prd
#
# Exit 0 = all checks pass
# Exit 1 = one or more checks failed (details on stderr)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATE_PRD_SCRIPT="${SCRIPT_DIR}/../validate-prd-tags.py"

PRD_FILE=""
VALIDATE_PRD=false
ERRORS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prd-file)
      PRD_FILE="$2"
      VALIDATE_PRD=true
      shift 2
      ;;
    --validate-prd)
      VALIDATE_PRD=true
      shift
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--prd-file PATH] [--validate-prd]" >&2
      exit 1
      ;;
  esac
done

# --------------------------------------------------------------------------
# Check 1: docs/agents/issue-tracker.md
# --------------------------------------------------------------------------
if [[ ! -f "docs/agents/issue-tracker.md" ]]; then
  ERRORS+=("docs/agents/issue-tracker.md not found — run /setup-zsl-superpowers to create it")
fi

# --------------------------------------------------------------------------
# Check 2: docs/agents/triage-labels.md
# --------------------------------------------------------------------------
if [[ ! -f "docs/agents/triage-labels.md" ]]; then
  ERRORS+=("docs/agents/triage-labels.md not found — run /setup-zsl-superpowers to create it")
fi

# --------------------------------------------------------------------------
# Check 3: clean working tree
# --------------------------------------------------------------------------
DIRTY=$(git status --porcelain 2>/dev/null || echo "")
if [[ -n "$DIRTY" ]]; then
  DIRTY_COUNT=$(echo "$DIRTY" | wc -l | tr -d ' ')
  ERRORS+=(
    "working tree has ${DIRTY_COUNT} dirty file(s) — stash or commit before running verify-coverage"
    "  (Tier B mutation-prove reverts require an exactly-clean tree to be safe)"
  )
fi

# --------------------------------------------------------------------------
# Check 4: PRD tag validation (optional)
# --------------------------------------------------------------------------
if [[ "$VALIDATE_PRD" == true ]]; then
  if [[ ! -f "$VALIDATE_PRD_SCRIPT" ]]; then
    ERRORS+=(
      "validate-prd-tags.py not found at: $VALIDATE_PRD_SCRIPT"
      "  Cannot validate PRD tags automatically — apply the rules in verify-coverage/SKILL.md manually"
    )
  else
    if [[ -n "$PRD_FILE" ]]; then
      TAG_RESULT=$(python3 "$VALIDATE_PRD_SCRIPT" --file "$PRD_FILE" 2>&1)
      TAG_EXIT=$?
    elif [[ -t 0 ]]; then
      # stdin is a terminal — cannot read PRD body interactively
      ERRORS+=(
        "--validate-prd requires PRD content on stdin (pipe it) or --prd-file PATH"
        "  Example: gh issue view <N> --json body -q .body | $0 --validate-prd"
      )
      TAG_EXIT=0  # already appended to ERRORS; don't double-report below
      TAG_RESULT=""
    else
      # Read from piped stdin
      PRD_TEXT=$(cat)
      TAG_RESULT=$(echo "$PRD_TEXT" | python3 "$VALIDATE_PRD_SCRIPT" 2>&1)
      TAG_EXIT=$?
    fi

    if [[ $TAG_EXIT -ne 0 ]]; then
      # Surface the structured JSON error details
      ERRORS+=("PRD tag validation failed:")
      while IFS= read -r line; do
        ERRORS+=("  $line")
      done <<< "$TAG_RESULT"
    fi
  fi
fi

# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
if [[ ${#ERRORS[@]} -gt 0 ]]; then
  echo "preflight failed:" >&2
  for err in "${ERRORS[@]}"; do
    echo "  $err" >&2
  done
  exit 1
fi

echo "preflight ok"
exit 0
