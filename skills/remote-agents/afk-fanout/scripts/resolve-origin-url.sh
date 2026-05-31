#!/usr/bin/env bash
# resolve-origin-url.sh — normalize a git origin URL to the canonical
# https://github.com/<owner>/<repo> form that a scheduled routine's
# `session_context.sources[].git_repository.url` must carry (the URL each
# /afk-worker clone is created from). This is a secretly-deterministic step:
# given an origin there is exactly one correct https form, and a missing or
# unrecognizable origin MUST fail loudly rather than let /afk-fanout schedule a
# sourceless routine that fires with no repo to clone.
#
# Usage:
#   resolve-origin-url.sh                # reads `git remote get-url origin`
#   resolve-origin-url.sh <url>          # normalizes the given URL (tests)
#
# Accepts the common GitHub origin shapes:
#   git@github.com:owner/repo.git        (SSH)
#   ssh://git@github.com/owner/repo.git  (SSH URL)
#   https://github.com/owner/repo.git    (HTTPS)
#   https://github.com/owner/repo
# and prints `https://github.com/owner/repo` (trailing .git stripped).
#
# Exit 0 + the URL on success. Exit 1 + a `resolve-origin-url:` reason on stderr
# (printing nothing to stdout) when the origin is missing, empty, or not a
# parseable github.com owner/repo — the loud failure the pre-flight relies on.
set -uo pipefail

err() {
  echo "resolve-origin-url: $1" >&2
  exit 1
}

# An explicitly-passed argument (even empty) is treated as the origin to validate;
# only a genuinely absent argument falls back to `git remote get-url origin`. This
# keeps `resolve-origin-url.sh ""` a loud failure (garbled origin) rather than
# silently resolving the surrounding repo's real origin.
if [ "$#" -ge 1 ]; then
  RAW="$1"
else
  RAW="$(git remote get-url origin 2>/dev/null)" \
    || err "no 'origin' remote — workers have nothing to clone; configure origin and retry"
fi
[ -n "$RAW" ] || err "origin URL is empty — workers have nothing to clone"

# Strip an optional scheme + userinfo, normalize the github.com host separator
# (':' for scp-style SSH, '/' for URL forms) to a single owner/repo capture.
path=""
case "$RAW" in
  git@github.com:*) path="${RAW#git@github.com:}" ;;
  ssh://git@github.com/*) path="${RAW#ssh://git@github.com/}" ;;
  ssh://github.com/*) path="${RAW#ssh://github.com/}" ;;
  https://github.com/*) path="${RAW#https://github.com/}" ;;
  http://github.com/*) path="${RAW#http://github.com/}" ;;
  git://github.com/*) path="${RAW#git://github.com/}" ;;
  *) err "origin '$RAW' is not a recognizable github.com URL — refusing to schedule a sourceless routine" ;;
esac

path="${path%/}"         # strip a stray trailing slash first…
path="${path%.git}"      # …so a trailing ".git/" still loses its .git

# Must be exactly owner/repo — both non-empty, no extra path segments.
case "$path" in
  */*/*) err "origin '$RAW' has extra path segments; expected owner/repo" ;;
  */*)
    owner="${path%%/*}"
    repo="${path#*/}"
    [ -n "$owner" ] && [ -n "$repo" ] \
      || err "origin '$RAW' is missing an owner or repo segment"
    ;;
  *) err "origin '$RAW' is not in owner/repo form" ;;
esac

echo "https://github.com/${owner}/${repo}"
