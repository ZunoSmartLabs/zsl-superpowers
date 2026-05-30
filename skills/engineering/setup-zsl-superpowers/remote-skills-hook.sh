#!/bin/bash
set -euo pipefail

# Make the ZSL Superpowers skills available to Claude Code on the web.
#
# Written into a repo by `/setup-zsl-superpowers` (Section F) and wired as a
# SessionStart hook. Locally you already have the skills via
# `/plugin install zsl@zsl-superpowers`, so this hook is a deliberate no-op
# outside the remote container — it only fires when CLAUDE_CODE_REMOTE=true.
#
# This is what lets the overnight loop (`/afk-fanout` → `/afk-worker`) work:
# a scheduled routine fires in a fresh remote session that has no plugins
# installed, so without this hook `/afk-worker` (and the skills it drives)
# would not resolve. Plugin availability is NOT configurable per claude.ai
# environment — the repo provisions its own skills here instead.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

REPO_URL="https://github.com/ZunoSmartLabs/zsl-superpowers"
REF="${ZSL_SUPERPOWERS_REF:-main}"
CACHE_DIR="${HOME}/.claude/cache/zsl-superpowers"
SKILLS_DIR="${HOME}/.claude/skills"

mkdir -p "$(dirname "$CACHE_DIR")" "$SKILLS_DIR"

if [ -d "$CACHE_DIR/.git" ]; then
  git -C "$CACHE_DIR" fetch --depth 1 origin "$REF" >/dev/null 2>&1
  git -C "$CACHE_DIR" checkout -q FETCH_HEAD
else
  git clone --depth 1 --branch "$REF" "$REPO_URL" "$CACHE_DIR" >/dev/null 2>&1
fi

linked=0
skipped=0
# remote-agents is load-bearing for the overnight loop — /afk-worker lives there.
for category in engineering productivity misc remote-agents; do
  category_dir="$CACHE_DIR/skills/$category"
  [ -d "$category_dir" ] || continue
  for skill_path in "$category_dir"/*/; do
    [ -d "$skill_path" ] || continue
    skill_name="$(basename "$skill_path")"
    target="$SKILLS_DIR/$skill_name"

    if [ -L "$target" ]; then
      rm "$target"
    elif [ -e "$target" ]; then
      # Real directory already there (local override) — leave it alone.
      skipped=$((skipped + 1))
      continue
    fi

    ln -s "${skill_path%/}" "$target"
    linked=$((linked + 1))
  done
done

echo "zsl-superpowers @ ${REF}: linked ${linked} skills, skipped ${skipped} (local overrides)"
