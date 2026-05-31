#!/usr/bin/env bash
# Tests for write-afk-entry.sh. Pure shell. Asserts the exact ledger schema +
# manifest separator, including the two ways the prose render goes wrong: a comma
# instead of the " · " separator, and outcome: scheduled instead of outcome: pending.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRITER="$SCRIPT_DIR/write-afk-entry.sh"
SEP=" · "
fails=0

note() { printf '  %s\n' "$1"; }
ok() { printf 'ok   - %s\n' "$1"; }
bad() {
  printf 'FAIL - %s\n' "$1"
  fails=$((fails + 1))
}
assert_eq() {
  if [ "$2" = "$3" ]; then ok "$1"; else
    bad "$1"
    note "expected: $2"
    note "actual:   $3"
  fi
}
assert_contains() {
  case "$2" in
    *"$3"*) ok "$1" ;;
    *)
      bad "$1"
      note "missing: $3"
      note "in:      $2"
      ;;
  esac
}
assert_not_contains() {
  case "$2" in
    *"$3"*)
      bad "$1"
      note "unexpectedly found: $3"
      ;;
    *) ok "$1" ;;
  esac
}

run_golden() {
  bash "$WRITER" \
    --date 2026-05-31 --feature-num 023 --title "Billing webhooks retry" \
    --slot "2026-06-01T08:07:00Z" --trigger-id trg_abc \
    --routine-url "https://claude.ai/code/routines/trg_abc" --root "$1"
}

# --- 1. Golden write.
work="$(mktemp -d)"
out="$(run_golden "$work")"
code=$?
assert_eq "golden: exit 0" 0 "$code"
entry="$work/2026-05-31/023.md"
manifest="$work/2026-05-31/_scheduled.md"
[ -f "$entry" ] && ok "golden: entry file written" || bad "golden: entry file written"
[ -f "$manifest" ] && ok "golden: manifest written" || bad "golden: manifest written"

entry_body="$(cat "$entry")"
assert_contains "entry: PRD header" "$entry_body" "PRD: 023 — Billing webhooks retry"
assert_contains "entry: trigger/slot/routine line" "$entry_body" "trigger: trg_abc   slot: 2026-06-01T08:07:00Z   routine: https://claude.ai/code/routines/trg_abc"
assert_contains "entry: claim scheduled" "$entry_body" "claim: scheduled"
assert_contains "entry: outcome pending" "$entry_body" "outcome: pending"
assert_contains "entry: pr dash" "$entry_body" "pr: -"
assert_contains "entry: reconciled dash" "$entry_body" "reconciled: -"

# --- 2. Fails-the-prose-way (a): the separator is " · ", never a comma.
manifest_body="$(cat "$manifest")"
assert_contains "manifest: middot separator" "$manifest_body" "023${SEP}Billing webhooks retry${SEP}2026-06-01T08:07:00Z${SEP}trg_abc${SEP}https://claude.ai/code/routines/trg_abc"
assert_not_contains "manifest: no comma-separated row" "$manifest_body" "023, Billing"

# --- 3. Fails-the-prose-way (b): outcome is pending, NOT scheduled (don't mirror claim).
assert_not_contains "entry: outcome is not 'scheduled'" "$entry_body" "outcome: scheduled"
rm -rf "$work"

# --- 4. Post-midnight slot stays under the passed --date (no roll to next day).
work="$(mktemp -d)"
bash "$WRITER" --date 2026-05-31 --feature-num 058 --title "OAuth device flow" \
  --slot "2026-06-01T00:07:00Z" --trigger-id trg_x --routine-url "https://x" --root "$work" >/dev/null
[ -f "$work/2026-05-31/058.md" ] && ok "post-midnight: filed under fanout date" || bad "post-midnight: filed under fanout date"
[ -d "$work/2026-06-01" ] && bad "post-midnight: must NOT roll to next day" || ok "post-midnight: did not roll to next day"
rm -rf "$work"

# --- 5. Idempotency: a second run for the same feature-num replaces its manifest row.
work="$(mktemp -d)"
run_golden "$work" >/dev/null
run_golden "$work" >/dev/null
count="$(grep -c '^023' "$work/2026-05-31/_scheduled.md")"
assert_eq "idempotent: manifest row appears exactly once" 1 "$count"
rm -rf "$work"

# --- 6. Validation boundary: missing required arg → exit 1, writes nothing.
work="$(mktemp -d)"
out="$(bash "$WRITER" --date 2026-05-31 --feature-num 1 --title T --slot S --trigger-id ID --root "$work" 2>&1)"
code=$?
assert_eq "missing-arg: exit 1" 1 "$code"
assert_contains "missing-arg: message" "$out" "--routine-url is required"
[ -z "$(ls -A "$work")" ] && ok "missing-arg: wrote nothing" || bad "missing-arg: wrote nothing"
rm -rf "$work"

# --- 7. Validation boundary: malformed date → exit 1.
work="$(mktemp -d)"
out="$(bash "$WRITER" --date 2026-5-1 --feature-num 1 --title T --slot S --trigger-id ID --routine-url U --root "$work" 2>&1)"
code=$?
assert_eq "bad-date: exit 1" 1 "$code"
assert_contains "bad-date: message" "$out" "must be YYYY-MM-DD"
rm -rf "$work"

echo
if [ "$fails" -eq 0 ]; then
  echo "write-afk-entry.sh: all tests passed"
  exit 0
else
  echo "write-afk-entry.sh: $fails assertion(s) failed"
  exit 1
fi
