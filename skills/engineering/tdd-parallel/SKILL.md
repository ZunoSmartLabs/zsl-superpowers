---
name: tdd-parallel
description: Full-auto PRD pipeline. Fans out the unblocked [AFK] sub-tasks of a parent PRD into parallel /tdd sub-agents, integrates them onto the PRD branch, auto-chains /verify-coverage to prove every user story has a passing non-vacuous test, auto-fixes any gaps (loop), then opens a single integration PR. Runs partially when an open [HITL] slice exists — fans out every slice whose blocker closure is HITL-free, defers the rest, and opens a [partial] PR that leaves the PRD open. Refuses only if no slice is runnable or an in-scope user story isn't expressible as an automatable test. PR-style repos only.
disable-model-invocation: true
---

# Parallel TDD

Full-auto pipeline from a PRD to a pushed integration PR: fanout → integrate → review → verify → fix → push, with no mid-run human gates in the happy path. Each `/tdd` sub-agent runs `/tdd <num> --no-ship` in its own worktree, committing locally but never pushing. The orchestrator merges every slice branch onto the parent's PRD branch (which doubles as the integration branch) in wave order with `--no-ff`, runs an integration code review, then chains `/verify-coverage --auto` and loops on any gaps it files before opening one consolidated PR.

`[HITL]` slices don't block the whole run — they're *deferred*. The pre-flight runs every slice whose transitive `Blocked by` closure is HITL-free and defers each open `[HITL]` slice plus everything transitively downstream of it. When anything is deferred, the run is **partial**: it ships the runnable slices in a `[partial]` PR that leaves the parent PRD *open*, with a re-entry recipe for landing the remainder after the gate clears via `/human-itl`. A PRD with no open `[HITL]` slices behaves exactly as a full run — closes the parent, no `[partial]` marker. The pre-flight still refuses any PRD whose *in-scope* user stories lack an `AC<n>:` acceptance criterion (per `/to-prd`'s story format), and refuses outright only when no slice is runnable at all. Once `/tdd-parallel` starts, it runs through to PR-push or a circuit-breaker halt.

PR-style repos only — direct-push fanouts merge straight to `main` without consolidation.

## Why partial runs are safe

The old blanket pre-flight refusal — *no open `[HITL]` sub-issues anywhere* — is stronger than the invariant it protects. The real invariant is **no human gate fires *after* invocation**: once the auto-loop starts, nothing should stop to wait on a human. That invariant is preserved by a weaker, graph-aware rule:

> Run only slices whose transitive `Blocked by` closure contains no open `[HITL]` slice. Defer every open `[HITL]` slice and everything transitively downstream of it.

Because every selected slice's *entire* blocker closure is HITL-free, no selected slice can become human-gated mid-run — the invariant holds just as firmly as under the blanket refusal, but without throwing away the work that doesn't depend on the gate. The deferred slices simply wait for a later run, after the gate clears via `/human-itl`. This carve is always on: there is no flag, and a PRD with zero open `[HITL]` slices is byte-for-byte the old behaviour (full fanout, closes the parent).

## Why one PR

Each push to a feature branch triggers CI workflows. With N sub-issues = N PRs you'd pay N × M CI runs over the life of a fanout. Staging slice work locally and pushing one consolidated branch costs one CI run. Trade-offs: one PR is a single review surface (no per-slice review granularity), and merge conflicts surface during local integration rather than during PR review. Both are acceptable when the wave model from `/to-issues` asserts same-wave slices are disjoint.

## Usage

```
/tdd-parallel <parent-issue> [--max N] [--max-coverage-rounds R] [--on-review-failure halt|continue]
```

- `<parent-issue>` — the parent (PRD) issue whose unblocked AFK sub-tasks should be fanned out.
- `--max N` — concurrency cap *within a wave*. Default 2.
- `--max-coverage-rounds R` — circuit breaker on the coverage auto-fix loop (step 4b). Default 3. On exhaustion, halts with the residual matrix; the user takes over.
- `--on-review-failure halt|continue` — what to do when step 4a's `/code-review --auto` applies findings but lint/tests fail and the review commit gets reverted. Default `halt` (preserves the interactive contract). `continue` proceeds to step 4c with the pre-review tip — all slices are still green individually, the integration polish just didn't land — and adds a `## ⚠️ Integration review failed` section to the PR body listing the attempted findings. Use `continue` from unattended paths (`/afk-worker`, the overnight per-PRD remote executor); the morning reviewer runs `/code-review` against the PR locally before merge.

Partial runs are **automatic and unconditional — there is no flag.** When the parent has open `[HITL]` slices (or slices still in triage), `/tdd-parallel` fans out everything not gated behind them and opens a `[partial]` PR, deferring the rest. A parent with no open `[HITL]` slices runs fully and closes the parent, exactly as before.

## AFK contract

Sub-agents spawned by this skill operate AFK. They make reasonable decisions and finish — they do **not** return mid-flight to ask routine questions. They escalate (return early with a question) only when they hit:

- A destructive operation that needs confirmation per auto mode rules.
- A missing access or credential they can't proceed without.
- A genuine architectural ambiguity that would change a public contract.

When an agent escalates, the orchestrator relays the question to the user and resumes the agent via `SendMessage` with the user's answer. Anything that routinely needs a manual human action mid-flight isn't AFK and shouldn't be in the fanout — it belongs as an `[HITL]` slice, cleared via `/human-itl`. (Routine *decisions* don't belong as `[HITL]` slices either — they're resolved upstream in `/grill-with-docs` + an ADR so the slice stays AFK.)

## Progress visibility

Sub-agents emit a one-line JSON heartbeat to `.tdd-progress.jsonl` in their worktree at each TDD phase. The orchestrator runs one `Monitor` per wave (with `tail -n +1 -F` over the wave's progress files) and renders a live wave board, so the user sees progress mid-flight rather than waiting for completion. `Monitor`'s stdout-line-per-notification model maps directly to one heartbeat record per notification.

Schema and phase list: see `engineering/tdd/SKILL.md` § Progress heartbeat. The contract is one direction only — agents emit, the orchestrator reads. Heartbeats are **not** an escalation channel: escalations still go through agent return + `SendMessage`. They are advisory; never gate merge logic on them.

## Process

### 1. Pre-flight

Four phases. 1a refuses on failure; 1b cleans up silently and continues; 1c either creates or adopts the PRD branch; 1d validates the parent PRD is auto-loop-eligible.

#### 1a. Environment validation

**Deterministic gate.** The mechanical parts of 1a + 1c (clean tree, HEAD not detached, the three required files exist, `.worktrees/` is gitignored) are scripted — each has one correct boolean answer. Resolve and run the validator; a `FAIL:` line means refuse with that message. It also covers 1c's clean-tree/not-detached checks, so 1c need not re-run them.

```bash
SP=$({ ls "$PWD"/skills/*/tdd-parallel/scripts/zsl-preflight.sh 2>/dev/null
       ls "$HOME/.claude/skills/tdd-parallel/scripts/zsl-preflight.sh" 2>/dev/null
       ls -d "$HOME"/.claude/plugins/cache/zsl-superpowers/zsl/*/skills/*/tdd-parallel/scripts/zsl-preflight.sh 2>/dev/null | sort -Vr; } | head -1)
if [ -n "$SP" ]; then
  bash "$SP" --clean-tree --not-detached \
    --require-file docs/agents/ship-style.md \
    --require-file docs/agents/issue-tracker.md \
    --require-file docs/agents/triage-labels.md \
    --ensure-gitignore-line '.worktrees/'
else
  echo "zsl-gate: zsl-preflight.sh unresolved — run the checks below by hand (Fallback)"
fi
```

Then the **one check the script can't make** — `docs/agents/ship-style.md` must *say PR-style*. That's a read of free-form prose, not a clean boolean, so it stays your call: open the file and refuse if it configures direct-push. Direct-push fanouts are unsupported — they'd land slices on `main` directly without consolidation, defeating the point.

**Fallback** (if `$SP` is empty — the gate didn't resolve): refuse with a clear error message if any of these fail, exactly as the script would:

- `docs/agents/ship-style.md` exists **and** says PR-style.
- `docs/agents/issue-tracker.md` exists.
- `docs/agents/triage-labels.md` exists.
- Working tree is clean (`git status --porcelain` empty) and HEAD is not detached.

Append `.worktrees/` to the repo root `.gitignore` if not already present (the exact line `.worktrees/`, only if absent).

#### 1b. Auto-clean stale slice worktrees and branches

Scan `.worktrees/*`. For each entry whose name matches the configured naming pattern (`<num>-<slug>` for GitHub/GitLab, `<feat>-<slice>-<slug>` for local-markdown — see 3c):

1. Parse the slice identifier from the directory name. GitHub/GitLab: `<num>` is the issue number. Local-markdown: `<feat>` is the feature dir number, `<slice>` is the per-feature slice file number; together they resolve to `.scratch/<feat>-*/issues/<slice>-*.md`.
2. Query the issue tracker for the slice's state.
3. **Skip** if the slice is OPEN — not ours to remove.
4. **Skip** if `git -C .worktrees/<dir> status --porcelain` is non-empty — uncommitted changes; the user should investigate.
5. Otherwise:
   - `git worktree remove .worktrees/<dir>` (no `--force`)
   - `git branch -d tdd/<dir>` (no `-D`) — branch name mirrors the worktree dir name
6. If `git branch -d` refuses because the branch isn't fully merged, **skip and log** — never `-D` automatically.

Print a one-block summary: `cleaned`, `skipped — open`, `skipped — uncommitted`, `skipped — unmerged branch`. Do not refuse on any skip.

#### 1c. Determine the PRD branch

The PRD branch doubles as the integration branch — sub-task branches will be merged onto it, and it gets pushed once at the end as the integration PR's source.

- Run `git fetch origin`.
- The dirty-tree / detached-HEAD refusal is already enforced by 1a's deterministic gate (`--clean-tree --not-detached`); `git fetch` doesn't touch the working tree, so it still holds here. (Fallback, if the gate didn't resolve: refuse if `git status --porcelain` is non-empty or HEAD is detached.)
- **If the orchestrator is on `main`**: create the PRD branch and switch to it.
  - Branch name: `feature/<parent-num>-<slug>`. Slug is kebab-case of the parent issue title, max 40 chars.
  - `git checkout -b feature/<parent-num>-<slug>` from `main`'s tip.
- **If the orchestrator is on a non-`main` branch**: treat it as the PRD branch. Do not switch, do not auto-rebase against `main` — the user owns its relationship to `main`.

After 1c the orchestrator is on the PRD branch with a clean working tree.

#### 1d. Parent PRD readiness

Fetch the parent issue and its sub-issues per `docs/agents/issue-tracker.md`. Refuse with a clear message if this fails:

- **Parent has a `## User Stories` section** — otherwise it isn't a PRD and this skill doesn't apply.

Then build the HITL-reachability picture and partition the open sub-issues. Parse each open slice's `## Blocked by` references and compute, over the parent's sub-tree:

- **runnable** = `[AFK]`, `ready-for-agent`, non-container slices whose *transitive* `Blocked by` closure contains **no open `[HITL]` slice** (a closed `[HITL]`, already cleared by `/human-itl`, does not gate). These are the slices this run fans out.
- **deferred** = every open `[HITL]` slice ∪ its transitive downstream closure (anything that, directly or through a chain of `Blocked by`, depends on an open `[HITL]`) ∪ any sub-issue still in triage (`needs-triage`, no `ready-for-agent` label). These wait for a later run.

This is a lightweight pass whose only job is to size `runnable`/`deferred` and scope the story gate below; step 2 rebuilds the full graph for execution, and step 3a's `satisfied` predicate enforces the same closure at pick time. The two cannot diverge: an open `[HITL]` blocker is never `satisfied` in 3a — not merged, not in `satisfied_oob` — so any slice 3a would ever pick is exactly a member of `runnable` here.

Refuse with a clear message if either of these fails:

- **`runnable` is empty** — every slice is deferred (gated behind an open `[HITL]`, or still in triage). There is nothing to do this run. List the open `[HITL]` issue numbers + titles and tell the user to clear them via `/human-itl <parent>` first, then re-invoke. This is the **only** `[HITL]`-related refusal — the presence of *some* open `[HITL]` slices alongside runnable ones is expected and triggers a partial run, not a refusal.
- **An in-scope user story is not automatable.** Scope this check to the stories the `runnable` slices cover — their `## User stories covered` sections (per `/to-issues`). Every such story must carry at least one `AC<n>:` acceptance-criterion sub-bullet in the exact format `/to-prd` writes — that criterion is what makes the story expressible as a test. Any in-scope story carrying no `AC<n>:` criterion is invalid — refuse with the offending story numbers and a pointer to `/to-prd`'s story format (typically the PRD pre-dates the requirement, or a non-automatable story was added by hand). A legacy `observable:` sub-bullet counts as one acceptance criterion for back-compat; a legacy `acceptance:` tag, if present, is ignored. Stories covered **only** by `deferred` slices need not satisfy this gate *this run* — they're checked when a later run makes them in-scope.

These checks fail fast and surface the exact thing to fix. Once 1d passes, the auto-loop is committed: it will run through to PR push (full or `[partial]`) or a circuit-breaker halt, with no further human prompts in the happy path.

### 2. Discover the dependency graph

Using `docs/agents/issue-tracker.md` conventions, fetch the parent issue's sub-issues. Keep only those that are:

- Open
- Title starts with `[AFK]` (`[HITL]` filtered out)
- Carry the configured `ready-for-agent` label
- Not a container (have no open sub-issues of their own)

For each surviving slice, parse the `## Blocked by` section to extract referenced issue numbers. Build the dependency graph in memory.

Some discovered `[AFK]` slices may be transitively `Blocked by` an open `[HITL]` slice — they belong to `deferred` (1d). They stay in the graph but never get picked: 3a's `satisfied` predicate never clears an open `[HITL]` blocker. Step 3a's empty-pick branch recognises them as deferred (partial-complete), not as a fault. (Open `[HITL]` slices themselves and still-in-triage items aren't in the discovered set — the `[AFK]` + `ready-for-agent` filter excludes them — but 3b and the `[partial]` PR still report them for the re-entry recipe.)

### 3. Wave-by-wave fanout loop

Maintain orchestrator state across iterations:

- `merged` — set of sub-task issue numbers whose branches **this run** merged onto the PRD branch.
- `attempted` — set of sub-task issue numbers we've spawned an agent for.
- `satisfied_oob` — set of blocker issue numbers confirmed satisfied *out of band*: closed/done in the parent's sub-tree but never merged by this run (e.g. a `[HITL]` slice cleared by `/human-itl`, or a slice a prior independent `/tdd` shipped). Populated lazily by 3a and cached so each blocker is queried at most once per run.

#### 3a. Pick the next wave

A slice is **unblocked** when every issue in its `Blocked by` section is **satisfied**. A blocker `b` is satisfied when *either*:

- `b ∈ merged` — its branch was merged onto the PRD branch this run; **or**
- `b ∈ satisfied_oob` — it is closed/done in the parent's sub-tree but was not merged by this run.

For any blocker that is in neither set, resolve it **once** via `docs/agents/issue-tracker.md` conventions: if that issue is **closed/done** *and* a member of the parent PRD's sub-tree, add it to `satisfied_oob`; otherwise leave it unsatisfied. The sub-tree-membership guard is mandatory — an unrelated closed issue number elsewhere on the tracker must **not** satisfy a dependency (that guard is the safety the old `merged`-only rule gave implicitly; don't drop it). Closure of slices *inside* this fanout stays irrelevant — AFK sub-issues never close mid-run, so `merged` remains their only signal; this second clause exists solely for blockers satisfied *outside* the fanout: `[HITL]` slices `/human-itl` cleared, or work a prior `/tdd` shipped.

Pick all unblocked, not-yet-attempted slices, sorted by issue number, capped by `--max`.

If the picked set is empty:

- If every discovered slice is in `merged` → fanout complete (full run). Go to step 4.
- Else if every still-unmerged discovered slice is in `deferred` (transitively `Blocked by` an open `[HITL]`) → **partial-complete**. There is no more *runnable* work this run; the deferred slices wait for a later invocation. Go to step 4 — do **not** halt. 3a already skips these correctly: an open `[HITL]` blocker is never `satisfied` (not merged, not in `satisfied_oob`), so a HITL-downstream slice never gets picked. The only bug the blanket halt introduced was treating this expected carve-out as a fault.
- Otherwise → **zero-progress halt** with hybrid RCA (see "RCA shape" below). This now means a genuine graph fault — a circular `Blocked by`, a slice depending on an *open non-`[HITL]`* issue outside this fanout, or a reference to a non-existent issue — because any blocker satisfiable by an out-of-band close was already absorbed into `satisfied_oob` above, and any slice gated behind an open `[HITL]` is in `deferred` and handled by the partial-complete branch. Stop.

#### 3b. Show the wave to the user

Print buckets:

- **Selected** (numbered): issue number + title + branch name + worktree path.
- **Skipped — over cap (this wave)**: issue number + title.
- **Deferred — HITL-blocked**: the open `[HITL]` slices in `deferred`, each with (a) the downstream slices it defers (slices whose `Blocked by` closure reaches it) and (b) the user-story numbers those deferred slices cover (from their `## User stories covered`). Append any still-in-triage sub-issues being deferred. This bucket is **expected and non-fatal** — it's the carve that makes the run partial. These ride into the `[partial]` PR's `## Deferred` section (4c) and land on a later run after the gate clears via `/human-itl <parent>`. A closed `[HITL]` (already cleared) does **not** appear here — it lives in `satisfied_oob`. (If this bucket is empty, the run is a full run and 4c closes the parent.)
- **Already merged**: list of issue numbers from prior waves.
- **Satisfied out-of-band**: issue numbers in `satisfied_oob` (closed/done outside this fanout — e.g. a `[HITL]` slice cleared by `/human-itl`), each with the slice it unblocked. Empty on a clean first run; non-empty after a `/human-itl` round-trip.
- **Pending future waves**: issue number + title + the `Blocked by` references it's still waiting on.

Confirm with the user before proceeding.

#### 3c. Create slice worktrees and spawn sub-agents

For each selected slice, derive:

- Slug: kebab-case of the issue title, max 40 chars.
- Branch: `tdd/<num>-<slug>` (GitHub/GitLab — `<num>` is globally unique); `tdd/<feat>-<slice>-<slug>` (local-markdown — slice numbers are per-feature scoped so the feature number disambiguates).
- Worktree path: `.worktrees/<num>-<slug>/` (GitHub/GitLab); `.worktrees/<feat>-<slice>-<slug>/` (local-markdown).

The conditional naming keeps slice worktrees unambiguous: in local-markdown mode slice numbers are per-feature scoped, so without the feature prefix two PRDs each with a `01-…` slice would collide on the same `.worktrees/01-<slug>/` path if `/tdd-parallel` is ever run against more than one PRD in the same checkout. (Overnight, `/afk-worker` gives each PRD its own clone, so this can't arise there — but the prefix keeps any single-checkout multi-PRD use safe too.) Detect the tracker mode from `docs/agents/issue-tracker.md` (set during `/setup-zsl-superpowers`).

Then:

1. `git worktree add .worktrees/<num>-<slug> -b tdd/<num>-<slug> HEAD` — `HEAD` is the PRD branch's current tip, so the slice inherits any prior waves' merges.
2. Handle residue: if the worktree dir already exists from a prior partial run, reuse it; if the branch exists but no worktree, attach without `-b`.
3. In one message (so they fire concurrently), start the wave's heartbeat `Monitor` and spawn each sub-agent:

```
Monitor({
  command: "tail -n +1 -F .worktrees/<num1>-<slug1>/.tdd-progress.jsonl .worktrees/<num2>-<slug2>/.tdd-progress.jsonl ...",
  description: "wave <N> heartbeat",
  persistent: true,
  timeout_ms: 3600000
})

Agent({
  description: "TDD <num>",
  subagent_type: "general-purpose",
  run_in_background: true,
  name: "tdd-<num>",
  prompt: <see template below>
})
// ... one Agent call per slice in the wave ...
```

Notes:

- `tail -n +1 -F` reads from line 1 and retries on missing files, so timing relative to agent emission is forgiving — heartbeat files don't need to exist when the `Monitor` starts.
- `persistent: true` is required: a wave can run longer than `Monitor`'s 60-minute hard cap on `timeout_ms`. With `persistent`, the watcher runs until you call `TaskStop`.
- Capture the `Monitor` task id from the response — you'll need it for `TaskStop` at end of wave.
- Don't filter the tail with `grep`. The progress file only contains heartbeat lines, so every line is signal. (`Monitor`'s "use grep" guidance is for raw log streams; this isn't one.)

Sub-agent prompt template:

```
You are running AFK as part of a /tdd-parallel fanout.

First action: cd <ABSOLUTE-PATH-TO-WORKTREE>

Then run: /tdd <num> --no-ship

You operate under the AFK contract:
- Make reasonable decisions and finish without coming back to ask routine questions.
- Escalate (return early with a question) ONLY for: destructive ops needing confirmation per auto mode rules, missing access/credentials, or genuine architectural ambiguity that would change a public contract.
- Be specific about what you need if you do escalate.

Lean slices: the slice's refactor phase must apply `/tdd`'s deletion discipline (see `engineering/tdd/SKILL.md` § Refactor) — dead code, unused imports, debug statements, commented-out blocks, comments explaining *what* code does. Bloated slices compound into a bloated integration PR.

Progress heartbeat: your invocation of `/tdd <num> --no-ship` MUST emit one-line JSON records to `.tdd-progress.jsonl` in the worktree at each TDD phase per `engineering/tdd/SKILL.md` § Progress heartbeat. Don't skip — the orchestrator depends on these for live status, and silence looks like a hang.

When done, report: branch name, last commit sha, the slice issue number you worked on (so the orchestrator can map slice → issue), and a one-paragraph summary of changes. Do NOT push. Do NOT open a PR.
```

Add each spawned issue number to `attempted`. Pass the *absolute* worktree path in the prompt — the sub-agent's first action must be to `cd` there before doing anything else, so its Bash CWD lands in the right worktree for the remainder of its session.

#### 3d. Wait for the wave to finish

While the wave runs, two streams of notifications interleave:

- **Heartbeat notifications** from the wave's `Monitor` — one JSONL record per notification. Parse `slice` + `phase` + `note`, update an in-memory wave board (`slice → latest phase + ts + last note`), and re-render to the user when a phase advances. Don't render on every notification — that's noise; render on phase change or every ~10s, whichever comes first.
- **Agent completion notifications** — handled per the steps below.

Process completion notifications as they arrive. For each completing agent:

1. Read its result.
2. **If escalated** (returned with a question rather than a completion summary): relay the question to the user verbatim, get their answer, then resume the agent: `SendMessage({ to: "tdd-<num>", message: <user's answer> })`. Do not proceed until the agent returns properly.
3. **If failed** (errored, refused, or returned without a mergeable branch and not as an escalation): **halt** with hybrid RCA. Stop.
4. **If completed normally**: record the branch name and commit sha.

Wait until **all** agents in the current wave have completed normally before moving to merge. (Halts in 3d cancel the rest — see "Halt semantics" below.)

Once the wave is done (or a halt fires), stop the wave's heartbeat `Monitor` with `TaskStop({ task_id: <wave-monitor-task-id> })`. Per-wave watchers (one `Monitor` spun up in 3c, stopped here) are simpler than one long-running watcher because the file set changes every wave. The final state of `.tdd-progress.jsonl` in each worktree survives — useful evidence on halt.

#### 3e. Merge the wave

The orchestrator is on the PRD branch. Merge each of the wave's slice branches in order — by letter for lettered slices (`1a`, `1b`, `1c`), by issue number otherwise. For each:

1. `git merge --no-ff tdd/<num>-<slug> -m "Merge slice [AFK] <wave><letter> — <slice-title> (#<num>)"`.
2. **If git reports a conflict**: attempt auto-resolve before halting.
   - For each conflicted file, read both sides. Understand the intent of the slice being merged in (its title, recent diff) and the integration tip (the last merged slice's title and diff). Produce a merged result that preserves both — don't pick one side blindly.
   - After editing, run project lint and tests (`make lint test` if a Makefile exposes them; otherwise infer from repo conventions). On pass, `git add` the resolved files and `git commit --no-edit` to complete the merge, then continue to the next branch.
   - If a clean merge isn't reachable — binary file, generated lockfile with a structural conflict, lint/tests still red after a couple of attempts, or genuine semantic conflict the orchestrator can't reason about — leave the merge in its conflicted state (do *not* `git merge --abort` — the user inspects in place) and halt with hybrid RCA. Stop.
3. **On success**: add the slice's issue number to `merged`. Continue to the next branch.

#### 3f. Loop

Go back to 3a. Newly-unblocked slices (whose `Blocked by` references are now all **satisfied** per 3a — in `merged` or `satisfied_oob`) become the next wave's candidates.

### 4. Open the integration PR

After all discovered slices are merged:

#### 4a. Integration code review (mandatory)

Run `/code-review --auto` against the PRD branch tip. Per-slice reviews ran inside each `/tdd` invocation; this pass catches the cross-slice issues those can't see — duplicate helpers introduced by parallel slices, stylistic drift, redundant imports after merge, leftover debug statements that slipped through individual refactors.

Auto-fixes commit onto the PRD branch (subject: `review: post-integration cleanup`) and ride into the same PR. Mid-confidence (60–79) findings get captured into the PR body under a **Deferred review findings** section with `file:line` references.

If `/code-review --auto` halts (lint or tests fail after applying review commits, and the review commit was reverted), behaviour depends on `--on-review-failure`:

- **`halt` (default)** — surface in RCA per "Halt semantics" as **integration review failure**. The PRD branch is left at its pre-review state; the user inspects and decides whether to re-run the fanout (which re-enters 4a) or merge by hand.
- **`continue`** — do not halt. The PRD branch is already at its pre-review state (the failing review commit was reverted), so it's the same green-individually state every slice arrived in via their own `/tdd` cycles. Capture the attempted findings (count, severity, `file:line` references, the reverted commit's sha for `git show <sha>`) and proceed to 4b. The captured payload rides into the PR body at 4c as the `## ⚠️ Integration review failed` section so the morning reviewer can re-run `/code-review` by hand. Used by `/afk-worker`.

#### 4b. Coverage check + auto-fix loop

Auto-chain `/zsl:verify-coverage --auto <parent>` against the
integrated tip. Verify-coverage runs Tier A then Tier B for every
in-scope user story (the per-story `AC<n>:` criteria
guaranteed at 1d mean there is no classification step), commits any
quarantined Tier-B-RED tests via `/commit`, files any gaps as
`ready-for-agent` sub-issues of the PRD, writes a coverage receipt,
and emits a structured terminal block.

Parse the terminal block's `matrix:` line and the receipt's
`verified-sha`. Then:

**Termination decision tree:**

| Outcome | Action |
|---|---|
| `mode: full`, `gap=0`, `deferred=0`, `verified-sha` == current tip | Loop done (full run). Proceed to 4c — closes the parent. |
| `mode: full`, `gap=0`, `deferred>0`, `verified-sha` == current tip | **Partial-complete.** Runnable slices are all merged and coverage-clean; only deferred stories remain. Do **not** loop, do **not** halt. Proceed to 4c — it omits `Closes #<parent>`, marks the PR `[partial]`, and adds a `## Deferred` section. |
| `mode: full`, `gap>0`, `verified-sha` == current tip | Gaps were filed. Update circuit-breaker counters (below). If a breaker fires → halt. Otherwise loop back to step 2 — the new gap sub-issues become the next wave. (Deferred stories are reported separately and do **not** count as gaps — see below.) |
| `mode: partial` | Halt: `coverage-mode mismatch`. `--auto` should never return `mode: partial` (that's the `--no-generate` receipt mode, unrelated to deferred stories); indicates a verify-coverage bug. |
| `verified-sha` ≠ current tip | Halt: `coverage-tree drift`. The tip moved between invocation and receipt write — should not happen inside the orchestrator. |
| verify-coverage halted internally | Halt: `coverage-verification failure`. Surface its terminal output. |

**Deferred ≠ gap.** A *gap* is a story claimed by a *shipped* slice but lacking a passing non-vacuous test — fixable now, so it loops back to step 2. A *deferred* story is one covered only by a not-yet-shipped slice (because that slice is gated behind an open `[HITL]`); there is nothing to fix this run, so it must **not** loop (it would re-file the same non-gap every round and never converge) and must **not** halt. verify-coverage reports the two in separate counts (`gap=<n>` vs `deferred=<n>` in its matrix block — see `/verify-coverage`); 4b loops only on `gap>0` and treats `deferred>0` as the partial-complete signal. The orchestrator already knows the deferred set from 1d/3b; the coverage `deferred` count is the cross-check.

**Circuit breakers (mandatory):**

Track in orchestrator state across rounds:

- `coverage_round` — incremented each time 4b runs. Cap is `--max-coverage-rounds` (default 3). On exhaustion → halt: `coverage-rounds-exhausted`.
- `gap_retry_count[<story-N>]` — incremented each time a gap is filed for story N (across rounds). If any story reaches 2 → halt: `coverage-per-story-exhausted`. Means Tier B keeps generating a test the remediation can't satisfy — usually a wrong-acceptance-criterion judgement or a misspecified story, needs a human eye.
- `no_progress_check` — if round N+1's gap set (by story numbers) equals round N's gap set → halt: `coverage-no-progress`. The loop isn't converging.

**Loop iteration mechanics:**

When looping back to step 2:

- Re-fetch the parent's sub-issues. The new gap sub-issues (just filed by verify-coverage) are now in the tree as `[automated-gap]` items labeled `ready-for-agent`. Treat them as discoverable AFK slices (they have no `[AFK]` prefix because verify-coverage doesn't assign one; recognise them by the `ready-for-agent` label and the absence of `[HITL]`).
- `merged`, `attempted`, and `satisfied_oob` carry over from the prior round (don't reset). Slices already merged stay merged; the loop only adds new fanout work on top.
- Step 3a picks the new gap-fix slices (their `## Blocked by` is "None" by template, so they're unblocked from round 2's pick).
- Step 3c spawns `/tdd` agents in worktrees just like the original fanout. Each remediation slice's acceptance criterion is literally "un-skip the quarantined test `<path::name>` and make it green," fully specified.
- After all gap-fix slices merge, step 3a sees `selected = empty, every discovered = merged` and falls through to step 4 again.
- 4a re-runs `/code-review --auto` on the now-bigger PRD branch tip. The reviewer sees the full diff (original slices + gap fixes); it'll mostly no-op on rounds 2+ because the new code is small and already reviewed by per-slice `/tdd`.
- 4b re-runs verify-coverage, this time hopefully with `gap=0`.

Halts in 4b leave the PRD branch with the latest verified state (gaps filed, quarantined tests committed, all original + remediation slices merged). The user takes over: read the matrix in the latest `## Coverage receipt — verify-coverage` comment, decide whether to fix by hand, edit the offending stories' `AC<n>:` acceptance criteria and re-invoke, or close specific gap issues as bogus and re-invoke.

#### 4c. Ship the integration PR

1. **Defensive commit pass.** Delegate to `/zsl:commit`. Skip if `git status --porcelain` is empty — the normal case, since every commit landed via per-wave merges (3e), 4a's review cleanup, or 4b's verify-coverage `/commit`-delegated quarantined-test commits across all loop rounds. If the tree is unexpectedly dirty (a hook wrote a generated file, etc.), `/commit` handles it under its session-vs-other-origin rules. Never open-code `git add`/`git commit` here — the no-`-A`, no-attribution, other-origin-confirmation rules live in one place.

2. **Push with upstream:**
   ```bash
   git push -u origin <prd-branch>
   ```
   Surface errors verbatim and stop on failure. Never `--force`, never `--no-verify`. (Same safety rails `/commit-push-pr` enforces — same rules, inlined here because `/tdd-parallel` needs its own structured PR template that `/commit-push-pr` doesn't produce.)

3. **Open the PR** with the structured integration template:

   ```
   gh pr create \
     --title "<title>" \
     --base main \
     --body "<see template>"
   ```

   Title is `<parent-title> (#<parent-num>)` on a full run (`deferred=0`), and `[partial] <parent-title> (#<parent-num>)` when `deferred>0`. The `[partial]` marker is the at-a-glance signal that the PRD stays open after this PR merges.

   PR body template:

   ```markdown
   ## Summary

   <one-line, parsed from the parent issue's `## Solution` section if present; otherwise the parent's title>

   ## ⚠️ Integration review failed

   Included **only when** 4a fell through under `--on-review-failure=continue`. Omit this whole section otherwise.

   `/code-review --auto` attempted <N> findings against the PRD branch tip but lint/tests failed after applying them; the review commit was reverted. The slices below were all individually green via their own `/tdd` cycles — cross-slice cleanup just didn't land. Re-run `/code-review` against this PR locally before merging.

   - Attempted findings: <count by severity, with `file:line` references>
   - Reverted review commit: <sha> (inspect via `git show <sha>`)

   ## Slices integrated

   In wave order, oldest first:

   - `[AFK] 1 — Slice 1 title` — #N
   - `[AFK] 2a — Slice 2a title` — #N
   - `[AFK] 2b — Slice 2b title` — #N
   - `[AFK] 3 — Slice 3 title` — #N

   ## Auto-fixed coverage gaps

   Filed and closed by `/verify-coverage --auto` across N coverage rounds. Omit this section if all gaps were resolved in round 1 (i.e. the coverage loop ran exactly once and returned `gap=0`).

   - Story <M>: `Cover PRD story <M> — <description>` — #N
   - ...

   ## Deferred

   Included **only when** `deferred>0` (a partial run). Omit this whole section on a full run.

   This run shipped every slice whose `Blocked by` closure is free of open `[HITL]` gates and deferred the rest. The parent PRD (#<parent>) stays **open** until the remainder lands.

   - Gating open `[HITL]` issue(s): `#<n> — <title>`, …
   - Deferred slices: `#<n> — <title>` (each downstream of a gate above, or still in triage)
   - Deferred user stories: <story numbers covered only by the deferred slices>

   **Re-entry:** clear the gate(s) via `/human-itl <parent>`, then re-run `/tdd-parallel <parent>` to land the remainder. The merged sub-issues below are already closed, so the next run only fans out what's left; the now-closed `[HITL]` slice satisfies its downstream slices via `satisfied_oob`.

   ## Closes

   On a **full run** (`deferred=0`) — closes the parent and every merged sub-issue:

   ```
   Closes #<parent>
   Closes #<sub-issue-1>
   Closes #<sub-issue-2>
   ...
   ```

   On a **partial run** (`deferred>0`) — OMIT `Closes #<parent>` (the PRD must stay open) and close only the merged sub-issues:

   ```
   Closes #<sub-issue-1>
   Closes #<sub-issue-2>
   ...
   ```

   ---
   Integrated by `/tdd-parallel` across <N> waves and <R> coverage rounds.
   <On a partial run, append: " — partial run, <N> slice(s) deferred behind open [HITL] gate(s); PRD left open.">
   ```

   If `gh pr create` fails because a PR for this branch already exists (e.g. a prior halted run pushed and opened it), fall back to `gh pr view --json url -q .url` and report the existing PR URL. If the repo has an auto-PR workflow (`.github/workflows/auto-pr.yml`) and the push already created the PR, skip `gh pr create` and resolve the URL the same way.

4. **Project board update** (if `docs/agents/project-board.md` exists). Bulk-move every merged sub-issue's project card (including the auto-filed gap issues from 4b) from "In progress" to the option mapped to "PR opened" (typically `In review`) via `updateProjectV2ItemFieldValue`. On a **full run**, also move the parent's card. On a **partial run** (`deferred>0`), **leave the parent's card where it is** (`In progress` / `tracking`) — the parent stays open and is still a tracking container. Use the same lookup-then-update procedure documented in `triage/SKILL.md` step 6. **This step is mandatory when the file exists — do not treat it as optional.** If an individual update fails, log the failure and continue with the rest of the items; only abort if every update fails (that would indicate a credential or project-id problem worth surfacing).

When the integration PR merges, GitHub's auto-close workflow closes every `Closes #N` issue and lands each card on `Done`. On a partial run, the parent is deliberately absent from `Closes`, so it stays open and on its tracking status — a later run lands the remainder and (being a full run then) closes it.

#### 4d. Re-run idempotency (partial runs)

A partial run needs **no special re-entry machinery** — a second `/tdd-parallel <parent>` after the gate clears lands the remainder by the same paths the first run used:

- The partial PR's merge closes its shipped sub-issues, so the next run's step-2 Open filter excludes them automatically — they aren't re-fanned-out.
- The `[HITL]` slice, once `/human-itl` closes it, satisfies its downstream slices via the existing `satisfied_oob` path in 3a (closed + a member of the parent's sub-tree).
- The parent PRD is still open (4c omitted `Closes #<parent>` on the partial run), so it remains the tracking container and the second run — now a full run with `deferred=0` — closes it via the normal `Closes #<parent>`.

The single hard requirement is that the partial run did **not** close the parent (4c). Everything else falls out of the existing Open-filter + `satisfied_oob` mechanics — there is no partial-specific state persisted between runs.

### 5. Done

Print a final summary:

- Parent issue + integration PR URL. State whether this was a **full run** (parent will close on merge) or a **`[partial]` run** (parent left open).
- Slices integrated, in merge order: number + title.
- **Deferred** (partial runs only): the open `[HITL]` gate(s), the deferred slices, the deferred user-story numbers, and the re-entry recipe (`/human-itl <parent>` then re-run `/tdd-parallel <parent>`).
- Auto-fixed coverage gaps, by round: which stories triggered a gap, which sub-issues were filed, which round finally cleared them.
- Total waves processed (across all coverage rounds).
- Total coverage rounds (final receipt's `verified-sha` matches the PR's tip).

The orchestrator session can now be closed. Slice worktrees and branches remain on disk; pre-flight 1b will sweep them on the next `/tdd-parallel` run, or you can clean them sooner by hand.

## Halt semantics

Seven failure paths halt the run, all with the same shape: print a hybrid RCA, leave state inspectable, stop. The orchestrator does not attempt resume — the user takes over from the halted state.

- **Pre-flight refusal** (1d): the parent isn't a PRD, an *in-scope* story carries no `AC<n>:` criterion, or **no slice is runnable** (every slice is deferred behind an open `[HITL]` or still in triage). Open `[HITL]` slices *alongside* runnable ones no longer refuse — they trigger a partial run. Refuses up front, before any branch work — no state to inspect.
- **Agent failure** (3d): a sub-agent errored, refused, or returned without a mergeable branch.
- **Unresolvable merge conflict** (3e): `git merge --no-ff` conflicted and the orchestrator's auto-resolve attempt couldn't produce a clean, lint+test-passing merge. The merge is left in its conflicted state on the PRD branch.
- **Zero-progress** (3a): no slices unblock and the fanout isn't complete.
- **Integration review failure** (4a, under default `--on-review-failure=halt`): `/code-review --auto` applied ≥80 findings to the merged PRD tip but lint or tests failed afterward; the review commit was reverted. The PRD branch is at pre-review state with all slices merged. Under `--on-review-failure=continue` this is **not** a halt — 4a falls through to 4b with a captured payload that lands in the PR body at 4c as `## ⚠️ Integration review failed`.
- **Coverage verification failure** (4b): `/verify-coverage --auto` itself halted internally (pre-flight refusal, mutation-check failure, tracker error). All slices for the round are merged but the receipt wasn't written.
- **Coverage circuit-breaker halt** (4b): one of three breakers fired during the auto-fix loop:
  - `coverage-rounds-exhausted` — hit `--max-coverage-rounds` without converging to `gap=0`.
  - `coverage-per-story-exhausted` — a single story produced a gap in 2+ rounds; Tier B's test is wrong or the story's acceptance criteria are misspecified.
  - `coverage-no-progress` — round N+1's gap set equals round N's; loop isn't converging.
  - `coverage-mode mismatch` / `coverage-tree drift` — invariant-violation halts; should not happen in normal operation.

  In every coverage circuit-breaker case, all originally-discovered and gap-fix slices remain merged onto the PRD branch; the latest coverage receipt records the residual matrix; the user takes over from there.

When a halt fires while other agents are still in flight, the orchestrator waits for those agents to return (so it can capture their state in the RCA), then halts. It does *not* cancel them mid-flight — let them either complete or escalate, and surface their final state.

## RCA shape

Every halt produces a structured RCA followed by an LLM-generated **Possible interpretation** paragraph. The structured part is deterministic, gathered via `git` and `gh`. The interpretation reads those facts and proposes the most likely cause — treat the facts as authoritative and the interpretation as a hint.

**Common header (all halt types):**

- Halt cause: agent failure / merge conflict / zero-progress.
- Last successful integration sha on the PRD branch.
- Slices already merged into the PRD branch (issue numbers).
- Slices still in flight when the halt fired (issue numbers + their final state on return).

**Agent failure (3d):**

- Failing slice: number, title, wave/letter, branch.
- Failure category: escalation / tool error / `/tdd` red-green-refactor failed / unknown.
- Agent's final return message verbatim (truncated if long).
- What the agent committed before failing (commit count, last commit subject, branch sha).
- Suggested next action: `cd <agent-worktree>` to inspect, retry by re-running `/tdd <num>` manually, or amend the slice's brief and re-run `/tdd-parallel`.

**Unresolvable merge conflict (3e):**

- Slices involved: the source slice being merged in (number, title, wave/letter, branch) and the integration tip's last merged slice (number, title).
- Files conflicted with line ranges (`git diff --check`).
- A short diff hunk from each side of the conflict (so the user can see intent without leaving the orchestrator).
- Auto-resolve outcome: what the orchestrator tried (which files it edited, which it skipped) and why it gave up (binary/lockfile, lint failure, test failure, semantic ambiguity).
- Wave classification: `same-wave overlap` (both slices in wave N — indicates `/to-issues` mis-sliced), `cross-wave drift` (downstream slice rebased onto an upstream wave that touched the same area), or `unknown`.
- `Blocked by` references each slice declared (helps spot a missing dependency that should have serialised them).
- Suggested next action: resolve the conflict in the orchestrator's checkout (already on the PRD branch, mid-merge), commit, run `/tdd-parallel` again to continue.

**Zero-progress (3a):**

- Un-attempted slices remaining: number, title, `Blocked by` references each is waiting on.
- Reference classification per blocker: `cycle` (other un-attempted siblings forming a cycle), `external-open` (an *open* issue outside the parent's sub-tree), `unresolvable` (non-existent issue number). An open `[HITL]` blocker never reaches this list — its downstream slices are `deferred` and handled by 3a's partial-complete branch, so an open `[HITL]` causes a partial run, not a zero-progress halt. A blocker that is closed/done within the parent's sub-tree never reaches this list either — 3a absorbs it into `satisfied_oob` — so it is never classified `unresolvable`; a halt that names a blocker you know is finished is a bug in the 3a predicate, not bad tracker data.
- Suggested next action: for `cycle` / `external-open` / `unresolvable`, edit the offending `Blocked by` sections to break the cycle / reference the right issue / drop the external dep, then re-run `/tdd-parallel`. (An open `[HITL]` blocker is not a zero-progress cause under partial runs — it defers its downstream and the run completes partially; clear it with `/human-itl <parent>` and re-run to land the remainder via `satisfied_oob`.)

**Integration review failure (4a):**

- PRD branch tip sha at review start.
- Findings the autonomous review tried to apply: count by severity, with `file:line` references.
- Lint/test failure: which command failed, last 50 lines of output.
- Reverted review commit sha (for inspection via `git show <sha>`).
- Suggested next action: inspect the reverted commit to see what the review attempted. Either fix the underlying issue and re-run `/tdd-parallel <parent>` (which finds slices already merged and re-enters 4a), or apply the review findings selectively by hand and continue from 4b manually.

**Coverage verification failure (4b):**

- Integration tip sha (the PRD branch HEAD; original slices + any gap fixes from prior rounds are merged).
- Coverage round in which verify-coverage halted (1-indexed).
- Verify-coverage's terminal output verbatim (or summary if long): the halt reason, the matrix counts up to that point, and any partial receipt path.
- Suggested next action: run `/verify-coverage <parent>` manually against the PRD branch to inspect the failure outside the orchestrator; fix the root cause (commonly: a story whose acceptance criteria are too vague to generate a non-vacuous test against, a Tier B mutation that can't be reverted cleanly because the working tree was dirty, or a tracker-side failure to file the gap issue), then re-run `/tdd-parallel <parent>` — it picks up where it left off (slices already merged, gap issues already filed from prior rounds).

**Coverage circuit-breaker halt (4b):**

- Integration tip sha (PRD branch HEAD; everything merged).
- Which breaker fired: `coverage-rounds-exhausted` / `coverage-per-story-exhausted` / `coverage-no-progress` / `coverage-mode mismatch` / `coverage-tree drift`.
- Round counter and `--max-coverage-rounds` cap.
- Per-round gap set (by story numbers): round 1 → {…}, round 2 → {…}, …
- For `coverage-per-story-exhausted`: the offending story number, its `AC<n>:` acceptance criteria verbatim, and the paths of both rounds' quarantined tests (so the user can compare what Tier B generated each time).
- Filed gap issue numbers (still open, awaiting human disposition).
- Suggested next action depends on the breaker:
  - `coverage-rounds-exhausted` or `coverage-no-progress`: read the residual matrix in the latest `## Coverage receipt — verify-coverage` comment, fix by hand, then either push manually or re-invoke with a higher `--max-coverage-rounds`.
  - `coverage-per-story-exhausted`: usually the story's acceptance criteria are misspecified — edit the PRD's story to pin better acceptance criteria, then re-invoke. Alternatively close the bogus gap issues and re-invoke.
  - `coverage-mode mismatch` / `coverage-tree drift`: bug — open an issue with the receipt and orchestrator logs; do not just retry.

## Cleanup

The framework auto-cleans nothing during the run. After the integration PR merges:

- `git worktree remove .worktrees/<num>-<slug>` for each slice.
- `git branch -d tdd/<num>-<slug>` (force with `-D` only if upstream branch was force-pushed).

Pre-flight 1b sweeps these on the next `/tdd-parallel` run, so manual cleanup is optional unless you want the disk space back sooner.

## Constraints

- **Orchestrator session must stay open** through the entire run, including all coverage-loop rounds. Closing it mid-loop abandons in-flight sub-agents and leaves the PRD branch with whatever was merged plus any gaps that hadn't been re-fanouted yet.
- **The user's checkout is the integration surface.** During the run, the orchestrator's main checkout sits on the PRD branch with merges accumulating on it. On halt, the user inspects/resolves in place.
- **PR-style repos only.** Direct-push repos that want parallel fanout should run `/tdd-parallel` after switching their `ship-style.md` to PR-style for the duration, or run individual `/tdd` sessions in parallel by hand.
- **Full-auto in the happy path.** Pre-flight 1d is the last human gate. From there to PR-push, the only human surface is a halt's RCA. Circuit breakers (4b) ensure the loop terminates even when verify-coverage makes wrong calls — pick the right `--max-coverage-rounds` for your appetite (default 3; lower for tight quality bars, higher for forgiving Tier B environments).
