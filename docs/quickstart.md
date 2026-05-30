# Quickstart

Five minutes from "never installed it" to "shipped a real change with it."

## 1. Install

In Claude Code:

```
/plugin marketplace add ZunoSmartLabs/zsl-superpowers
/plugin install zsl@zsl-superpowers
```

Restart Claude Code. The skills now surface as `/zsl:<skill-name>`.

## 2. Try the smallest skill first

Open Claude Code in any repo and run:

```
/zsl:grill-me
```

Tell it about something you're stuck on. It'll interview you until your decision
tree is fully resolved — no code changes, no commits, just a conversation that
forces clarity. This is the cheapest way to feel the difference: the agent stops
guessing and starts asking.

You can also try [`/zsl:caveman`](skills/caveman.md) for a token-cut compressed
reply mode, [`/zsl:timesheet`](skills/timesheet.md) to turn this morning's
sessions into standup notes, or [`/zsl:handoff`](skills/handoff.md) to compact
a long conversation into a tmp-dir doc your next session can pick up.

## 3. Configure a repo

For the engineering skills (`tdd`, `triage`, `to-prd`, `to-issues`,
`improve-codebase-architecture`, `diagnose`, `zoom-out`) you need to teach the
plugin about *this* repo's setup. From inside the repo, run:

```
/zsl:setup-zsl-superpowers
```

It asks four questions:

1. **Issue tracker** — GitHub, GitLab, or local markdown files under `.scratch/`.
2. **Triage label vocabulary** — the actual label strings you use (the plugin
   maps these to canonical roles like `ready-for-agent`).
3. **Where domain docs live** — `CONTEXT.md`, ADRs path, etc.
4. **Ship style** — PR-style or direct-push.

The output lands in `AGENTS.md` (or `CLAUDE.md`), `docs/agents/`, and (for
PR-style repos) the project board mapping at `docs/agents/project-board.md`.

[Full setup details →](setup.md)

## 4. Ship one thing through the loop

Pick something small — a one-day feature, a bug you've been putting off. Then:

1. **`/zsl:grill-with-docs`** — interview, sharpens terminology, updates
   `CONTEXT.md` and ADRs as decisions crystallise.
2. **`/zsl:to-prd`** — write the conversation up as a PRD on your issue tracker.
3. **`/zsl:to-issues`** — slice the PRD into vertical-slice sub-issues with
   explicit `Blocked by` graphs.
4. **`/zsl:triage`** — move each child to `ready-for-agent` with an agent brief.
5. **`/zsl:tdd-parallel`** — fan the AFK slices out into worktrees in waves and
   open one integration PR. (PR-style repos only — see the
   [deep-dive](tdd-parallel.md).)

You'll feel the shift around step 3: instead of an agent diving in
flailing, you're handed a slicing plan you can edit before any code gets written.

[The full loop →](workflow.md)

## What to read next

- [Why these skills exist](why.md) — the failure modes behind the loop, with the book quotes.
- [The loop](workflow.md) — how the skills compose, concept and command per phase.
- [Parallel TDD deep-dive](tdd-parallel.md) — why one PR, what an integration PR looks like.
- [Remote agents deep-dive](remote-agents.md) — schedule PRDs to build unattended overnight, then reconcile and merge in the morning.
- [Skills](skills/index.md) — every skill, with its trigger phrases.
- [FAQ](faq.md) — Codex/Cursor compatibility, telemetry, opt-in subset, updates.
