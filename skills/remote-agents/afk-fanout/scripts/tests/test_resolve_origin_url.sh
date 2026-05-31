#!/usr/bin/env bash
# test_resolve_origin_url.sh — assertion runner for resolve-origin-url.sh.
# Pure bash, no framework: each check prints PASS/FAIL; non-zero exit on any failure.
# Includes the "fails the old prose way" cases (the contract requirement): a
# garbled / non-github origin MUST fail loudly (exit 1, nothing on stdout) rather
# than be passed through verbatim into a routine's sources — the sourceless-routine
# bug this gate exists to prevent.
#
# Run: bash skills/remote-agents/afk-fanout/scripts/tests/test_resolve_origin_url.sh
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../resolve-origin-url.sh"

pass=0 fail=0
ok() {
  echo "PASS: $1"
  pass=$((pass + 1))
}
bad() {
  echo "FAIL: $1"
  fail=$((fail + 1))
}

# assert: input normalizes to expected https URL
expect_url() {
  got="$(bash "$SCRIPT" "$1" 2>/dev/null)"
  if [ "$got" = "$2" ]; then ok "$1 → $2"; else bad "$1 → '$got' (wanted '$2')"; fi
}

# assert: input is rejected (exit 1) AND prints nothing on stdout
expect_fail() {
  got="$(bash "$SCRIPT" "$1" 2>/dev/null)"
  rc=$?
  if [ "$rc" -ne 0 ] && [ -z "$got" ]; then ok "rejects: $1"; else bad "should reject: $1 (rc=$rc out='$got')"; fi
}

EXPECT="https://github.com/ZunoSmartLabs/zsl-superpowers"

# ── normalization: every accepted shape lands on the same canonical https URL ──
expect_url "git@github.com:ZunoSmartLabs/zsl-superpowers.git" "$EXPECT"
expect_url "git@github.com:ZunoSmartLabs/zsl-superpowers" "$EXPECT"
expect_url "ssh://git@github.com/ZunoSmartLabs/zsl-superpowers.git" "$EXPECT"
expect_url "https://github.com/ZunoSmartLabs/zsl-superpowers.git" "$EXPECT"
expect_url "https://github.com/ZunoSmartLabs/zsl-superpowers" "$EXPECT"
expect_url "https://github.com/ZunoSmartLabs/zsl-superpowers/" "$EXPECT"
expect_url "https://github.com/ZunoSmartLabs/zsl-superpowers.git/" "$EXPECT"

# ── fails-the-prose-way: must fail loudly, never pass garbage through ──────────
expect_fail ""                                            # empty origin
expect_fail "git@gitlab.com:owner/repo.git"               # not github
expect_fail "https://github.com/owner"                    # missing repo segment
expect_fail "https://github.com/owner/repo/extra"         # extra path segments
expect_fail "not-a-url"                                    # unparseable

echo
echo "resolve-origin-url.sh: $pass passed, $fail failed"
[ "$fail" -gt 0 ] && exit 1 || true
echo "OK"
