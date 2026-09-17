---
name: timesheet
description: Summarize recent Claude Code session histories, plus Granola meetings from the same window, into copy/paste-ready timesheet bullets grouped by project. Use when the user asks "what did I do today", wants a timesheet entry, daily standup notes, or a summary of recent Claude Code sessions.
---

# Timesheet

Build a copy/paste-ready Markdown summary of work over a recent window (default 12 hours): Claude Code sessions grouped by project, plus the Granola meetings that fell inside the window. The script extracts raw session data; **Claude synthesizes the bullets** by reading the bash commands, user prompts, and files touched directly — no command parsing lives in the script.

## Resolve the script (deterministic gate)

The digest script renders the deterministic parts — each project's duration label (`Xh`/`X.Yh`/`Xm`) and the window header — so you copy them verbatim instead of re-deriving arithmetic or timezone conversion. Resolve its path **once**; this search covers the installed plugin, a personal skill, the remote `~/.claude/skills` symlink, and this repo's own checkout:

```bash
DIGEST=$({ ls "$PWD"/skills/*/timesheet/scripts/digest_sessions.py 2>/dev/null
           ls "$HOME/.claude/skills/timesheet/scripts/digest_sessions.py" 2>/dev/null
           ls -d "$HOME"/.claude/plugins/cache/zsl-superpowers/zsl/*/skills/*/timesheet/scripts/digest_sessions.py 2>/dev/null | sort -Vr; } | head -1)
[ -n "$DIGEST" ] && echo "resolved: $DIGEST" || echo "zsl-gate: digest_sessions.py unresolved — see Fallback"
```

Use `python3 "$DIGEST" …` for every invocation below.

**Fallback (if `$DIGEST` is empty):** find the script under your install (`skills/productivity/timesheet/scripts/digest_sessions.py` in the repo) and invoke it by absolute path. If you cannot run it at all, compute the renders by hand:

- **`duration_label`** from integer `active_minutes`: `< 60` → `"{minutes}m"`; else `h = minutes/60` → `"{int}h"` when whole, else `"{h:.1f}h"` (270 → `4.5h`, 90 → `1.5h`, 180 → `3h`, 45 → `45m`).
- **`window_header`**: `window_start`/`window_end` in **local** time as `"_{start:%Y-%m-%d %H:%M} → {end:%H:%M} {TZ}_"`. **`window_phrase`**: `"last {n} hour{s}"`, singular only when `n == 1`.

## Required workflow

**Never render the final timesheet without first asking which repos to exclude.** Even on "show me the timesheet" — they will likely want to trim repos, and unsolicited renders waste their attention.

1. **List candidates.** `python3 "$DIGEST" --list` shows projects with active hours and full path.

2. **Ask which to exclude.** *"Any of these to exclude before I build the timesheet?"* Wait; render nothing yet.

3. **Extract sessions.** `python3 "$DIGEST" [--exclude PATTERN] [--only PATTERN] [--merge-nested]` prints JSON. Top level: `window_start`/`window_end` (ISO, UTC), `window_header`, `window_phrase`, `customers[]` (name, `duration_label`, already ordered) and `customer_config` (the user's map, echoed). Per project: `customer`, `duration_label` and `sessions[]`, each with `user_prompts`, `files_touched`, `bash_commands` (deduped). **Copy every `duration_label`, `window_header`, and `window_phrase` verbatim.**

   `customers` is `null` when `~/.claude/timesheet-customers.json` does not exist. Then, once, propose the file from the day's projects (one entry per customer with `paths`, `domains`, `titles`; the user's own company as `self`), write it on their yes, and re-run. A project whose `customer` is `null` gets one question — which customer? — and an added `paths` pattern. Never keep the map in memory alone: the file is what makes the grouping repeatable.

4. **Fetch meetings (Granola).** If the Granola MCP tools exist (`mcp__claude_ai_Granola__list_meetings`, `mcp__claude_ai_Granola__get_meetings`; load them via ToolSearch when deferred), call `list_meetings` with `time_range: "custom"`, `custom_start`/`custom_end` set to the JSON's `window_start`/`window_end` verbatim, and `involvement` `{captured_by_me: true, listed_as_participant: true}`. Then `get_meetings` on the returned ids (ten per call) for the summaries. No Granola tools → skip this step silently; never ask the user to connect it.

5. **Synthesize the timesheet.** Write outcome bullets per the rules below and print with the standard header.

6. **Offer to copy.** Once the user approves (or stays silent on a clean render): *"Copy this to your clipboard?"* On yes, `printf '%s' "<bullets>" | pbcopy` (macOS) / `wl-copy` / `xclip -selection clipboard` / `clip` (Windows).

**Skip the list+ask step only when** the request already names the exact projects ("timesheet for spark-asset-iq, last 4 hours"). When in doubt, list and ask.

## Synthesis rules

Apply in order:

- **One bullet per delivered outcome.** Find git commits in `bash_commands` (`git commit -m`, `-am`, heredoc forms — read natively, no regex). The commit subject is the bullet text.
- **PR opens count too.** `gh pr create --title "..."` → `Opened PR: <title>`.
- **Drop redundant signals.** `gh pr merge` is implied by the prior open; `git push` is plumbing. Neither gets a bullet.
- **Drop projects with no outcomes.** Sessions with only edits and no commit / PR are omitted entirely — no "in progress" lines.
- **Collapse WIP sequences.** Commits that all advance one outcome ("wip", "fix typo", "Add foo") become one bullet with the outcome subject.
- **Dedupe within a project.** Identical subjects appear once.
- **Tense.** Keep the commit messages' imperative ("Add X", "Remove Y").
- **Meetings are outcomes.** One bullet per meeting, in start order: `**<title>** — <counterparties by organisation> · <the decision or next step>`. Summaries only — never quote transcripts, credentials, or personal contact details. A window with meetings but no commits still renders.
- **Group by customer.** Every repo and meeting sits under a `## <Customer>` heading. Repos carry `customer` from the JSON; a meeting belongs to the customer whose `domains` match its participants' email domains or whose `titles` match its title, else to `self`. Customer order is the JSON's `customers[]` order: unassigned first, then by active time, the user's own company last.
- **Close with "How the day went".** After the outcome sections, a `### How the day went` section: three to six bullets in clock order, each opening with a bold time range and thread name, telling what was investigated, decided, or built — including work that produced no commit, which is exactly what the outcome bullets drop. Two sentences per bullet at most.

Output format: title line `# Timesheet — <window_phrase>`, second line `window_header`, then one `## <Customer>` block per customer holding its repos (`### <name> · <duration_label>`, active time descending) and its `### Meetings · <count>` (omit when none), then a single `## How the day went` for the whole window. `window_phrase`, `window_header` and every `duration_label` are copied verbatim, never recomputed:

```
# Timesheet — last 12 hours
_2026-05-09 12:00 → 00:00 NZST_

## Spark

### spark-asset-iq · 4.5h
- Migrate Cognito user/identity pools to ap-southeast-6
- Polish READMEs with cross-references and updated seed-data layout

### Meetings · 1
- **AssetIQ platform review** — Cloudflare, Spark · Cloudflare to send a platform blueprint; next step is a working AI demo for Spark leadership

## ZunoSmart Labs

### zsl-superpowers · 3h
- Add timesheet skill for Claude Code session summaries

## How the day went
- **09:00 to 12:30, Cognito move.** Migrated both pools to the new region and re-pointed the SPA. The identity pool needed its trust policy rewritten by hand.
- **14:00, platform review.** Demoed the estate page to Cloudflare; Workers and Durable Objects flagged as a fit for the API layer.
```

## Common flags

- `--hours N` — window size, decimals OK. Default 12.
- `--list` — project picker (basename, active hours, session count, full path) instead of JSON.
- `--only PATTERN` / `--exclude PATTERN` — bare patterns match basename (case-insensitive substring); patterns containing `/` match the full cwd. Repeatable; `--exclude` is ignored when `--only` is set.
- `--merge-nested` — fold projects nested under another project's cwd into the parent. Monorepos only: a repo cloned inside a plain customers folder would be renamed after the folder.
- `--include-noise` — keep ClaudeProbe / CodexBar health-check sessions. Implicit with `--only`.
- `--customers PATH` — customer map JSON; default `~/.claude/timesheet-customers.json`. `{"self": "<my company>", "customers": {"<name>": {"paths": [...], "domains": [...], "titles": [...]}}}`; `paths` use the `--only` matching rules, first matching entry wins, so list specific repos before an org-wide catch-all, and write them with a `/` (`zunosmartlabs/spark-asset-iq`) so the repo's worktrees and `.scratch` sessions inherit the customer.
- `--projects-dir PATH` — alternative to `~/.claude/projects` (rare).
