---
name: afk-worker
description: Remote per-PRD executor fired by an /afk-fanout-scheduled one-shot routine. Runs unattended in its own remote claude.ai session — own clone, own working tree, own branch — so it never contends with other PRDs' workers. Flips the PRD's scheduled claim to in-progress, runs /tdd-parallel <num> --on-review-failure=continue --max 2, opens one integration PR, and on halt records the offending slice + RCA. Reports its outcome (claim state, PR URL or halt RCA) as a per-PRD entry on the shared afk-runs git branch that /morning-review reconciles back into the tracker, and fires a best-effort Telegram heads-up. Invoked by the scheduled routine, not by hand.
---

# AFK Worker

The unattended per-PRD executor. One `/afk-worker` invocation = one remote claude.ai session = one PRD driven to a PR (or a clean halt). `/afk-fanout` schedules these; each fires at its 2h slot in its own fresh clone. Because every worker owns its clone, workers never race each other on the working tree — that isolation is the whole reason fan-out happens at the session level.

This skill runs with **no human in the chair**. There is nobody to answer questions. It makes reasonable decisions, finishes, and records what happened for the morning reviewer.

## Why this exists

`/tdd-parallel` does the real work — parallel slice fanout, wave-by-wave merge, integration review, coverage auto-fix, PR open — but it assumes a human is around for escalations. `/afk-worker` is the thin contract boundary that lets it run unattended against one PRD:

- **Owns its clone — so its tracker writes don't auto-sync.** A worker session is alone in its clone; nothing it commits to `.scratch/` on its local `main` reaches your canonical tracker (PR-style — only merged PRs travel home). Successes ride home in the integration PR. Everything without a PR — the claim flip and any halt's `needs-info` move + RCA — is instead **recorded as a per-PRD entry on the shared `afk-runs` branch** (§4, defined in `/afk-fanout`'s SKILL.md), which `/morning-review` reconciles back into `.scratch/`. So the worker doesn't waste effort committing lost tracker state locally — it writes its outcome to the ledger.
- **Escalation → halt-and-record.** Any `/tdd-parallel` halt is captured to the ledger (slice → `needs-info` intent + RCA), not raised to a human. The session then ends; the next night's `/afk-fanout` can re-queue the PRD after `/morning-review` reconciles the halt and a human re-triages.
- **Graceful integration-review degradation.** Always passes `--on-review-failure=continue`, so a 4a failure becomes a PR-body warning instead of a session-ending halt. `/morning-review` runs `/code-review` by hand before merge.

## Usage

```
/afk-worker <feature-num>
```

Invoked by the one-shot routine `/afk-fanout` scheduled (`prompt: "/afk-worker <feature-num>"`). Not intended for direct human use — if you want to run a single PRD interactively, call `/tdd-parallel <num>` yourself.

## Pre-flight

The routine starts a fresh clone of `main`, so the invariants should already hold; verify and refuse cleanly if not:

- `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/ship-style.md` (PR-style) exist.
- Working tree clean, HEAD on `main`.
- The `<feature-num>` PRD exists and has ≥1 open `[AFK]` `ready-for-agent` child.
- The worker is claimed for this PRD. In `.scratch/` mode read the claim from the **ledger entry** — `git fetch origin afk-runs` then read `.afk-runs/<date>/<feature-num>.md` (the initial entry `/afk-fanout` serialized via `scripts/write-afk-entry.sh`); it must say `claim: scheduled` (the `main`-local claim is not pushed, so don't look there). In GitHub-issues mode read the parent label. If the entry/label is missing or already `in-progress`/terminal, another worker is or was handling it — log and exit without acting.

## Process

### 1. Claim transition: scheduled → in-progress

Flip the claim from `scheduled` to `in-progress` so a stray re-schedule won't double-run the PRD:

- **`.scratch/` mode:** set `claim: in-progress` in this PRD's ledger entry `.afk-runs/<date>/<feature-num>.md` on the `afk-runs` branch and push it (`git pull --rebase origin afk-runs` first, then push; one file per PRD means no content conflict). Do **not** touch `.scratch/` on `main` — that write would be lost and never reaches the reviewer.
- **GitHub-issues mode:** swap the parent label `scheduled` → `in-progress` and comment.

### 2. Run /tdd-parallel

```
/tdd-parallel <feature-num> --on-review-failure=continue --max 2
```

Operate under the AFK contract:

- Make reasonable decisions and finish. Do not come back to ask routine questions.
- **Do NOT escalate via `SendMessage`** — there is no human in this chain. Any code path reaching `SendMessage` is a bug.
- If `/tdd-parallel` returns a halt RCA, capture it verbatim for §3.
- Do not push branches or open PRs beyond what `/tdd-parallel` does.

### 3. Determine the outcome

Don't write canonical tracker state here — in `.scratch/` mode you're in an isolated clone and any `.scratch/` commit on `main` is lost. Instead, decide the outcome and the **ledger fields** §4 will record; `/morning-review` replays them into `.scratch/` during reconciliation.

- **Success** — `/tdd-parallel` opened the integration PR and closed the slices via `Closes #N`. Ledger: `claim: done`, `outcome: success`, `pr: <url>`, `slices-closed: <#refs>`. The PR auto-closes the parent on merge.

- **Clean-tree halt** (3a zero-progress, 3d agent failure — including session-budget-exhaustion-flavoured 3d): the work didn't ship. Ledger: `claim: tracking` (so it re-queues once re-triaged), `outcome: halt-3a`/`halt-3d`, `slices-needs-info:` listing each attributable slice (for 3a, every un-attempted slice the RCA names; for 3d, the failing slice), and the `rca:` block **verbatim from `/tdd-parallel`** in this shape — `/morning-review` posts it as the slice comment when it replays the `needs-info` move:

  ```
  > *This was generated by AI during /afk-worker (overnight).*

  ## Halt RCA — /tdd-parallel halted

  **Halt type:** <type>
  **Run date (UTC):** <ISO-8601>
  **PRD:** <feature-num> — <PRD title>

  <RCA verbatim from /tdd-parallel>

  Moved to `needs-info`. Re-triage via `/triage <slice-ref>` once understood.
  The slice's `## Acceptance criteria` have not been modified.
  ```

- **Dirty-tree halt** (3e unresolvable merge conflict): the working tree is conflicted on a feature branch. **Do nothing destructive** — leave the clone as-is for inspection. Ledger: `claim: in-progress` (so it's visibly stuck), `outcome: halt-3e`, no `slices-needs-info` (3e is cross-slice — no single attribution), `rca:` on the PRD as above. Because this is an isolated remote session, the conflicted tree affects nothing else — no other PRD's worker is touched.

See `/tdd-parallel`'s seven halt types and the attribution rules below.

### 4. Record the ledger entry, then heads-up

- **`.scratch/` mode:** finalize this PRD's entry `.afk-runs/<date>/<feature-num>.md` on the `afk-runs` branch with the §3 fields plus `run-ts: <now UTC>`, leaving `reconciled:` empty (that's `/morning-review`'s to set). The entry's full schema is in `/afk-fanout`'s SKILL.md (§"The `afk-runs` ledger branch"). Push it — `git pull --rebase origin afk-runs` then `git push`; retry the rebase+push if the ref moved. One file per PRD means the rebase never hits a content conflict.
- **GitHub-issues mode:** no file — the PR and the tracker comments are the record; `/morning-review` queries them.

Then fire a **best-effort Telegram heads-up** so the human wakes to a one-line status before opening the laptop. This is purely a notification — it carries no load-bearing data (the ledger already has everything), so **never let it fail the run**: if the secrets are unset or the call errors, skip silently.

```bash
# Skip entirely if either var is unset.
[ -n "$AFK_TELEGRAM_BOT_TOKEN" ] && [ -n "$AFK_TELEGRAM_CHAT_ID" ] && \
  curl -s --max-time 10 "https://api.telegram.org/bot${AFK_TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="${AFK_TELEGRAM_CHAT_ID}" \
    -d parse_mode=Markdown \
    -d text="PRD <feature-num> <title> — <✅ PR #<n> | ⚠️ halted-3e — needs re-triage | ⛔ refused-1d>" \
    >/dev/null || true
```

`AFK_TELEGRAM_BOT_TOKEN` / `AFK_TELEGRAM_CHAT_ID` are secrets supplied as **environment variables in the remote Claude Code environment** (never committed; `docs/agents/remote-env.md` records only the var *names*). Send one line per terminal outcome — success, each halt type, or a 1d refusal.

## Halt attribution

Inherits `/tdd-parallel`'s seven halt types. `/afk-worker` invents none of its own; it observes them from the run and attributes to the tracker:

| Halt type | Slice attribution |
|---|---|
| Pre-flight refusal (1d) | None — comment on PRD parent. |
| Agent failure (3d) | The specific failing slice named in the RCA. |
| Unresolvable merge conflict (3e) | None moved — dirty tree left for inspection, RCA on PRD parent, claim left `in-progress`. |
| Zero-progress (3a) | Every un-attempted slice named in the RCA. |
| Integration review failure (4a) | N/A — `--on-review-failure=continue` turns 4a into a PR-body warning, not a halt. |
| Coverage verification failure (4b) | None directly — RCA on PRD parent; `/morning-review` runs `/verify-coverage` by hand. |
| Coverage circuit-breaker (4b) | Per-story-exhausted variant attributes to the story's gap sub-issue; other variants comment on PRD parent. |

All attribution is recorded in the ledger entry (`claim:`, `slices-needs-info:`, `rca:`), never written to `.scratch/` from the clone. When attribution is "PRD parent," the ledger `claim:` stays `tracking` (after a clean halt) or `in-progress` (after 3e) and no `slices-needs-info` are listed — `/morning-review` replays it and the reviewer decides next steps.

## Constraints

- **No interactive escalation.** No `SendMessage`. The worker returns a halt to the tracker, never a question to a human.
- **One PRD per session.** A worker handles exactly the `<feature-num>` it was scheduled for. It never enumerates or touches other PRDs.
- **Owns its clone; never commits to others' work.** All clone commits are to this PRD's slice/integration branches. The **one** shared write is appending/updating this PRD's own entry on the `afk-runs` branch (a disjoint path; pushed with pull-rebase-retry) — never another PRD's entry, never `main`.
- **Telegram is best-effort.** The heads-up never blocks or fails the run; the `afk-runs` ledger is the load-bearing record.
- **Depends on `/tdd-parallel` flags.** Needs `--on-review-failure=continue` and `--max`. Older `/tdd-parallel` versions without them will fail; the worker should surface that as a 1d-style refusal in its ledger entry rather than crash silently.
