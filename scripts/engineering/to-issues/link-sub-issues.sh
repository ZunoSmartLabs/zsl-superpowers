#!/usr/bin/env bash
# Link a GitHub issue as a sub-issue of a parent issue.
#
# Used by: /to-issues (step 6), /verify-coverage (step 7 gap-filing)
#
# Requirements:
#   - gh CLI, authenticated (gh auth status)
#   - The addSubIssue GraphQL mutation must be available (GitHub repos on plans that
#     support sub-issues; free/legacy repos may return "UNPROCESSABLE" — the script
#     surfaces that error clearly)
#
# Usage:
#   ./link-sub-issues.sh OWNER REPO PARENT_NUM CHILD_NUM
#
# Example:
#   ./link-sub-issues.sh acme my-repo 42 57
#
# Exit 0 = success
# Exit 1 = failure (reason printed to stderr)

set -uo pipefail

OWNER="${1:?Error: OWNER required. Usage: $0 OWNER REPO PARENT_NUM CHILD_NUM}"
REPO="${2:?Error: REPO required. Usage: $0 OWNER REPO PARENT_NUM CHILD_NUM}"
PARENT_NUM="${3:?Error: PARENT_NUM required. Usage: $0 OWNER REPO PARENT_NUM CHILD_NUM}"
CHILD_NUM="${4:?Error: CHILD_NUM required. Usage: $0 OWNER REPO PARENT_NUM CHILD_NUM}"

# Validate numeric args
if ! [[ "$PARENT_NUM" =~ ^[0-9]+$ ]]; then
  echo "error: PARENT_NUM must be a positive integer, got: '$PARENT_NUM'" >&2
  exit 1
fi
if ! [[ "$CHILD_NUM" =~ ^[0-9]+$ ]]; then
  echo "error: CHILD_NUM must be a positive integer, got: '$CHILD_NUM'" >&2
  exit 1
fi

echo "Fetching node IDs for ${OWNER}/${REPO}#${PARENT_NUM} and #${CHILD_NUM}..."

PARENT_ID=$(gh api graphql \
  -f query="query{repository(owner:\"${OWNER}\",name:\"${REPO}\"){issue(number:${PARENT_NUM}){id}}}" \
  -q '.data.repository.issue.id' 2>&1) || true

if [[ -z "$PARENT_ID" || "$PARENT_ID" == "null" ]]; then
  echo "error: could not fetch node ID for parent #${PARENT_NUM} in ${OWNER}/${REPO}" >&2
  echo "  Check: issue exists, gh is authenticated, and you have read access." >&2
  exit 1
fi

CHILD_ID=$(gh api graphql \
  -f query="query{repository(owner:\"${OWNER}\",name:\"${REPO}\"){issue(number:${CHILD_NUM}){id}}}" \
  -q '.data.repository.issue.id' 2>&1) || true

if [[ -z "$CHILD_ID" || "$CHILD_ID" == "null" ]]; then
  echo "error: could not fetch node ID for child #${CHILD_NUM} in ${OWNER}/${REPO}" >&2
  echo "  Check: issue exists, gh is authenticated, and you have read access." >&2
  exit 1
fi

echo "Linking #${CHILD_NUM} (${CHILD_ID}) as sub-issue of #${PARENT_NUM} (${PARENT_ID})..."

RESULT=$(gh api graphql \
  -f query='mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){subIssue{number}}}' \
  -f p="$PARENT_ID" \
  -f c="$CHILD_ID" 2>&1) || {
    echo "error: GraphQL mutation failed:" >&2
    echo "$RESULT" >&2
    exit 1
  }

# Parse the returned sub-issue number to confirm success
SUB_NUMBER=$(echo "$RESULT" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d['data']['addSubIssue']['subIssue']['number'])" \
  2>/dev/null || echo "")

if [[ -n "$SUB_NUMBER" ]]; then
  echo "ok: #${CHILD_NUM} is now a sub-issue of #${PARENT_NUM}"
  exit 0
else
  # Check for GraphQL errors block
  ERRORS=$(echo "$RESULT" | python3 -c \
    "import json,sys; d=json.load(sys.stdin); errs=d.get('errors',[]); print('; '.join(e.get('message','') for e in errs))" \
    2>/dev/null || echo "")
  if [[ -n "$ERRORS" ]]; then
    echo "error: mutation returned errors: $ERRORS" >&2
  else
    echo "error: unexpected response from addSubIssue mutation:" >&2
    echo "$RESULT" >&2
  fi
  exit 1
fi
