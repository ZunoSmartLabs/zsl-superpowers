---
name: tdd-parallel
description: Fan out the unblocked [AFK] sub-tasks of a parent (PRD) issue into parallel /tdd sub-agents in worktrees. Sub-agents commit but do NOT push; the orchestrator merges every slice branch onto the PRD branch in wave order with --no-ff, then opens a single integration PR. AFK-only — [HITL] slices are skipped. PR-style repos only.
disable-model-invocation: true
---

# Parallel TDD

Fan out the unblocked **[AFK]** sub-tasks of a parent issue into parallel `/tdd` sub-agents. Each sub-agent runs `/tdd <num> --no-ship` in its own worktree, committing locally but never pushing. The orchestrator merges every slice branch onto the parent's PRD branch (which doubles as the integration branch) in wave order with `--no-ff`, then opens a single integration PR.

`[HITL]` slices are filtered out — they require a manual human action and are cleared via `/human-itl` (not `/tdd` — a HITL slice is a manual action, not a unit of red-green-refactor). PR-style repos only — direct-push fanouts merge straight to `main` without consolidation.

## Why one PR

Each push to a feature branch triggers CI workflows. With N sub-issues = N PRs you'd pay N × M CI runs over the life of a fanout. Staging slice work locally and pushing one consolidated branch costs one CI run. Trade-offs: one PR is a single review surface (no per-slice review granularity), and merge conflicts surface during local integration rather than during PR review. Both are acceptable when the wave model from `/to-issues` asserts same-wave slices are disjoint.

## Usage

```
/tdd-parallel <parent-issue> [--max N]
```

- `<parent-issue>` — the parent (PRD) issue whose unblocked AFK sub-tasks should be fanned out.
- `--max N` — concurrency cap *within a wave*. Default 2.

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

Three phases. 1a refuses on failure; 1b cleans up silently and continues; 1c either creates or adopts the PRD branch.

#### 1a. Environment validation

Refuse with a clear error message if any of these fail.

- `docs/agents/ship-style.md` exists **and** says PR-style. Direct-push fanouts are unsupported — they'd land slices on `main` directly without consolidation, defeating the point.
- `docs/agents/issue-tracker.md` exists.
- `docs/agents/triage-labels.md` exists.

Append `.worktrees/` to the repo root `.gitignore` if not already present.

#### 1b. Auto-clean stale slice worktrees and branches

Scan `.worktrees/*`. For each entry whose name matches `<num>-<slug>`:

1. Parse the issue number from the directory name.
2. Query the issue tracker for the issue's state.
3. **Skip** if the issue is OPEN — not ours to remove.
4. **Skip** if `git -C .worktrees/<dir> status --porcelain` is non-empty — uncommitted changes; the user should investigate.
5. Otherwise:
   - `git worktree remove .worktrees/<num>-<slug>` (no `--force`)
   - `git branch -d tdd/<num>-<slug>` (no `-D`)
6. If `git branch -d` refuses because the branch isn't fully merged, **skip and log** — never `-D` automatically.

Print a one-block summary: `cleaned`, `skipped — open`, `skipped — uncommitted`, `skipped — unmerged branch`. Do not refuse on any skip.

#### 1c. Determine the PRD branch

The PRD branch doubles as the integration branch — sub-task branches will be merged onto it, and it gets pushed once at the end as the integration PR's source.

- Run `git fetch origin`.
- Refuse if the working tree is dirty (`git status --porcelain` non-empty) or HEAD is detached.
- **If the orchestrator is on `main`**: create the PRD branch and switch to it.
  - Branch name: `feature/<parent-num>-<slug>`. Slug is kebab-case of the parent issue title, max 40 chars.
  - `git checkout -b feature/<parent-num>-<slug>` from `main`'s tip.
- **If the orchestrator is on a non-`main` branch**: treat it as the PRD branch. Do not switch, do not auto-rebase against `main` — the user owns its relationship to `main`.

After 1c the orchestrator is on the PRD branch with a clean working tree.

### 2. Discover the dependency graph

Using `docs/agents/issue-tracker.md` conventions, fetch the parent issue's sub-issues. Keep only those that are:

- Open
- Title starts with `[AFK]` (`[HITL]` filtered out)
- Carry the configured `ready-for-agent` label
- Not a container (have no open sub-issues of their own)

For each surviving slice, parse the `## Blocked by` section to extract referenced issue numbers. Build the dependency graph in memory.

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

- If every discovered slice is in `merged` → fanout complete. Go to step 4.
- Otherwise → **zero-progress halt** with hybrid RCA (see "RCA shape" below). By construction this now means a genuine graph fault — a circular `Blocked by`, a slice depending on an *open* issue outside this fanout, or a reference to a non-existent issue — because any blocker satisfiable by an out-of-band close was already absorbed into `satisfied_oob` above. Stop.

#### 3b. Show the wave to the user

Print buckets:

- **Selected** (numbered): issue number + title + branch name + worktree path.
- **Skipped — over cap (this wave)**: issue number + title.
- **Skipped — HITL**: issue number + title; tell the user to clear them with `/human-itl <parent>` (the manual steps a coding agent can't perform), then re-run this fanout — not `/tdd`.
- **Already merged**: list of issue numbers from prior waves.
- **Satisfied out-of-band**: issue numbers in `satisfied_oob` (closed/done outside this fanout — e.g. a `[HITL]` slice cleared by `/human-itl`), each with the slice it unblocked. Empty on a clean first run; non-empty after a `/human-itl` round-trip.
- **Pending future waves**: issue number + title + the `Blocked by` references it's still waiting on.

Confirm with the user before proceeding.

#### 3c. Create slice worktrees and spawn sub-agents

For each selected slice, derive:

- Slug: kebab-case of the issue title, max 40 chars.
- Branch: `tdd/<num>-<slug>`.
- Worktree path: `.worktrees/<num>-<slug>/`.

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

#### 4a. Coverage gate (mandatory)

An **execution gate, not an outcome gate**: it enforces that
`/verify-coverage` *ran* against the integrated tip, never that its
matrix came back clean. Open gaps are fine — they ride a later fanout;
skipping the check is what's blocked.

1. Fetch the latest coverage receipt for this PRD per
   `docs/agents/issue-tracker.md`: GitHub/GitLab → the most recent PRD
   comment whose first line is `## Coverage receipt — verify-coverage`;
   local-markdown → `.scratch/<feature>/verify-coverage-receipt.md`.
2. The receipt is **valid** iff *both*:
   - `mode: full` (a `--no-generate` `partial` receipt does not count), and
   - its `verified-sha` equals the PRD branch tip (`git rev-parse HEAD`) —
     nothing was integrated after it ran.
3. **Valid** → proceed to 4b.
4. **Missing, partial, or stale** → block. Do not push, do not open the
   PR. Tell the user verbatim:

   > Coverage gate: this fanout integrated <N> slices, but
   > `/verify-coverage <parent>` has not been run against the current
   > integrated tip (<no receipt | partial `--no-generate` run | receipt
   > is for an older sha>). This run stays open — invoke
   > `/verify-coverage <parent>` now (it's `disable-model-invocation`;
   > the orchestrator never chains it), then reply to continue. Reply
   > `skip` to abandon the PR and take the integrated branch over by hand.

   This is a blocking checkpoint, like an escalating sub-agent — the
   orchestrator session is required to stay open anyway (Constraints).
   When the user says they're done, re-fetch and re-validate (step 2);
   loop until valid. The user's `/verify-coverage` run commits its
   quarantined tests onto the PRD branch, so they ride this same PR; any
   gap sub-issues it files ride a *later* `/tdd-parallel <parent>`, not
   this run. If the user replies `skip` → **coverage-gate halt** (see
   Halt semantics): leave the integrated branch in place, unpushed, no PR.

#### 4b. Push and open the PR

1. `git push -u origin <prd-branch>`.
2. Open the PR:

```
gh pr create \
  --title "<parent-title> (#<parent-num>)" \
  --base main \
  --body "<see template>"
```

PR body template:

```markdown
## Summary

<one-line, parsed from the parent issue's `## Solution` section if present; otherwise the parent's title>

## Slices integrated

In wave order, oldest first:

- `[AFK] 1 — Slice 1 title` — #N
- `[AFK] 2a — Slice 2a title` — #N
- `[AFK] 2b — Slice 2b title` — #N
- `[AFK] 3 — Slice 3 title` — #N

## Closes

Closes #<parent>
Closes #<sub-issue-1>
Closes #<sub-issue-2>
...

---
Integrated by `/tdd-parallel` across <N> waves.
```

3. **Project board update** (if `docs/agents/project-board.md` exists). Bulk-move the parent issue and every merged sub-issue's project card from "In progress" to the option mapped to "PR opened" (typically `In review`) via `updateProjectV2ItemFieldValue`. Use the same lookup-then-update procedure documented in `triage/SKILL.md` step 6. **This step is mandatory when the file exists — do not treat it as optional.** If an individual update fails, log the failure and continue with the rest of the items; only abort if every update fails (that would indicate a credential or project-id problem worth surfacing).

When the integration PR merges, GitHub's auto-close workflow closes every `Closes #N` issue and lands each card on `Done`.

### 5. Done

Print a final summary:

- Parent issue + integration PR URL.
- Slices integrated, in merge order: number + title.
- HITL slices skipped (with the hint to clear them with `/human-itl <parent>`, then re-run this fanout).
- Total waves processed.

The orchestrator session can now be closed. Slice worktrees and branches remain on disk; pre-flight 1b will sweep them on the next `/tdd-parallel` run, or you can clean them sooner by hand.

## Halt semantics

Four failure paths halt the run, all with the same shape: print a hybrid RCA, leave state inspectable, stop. The orchestrator does not attempt resume — the user takes over from the halted state.

- **Agent failure** (3d): a sub-agent errored, refused, or returned without a mergeable branch.
- **Unresolvable merge conflict** (3e): `git merge --no-ff` conflicted and the orchestrator's auto-resolve attempt couldn't produce a clean, lint+test-passing merge. The merge is left in its conflicted state on the PRD branch.
- **Zero-progress** (3a): no slices unblock and the fanout isn't complete.
- **Coverage gate declined** (4a): the user replied `skip` to the mandatory coverage gate. All slices are merged onto the PRD branch but it is left unpushed with no PR — the user pushes and opens it by hand if they choose to.

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
- Reference classification per blocker: `cycle` (other un-attempted siblings forming a cycle), `external-open` (an *open* issue outside the parent's sub-tree), `unresolvable` (non-existent issue number), `open-hitl` (a `[HITL]` slice in the parent's sub-tree, not yet cleared). A blocker that is closed/done within the parent's sub-tree never reaches this list — 3a absorbs it into `satisfied_oob` — so it is never classified `unresolvable`; a halt that names a blocker you know is finished is a bug in the 3a predicate, not bad tracker data.
- Suggested next action: for `cycle` / `external-open` / `unresolvable`, edit the offending `Blocked by` sections to break the cycle / reference the right issue / drop the external dep. For `open-hitl`, run `/human-itl <parent>` to clear the manual step. Then re-run `/tdd-parallel` — the cleared blocker is now picked up via `satisfied_oob`.

**Coverage gate declined (4a):**

- Integration tip sha (the PRD branch HEAD, fully merged, unpushed).
- Slices merged into it (issue numbers) — the work is intact, only the PR step was skipped.
- Receipt state at decline: `none` / `partial (--no-generate)` / `stale (verified-sha <sha> ≠ tip <sha>)`.
- Suggested next action: run `/verify-coverage <parent>` against the PRD branch (it commits its quarantined tests onto this same branch), then `git push -u origin <prd-branch>` and open the PR by hand — or re-run `/tdd-parallel <parent>`, which finds every slice already merged and stops again at the now-satisfiable gate.

## Cleanup

The framework auto-cleans nothing during the run. After the integration PR merges:

- `git worktree remove .worktrees/<num>-<slug>` for each slice.
- `git branch -d tdd/<num>-<slug>` (force with `-D` only if upstream branch was force-pushed).

Pre-flight 1b sweeps these on the next `/tdd-parallel` run, so manual cleanup is optional unless you want the disk space back sooner.

## Constraints

- **Orchestrator session must stay open** through the entire run. Closing it before step 4 abandons in-flight sub-agents and leaves the PRD branch with whatever was merged.
- **The user's checkout is the integration surface.** During the run, the orchestrator's main checkout sits on the PRD branch with merges accumulating on it. On halt, the user inspects/resolves in place.
- **PR-style repos only.** Direct-push repos that want parallel fanout should run `/tdd-parallel` after switching their `ship-style.md` to PR-style for the duration, or run individual `/tdd` sessions in parallel by hand.
