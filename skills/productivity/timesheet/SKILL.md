---
name: timesheet
description: Summarize recent Claude Code session histories into copy/paste-ready timesheet bullets, grouped by project. Use when the user asks "what did I do today", wants a timesheet entry, daily standup notes, or a summary of recent Claude Code sessions.
---

# Timesheet

Build a copy/paste-ready Markdown summary of Claude Code work over a recent window (default 12 hours). The script extracts raw structured session data; **Claude synthesizes the bullets**. No regex parsing of shell commands lives in the script — Claude reads the bash commands, user prompts, and files-touched data directly and infers outcomes.

The script is at `skills/productivity/timesheet/scripts/digest_sessions.py`. From other repos, invoke by absolute path.

## Required workflow

**Never render the final timesheet without first asking which repos to exclude.** This applies even when the user says "show me the timesheet" — they will likely want to trim repos out, and unsolicited renders waste their attention.

1. **List candidates.** Show projects with active hours and full path:

   ```bash
   ./scripts/digest_sessions.py --list
   ```

2. **Ask which to exclude.** Wait for the response. Suggested phrasing: *"Any of these to exclude before I build the timesheet?"* Do not render anything yet.

3. **Extract structured data.** Once filtered:

   ```bash
   ./scripts/digest_sessions.py [--exclude PATTERN] [--only PATTERN] [--merge-nested]
   ```

   Output is JSON: per project, `active_minutes` and `sessions[]`; per session, `user_prompts`, `files_touched`, `bash_commands` (deduped, truncated to 300 chars).

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

Output format (paste-ready Markdown). Group bullets under a per-repo heading, repos sorted by total active time descending. Include the project's `active_minutes` next to the heading as `Xh` / `Xm` so the timesheet entry shows time-per-project at a glance:

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
