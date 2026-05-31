#!/usr/bin/env bash
# write-afk-entry.sh — serialize the INITIAL afk-runs ledger entry + manifest row
# for one scheduled PRD, to the exact schema shared across /afk-fanout, /afk-worker,
# and /morning-review (the 4-file remote-agents contract; schema lives in
# /afk-fanout's SKILL.md § "The afk-runs ledger branch"). Given the scheduled facts
# there is exactly one correct serialization and one correct path, so this owns the
# entry shape rather than re-typing it from prose in three places.
#
# Writes, under <root>/<date>/ (root defaults to .afk-runs, relative to CWD — run it
# with the afk-runs branch checked out):
#   _scheduled.md     append/replace the manifest row for this feature-num
#   <feature-num>.md  the initial per-PRD entry (claim: scheduled, outcome: pending)
#
# The date is the EVENING /afk-fanout ran (post-midnight slots stay under it), so it
# is passed in explicitly — the script never derives it from the clock.
#
# Exit 0 on success; exit 1 on any missing/invalid argument (writes nothing).
set -uo pipefail

DATE="" FEATURE_NUM="" TITLE="" SLOT="" TRIGGER_ID="" ROUTINE_URL="" ROOT=".afk-runs"
SEP=" · " # space-middot-space — the exact manifest field separator

err() {
  echo "write-afk-entry.sh: $1" >&2
  exit 1
}

usage() {
  cat >&2 <<'EOF'
usage: write-afk-entry.sh --date YYYY-MM-DD --feature-num N --title TXT \
                          --slot ISO-8601-UTC --trigger-id ID --routine-url URL \
                          [--root .afk-runs]
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --date)
      DATE="${2-}"
      shift 2 || err "missing value for --date"
      ;;
    --feature-num)
      FEATURE_NUM="${2-}"
      shift 2 || err "missing value for --feature-num"
      ;;
    --title)
      TITLE="${2-}"
      shift 2 || err "missing value for --title"
      ;;
    --slot)
      SLOT="${2-}"
      shift 2 || err "missing value for --slot"
      ;;
    --trigger-id)
      TRIGGER_ID="${2-}"
      shift 2 || err "missing value for --trigger-id"
      ;;
    --routine-url)
      ROUTINE_URL="${2-}"
      shift 2 || err "missing value for --routine-url"
      ;;
    --root)
      ROOT="${2-}"
      shift 2 || err "missing value for --root"
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *) err "unknown arg: $1" ;;
  esac
done

# Validate — write nothing unless every required field is present and well-formed.
[ -n "$DATE" ] || {
  usage
  err "--date is required"
}
[ -n "$FEATURE_NUM" ] || err "--feature-num is required"
[ -n "$TITLE" ] || err "--title is required"
[ -n "$SLOT" ] || err "--slot is required"
[ -n "$TRIGGER_ID" ] || err "--trigger-id is required"
[ -n "$ROUTINE_URL" ] || err "--routine-url is required"
case "$DATE" in
  [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) : ;;
  *) err "--date must be YYYY-MM-DD (got: $DATE)" ;;
esac

DIR="$ROOT/$DATE"
mkdir -p "$DIR"

# Manifest row — append, replacing any existing row for this feature-num so a second
# /afk-fanout run the same evening doesn't duplicate it. Rows are "<num>·<title>·…".
MANIFEST="$DIR/_scheduled.md"
ROW="${FEATURE_NUM}${SEP}${TITLE}${SEP}${SLOT}${SEP}${TRIGGER_ID}${SEP}${ROUTINE_URL}"
if [ -f "$MANIFEST" ]; then
  grep -v "^${FEATURE_NUM}${SEP}" "$MANIFEST" >"$MANIFEST.tmp" 2>/dev/null || true
  mv "$MANIFEST.tmp" "$MANIFEST"
fi
printf '%s\n' "$ROW" >>"$MANIFEST"

# Initial per-PRD entry — fixed field set, fixed initial values. claim: scheduled and
# outcome: pending (NOT outcome: scheduled — outcome tracks the run, claim tracks the
# lifecycle). reconciled: - so /morning-review sees it as un-reconciled.
ENTRY="$DIR/${FEATURE_NUM}.md"
cat >"$ENTRY" <<EOF
PRD: ${FEATURE_NUM} — ${TITLE}
trigger: ${TRIGGER_ID}   slot: ${SLOT}   routine: ${ROUTINE_URL}
claim: scheduled
outcome: pending
pr: -
slices-closed: -
run-ts: -
reconciled: -
EOF

echo "wrote $ENTRY and manifest row in $MANIFEST"
