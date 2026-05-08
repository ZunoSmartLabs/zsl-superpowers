# ZSL Superpowers

Agent skills for real engineering, not vibe coding. Small, composable, model-agnostic — adapt them to your repo instead of letting a process framework take over.

## Install

```
/plugin marketplace add ZunoSmartLabs/zsl-superpowers
/plugin install zsl@zsl-superpowers
```

Skills surface as `/zsl:<skill-name>` once installed (`/zsl:tdd`, `/zsl:triage`, …).

## What's in here

[The end-to-end loop](workflow.md)
:   How the skills compose into one engineering workflow — `grill-with-docs` → `to-prd` → `to-issues` → `triage` → `tdd-parallel` → `code-review` → `commit`.

[Skills reference](skills.md)
:   Every skill, what it does, when to use it.

[Per-repo setup](setup.md)
:   `/zsl:setup-zsl-superpowers` and the config it generates so the engineering skills know your issue tracker, triage labels, domain doc layout, and ship style.

## Why these skills exist

These skills are a way to fix common failure modes we see with Claude Code, Codex, and other coding agents:

- **The agent didn't do what I want** → use [`/zsl:grill-me`](skills.md#grill-me) or [`/zsl:grill-with-docs`](skills.md#grill-with-docs) before you start coding.
- **The agent is way too verbose** → build a shared language with [`/zsl:grill-with-docs`](skills.md#grill-with-docs); it updates `CONTEXT.md` and ADRs inline.
- **The code doesn't work** → [`/zsl:tdd`](skills.md#tdd) for red-green-refactor; [`/zsl:diagnose`](skills.md#diagnose) when the bug is real.
- **We built a ball of mud** → [`/zsl:improve-codebase-architecture`](skills.md#improve-codebase-architecture) every few days; [`/zsl:zoom-out`](skills.md#zoom-out) when entering unfamiliar code.
