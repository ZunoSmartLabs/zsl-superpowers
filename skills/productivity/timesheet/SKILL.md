---
name: timesheet
description: Summarize recent Claude Code session histories into copy/paste-ready timesheet bullets, grouped by project with active hours. Use when the user asks "what did I do today", wants a timesheet entry, daily standup notes, or a summary of recent Claude Code sessions.
---

# Timesheet

Build a copy/paste-ready Markdown summary of Claude Code work over a recent window (default 12 hours). Each project gets a heading with active hours, then outcome bullets pulled from commit subjects and PR titles.

The script is at `skills/productivity/timesheet/scripts/digest_sessions.py`. From other repos, invoke by absolute path.

## Required workflow: list → confirm → render

**Never render the final timesheet without first asking which repos to exclude.** This applies even when the user says "show me the timesheet", "what does the output look like", or any other phrasing that sounds like a direct request — the user will likely want to trim repos out, and unsolicited renders waste their attention.

Steps:

1. **List candidates.** Show the user which projects had Claude Code activity in the window:

   ```bash
   ./scripts/digest_sessions.py --list
   ```

2. **Ask which to exclude.** Wait for the response. Suggested phrasing: *"Any of these to exclude before I render the timesheet?"* Do not render anything yet — even a "preview".

3. **Render filtered.** Once the user has answered:

   - Include all → `./scripts/digest_sessions.py`
   - Exclude some → `--exclude PATTERN` (repeatable)
   - Only some → `--only PATTERN` (repeatable)

4. **Offer to copy to clipboard.** After the rendered timesheet looks good (user signals approval, asks no further changes, or stays silent), offer: *"Copy this to your clipboard?"* — and on yes, re-run the same invocation with `--copy` appended. The script handles `pbcopy` / `xclip` / `wl-copy` / `clip` automatically. Skip the offer if the user is clearly still iterating on content.

**Skip the list+ask step only when** the user's request already names the exact projects in or out (e.g. "timesheet for spark-asset-iq, last 4 hours", "timesheet excluding terraform-aws"). When in doubt, list and ask.

## Common flags

- `--hours N` — window size, decimals OK (`--hours 1.5`, `--hours 24`). Default 12.
- `--list` — print just the project list, no outcome bullets.
- `--only PATTERN` — include only projects matching PATTERN. Bare patterns match basename (case-insensitive substring); patterns containing `/` match the full cwd. Repeatable.
- `--exclude PATTERN` — exclude matching projects (same rules). Ignored if `--only` is set.
- `--merge-nested` — collapse projects whose cwd is a subdirectory of another project's cwd into the parent (useful for monorepos where sessions in `packages/api/foo` would otherwise list separately from the parent repo). Active time is unioned, not summed — no double-counting.
- `--include-noise` — keep ClaudeProbe / CodexBar health-check sessions that the default filter strips. Implicit when `--only` is set.
- `--copy` — also pipe the rendered output to the system clipboard. Tries `pbcopy` (macOS), `wl-copy` / `xclip` / `xsel` (Linux), `clip` (Windows). Exits with code 3 if no tool is available.
- `--format json` — structured digest with full prompts, files, raw commands. Use only when the default Markdown doesn't capture the work and you need to synthesize prose bullets manually.

## Output shape

```
## Timesheet — last 12 hours
_2026-05-08 11:45 → 23:45 NZST_

- spark-asset-iq · Opened PR: Migrate Cognito to ap-southeast-6
- zsl-superpowers · Remove scaffold-exercises skill
- zsl-superpowers · Add prototype skill for throwaway design exploration
- zsl-superpowers · Document done/ archive convention for local issue tracker
```

Each bullet is one delivered outcome — a commit subject or a PR title — prefixed by the repo name. Bullets are deduped per project. Projects with no real outcomes (only exploration, in-progress files, or pre-window pushes) are dropped from the timesheet entirely.

Active hours per project (5-minute event buckets, unioned, not summed) are still computed internally — they show up in `--list` and in `--format json` for downstream synthesis.

## When to synthesize manually

The default Markdown is mechanical — it surfaces what already has a clear written outcome. Re-run with `--format json` and write your own bullets when:

- Multiple commits all advance one outcome (collapse them: three "WIP" commits → one "Implemented X").
- Commit messages are vague or noisy (`fix typo`, `wip`) and the user prompts reveal the real intent.
- The window only caught files-touched / pushes with no commit subjects to anchor on.

When you do synthesize, follow the same rules: outcomes not activity, one bullet per outcome, past tense, tight (≤ 15 words).
