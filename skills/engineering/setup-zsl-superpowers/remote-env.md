# Remote agent environment

Per-repo config for the overnight remote-agent loop (`/afk-fanout`, `/afk-worker`, `/morning-review`). `/afk-fanout` reads this file to schedule one remote claude.ai routine per PRD; it refuses at pre-flight if this file is missing or has no `environment_id`. This is the operator reference for the environment the loop runs in — fill it from `/setup-zsl-superpowers` Section F.

## The environment is repo-agnostic (reused across projects)

A Claude Code **environment** on claude.ai has **no repo field** — its config screen is only Name / Network access / Environment variables / Setup script. The repo a routine works on is selected **per-routine** by `/afk-fanout`, which sets `job_config.ccr.session_context.sources` from *this* repo's `origin` at schedule time. So **one generic environment is reused across every project** — you do not create a new environment per repo. This file records *which* shared environment this repo schedules into.

- **Environment name:** `<e.g. Full Network + GH + Telegram>`
- **environment_id:** `env_xxxxxxxxxxxxxxxxxxxxxx`

  How to get it (it is **not** shown in the env config dialog): read it off any routine — `RemoteTrigger({action:"list"})` → `job_config.ccr.environment_id`. The env page URL may also surface it.

## Environment variables (names only — values live in claude.ai, never here)

The `.env` box on the environment is **not a secret vault** (the UI warns its values are visible to anyone using the environment). Use a minimally-scoped, **rotatable** GitHub PAT. Set these in the environment, record only the *names* here:

- **`GH_TOKEN`** — GitHub PAT. Scopes: **read** on `zsl-superpowers` (the `SessionStart` hook clones it) **+ read/write on the repos workers ship to** (`contents` + `pull requests` fine-grained, or classic `repo`). This authenticates the worker's feature-branch push, PR open, and `afk-runs` ledger push.
- **`ZSL_SUPERPOWERS_REF`** — ref the skills-provisioning hook checks out (default `main`).
- **`AFK_TELEGRAM_BOT_TOKEN`** / **`AFK_TELEGRAM_CHAT_ID`** — only if Telegram heads-up is enabled (see Notifications).
- **`<cloud-cred names, if any>`** — if this repo's tests/slices need cloud credentials at run time (e.g. AWS for infra work), the environment must carry **static keys or a CI role** — interactive SSO won't work in a headless routine session, and workers will stall on integration tests without them. Record the var names here. Pure-code repos need none.

## Setup script (verbatim)

Set this as the environment's Setup script. `gh auth setup-git` is load-bearing — it makes raw `git push` authenticate via `GH_TOKEN`; installing `gh` alone is not enough.

```bash
#!/bin/bash
apt update && apt install -y gh
gh auth setup-git
```

## Network access

**Full** — required for `git push`, the `gh` CLI, the Telegram Bot API, and package installs.

## Remote-skills hook (required in this repo)

A scheduled routine fires in a fresh remote session with **no plugins installed**, and plugin availability is **not** configurable per claude.ai environment — so the skills are provisioned by a repo-level `SessionStart` hook instead. `/setup-zsl-superpowers` (Section F5) writes `.claude/hooks/zsl-remote-skills.sh` and wires it in `.claude/settings.json`; it clones zsl-superpowers and symlinks the skills into `~/.claude/skills/` only when `CLAUDE_CODE_REMOTE=true` (a no-op locally). Without it, `/afk-worker` won't resolve in the scheduled session.

## Scheduling defaults

- **Overnight window:** 20:00–08:00 local (override at schedule time).
- **Slot spacing:** fixed 2h — a deliberate throttle to keep each rolling 5-hour usage window under the token cap. Don't compress it; overflow drops to the next evening.
- **Schedule timezone:** UTC. `/afk-fanout` computes each slot's `run_once_at` (a native one-off) in UTC.
- **`job_config.ccr.session_context.sources`:** set by `/afk-fanout` from this repo's `origin` (normalized to `https://github.com/<owner>/<repo>`) — selects the repo each routine clones. It lives **inside** `session_context` (a `ccr`-level sibling is rejected HTTP 400 — live-probe confirmed).
- **`session_context.allowed_tools`:** must include `Skill` and `Task` (so `/afk-worker` can be invoked and `/tdd-parallel` can fan out its sub-agents). Default to the `preset:default` superset.

The full verified `RemoteTrigger` create body — where the prompt lives in `job_config.ccr.events[]` as an SDK user-message event and the repo in `job_config.ccr.session_context.sources` — is documented in `/afk-fanout`'s `SKILL.md`, step 5.

## Results transport: the `afk-runs` ledger branch

Workers run in isolated clones, so their outcomes can't reach your local `/morning-review` through `.scratch/` on `main`. They come home on a shared orphan git branch, `afk-runs` — one ledger entry per PRD (claim state, PR URL, halt RCA). `/morning-review` reconciles it back into `.scratch/`. Two requirements:

- **Writable remote.** Workers `git push` their ledger entries to `afk-runs`; without push access from the remote environment (the `GH_TOKEN` PAT above), results never come home. `/afk-fanout` pre-flights this with `git push --dry-run`.
- **Branch layout & entry schema** are defined in `/afk-fanout`'s `SKILL.md` (§"The `afk-runs` ledger branch"). All three skills (`/afk-fanout`, `/afk-worker`, `/morning-review`) must agree on it.

## Notifications (optional)

Each `/afk-worker` fires a **best-effort** Telegram heads-up when it finishes a PRD, so you wake to a one-line status. Purely a notification — the `afk-runs` ledger is the load-bearing record, so a missing or failing notification never affects a run. Set these as environment variables in the remote environment (never commit the values):

- **`AFK_TELEGRAM_BOT_TOKEN`** — a bot token from [@BotFather](https://t.me/BotFather) (`/newbot`).
- **`AFK_TELEGRAM_CHAT_ID`** — the chat/DM id. Get it: message your bot once, then `GET https://api.telegram.org/bot<TOKEN>/getUpdates` and read `result[].message.chat.id` (your own user id for a self-DM).

If either is unset, workers skip the heads-up silently. No MCP connector is involved — the worker posts via a plain HTTPS call to the Telegram Bot API, which works in headless routine sessions.
