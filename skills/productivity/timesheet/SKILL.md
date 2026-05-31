---
name: timesheet
description: Summarize recent Claude Code session histories into copy/paste-ready timesheet bullets, grouped by project. Use when the user asks "what did I do today", wants a timesheet entry, daily standup notes, or a summary of recent Claude Code sessions.
---

# Timesheet

Build a copy/paste-ready Markdown summary of Claude Code work over a recent window (default 12 hours). The script extracts raw structured session data; **Claude synthesizes the bullets**. No regex parsing of shell commands lives in the script — Claude reads the bash commands, user prompts, and files-touched data directly and infers outcomes.

## Resolve the script (deterministic gate)

The digest script renders the deterministic parts of the timesheet for you — each project's duration label (`Xh`/`X.Yh`/`Xm`) and the window/timezone header line — so you copy them verbatim rather than re-deriving minute→label arithmetic or timezone conversion by hand. Resolve its absolute path **once** (this works whether the skill is the installed plugin, a personal skill, the remote `~/.claude/skills` symlink, or this repo's own checkout):

```bash
DIGEST=$({ ls "$PWD"/skills/*/timesheet/scripts/digest_sessions.py 2>/dev/null
           ls "$HOME/.claude/skills/timesheet/scripts/digest_sessions.py" 2>/dev/null
           ls -d "$HOME"/.claude/plugins/cache/zsl-superpowers/zsl/*/skills/*/timesheet/scripts/digest_sessions.py 2>/dev/null | sort -Vr; } | head -1)
[ -n "$DIGEST" ] && echo "resolved: $DIGEST" || echo "zsl-gate: digest_sessions.py unresolved — see Fallback"
```

Use `python3 "$DIGEST" …` for every invocation below.

**Fallback (if `$DIGEST` is empty):** the gate didn't resolve — find the script under your install (it lives at `skills/productivity/timesheet/scripts/digest_sessions.py` in the repo) and invoke it by absolute path. If you cannot run it at all, compute the two renders by hand with these exact rules:

- **`duration_label`** from a project's integer `active_minutes`: if `< 60`, `"{minutes}m"`; else hours `= minutes/60` → `"{int}h"` when whole, else `"{h:.1f}h"` (e.g. 270 → `4.5h`, 90 → `1.5h`, 180 → `3h`, 45 → `45m`).
- **`window_header`**: convert `window_start`/`window_end` to **local** time and render `"_{start:%Y-%m-%d %H:%M} → {end:%H:%M} {TZ}_"`. **`window_phrase`**: `"last {n} hour{s}"` — singular `hour` only when `n == 1` (e.g. `last 1 hour`, `last 12 hours`).

## Required workflow

**Never render the final timesheet without first asking which repos to exclude.** This applies even when the user says "show me the timesheet" — they will likely want to trim repos out, and unsolicited renders waste their attention.

1. **List candidates.** Show projects with active hours and full path:

   ```bash
   python3 "$DIGEST" --list
   ```

2. **Ask which to exclude.** Wait for the response. Suggested phrasing: *"Any of these to exclude before I build the timesheet?"* Do not render anything yet.

3. **Extract structured data.** Once filtered:

   ```bash
   python3 "$DIGEST" [--exclude PATTERN] [--only PATTERN] [--merge-nested]
   ```

   Output is JSON. Top level: `window_header` (the pre-rendered `_<start> → <end> <tz>_` line) and `window_phrase` (e.g. `last 12 hours`). Per project: `active_minutes`, `duration_label` (the pre-rendered `Xh`/`X.Yh`/`Xm`), and `sessions[]`; per session, `user_prompts`, `files_touched`, `bash_commands` (deduped, truncated to 300 chars). **Copy `duration_label`, `window_header`, and `window_phrase` verbatim** — don't recompute them.

4. **Synthesize the timesheet.** Read the JSON and write outcome bullets following the rules below. Print the result with the standard header.

5. **Offer to copy.** Once the user signals approval (or stays silent on a clean render), offer: *"Copy this to your clipboard?"* — and on yes, pipe the same text via `printf '%s' "<bullets>" | pbcopy` (macOS) / `wl-copy` / `xclip -selection clipboard` / `clip` (Windows).

**Skip the list+ask step only when** the user's request already names the exact projects (e.g. "timesheet for spark-asset-iq, last 4 hours"). When in doubt, list and ask.

## Synthesis rules

Build the bullets from the JSON. Apply these rules in order:

- **One bullet per delivered outcome.** Find git commits in `bash_commands` (look for `git commit -m`, `git commit -am`, heredoc forms — Claude reads these natively, no regex). Pull the commit subject as the bullet text.
- **PR opens count too.** `gh pr create --title "..."` patterns produce bullets prefixed `Opened PR: <title>`.
- **Drop redundant signals.** `gh pr merge` is implied by the prior open — don't bullet it. `git push` is plumbing — don't bullet it.
- **Drop projects with no outcomes.** If a project's sessions show only file edits with no commit / PR, omit the project entirely from the timesheet (don't write "in progress" lines).
- **Collapse WIP sequences.** If three commits all advance one outcome ("wip", "fix typo", "Add foo"), collapse into one bullet with the outcome subject.
- **Dedupe within a project.** Identical commit subjects appear once.
- **Tense.** Keep commit-message-style imperative ("Add X", "Remove Y") to match how the messages are written.

Output format (paste-ready Markdown). Group bullets under a per-repo heading, repos sorted by total active time descending. The title line is `## Timesheet — <window_phrase>` and the second line is `window_header`, both copied verbatim from the JSON. Each per-repo heading shows that project's `duration_label` next to the name (`### <name> · <duration_label>`) — copied verbatim, **not** recomputed from `active_minutes`:

```
## Timesheet — last 12 hours
_2026-05-09 12:00 → 00:00 NZST_

### spark-asset-iq · 4.5h
- Migrate Cognito user/identity pools to ap-southeast-6
- Polish READMEs with cross-references and updated seed-data layout

### zsl-superpowers · 3h
- Add timesheet skill for Claude Code session summaries
- Bump to 0.4.0 for timesheet skill
```

## Common flags

- `--hours N` — window size, decimals OK (`--hours 1.5`, `--hours 24`). Default 12.
- `--list` — print the project picker (basename, active hours, session count, full path) instead of JSON.
- `--only PATTERN` — include only projects matching PATTERN. Bare patterns match basename (case-insensitive substring); patterns containing `/` match the full cwd. Repeatable.
- `--exclude PATTERN` — exclude matching projects (same rules). Ignored if `--only` is set.
- `--merge-nested` — collapse projects whose cwd is a subdirectory of another project's cwd into the parent (useful for monorepos). Active time is unioned, not summed.
- `--include-noise` — keep ClaudeProbe / CodexBar health-check sessions that the default filter strips. Implicit when `--only` is set.
- `--projects-dir PATH` — alternative to `~/.claude/projects` (rare).
