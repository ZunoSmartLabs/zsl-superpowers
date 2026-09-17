---
name: timesheet
description: Summarize recent Claude Code sessions, Granola meetings and calendar events into timesheet bullets grouped by customer, then propose and log the matching Harvest time entries. Use when the user asks "what did I do today", wants a timesheet entry, daily standup notes, a summary of recent Claude Code sessions, or to log their day in Harvest.
---

# Timesheet

Build a copy/paste-ready Markdown summary of work over a recent window (default 12 hours) — Claude Code sessions grouped by customer, the meetings that fell inside the window, a short narrative of the day — and, where Harvest is connected, the time entries that record it. The script extracts raw session data; **Claude synthesizes the bullets** by reading the bash commands, user prompts, and files touched directly — no command parsing lives in the script.

## Resolve the script (deterministic gate)

The digest script renders the deterministic parts — each project's duration label (`Xh`/`X.Yh`/`Xm`), the window header, the customer roll-up, and each project's activity blocks — so you copy them verbatim instead of re-deriving arithmetic or timezone conversion. Resolve its path **once**; this search covers the installed plugin, a personal skill, the remote `~/.claude/skills` symlink, and this repo's own checkout:

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
- **`blocks`**: sort a project's active 5-minute buckets and split wherever two neighbours are more than 30 minutes apart; each run is one block from its first bucket's start to its last bucket's end.

## Required workflow

**Never render the final timesheet without first asking which repos to exclude.** Even on "show me the timesheet" — they will likely want to trim repos, and unsolicited renders waste their attention.

1. **List candidates.** `python3 "$DIGEST" --list` shows projects with active hours, full path and customer.

2. **Ask which to exclude.** *"Any of these to exclude before I build the timesheet?"* Wait; render nothing yet.

3. **Extract sessions.** `python3 "$DIGEST" [--exclude PATTERN] [--only PATTERN] [--merge-nested]` prints JSON. Top level: `window_start`/`window_end` (ISO, UTC), `window_header`, `window_phrase`, `customers[]` (name, `duration_label`, already ordered) and `customer_config` (the user's map, echoed). Per project: `customer`, `duration_label`, `blocks[]` (local `start`/`end`/`minutes`) and `sessions[]`, each with `user_prompts`, `files_touched`, `bash_commands` (deduped). **Copy every `duration_label`, `window_header`, `window_phrase` and block boundary verbatim.**

   `customers` is `null` when `~/.claude/timesheet-customers.json` does not exist. Then, once, propose the file from the day's projects (one entry per customer with `paths`, `domains`, `titles`, `harvest`; the user's own company as `self`; their `calendar` id), write it on their yes, and re-run. A project whose `customer` is `null` gets one question — which customer? — and an added `paths` pattern. Never keep the map in memory alone: the file is what makes the grouping repeatable.

4. **Fetch meetings (Granola).** If the Granola MCP tools exist (`mcp__claude_ai_Granola__list_meetings`, `mcp__claude_ai_Granola__get_meetings`; load them via ToolSearch when deferred), call `list_meetings` with `time_range: "custom"`, `custom_start`/`custom_end` set to the JSON's `window_start`/`window_end` verbatim, and `involvement` `{captured_by_me: true, listed_as_participant: true}`. Then `get_meetings` on the returned ids (ten per call) for the summaries.

5. **Fetch the calendar.** If the Google Calendar MCP tools exist (`mcp__claude_ai_Google_Calendar__list_events`), call it with `calendarId` = `customer_config.calendar` (primary when unset), `startTime`/`endTime` = the same window, `orderBy: "startTime"`. Calendar events are the source of truth for **when** and **how long**: they give Granola meetings their end time, add meetings Granola never saw (in-person, uncaptured), and mark context. Drop events the user declined (`self` attendee with `responseStatus: declined`); all-day and free (`transparency: transparent`) events are context for the narrative, never time entries.

   No Granola or Calendar tools → skip that step silently; never ask the user to connect them.

6. **Synthesize the timesheet.** Write outcome bullets per the rules below and print with the standard header.

7. **Propose Harvest entries.** If the Harvest MCP tools exist (`mcp__harvest__list_projects`, `mcp__harvest__list_project_assignments`, `mcp__harvest__list_time_entries`, `mcp__harvest__log_time`), build the entries per the Harvest rules below, check `list_time_entries` for the window's dates so nothing already logged is proposed twice, and print the table under the timesheet. **Never call `log_time` before the user has said yes to the table**; on yes, log each row with `spent_at`, `started_time`/`ended_time`, `project_id`, `task_id` and `notes`, then confirm the ids. No Harvest tools → end with *"Copy this to your clipboard?"* and on yes `printf '%s' "<bullets>" | pbcopy` (macOS) / `wl-copy` / `xclip -selection clipboard` / `clip` (Windows).

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
- **Meetings are outcomes.** One bullet per meeting, in start order: `**<title>** — <counterparties by organisation> · <the decision or next step>`. A Granola summary supplies the outcome; a calendar-only meeting gets its attendees' organisations and, failing anything better, its title. Summaries only — never quote transcripts, credentials, or personal contact details. A window with meetings but no commits still renders.
- **Group by customer.** Every repo and meeting sits under a `## <Customer>` heading. Repos carry `customer` from the JSON; a meeting belongs to the customer whose `domains` match its participants' email domains or whose `titles` match its title, else to `self`. Customer order is the JSON's `customers[]` order: unassigned first, then by active time, the user's own company last.
- **Close with "How the day went".** After the outcome sections, a `## How the day went` section: three to six bullets in clock order, each opening with a bold time range and thread name, telling what was investigated, decided, or built — including work that produced no commit, which is exactly what the outcome bullets drop. Two sentences per bullet at most.

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

## Harvest rules

- **One row per project block, one row per meeting.** A project's `blocks[]` become rows on its customer's `harvest.project` and `harvest.task`; each accepted meeting becomes a row on its customer's project, using `harvest.meetings_task` when set. Round block edges to the enclosing five minutes; never merge across a meeting.
- **Calendar wins on duration.** A meeting's row spans the calendar event. With no calendar event, one hour from the Granola start, flagged as assumed.
- **Notes carry the timesheet.** A row's notes are that customer's bullets for the block or the meeting's bullet, followed by the matching "How the day went" lines. No transcripts, no credentials.
- **Resolve ids, don't guess.** `list_projects` (active) for the project id, `list_project_assignments` with `assignment_type: "tasks"` for the task id; `get_account_settings` tells you whether the account takes `started_time`/`ended_time` (`wants_timestamp_timers`) or only `hours`, and whether notes are required.
- **Show gaps, don't fill them.** Time with no session, meeting or calendar evidence is listed under the table as unaccounted, for the user to fill.
- **Table columns:** `#`, project, task, time, hours, notes carry. Then a one-line total split billable / non-billable, taken from each project's `is_billable`.

## Common flags

- `--hours N` — window size, decimals OK. Default 12.
- `--list` — project picker (basename, active hours, session count, full path, customer) instead of JSON.
- `--only PATTERN` / `--exclude PATTERN` — bare patterns match basename (case-insensitive substring); patterns containing `/` match the full cwd. Repeatable; `--exclude` is ignored when `--only` is set.
- `--merge-nested` — fold projects nested under another project's cwd into the parent. Monorepos only: a repo cloned inside a plain customers folder would be renamed after the folder.
- `--include-noise` — keep ClaudeProbe / CodexBar health-check sessions. Implicit with `--only`.
- `--customers PATH` — customer map JSON; default `~/.claude/timesheet-customers.json`. `{"self": "<my company>", "calendar": "<calendar id>", "customers": {"<name>": {"paths": [...], "domains": [...], "titles": [...], "harvest": {"project": "<name>", "task": "<name>", "meetings_task": "<name>"}}}}`; `paths` use the `--only` matching rules, first matching entry wins, so list specific repos before an org-wide catch-all, and write them with a `/` (`zunosmartlabs/spark-asset-iq`) so the repo's worktrees and `.scratch` sessions inherit the customer.
- `--projects-dir PATH` — alternative to `~/.claude/projects` (rare).
