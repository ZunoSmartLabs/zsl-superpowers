# The end-to-end loop

The skills compose into one engineering loop. Most days you only touch a few of them.

## One-time setup

[`/zsl:setup-zsl-superpowers`](setup.md)
:   Configure the issue tracker, triage label vocabulary, domain doc layout, and ship style for the repo. Run once before anything else.

## Plan

[`/zsl:grill-me`](skills.md#grill-me) or [`/zsl:grill-with-docs`](skills.md#grill-with-docs)
:   Interview yourself to surface what you're actually building. `grill-with-docs` also updates `CONTEXT.md` and ADRs inline.

[`/zsl:to-prd`](skills.md#to-prd)
:   Synthesise that conversation into a PRD on the issue tracker.

## Break down

[`/zsl:to-issues`](skills.md#to-issues)
:   Break the PRD into vertical-slice sub-issues. Children are labeled `needs-triage`; the PRD parent is auto-relabeled to `tracking`. Slice titles use the `[AFK|HITL] <wave>[<letter>] — <description>` format so the dependency graph reads at a glance (same wave = runnable in parallel).

[`/zsl:triage`](skills.md#triage)
:   Triage **each child** to `ready-for-agent` (with an agent brief), `ready-for-human`, or `needs-info`. Skip triaging the PRD itself; you just wrote it.

## Build

[`/zsl:tdd-parallel`](skills.md#tdd-parallel) `<PRD>`
:   Fan out the unblocked **`[AFK]`** `ready-for-agent` children into parallel `/tdd` sub-agents in worktrees. Sub-agents commit but do **not** push (`/tdd --no-ship`). The orchestrator merges every slice branch onto the PRD branch in wave order with `--no-ff`, then opens **one consolidated integration PR**. Halts with a structured RCA on agent failure, merge conflict, or zero-progress cycles. PR-style repos only; `[HITL]`, container, and blocked items are skipped.

[`/zsl:tdd`](skills.md#tdd) `<child>`
:   Single-issue red-green-refactor. Refuses if you point it at a container.

## Ship

Each `/zsl:tdd` reads `docs/agents/ship-style.md`. PR-style opens a PR per slice; direct-push pushes the feature branch and you merge by hand.

[`/zsl:commit`](skills.md#commit) for clean, attribution-free commits.

[`/zsl:code-review`](skills.md#code-review) before opening the PR.

## Cleanup

After children merge, manually run `git worktree remove` and `git branch -d` to clean up the parallel-tdd worktrees and branches (the next `/zsl:tdd-parallel` run also sweeps these in its pre-flight).

## Track and close

Every issue carries one category role (`bug` or `enhancement`) and one state role: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `tracking`, or `wontfix`. See [`/zsl:triage`](skills.md#triage) for the full state machine and transitions.

Where state is stored and how closure works depends on the backend you picked in [`/zsl:setup-zsl-superpowers`](setup.md):

**GitHub project dashboard** — state lives as labels on each issue and is mirrored to the project board's `Status` field via the mapping in `docs/agents/project-board.md`. `/zsl:triage` updates both. When a child issue's PR merges, GitHub closes the child; when the last child of a `tracking` PRD closes, GitHub auto-closes the parent — no manual transition needed.

**Local markdown files** — state lives as a `Status:` line near the top of each `.md` file under `.scratch/<feature-slug>/`. Closure is folder-based, and nothing is deleted:

- Close an issue → move `.scratch/<feature-slug>/issues/<NN>-<slug>.md` to `.scratch/<feature-slug>/issues/done/<NN>-<slug>.md`. The filename and final `Status:` line are preserved so the archive records why it closed (e.g. shipped from `ready-for-agent` vs `wontfix`).
- Close a feature → move the whole `.scratch/<feature-slug>/` directory to `.scratch/done/<feature-slug>/`, preserving its internal layout. There's no auto-close: move the feature explicitly once all its issues sit in `issues/done/` (or you've decided to abandon it).

## Cross-cutting

[`/zsl:triage`](skills.md#triage) is also the entry point for **inbound issues** (bugs, feature requests from others) and re-evaluating stale ones — not just for the children you just sliced.

[`/zsl:diagnose`](skills.md#diagnose) for hard bugs and performance regressions.

[`/zsl:improve-codebase-architecture`](skills.md#improve-codebase-architecture) every few days to fight entropy.

[`/zsl:zoom-out`](skills.md#zoom-out) when you need a higher-level view of unfamiliar code.
