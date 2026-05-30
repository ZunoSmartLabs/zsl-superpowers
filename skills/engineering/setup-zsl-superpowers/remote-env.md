# Remote agent environment

Per-repo config for the overnight remote-agent loop (`/afk-fanout`, `/afk-worker`). `/afk-fanout` reads this file to schedule one remote claude.ai routine per PRD; it refuses at pre-flight if this file is missing or has no `environment_id`.

## Environment

- **environment_id:** `env_xxxxxxxxxxxxxxxxxxxxxx`

  The Claude Code environment on claude.ai that each scheduled routine runs in (the clone + setup the remote session uses). Find it in claude.ai → Code → Environments, or read it off any existing routine: `RemoteTrigger({action:"list"})` → `job_config.ccr.environment_id`.

- **Remote-skills hook installed in this repo:** required. A scheduled routine fires in a fresh remote session with **no plugins installed**, and plugin availability is **not** configurable per claude.ai environment — so the skills are provisioned by a repo-level `SessionStart` hook instead. `/setup-zsl-superpowers` (Section F) writes `.claude/hooks/zsl-remote-skills.sh` and wires it in `.claude/settings.json`; it clones zsl-superpowers and symlinks the skills into `~/.claude/skills/` only when `CLAUDE_CODE_REMOTE=true` (a no-op locally). Without it, `/afk-worker` won't resolve in the scheduled session.

## Scheduling defaults

- **Overnight window:** 20:00–08:00 local (override at schedule time).
- **Slot spacing:** fixed 2h — a deliberate throttle to keep each rolling 5-hour usage window under the token cap. Don't compress it; overflow drops to the next evening.
- **Cron timezone:** UTC. `/afk-fanout` computes each slot's `cron_expression` in UTC.
- **`session_context.allowed_tools`:** must include `Skill` and `Task` (so `/afk-worker` can be invoked and `/tdd-parallel` can fan out its sub-agents). Default to the `preset:default` superset.

The full verified `RemoteTrigger` create body — where the prompt lives in `job_config.ccr.events[]` as an SDK user-message event — is documented in `/afk-fanout`'s `SKILL.md`, step 5.

## Results transport: the `afk-runs` ledger branch

Workers run in isolated clones, so their outcomes can't reach your local `/morning-review` through `.scratch/` on `main`. They come home on a shared orphan git branch, `afk-runs` — one ledger entry per PRD (claim state, PR URL, halt RCA). `/morning-review` reconciles it back into `.scratch/`. Two requirements:

- **Writable remote.** Workers `git push` their ledger entries to `afk-runs`; without push access from the remote environment, results never come home. `/afk-fanout` pre-flights this.
- **Branch layout & entry schema** are defined in `/afk-fanout`'s `SKILL.md` (§"The `afk-runs` ledger branch"). All three skills (`/afk-fanout`, `/afk-worker`, `/morning-review`) must agree on it.

## Notifications (optional)

Each `/afk-worker` fires a **best-effort** Telegram heads-up when it finishes a PRD, so you wake to a one-line status. Purely a notification — the `afk-runs` ledger is the load-bearing record, so a missing or failing notification never affects a run.

Set these as **environment variables/secrets in the remote Claude Code environment** (never commit the values — only the names live here):

- **`AFK_TELEGRAM_BOT_TOKEN`** — a Telegram bot token from [@BotFather](https://t.me/BotFather).
- **`AFK_TELEGRAM_CHAT_ID`** — the chat/DM id to post to (your own user id for a self-DM).

If either is unset, workers skip the heads-up silently. No MCP connector is involved — the worker posts via a plain HTTPS call to the Telegram Bot API, which works in headless routine sessions.
