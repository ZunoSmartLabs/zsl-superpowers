#!/usr/bin/env bash
# set-status-options.sh — replace a GitHub Projects v2 single-select `Status`
# field's options with the five canonical states the engineering skills map onto
# (`Backlog`, `Ready`, `In progress`, `In review`, `Done`). This is a
# secretly-deterministic step: the `updateProjectV2Field` mutation has exactly
# one correct shape, and the obvious prose version drifts — the current GitHub
# GraphQL schema REJECTS a `projectId` argument on `UpdateProjectV2FieldInput`
# (`InputObject 'UpdateProjectV2FieldInput' doesn't accept argument 'projectId'`),
# so a hand-typed mutation that includes it fails mid-setup. This script is the
# single source of the correct mutation (fieldId + singleSelectOptions only).
#
# Usage:
#   set-status-options.sh <status-field-id>   # run the mutation; print "id name" per option
#   set-status-options.sh --emit-query        # print the GraphQL query only (no gh call; tests/dry-run)
#
# Exit 0 on success. Exit 1 + a `set-status-options:` reason on stderr when the
# field id is missing or the mutation fails.
set -uo pipefail

err() {
  echo "set-status-options: $1" >&2
  exit 1
}

# The canonical mutation. Note: NO `projectId` — only `fieldId` is accepted by
# UpdateProjectV2FieldInput. Changing the option set here is the one place to do
# it; the SKILL.md and project-board.md mapping must stay in lockstep.
read -r -d '' QUERY <<'GQL' || true
mutation($fieldId: ID!) {
  updateProjectV2Field(input: {
    fieldId: $fieldId
    singleSelectOptions: [
      {name: "Backlog",     color: GRAY,   description: ""}
      {name: "Ready",       color: BLUE,   description: ""}
      {name: "In progress", color: YELLOW, description: ""}
      {name: "In review",   color: PURPLE, description: ""}
      {name: "Done",        color: GREEN,  description: ""}
    ]
  }) {
    projectV2Field {
      ... on ProjectV2SingleSelectField { id options { id name } }
    }
  }
}
GQL

if [ "${1:-}" = "--emit-query" ]; then
  printf '%s\n' "$QUERY"
  exit 0
fi

FIELD_ID="${1:-}"
[ -n "$FIELD_ID" ] || err "missing Status field id (PVTSSF_…) — pass it as the first argument"

OUT="$(gh api graphql -f query="$QUERY" -F fieldId="$FIELD_ID" 2>&1)" \
  || err "mutation failed: $OUT"

# Emit "optionId optionName" lines so the caller can capture the new option IDs
# for docs/agents/project-board.md without a second field-list round-trip.
echo "$OUT" | grep -oE '"id":"[^"]+","name":"[^"]+"' \
  | sed -E 's/"id":"([^"]+)","name":"([^"]+)"/\1 \2/' \
  || err "could not parse option ids from response: $OUT"
