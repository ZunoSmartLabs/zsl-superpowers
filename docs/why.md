# Why these skills exist

ZSL Superpowers is a set of small, composable skills that fix the failure
modes we kept hitting with Claude Code, Codex, and other coding agents.
Each skill exists to fix **one specific failure**. This page is the
argument for the whole plugin — read it once and the rest of the docs
become a reference rather than a sales pitch.

If you just want to start typing, jump to the
[Quickstart](quickstart.md). If you want the mechanics, read
[The loop](workflow.md).

## #1 — The agent didn't do what I want

!!! quote
    "No-one knows exactly what they want."
    — David Thomas & Andrew Hunt, *The Pragmatic Programmer*

**The problem.** The most common failure mode in software is
misalignment. You *think* the agent understood you. Then you see what it
built and realise it didn't. The communication gap between you and the
agent is exactly the gap between a developer and a domain expert — and it
costs the same: an hour reverse-engineering a forty-file PR before you can
even review it.

**The fix.** A *grilling session* — the agent interviews **you**,
relentlessly, until every branch of the decision tree is resolved, before
a line of code is written.

- [`/zsl:grill-me`](skills/grill-me.md) — interview only, for non-code planning.
- [`/zsl:grill-with-docs`](skills/grill-with-docs.md) — the same interview, plus it updates `CONTEXT.md` and ADRs inline (see below).

These are the highest-leverage skills in the plugin. Use them *every*
time you make a change of any size.

## #2 — The agent is way too verbose

!!! quote
    "With a ubiquitous language, conversations among developers and
    expressions of the code are all derived from the same domain model."
    — Eric Evans, *Domain-Driven Design*

**The problem.** Agents get dropped into a project and asked to infer the
jargon as they go, so they use twenty words where one would do. The same
bug can be described two ways:

- **Before:** "There's a problem when a lesson inside a section of a course is made 'real' (given a spot in the file system)."
- **After:** "There's a problem with the materialization cascade."

**The fix.** A shared language — a document that decodes the project's
jargon — built up *as you plan*. This is what
[`/zsl:grill-with-docs`](skills/grill-with-docs.md) does: every grilling
session sharpens `CONTEXT.md` (the shared language) and records
hard-to-explain decisions as ADRs.

!!! tip "A shared language pays off everywhere"
    - Variables, functions and files get named consistently from the shared vocabulary.
    - The codebase becomes easier for the agent to navigate.
    - The agent spends fewer tokens *thinking*, because it has a more concise language to think in.

## #3 — The code doesn't work

!!! quote
    "Always take small, deliberate steps. The rate of feedback is your
    speed limit. Never take on a task that's too big."
    — David Thomas & Andrew Hunt, *The Pragmatic Programmer*

**The problem.** Even when you and the agent are aligned, the agent can
still produce code that doesn't run — because it's flying blind without
feedback on how its code actually behaves.

**The fix.** Tighten the feedback loops: static types, browser access, and
automated tests. For tests specifically, a **red-green-refactor** loop is
critical — the agent writes a failing test *first*, then makes it pass, so
it can't quietly change the spec to match a broken implementation.

- [`/zsl:tdd`](skills/tdd.md) — red-green-refactor for one slice at a time.
- [`/zsl:diagnose`](skills/diagnose.md) — a disciplined reproduce → minimise → fix loop for real bugs and perf regressions.

## #4 — We built a ball of mud

!!! quote
    "Invest in the design of the system *every day*."
    — Kent Beck, *Extreme Programming Explained*

!!! quote
    "The best modules are deep. They allow a lot of functionality to be
    accessed through a simple interface."
    — John Ousterhout, *A Philosophy of Software Design*

**The problem.** Agents radically speed up coding — which means they also
radically speed up *entropy*. Codebases get complex faster than ever.

**The fix.** Care about the design of the code, on every loop. It's built
into every layer of these skills:

- [`/zsl:to-prd`](skills/to-prd.md) quizzes you about which modules you're touching before writing the PRD.
- [`/zsl:improve-codebase-architecture`](skills/improve-codebase-architecture.md) rescues a codebase that's already a ball of mud — run it every few days.

## The throughline

Software-engineering fundamentals matter *more* in the AI age, not less.
These skills condense those fundamentals into repeatable practices and
chain them into one [end-to-end loop](workflow.md): plan → break down →
build → ship → track. Most days you touch only a few of them.

[See the loop →](workflow.md){ .md-button .md-button--primary }
[Browse every skill →](skills/index.md){ .md-button }
