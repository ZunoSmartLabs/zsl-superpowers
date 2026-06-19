---
name: ask-zsl
description: Interactive router that helps you find the right ZSL skill for what you're doing right now, without leaving your work. Use when you're mid-session and unsure which skill fits — "which ZSL skill should I use", "how do I do X with these skills", or when you want to be routed to the right part of the loop.
disable-model-invocation: true
---

# Ask ZSL

A thin interactive router. You're mid-session, you know roughly what you want to
do, but you're not sure which ZSL skill fits — `ask-zsl` asks you a couple of
situational questions and points you at the right one. It's **routing logic only**:
it doesn't re-describe each skill (the [Skills overview](../../../docs/skills/index.md)
and each `SKILL.md` already do that) — it just gets you to the right door.

User-invoked only (`disable-model-invocation: true`): you ask it; it never fires on
its own.

## How to route

Ask the user a short, situational question, branch on the answer, and name the
skill (and *why* it fits) — then stop. Don't run the skill for them; hand them the
slash command. If they're already deep in one phase, jump straight to that branch.

### "What are you trying to do right now?"

- **Mature a fuzzy, multi-session idea before it's a PRD** → `/decision-mapping`
  (decision map under `.scratch/decision-maps/`, then hands to `/to-prd`).
- **Stress-test a concrete plan / align on what to build** → `/grill-me` (non-code)
  or `/grill-with-docs` (sharpens `CONTEXT.md` + ADRs inline).
- **Package the current conversation into a PRD** → `/to-prd`.
- **Break a PRD into independently-grabbable slices** → `/to-issues`, then
  `/triage` each child to `ready-for-agent`.
- **Build it** → see the build sub-questions below.
- **Hunt a bug or perf regression** → `/diagnose`.
- **Understand an unfamiliar repo before touching it** → `/teach-me-the-codebase`.
- **Fight architectural entropy** → `/improve-codebase-architecture`.
- **Ship / review / commit** → `/code-review`, then `/commit` or `/commit-push-pr`
  (and `/git-branch` first if you're still on the default branch).

### Build: one slice or many?

- **One slice, here, now** → `/tdd` (single-issue red-green-refactor on your branch).
- **Several unblocked `[AFK]` slices of a PRD, integrated into one PR** →
  `/tdd-parallel` (fans out, integrates, auto-chains coverage, opens one PR).
- **Manual `[HITL]` steps an agent can't do** → `/human-itl` first — `/tdd-parallel`
  refuses while any `[HITL]` is open.
- **`/tdd` vs `/tdd-parallel`?** One issue at a time on the current checkout → `/tdd`.
  A whole PRD's worth of parallel slices into a single integration PR →
  `/tdd-parallel`.

### Verify and prove coverage

- **Is every PRD user story actually covered by a passing, non-vacuous test?** →
  `/verify-coverage` (Tier A maps to an existing test; Tier B generates one and
  mutation-proves it). Usually auto-chained by `/tdd-parallel`; invoke it directly
  to audit a PRD whose slices shipped elsewhere.

### Run it overnight (remote agents)

- **Schedule unattended overnight runs of several PRDs** → `/afk-fanout` in the
  evening (one remote routine per PRD, 2h apart).
- **What each scheduled routine fires** → `/afk-worker` (per-PRD remote executor;
  you don't invoke it by hand).
- **Walk the overnight results in the morning** → `/morning-review` (reconciles the
  `afk-runs` ledger, surfaces PRs to verify/merge and halts to re-triage).

### Off the loop

- **Throwaway exploration of a design** → `/prototype`.
- **Compact this session for the next agent** → `/handoff`.
- **Standup notes from recent sessions** → `/timesheet`.
- **Author or sharpen a skill** → `/writing-great-skills`.

## Keep routing in sync

`ask-zsl` and the "Which skill do I want?" decision tree in
[`docs/skills/index.md`](../../../docs/skills/index.md) are two views of the same
routing. When a loop skill is added or removed, **both** must change together —
this pairing is recorded in `CLAUDE.md`'s skill-sync contract. If you find yourself
routing to a skill that isn't in the tree (or vice versa), one of them is stale.

## What this skill is not

- **Not a doc.** It defers every skill's *description* to that skill's page — it
  only owns the *routing*.
- **Not an executor.** It points you at a slash command; it never runs the skill on
  your behalf.
