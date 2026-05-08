---
hide:
  - navigation
---

# Agent skills for real engineering

<p style="font-size:1.15rem; color: var(--md-default-fg-color--light); margin-top:-0.5rem;">
Not vibe coding. Small, composable, model-agnostic skills you can adapt to your repo
instead of letting a process framework take over.
</p>

[Get started in 60 seconds :material-arrow-right:](quickstart.md){ .md-button .md-button--primary }
[How the loop fits together](workflow.md){ .md-button }

---

## What changes when you install this

<div markdown class="grid cards" >

-   :material-close-circle-outline:{ .lg .middle } **Without these skills**

    ---

    *"Build me a feature for X."*

    Agent dives in, invents file paths, half-implements three layers, opens a PR
    that touches forty files and misses the constraint you only mentioned in
    passing. You spend an hour reverse-engineering what it built before you can
    review it.

-   :material-check-circle-outline:{ .lg .middle } **With these skills**

    ---

    `/zsl:grill-with-docs` interviews you against the project's `CONTEXT.md` and
    ADRs until the plan is concrete. `/zsl:to-prd` writes it up. `/zsl:to-issues`
    slices it into vertical-slice sub-issues with explicit `Blocked by` graphs.
    `/zsl:tdd-parallel` fans the unblocked AFK slices out into worktrees,
    merges in wave order, and opens **one** consolidated integration PR.

</div>

You stay in the loop where it matters (the plan, the slicing, the review) and
delegate the parts that are mechanical (the test scaffolding, the merging, the
busywork of opening N PRs).

---

## Install

```
/plugin marketplace add ZunoSmartLabs/zsl-superpowers
/plugin install zsl@zsl-superpowers
```

Skills surface as `/zsl:<skill-name>` once installed (`/zsl:tdd`, `/zsl:triage`, …).
Run [`/zsl:setup-zsl-superpowers`](setup.md) once per repo to teach the engineering
skills your issue tracker, label vocabulary, doc layout, and ship style.

[Quickstart →](quickstart.md){ .md-button }

---

## Why these skills exist

We built these to fix specific failure modes we kept hitting with Claude Code,
Codex, and other coding agents:

| You hit this | Reach for |
|---|---|
| The agent didn't do what I want | [`/zsl:grill-me`](skills/grill-me.md) or [`/zsl:grill-with-docs`](skills/grill-with-docs.md) before you start |
| The agent is way too verbose | [`/zsl:grill-with-docs`](skills/grill-with-docs.md) — builds shared language inline in `CONTEXT.md` and ADRs |
| The code doesn't work | [`/zsl:tdd`](skills/tdd.md) for red-green-refactor; [`/zsl:diagnose`](skills/diagnose.md) when the bug is real |
| We built a ball of mud | [`/zsl:improve-codebase-architecture`](skills/improve-codebase-architecture.md) every few days |
| I'm lost in this code | [`/zsl:zoom-out`](skills/zoom-out.md) |
| Need to break a PRD into work | [`/zsl:to-prd`](skills/to-prd.md) → [`/zsl:to-issues`](skills/to-issues.md) → [`/zsl:triage`](skills/triage.md) |
| Multiple slices ready to ship at once | [`/zsl:tdd-parallel`](tdd-parallel.md) — one integration PR, not N |

---

## Where to next

[Quickstart](quickstart.md)
:   Install, run one skill, see what changed. Five minutes.

[The workflow](workflow.md)
:   How the skills compose into one engineering loop, end to end.

[Parallel TDD deep-dive](tdd-parallel.md)
:   Why we built it, how the wave model works, what an integration PR looks like.

[Skills](skills/index.md)
:   Every skill, what it does, when it activates.

[FAQ](faq.md)
:   Compatibility, telemetry, namespacing, opt-in subset.
