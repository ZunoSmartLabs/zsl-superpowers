---
name: afk-fanout
description: Interactive local-session scheduler for overnight remote /tdd-parallel runs. Reviews the queue of tracking PRDs with ready-for-agent children, lets the human pick which to run overnight and in what order, then schedules one one-shot remote routine per selected PRD spaced a fixed 2h apart — each fires its own remote claude.ai session running /afk-worker against one PRD. The 2h spacing is a deliberate throttle to stay under the per-5h-window token cap. Places a light scheduled claim on each PRD so a re-run the same evening won't double-book. Morning you walks the results via /morning-review.
---

# AFK Fanout

Interactive overnight scheduler. Run it yourself in a local Claude Code session in the evening: it shows you the queue of actionable PRDs, you pick which ones to run overnight and in what priority, and it schedules **one dedicated remote session per PRD** — fixed 2h apart — each running `/afk-worker` to drive `/tdd-parallel` against a single PRD in its own clone. In the morning you walk the resulting PRs and halts via `/morning-review`.

This is **not** an unattended cron job. The human is the dispatcher: judgment about *which* PRDs are worth overnight budget goes in here, once, interactively. The autonomy lives downstream in each scheduled `/afk-worker` remote session.

## Why this exists

`/tdd-parallel` works one PRD at a time and treats the session's checkout as its integration surface — so two `/tdd-parallel` runs **cannot** share one session without racing on the working tree and branch. The fix is to fan out at the *session* level: each PRD gets its own remote claude.ai session, hence its own fresh clone, its own working tree, its own branch. Checkout contention disappears because there's no shared checkout.

That reframing changes three things versus a single overnight orchestrator session:

- **Human judgment at selection.** A local interactive pass lets you skip a PRD whose brief is still shaky instead of spending a whole remote session's budget discovering it.
- **No queue-claiming race.** Selection happens once, by a human, so there's no concurrent dispatcher to coordinate with. A light scheduled claim only guards against *you* running `/afk-fanout` twice the same evening.
- **Per-session isolation contains failures.** A dirty-tree (3e) halt now only dirties that one worker's clone — it can't force the next PRD to reset `main` and destroy evidence, because the next PRD is a different session entirely.

## The 2h throttle — do not "optimise" this away

Selected PRDs are scheduled a **fixed 2 hours apart**, never compressed. This is a token-budget throttle, not a correctness device. claude.ai usage is capped per rolling **5-hour window**; one `/afk-worker` session is a heavy consumer (`/tdd-parallel` fans out per-slice sub-agents). At 2h spacing, at most ~2 worker sessions start inside any 5h window, which keeps each window under the cap. Fire them closer together and a single window's PRDs can blow the limit and get throttled mid-run.

Because workers run in isolated clones, spacing is **not** needed to avoid the checkout race (that's already solved) and does **not** reduce PR-vs-PR merge conflicts (every worker branches from tonight's `main` regardless of when it fires; `/morning-review` resolves cross-PR conflicts at merge time either way). Spacing buys exactly one thing: staying under the token cap. Keep it fixed.

## The per-day routine cap — why one-off scheduling sidesteps it

claude.ai caps how many **recurring routines you can run per day** (as of 2026-05: Pro 5 · Max 15 · Team/Enterprise 25 — confirm, these change), drawing from the same subscription usage as interactive sessions. **One-off runs are exempt from that cap.** Because each `/afk-worker` is scheduled as a native one-off (`run_once_at` — §5), it does *not* draw down the daily routine allowance; it consumes ordinary subscription usage like any other session.

So the routine-count cap does **not** bound a night's selection. Only two things do: the overnight window (how many 2h slots fit) and the per-5h *token* throttle the 2h spacing enforces (§"The 2h throttle"). A night is limited by slots and tokens — never by a routine quota.

## The `afk-runs` ledger branch — how results come home

Workers run in isolated clones, so nothing a worker commits to `.scratch/` on its own `main` ever reaches your canonical tracker (PR-style: only merged PRs travel home). Successes ride home in the integration PR; **everything without a PR — the claim flips and any halt's `needs-info` move + RCA — has no carrier.** The fix is a shared git branch the loop uses as a coordination ledger.

`afk-runs` is a long-lived **orphan branch** (no shared history with `main`, carries no app code) holding one dated run directory per night:

```
afk-runs (orphan)
└── .afk-runs/
    └── <YYYY-MM-DD>/            # the evening /afk-fanout ran (post-midnight slots included)
        ├── _scheduled.md        # manifest — written by /afk-fanout
        └── <feature-num>.md     # one ledger entry per PRD — owned by that PRD's worker
```

**One file per PRD** is load-bearing: every worker touches a disjoint path, so concurrent pushes never conflict on content — push with `git pull --rebase` + retry to absorb the ref race (the 2h spacing makes even that rare). The date is the **evening `/afk-fanout` ran**; post-midnight slots land under that same dir, not the next day's.

Each `<feature-num>.md` carries the PRD's whole lifecycle:

```
PRD: <feature-num> — <title>
trigger: <trigger-id>   slot: <ISO-8601 UTC>   routine: <url>
claim: scheduled | in-progress | done | tracking
outcome: pending | success | halt-3a | halt-3d | halt-3e | refusal-1d | coverage-4b
pr: <url | ->
slices-closed: <#refs | ->
slices-needs-info:                 # present only on a clean halt
  - <#ref>
rca: |                             # present only on halt/refusal — verbatim from /tdd-parallel
  <...>
run-ts: <ISO-8601 UTC | ->
reconciled: <- | YYYY-MM-DD>       # set by /morning-review once it replays the entry
```

The **initial** entry + manifest row (the `claim: scheduled` / `outcome: pending` state) are serialized by `scripts/write-afk-entry.sh` (§6's deterministic gate) — that script is the single source of this schema's initial shape, so any change to the field set, the fixed initial values, the ` · ` separator, or the dated path must update the script and stay in lockstep with `/afk-worker`'s §4 reader and `/morning-review`'s §1 replay.

Who touches it:

| Session | Writes | Reads |
|---|---|---|
| `/afk-fanout` (local, eve) | `_scheduled.md` + initial `<num>.md` (`claim: scheduled`, `outcome: pending`); pushes | — |
| `/afk-worker` (remote, slot) | flips its own `<num>.md` → `in-progress`, then terminal + outcome/PR/RCA; pushes | its `<num>.md` (pre-flight claim check) |
| `/morning-review` (local, morn) | sets `reconciled:` after replay; pushes | every un-reconciled date dir |

The ledger is the **transport**, not the canonical tracker — `.scratch/` on `main` stays canonical, and `/morning-review` reconciles ledger → `.scratch/` (see that skill). This is why the loop needs a **writable remote**: the branch is how isolated clones and your local sessions share state without violating PR-style — a coordination branch is not shipped code.

## Usage

```
/afk-fanout
```

No arguments. Interactive. Run it locally in the evening.

## Pre-flight

Refuse with a clear message if any of these fail:

- `docs/agents/issue-tracker.md` exists.
- `docs/agents/triage-labels.md` exists.
- `docs/agents/ship-style.md` exists and says PR-style. `/tdd-parallel` refuses on direct-push; failing here produces a cleaner error than letting every scheduled worker refuse identically at 2am.
- Working tree is clean (`git status --porcelain` empty) and HEAD is on `main`. You're scheduling work against `main`; a dirty or off-branch local tree means the queue enumeration can't be trusted.
- `RemoteTrigger` is available (the claude.ai routines API). Without it there's no way to schedule the remote sessions — refuse rather than silently fall back to a single-session serial run.
- `docs/agents/remote-env.md` exists and carries an `environment_id` (the `job_config.ccr.environment_id` each routine runs in). The environment is **repo-agnostic** — its claude.ai config screen has only name / network-access / env-vars / setup-script, **no repo field** — so a single generic environment (e.g. "Full Network + GH + Telegram") is reused across every project; the target repo is selected **per-routine** via `session_context.sources` (set in §5), not per-environment. Also require that the repo has the remote-skills `SessionStart` hook installed (`.claude/hooks/zsl-remote-skills.sh` wired in `.claude/settings.json`). The hook is what makes the skills resolve in the fresh remote session — plugin availability is **not** configurable per claude.ai environment, so without the hook `/afk-worker` won't resolve. Both are written by `/setup-zsl-superpowers` (Section F). If `remote-env.md` is missing or the hook isn't wired, refuse and point the user at `/setup-zsl-superpowers` — without a valid environment id every `create` produces a trigger that can't run, and without the hook the trigger runs but `/afk-worker` is undefined.
- The repo's `origin` remote resolves to a clean `https://github.com/<owner>/<repo>` URL. **This is the URL each scheduled routine's `sources` carries — what every worker's clone is created from (§5)** — so a missing or garbled origin must **fail loudly here**, never schedule a sourceless routine that fires with no repo to clone. Resolve it with the deterministic gate below; capture the result as `<origin https URL>` for §5.

  **Deterministic gate — resolve the origin URL.** Normalizing an origin to canonical https (strip `.git`, convert `git@github.com:owner/repo` SSH form to https, reject anything that isn't a github.com `owner/repo`) has exactly one correct answer, and the loud-failure requirement is the whole point — so delegate it to the bundled script:

  ```bash
  RO=$({ ls "$PWD"/skills/*/afk-fanout/scripts/resolve-origin-url.sh 2>/dev/null
         ls "$HOME/.claude/skills/afk-fanout/scripts/resolve-origin-url.sh" 2>/dev/null
         ls -d "$HOME"/.claude/plugins/cache/zsl-superpowers/zsl/*/skills/*/afk-fanout/scripts/resolve-origin-url.sh 2>/dev/null | sort -Vr; } | head -1)
  if [ -n "$RO" ]; then
    ORIGIN_URL=$(bash "$RO") || { echo "afk-fanout: origin unresolved — refusing to schedule sourceless routines"; exit 1; }
    echo "origin → $ORIGIN_URL"
  else
    echo "zsl-gate: resolve-origin-url.sh unresolved — resolve the origin by hand per the Fallback below"
  fi
  ```

  **Fallback** (if `$RO` is empty): run `git remote get-url origin`, strip a trailing `.git`, convert a `git@github.com:owner/repo` SSH URL to `https://github.com/owner/repo`, and **refuse** (don't schedule anything) if the result isn't a clean `https://github.com/<owner>/<repo>` — a sourceless routine fires with nothing to clone, which the worker can't recover from.
- The repo has a **writable remote**. Workers push their per-PRD entries to the shared `afk-runs` branch (§"The `afk-runs` ledger branch") — without push access their results can't come home. A quick `git push --dry-run` against the remote is enough to confirm.

## Process

### 1. Enumerate the queue

Build the list of actionable PRDs. Local-markdown (`.scratch/`) and GitHub-issues modes both work; the tracker docs document the exact lookups. A PRD is **queueable** when:

- Its parent state is `tracking` (per `triage-labels.md`). In `.scratch/` mode that's the `Status:` line of `.scratch/<NNN>-<slug>/PRD.md`; in GitHub-issues mode it's the configured label on the parent issue.
- It has at least one open `[AFK]` child carrying `ready-for-agent`.
- It is **not** already claimed `scheduled` (see §4) and **not** already represented by an open integration PR (`gh pr list --search "in:title <feature-num>"` or the `Closes #<parent>` reference). A PRD with a live claim or open PR is in flight; skip it.

Present the queueable set as a table, sorted lowest feature number first, including the **verify-after mix** of its children — useful selection signal. Under each PRD, list the specific `[AFK]` children that will be worked (its open `ready-for-agent` issues — the exact set criterion 2 of §1 matched on), each tagged with its own verify-after kind. The human is committing a remote session's budget per PRD, so showing *which* issues get touched — not just how many — is what makes the selection an informed one:

```
  #   PRD                                  ready  verify-after mix
  023 Billing webhooks retry               3      ci:2  local-run:1
      ├─ #124 Retry queue backoff                 ci
      ├─ #125 Dead-letter table migration         ci
      └─ #126 Webhook replay CLI                   local-run
  041 Search re-indexing                   2      ci:2
      ├─ #131 Incremental index writer            ci
      └─ #132 Reindex backfill job                 ci
  058 OAuth device flow                    4      ci:1  staging:1  local-run:2
      ├─ #140 Device-code grant endpoint          ci
      ├─ #141 Polling + token exchange            local-run
      ├─ #142 Rate-limit device polling           local-run
      └─ #143 Staging smoke test                   staging
```

Each child is referenced by its tracker id (`#NNN` in GitHub-issues mode; the `.scratch/<NNN>-<slug>/` slice id in `.scratch/` mode) so the human can open any one to sanity-check the brief before scheduling. A PRD that's all `ci` is a safe overnight bet (skim-and-merge in the morning); one with `staging`/`local-run` children means more morning work, which may affect whether you schedule it tonight.

### 2. Interactive selection

Ask the human which PRDs to schedule overnight, and in what priority order (earlier priority → earlier slot). This is the whole point of the skill — present the queue and take a selection. Confirm the chosen set back before scheduling anything.

### 3. Window and slotting

- Establish the overnight window. Default to tonight 20:00 → 08:00 local; let the human override.
- Assign each selected PRD a slot **2 hours apart** in priority order, starting at the window's start. Pin **off-`:00`** minutes (e.g. `20:07`, `22:07`, `00:07`) so the routines don't land on the global cron rush.
- **Overflow policy: drop, never compress.** The 2h spacing is fixed (§"The 2h throttle"). If the selection needs more slots than the window holds (e.g. 7 PRDs into a 12h window = 14h), schedule the ones that fit and **report the overflow** — the human re-runs `/afk-fanout` tomorrow evening for the rest. Do not shrink the spacing to make them fit. The window is the only cap: one-off workers are exempt from the per-day routine quota (§"The per-day routine cap"), so there's no second ceiling to drop against.

Print the proposed timetable and get explicit confirmation before creating any routines.

### 4. Light scheduled claim

Before creating each routine, place a **light claim** so a second `/afk-fanout` run the same evening (or an in-flight worker) won't double-book the PRD:

- **`.scratch/` mode:** set the PRD parent's `Status:` line to `scheduled` and append a `## Comments` entry: `Scheduled for <ISO-8601 slot> via /afk-fanout (routine <trigger-id>).` Commit via `/zsl:commit`.
- **GitHub-issues mode:** add a `scheduled` label to the parent issue (add it to `triage-labels.md` if absent) and post the same comment.

In `.scratch/` mode this `main`-local claim guards only against a **second `/afk-fanout` the same evening** — that's all it needs to do, since enumeration (§1) reads canonical `.scratch/` on `main`. The **cross-session** claim the remote worker actually reads (and flips) lives in the worker's ledger entry, created in §6 on the `afk-runs` branch — `main` isn't pushed, so the worker can't see a `main`-local claim.

The claim is "light" because it's advisory, not a lock: it exists only to make queue enumeration (§1) skip already-scheduled PRDs. `/afk-worker` flips the claim to `in-progress` when it starts and to its terminal state when it finishes; a `scheduled` claim older than ~24h with no corresponding worker result is stale and reclaimable by the next `/afk-fanout`.

### 5. Schedule one remote routine per PRD

For each selected PRD, create a remote routine via `RemoteTrigger`. This `create` body is **fully verified** against the live `/v1/code/triggers` API — both the read path (a UI-created routine) and the write path (round-tripped through `create`/`update`):

```
RemoteTrigger({
  action: "create",
  body: {
    name: "afk-worker-PRD-<feature-num>",
    run_once_at: "<ISO-8601 UTC timestamp for the slot — must be in the future, off-:00 minute>",
    enabled: true,
    persist_session: false,
    job_config: {
      ccr: {                                      // "ccr" = Claude Code Routine
        environment_id: "<the reused generic Claude Code environment id — from remote-env.md>",
        events: [                                 // the prompt lives HERE — an SDK user-message event
          {
            data: {
              type: "user",
              message: { role: "user", content: "/afk-worker <feature-num>" },
              parent_tool_use_id: null,
              session_id: "",
              uuid: "<a fresh uuid v4>"
            }
          }
        ],
        session_context: {
          // MUST include Skill (to invoke /afk-worker) and Task (so /tdd-parallel can fan out
          // sub-agents). The standard "preset:default" superset covers both — prefer it.
          allowed_tools: ["preset:default", "Task", "Skill", "Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch"],
          autofix_on_pr_create: false,
          // sources SELECTS THE REPO this routine clones — it lives INSIDE session_context.
          // (A ccr-level `sources` is rejected HTTP 400 "unknown field sources" — exact
          // nesting matters.) <origin https URL> is the pre-flight-resolved origin. WITHOUT
          // this the routine fires with no checkout and /afk-worker → /tdd-parallel has
          // nothing to operate on.
          sources: [{ git_repository: { url: "<origin https URL>" } }]
        }
      }
    }
  }
})
```

**Confirmed by live probing:**

- **The prompt is `job_config.ccr.events[]`** — an array of SDK-style input events, *not* a scalar field (which is why `prompt`/`message`/`task`/`initial_prompt`/`messages` all got rejected). Each event is `{data: {type:"user", message:{role:"user", content:"<the slash command>"}, parent_tool_use_id:null, session_id:"", uuid:"<uuid>"}}`. Generate a fresh uuid v4 per event; leave `session_id` empty for a new session.
- **`run_once_at` is the schedule — a native one-off.** Pass exactly one of `run_once_at` *or* `cron_expression`; for overnight workers always use `run_once_at` (an RFC3339 UTC timestamp, must be in the future). Confirmed by live probing (2026-05-31): the API echoes `run_once_at` back and computes a real `next_run_at` from it, fires the routine **once**, then **auto-disables** it (`ended_reason: "run_once_fired"`, shown as "Ran" in the UI). Compute each 2h slot in UTC, not local time, and echo the returned `next_run_at` back. **Field-name caveat:** the API **silently drops unknown fields** with no error — `run_at`/`scheduled_at` are accepted-then-ignored and the trigger never fires (`next_run_at` comes back as the zero `0001-01-01T00:00:00Z`), so the field must be exactly `run_once_at`.
- **`job_config.ccr.session_context.sources` selects the repo this routine clones** — and the nesting must be **inside `session_context`**, not at the `ccr` level. Confirmed two ways by live API (2026-05-31): (a) an existing scheduled routine read via `RemoteTrigger({action:"list"})` carries `session_context.sources: [{ git_repository: { url } }]` with the repo URL; (b) a `create` that placed `sources` at the `ccr` level (a sibling of `session_context`) was **rejected HTTP 400** — `translate job_config v1→v2: … unknown field "sources"`. So it's a hard error, not a silent drop: get the nesting exactly right. Without `sources` the routine fires with no checkout and `/afk-worker` → `/tdd-parallel` has nothing to operate on — the bug this skill exists to avoid. The URL is the pre-flight-resolved `<origin https URL>`; never hardcode it (`/afk-fanout` runs against whatever repo the PRDs live in).
- **`outcomes` is NOT set at create — leave it unset.** It auto-populates as an **output** field: the same existing routine read via `list` carried `session_context.outcomes` with run-produced `git_info` (the repo + branches the run created), derived from `sources` and the run itself — not something the scheduler provides. The worker's `gh pr create` targets the repo of its checkout, which is the `sources` repo, so setting `sources` alone is sufficient and correct.
- `job_config.ccr.environment_id` is **required** — the Claude Code environment on claude.ai the session runs in. **Environments are repo-agnostic** (their config screen has only name / network-access / env-vars / setup-script — no repo field), so this is a single generic environment reused across every project (the repo is chosen per-routine via `sources`, above), **not** a per-repo one. Read it from `docs/agents/remote-env.md` (written by `/setup-zsl-superpowers` Section F); pre-flight refuses if that file is absent. **`/afk-worker` resolves via the repo's remote-skills `SessionStart` hook** (`.claude/hooks/zsl-remote-skills.sh`), which clones zsl-superpowers and symlinks the skills into `~/.claude/skills/` when `CLAUDE_CODE_REMOTE=true` — *not* via a per-environment plugin install, which doesn't exist. (`enabled_plugins` exists at the trigger level for *additional* marketplace plugins and is normally left empty.)
- `session_context.allowed_tools` **must include `Skill` and `Task`**, or `/afk-worker` can't be invoked and `/tdd-parallel` can't spawn its per-slice sub-agents. The `preset:default` superset is the safe choice. `session_context.autofix_on_pr_create` is a known bool (default false). `mcp_connections` auto-populates from the account's connectors — don't set it.

**Two properties of one-off routines that matter here:**

- **Cap-exempt.** One-off (`run_once_at`) runs do **not** count against the per-day routine cap (§"The per-day routine cap") — they draw ordinary subscription usage. Scheduling a full night of workers never spends routine quota.
- **Auto-disable, no sweep.** After firing, a one-off auto-disables (`ended_reason: "run_once_fired"`) — there's nothing to disable by hand and no fired-trigger sweep for `/morning-review` to run. Spent triggers stay listed as disabled; `RemoteTrigger` has no `delete` action, so the human clears leftovers in the claude.ai UI when convenient. That's cosmetic — it never affects a run.

Relay the returned `next_run_at` and the routine's claude.ai URL back to the human for each PRD so they can confirm the slot and know where each result will surface.

If a `create` call fails for a PRD, **roll back its claim** (set the parent back to `tracking`, post a `Scheduling failed, claim released.` comment) so the next `/afk-fanout` retries it instead of silently dropping it.

### 6. Manifest and confirmation

Write a scheduling manifest so `/morning-review` knows what was *supposed* to run, not just what produced a PR — the gap (scheduled but no result) is itself a morning signal:

- **`.scratch/` mode:** on the `afk-runs` branch (§"The `afk-runs` ledger branch"), write `.afk-runs/<YYYY-MM-DD>/_scheduled.md` — one row per scheduled PRD (`<feature-num> · <title> · <slot> · <trigger-id> · <routine URL>`) — **and** an initial per-PRD entry `.afk-runs/<YYYY-MM-DD>/<feature-num>.md` with `claim: scheduled`, `outcome: pending`, and the trigger/slot/routine fields filled.

  **Deterministic gate — serialize the entry + row with the shared writer.** The schema (field set, fixed initial values, the ` · ` manifest separator, the dated path) is one correct serialization shared verbatim by `/afk-worker` (§4) and `/morning-review` (§1). Use the writer so the three never drift; pass `<date>` explicitly (the **evening `/afk-fanout` ran** — post-midnight slots do *not* roll). With the `afk-runs` branch checked out, run once per selected PRD:

  ```bash
  WE=$({ ls "$PWD"/skills/*/afk-fanout/scripts/write-afk-entry.sh 2>/dev/null
         ls "$HOME/.claude/skills/afk-fanout/scripts/write-afk-entry.sh" 2>/dev/null
         ls -d "$HOME"/.claude/plugins/cache/zsl-superpowers/zsl/*/skills/*/afk-fanout/scripts/write-afk-entry.sh 2>/dev/null | sort -Vr; } | head -1)
  if [ -n "$WE" ]; then
    bash "$WE" --date <YYYY-MM-DD> --feature-num <num> --title "<title>" \
      --slot "<ISO-8601 UTC>" --trigger-id <trigger-id> --routine-url "<url>"
  else
    echo "zsl-gate: write-afk-entry.sh unresolved — hand-write the entry per the schema below (Fallback)"
  fi
  ```

  Then `git push` the branch. This initial entry is the cross-session claim the worker reads at pre-flight and flips as it runs; `/morning-review` reconciles its final state back into `.scratch/`. Don't commit any of this to `main` — the ledger lives only on `afk-runs`. **Fallback** (if `$WE` is empty): hand-write `_scheduled.md`'s row and `<feature-num>.md` exactly per the schema in §"The `afk-runs` ledger branch" — `claim: scheduled`, `outcome: pending` (not `scheduled`), the ` · ` separator (not a comma), `reconciled: -`.
- **GitHub-issues mode:** no file needed — `/morning-review` reconstructs the scheduled set from the `scheduled`/`in-progress` labels and the routines list.

Print a final summary to the session:

```
/afk-fanout scheduled <N> PRDs for tonight (<window>)
  20:07  PRD 023 — Billing webhooks retry      → <routine URL>
  22:07  PRD 041 — Search re-indexing          → <routine URL>
  00:07  PRD 058 — OAuth device flow           → <routine URL>
  Overflow (not scheduled, re-run tomorrow): PRD 072, PRD 089
Morning: run /morning-review to walk the results.
```

## Constraints

- **Interactive and local only.** This skill takes a human selection; it is not itself a Routine and must not be scheduled to run unattended. The *workers* it schedules are the unattended part.
- **Fixed 2h spacing.** Non-negotiable throttle for the per-5h token cap. Overflow drops to a later evening; spacing is never compressed.
- **One scheduling pass per evening per repo.** The light claim guards against an accidental second run, but don't design around concurrent schedulers — there's one human, one evening pass.
- **Depends on `/afk-worker` and `RemoteTrigger`.** The worker skill is what each routine invokes; the routines API is how they're scheduled. Refuse pre-flight if `RemoteTrigger` is unavailable.
- **Does not run `/tdd-parallel` itself.** It never touches the integration surface — it only enumerates, claims, and schedules. All the heavy work happens in the remote worker sessions.
