#!/usr/bin/env bash
# test_set_status_options.sh — assertion runner for set-status-options.sh.
# Pure bash, no framework: each check prints PASS/FAIL; non-zero exit on any
# failure. Tests the deterministic part — the mutation the script emits — without
# hitting the network (--emit-query), so it runs offline in CI.
#
# Includes the "fails the old prose way" case (the contract requirement): the
# emitted mutation must NOT contain `projectId`, because the current GitHub
# GraphQL schema rejects it on UpdateProjectV2FieldInput. A regression that
# re-adds projectId (the bug this script exists to prevent) fails this test
# instead of failing live, mid-setup, for the next user.
#
# Run: bash skills/engineering/setup-zsl-superpowers/scripts/tests/test_set_status_options.sh
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../set-status-options.sh"

pass=0 fail=0
ok() {
  echo "PASS: $1"
  pass=$((pass + 1))
}
bad() {
  echo "FAIL: $1"
  fail=$((fail + 1))
}

QUERY="$(bash "$SCRIPT" --emit-query 2>/dev/null)"

contains() {
  if printf '%s' "$QUERY" | grep -qF "$1"; then ok "query contains: $1"; else bad "query missing: $1"; fi
}
absent() {
  if printf '%s' "$QUERY" | grep -qF "$1"; then bad "query must NOT contain: $1"; else ok "query omits: $1"; fi
}

# ── correct mutation shape ────────────────────────────────────────────────────
contains "updateProjectV2Field"
contains "singleSelectOptions"
contains '$fieldId: ID!'
contains "fieldId: \$fieldId"

# ── all five canonical options present ────────────────────────────────────────
for opt in "Backlog" "Ready" "In progress" "In review" "Done"; do
  contains "\"$opt\""
done

# ── fails-the-prose-way: projectId must be gone (schema rejects it) ───────────
absent "projectId"

# ── missing field id is a loud failure (not a silent no-op) ───────────────────
out="$(bash "$SCRIPT" 2>/dev/null)"
rc=$?
if [ "$rc" -ne 0 ] && [ -z "$out" ]; then ok "rejects: no field id"; else bad "should reject: no field id (rc=$rc out='$out')"; fi

echo
echo "set-status-options.sh: $pass passed, $fail failed"
[ "$fail" -gt 0 ] && exit 1 || true
echo "OK"
