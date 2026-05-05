---
name: tdd-parallel
description: Fan out the unblocked [AFK] sub-tasks of a parent (PRD) issue into parallel /tdd sub-agents in worktrees. Sub-agents commit but do NOT push; the orchestrator merges every slice branch onto the PRD branch in wave order with --no-ff, then opens a single integration PR. AFK-only — [HITL] slices are skipped. PR-style repos only.
disable-model-invocation: true
---

# Parallel TDD

Fan out the unblocked **[AFK]** sub-tasks of a parent issue into parallel `/tdd` sub-agents. Each sub-agent runs `/tdd <num> --no-ship` in its own worktree, committing locally but never pushing. The orchestrator merges every slice branch onto the parent's PRD branch (which doubles as the integration branch) in wave order with `--no-ff`, then opens a single integration PR.

`[HITL]` slices are filtered out — they require human interaction and must be run via `/tdd` directly. PR-style repos only — direct-push fanouts merge straight to `main` without consolidation.

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

When an agent escalates, the orchestrator relays the question to the user and resumes the agent via `SendMessage` with the user's answer. Anything that would routinely need human input mid-flight isn't AFK and shouldn't be in the fanout — it belongs as an `[HITL]` slice.

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

- `merged` — set of sub-task issue numbers whose branches have been merged onto the PRD branch.
- `attempted` — set of sub-task issue numbers we've spawned an agent for.

#### 3a. Pick the next wave

A slice is **unblocked** when every issue in its `Blocked by` section is in `merged`. (Issue *closure* is irrelevant in this architecture — sub-issues never close mid-fanout because they're never pushed.)

Pick all unblocked, not-yet-attempted slices, sorted by issue number, capped by `--max`.

If the picked set is empty:

- If `merged` covers every discovered slice → fanout complete. Go to step 4.
- Otherwise → **zero-progress halt** with hybrid RCA (see "RCA shape" below). Most likely cause: a circular `Blocked by`, a slice depending on an issue outside this fanout, or a reference to a non-existent issue. Stop.

#### 3b. Show the wave to the user

Print buckets:

- **Selected** (numbered): issue number + title + branch name + worktree path.
- **Skipped — over cap (this wave)**: issue number + title.
- **Skipped — HITL**: issue number + title; tell the user to run `/tdd <num>` directly in a normal session.
- **Already merged**: list of issue numbers from prior waves.
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
3. Spawn the sub-agent (all in a single message so they run concurrently):

```
Agent({
  description: "TDD <num>",
  subagent_type: "general-purpose",
  run_in_background: true,
  name: "tdd-<num>",
  prompt: <see template below>
})
```

Sub-agent prompt template:

```
You are running AFK as part of a /tdd-parallel fanout.

First action: cd <ABSOLUTE-PATH-TO-WORKTREE>

Then run: /tdd <num> --no-ship

You operate under the AFK contract:
- Make reasonable decisions and finish without coming back to ask routine questions.
- Escalate (return early with a question) ONLY for: destructive ops needing confirmation per auto mode rules, missing access/credentials, or genuine architectural ambiguity that would change a public contract.
- Be specific about what you need if you do escalate.

When done, report: branch name, last commit sha, the slice issue number you worked on (so the orchestrator can map slice → issue), and a one-paragraph summary of changes. Do NOT push. Do NOT open a PR.
```

Add each spawned issue number to `attempted`. Pass the *absolute* worktree path in the prompt — the sub-agent's first action must be to `cd` there before doing anything else, so its Bash CWD lands in the right worktree for the remainder of its session.

#### 3d. Wait for the wave to finish

Process completion notifications as they arrive. For each completing agent:

1. Read its result.
2. **If escalated** (returned with a question rather than a completion summary): relay the question to the user verbatim, get their answer, then resume the agent: `SendMessage({ to: "tdd-<num>", message: <user's answer> })`. Do not proceed until the agent returns properly.
3. **If failed** (errored, refused, or returned without a mergeable branch and not as an escalation): **halt** with hybrid RCA. Stop.
4. **If completed normally**: record the branch name and commit sha.

Wait until **all** agents in the current wave have completed normally before moving to merge. (Halts in 3d cancel the rest — see "Halt semantics" below.)

#### 3e. Merge the wave

The orchestrator is on the PRD branch. Merge each of the wave's slice branches in order — by letter for lettered slices (`1a`, `1b`, `1c`), by issue number otherwise. For each:

1. `git merge --no-ff tdd/<num>-<slug> -m "Merge slice [AFK] <wave><letter> — <slice-title> (#<num>)"`.
2. **If git reports a conflict**: leave the merge in its conflicted state (do *not* `git merge --abort` — the user inspects the conflict in place). Halt with hybrid RCA. Stop.
3. **On success**: add the slice's issue number to `merged`. Continue to the next branch.

#### 3f. Loop

Go back to 3a. Newly-unblocked slices (whose `Blocked by` references are now all in `merged`) become the next wave's candidates.

### 4. Open the integration PR

After all discovered slices are merged:

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

3. **Project board update** (best-effort, if `docs/agents/project-board.md` exists). Bulk-move the parent issue and every merged sub-issue's project card from "In progress" to the option mapped to "PR opened" (typically `In review`) via `updateProjectV2ItemFieldValue`. Use the same lookup-then-update procedure documented in `triage/SKILL.md` step 6. Log failures but do not abort — label/PR state is the source of truth, the board sync is best-effort.

When the integration PR merges, GitHub's auto-close workflow closes every `Closes #N` issue and lands each card on `Done`.

### 5. Done

Print a final summary:

- Parent issue + integration PR URL.
- Slices integrated, in merge order: number + title.
- HITL slices skipped (with the hint to run `/tdd <num>` directly).
- Total waves processed.

The orchestrator session can now be closed. Slice worktrees and branches remain on disk; pre-flight 1b will sweep them on the next `/tdd-parallel` run, or you can clean them sooner by hand.

## Halt semantics

Three failure paths halt the run, all with the same shape: print a hybrid RCA, leave state inspectable, stop. The orchestrator does not attempt resume — the user takes over from the halted state.

- **Agent failure** (3d): a sub-agent errored, refused, or returned without a mergeable branch.
- **Merge conflict** (3e): `git merge --no-ff` reported a conflict. The merge is left in its conflicted state on the PRD branch.
- **Zero-progress** (3a): no slices unblock and the fanout isn't complete.

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

**Merge conflict (3e):**

- Slices involved: the source slice being merged in (number, title, wave/letter, branch) and the integration tip's last merged slice (number, title).
- Files conflicted with line ranges (`git diff --check`).
- A short diff hunk from each side of the conflict (so the user can see intent without leaving the orchestrator).
- Wave classification: `same-wave overlap` (both slices in wave N — indicates `/to-issues` mis-sliced), `cross-wave drift` (downstream slice rebased onto an upstream wave that touched the same area), or `unknown`.
- `Blocked by` references each slice declared (helps spot a missing dependency that should have serialised them).
- Suggested next action: resolve the conflict in the orchestrator's checkout (already on the PRD branch, mid-merge), commit, run `/tdd-parallel` again to continue.

**Zero-progress (3a):**

- Un-attempted slices remaining: number, title, `Blocked by` references each is waiting on.
- Reference classification per blocker: `cycle` (other un-attempted siblings forming a cycle), `external` (issue outside the parent's sub-tree), `unresolvable` (non-existent issue number).
- Suggested next action: edit the offending `Blocked by` sections in the issue tracker to break the cycle / reference the right issue / drop the external dep, then re-run `/tdd-parallel`.

## Cleanup

The framework auto-cleans nothing during the run. After the integration PR merges:

- `git worktree remove .worktrees/<num>-<slug>` for each slice.
- `git branch -d tdd/<num>-<slug>` (force with `-D` only if upstream branch was force-pushed).

Pre-flight 1b sweeps these on the next `/tdd-parallel` run, so manual cleanup is optional unless you want the disk space back sooner.

## Constraints

- **Orchestrator session must stay open** through the entire run. Closing it before step 4 abandons in-flight sub-agents and leaves the PRD branch with whatever was merged.
- **The user's checkout is the integration surface.** During the run, the orchestrator's main checkout sits on the PRD branch with merges accumulating on it. On halt, the user inspects/resolves in place.
- **PR-style repos only.** Direct-push repos that want parallel fanout should run `/tdd-parallel` after switching their `ship-style.md` to PR-style for the duration, or run individual `/tdd` sessions in parallel by hand.
