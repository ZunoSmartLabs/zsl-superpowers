---
name: human-itl
description: Walk a human through the manual-action [HITL] sub-tasks of a parent (PRD) issue — the steps a coding agent physically cannot perform — recording each as an audit trail and marking them done so the dependent [AFK] slices unblock, then hand back to /tdd-parallel. Use when /tdd-parallel skipped HITL slices, when the user wants to clear manual steps before a fanout, or when the user invokes /human-itl directly.
disable-model-invocation: true
---

# Human in the loop

`/tdd-parallel` fans out only the **`[AFK]`** slices of a PRD — the ones an
agent can run unattended. The **`[HITL]`** slices it skips need a human's
hands or authority. This skill is the serial, human-present counterpart:
it walks you through each manual-action slice, records what you did, and
marks it done so the `[AFK]` slices that were `Blocked by` it unblock.

It does **not** write code or run red-green-refactor — that's `/tdd`. A
`[HITL]` slice is a manual *action*, not a unit of TDD work.

## What counts as HITL

A legitimate `[HITL]` slice requires a manual action a coding agent
**physically cannot perform**:

- Clicking through a third-party console (DNS registrar, cloud dashboard).
- Rotating or issuing a real credential / secret / certificate.
- Obtaining external sign-off (legal, security, a stakeholder).
- Running a one-off production migration or cut-over by hand.

It is **not** an architectural decision or a design review. Those must be
resolved upstream via `/grill-with-docs` and recorded as ADRs *before*
issues are cut, so slices fall out maximally AFK — see `/to-issues`.

**Hard refuse decision slices.** If a slice is really a decision in
disguise (`Decide auth provider`, `Pick the cache strategy`), do **not**
walk the user through it. Flag it as a process leak and stop on that
slice: tell the user to resolve it with `/grill-with-docs` + an ADR, then
relabel it and its dependents `[AFK]` and re-run the fanout. Continue with
the remaining genuine `[HITL]` slices.

If a "HITL" slice turns out to be implementable code, it's mislabeled —
say so and tell the user it belongs in the AFK fanout (`[AFK]`).

## Usage

```
/zsl:human-itl <parent-issue>   # clear all HITL slices of a PRD
/zsl:human-itl <hitl-issue>     # clear one HITL slice
/zsl:human-itl                  # no arg → picker of open HITL slices
```

## Process

### 1. Pre-flight

- `docs/agents/issue-tracker.md` exists (run `/setup-zsl-superpowers` if
  not). `docs/agents/triage-labels.md` exists.
- Resolve the input. A parent issue → its sub-issues. A single issue →
  just that one. No argument → fetch open `[HITL]` issues carrying the
  configured `ready-for-agent` label and present a numbered picker.
- Refuse a container issue (one with open sub-issues that is itself
  titled `[HITL]`) the same way the other skills do.

### 2. Discover the slices

Using `docs/agents/issue-tracker.md` conventions, fetch the parent's
sub-issues. Keep only those that are:

- Open
- Title starts with `[HITL]`
- Carry the configured `ready-for-agent` label
- Not a container

Parse each slice's `## Blocked by` section. A `[HITL]` slice may itself be
blocked by an `[AFK]` slice that a prior fanout already merged — process
slices in dependency order, skipping any whose blockers aren't satisfied
yet (report them as "still blocked").

### 3. Walk the slices

Show the user the buckets first — **To clear** (numbered), **Still
blocked** (issue + unmet blockers), **Refused — decision slice** (issue +
why) — and confirm before starting.

Then, for each slice in dependency order:

1. Present the slice: title, the `## What to build` action, and the
   `## Acceptance criteria` ("Done when") checklist.
2. **Pause.** The user performs the manual action out of band.
3. Ask the user for a one-line confirmation note (what they did; any
   id/link/ticket as evidence). Post it as a comment on the issue per
   `docs/agents/issue-tracker.md` — this is the audit trail.
4. If the action embodies a decision worth keeping (a chosen provider, a
   negotiated limit), write or update an ADR — lazily, like
   `/grill-with-docs`. Don't batch; capture it now.
5. Mark the issue done per the tracker convention (close it / `git mv`
   into `issues/done/` for local-markdown). This is what unblocks the
   dependent `[AFK]` slices.

### 4. Finish

Print a summary: slices cleared (issue + note), slices still blocked,
slices refused as decision leaks. Then **stop** with the explicit next
step — do not chain:

> Cleared N HITL slices. Run `/tdd-parallel <parent>` to fan out the
> now-unblocked AFK work.

## Not in scope

- Writing code or running red-green-refactor — that's `/tdd`.
- Resolving decisions — that's `/grill-with-docs` + an ADR, upstream.
- Invoking `/tdd-parallel` for the user — this skill ends with the hint.
