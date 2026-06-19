# ZSL Superpowers

Agent skills for real engineering, not vibe coding. Small, composable, model-agnostic — adapt them to your repo instead of letting a process framework take over.

📖 **Full guide: [superpowers.zsl.dev](https://superpowers.zsl.dev)**

> [!IMPORTANT]
> **Built for Claude Code.** Skills depend on Claude Code's slash commands, `/plugin` install path, and tool surface (`Agent`, `Monitor`, `Bash`, `SendMessage`, `TaskStop`). They aren't drop-in for Cursor, Codex, Cline, or general LLM chat. ("Model-agnostic" above means any Claude model — Opus, Sonnet, Haiku — not any harness.) See [Compatibility](https://superpowers.zsl.dev/faq/#compatibility) for what porting would look like.

## Workflow

The skills compose into one end-to-end loop. Most days you only touch a few of them.

### One-time setup

- **[`/setup-zsl-superpowers`](./skills/engineering/setup-zsl-superpowers/SKILL.md)** — configure the issue tracker, triage label vocabulary, domain doc layout, and ship style for this repo. Run once before anything else.

### Plan

- **[`/grill-me`](./skills/productivity/grill-me/SKILL.md)** or **[`/grill-with-docs`](./skills/engineering/grill-with-docs/SKILL.md)** — interview yourself to surface what you're actually building. `grill-with-docs` also updates `CONTEXT.md` and ADRs inline.
- **[`/to-prd`](./skills/engineering/to-prd/SKILL.md)** — synthesise that conversation into a PRD on the issue tracker.

### Break down

- **[`/to-issues`](./skills/engineering/to-issues/SKILL.md)** — break the PRD into vertical-slice sub-issues. Children are labeled `needs-triage`; the PRD parent is auto-relabeled to `tracking`. Slice titles use the `[AFK|HITL] <wave>[<letter>] — <description>` format so the dependency graph reads at a glance (same wave = runnable in parallel).
- **[`/triage`](./skills/engineering/triage/SKILL.md)** — triage **each child** to `ready-for-agent` (with an agent brief), `ready-for-human`, or `needs-info`. Skip triaging the PRD itself; you just wrote it.

### Build

- **[`/human-itl`](./skills/engineering/human-itl/SKILL.md) `<PRD>`** — clear all `[HITL]` slices first: the manual actions a coding agent can't perform (console clicks, credential rotation, sign-off). Records each as an audit-trail comment, marks them done. Must be cleared **before** `/tdd-parallel`, not interleaved — the auto-pipeline refuses to start with any `[HITL]` open. Hard-refuses slices that are really decisions in disguise (those belong upstream in `/grill-with-docs` + an ADR).
- **[`/tdd-parallel`](./skills/engineering/tdd-parallel/SKILL.md) `<PRD>`** — full-auto pipeline from a PRD to a pushed integration PR. Fans out the unblocked **`[AFK]`** `ready-for-agent` children into parallel `/tdd` sub-agents in worktrees (`/tdd --no-ship`). The orchestrator merges every slice branch onto the PRD branch in wave order with `--no-ff`, runs an integration `/code-review --auto` (step 4a), auto-chains `/verify-coverage --auto` (step 4b), and **auto-fixes any gaps it finds** — gap sub-issues land as `ready-for-agent` and re-fanout in the next round; loop iterates until `gap=0` or a circuit breaker fires (`--max-coverage-rounds`, default 3). On clean coverage, step 4c delegates the defensive commit to `/commit` then pushes and opens **one consolidated integration PR**. Pre-flight (1d) refuses up front if any `[HITL]` is open or any user story isn't `acceptance: automatable` — both gates ensure the post-invocation pipeline runs through to PR-push with no human gates in the happy path. PR-style repos only.
- **[`/tdd`](./skills/engineering/tdd/SKILL.md) `<child>`** — single-issue red-green-refactor. Refuses if you point it at a container. On local-markdown trackers, you can also call it with **no argument** — it scans `.scratch/`, resolves each open issue's `## Blocked by` against the `issues/done/` archive, and lets you pick from the unblocked ones.

### Verify

- **[`/verify-coverage`](./skills/engineering/verify-coverage/SKILL.md) `<PRD>`** — check every PRD `## User Stories` entry against the *implemented code via tests*, not prose. Tier A maps each story to a passing behavioral test; for stories with none, Tier B generates one from the story's `AC<n>:` acceptance criteria, mutation-proves it non-vacuous, and runs it. Quarantines failing tests, auto-files gaps as sub-issues of the PRD, and writes a coverage receipt against the verified sha. **Almost always chained by `/tdd-parallel` step 4b in `--auto` mode** (gaps filed as `ready-for-agent` directly, no triage hop; the orchestrator loops on them). Direct user invocation is for auditing PRDs whose slices shipped via a different path. The human-attestation HITL lane has been removed — non-automatable stories are refused at `/to-prd` time, so visual/UX/external work goes through a separate manual path that doesn't touch `/tdd-parallel`.

### Ship

- Each `/tdd` reads `docs/agents/ship-style.md`. PR-style opens a PR per slice; direct-push pushes the feature branch and you merge by hand.
- **[`/commit`](./skills/engineering/commit/SKILL.md)** for clean, attribution-free commits.
- **[`/code-review`](./skills/engineering/code-review/SKILL.md)** before opening the PR.

### Overnight (remote agents)

A three-step loop that fans work out to dedicated remote claude.ai sessions — one per PRD — so multiple `/tdd-parallel` runs can happen overnight without contending on a shared checkout.

- **[`/afk-fanout`](./skills/remote-agents/afk-fanout/SKILL.md)** — Run it yourself in the evening. It shows the queue of `tracking` PRDs with `ready-for-agent` children, you pick which to run overnight and in what order, and it schedules one one-shot remote routine per PRD a **fixed 2h apart** (a throttle to stay under the per-5h-window token cap). A light `scheduled` claim stops a re-run double-booking.
- **[`/afk-worker`](./skills/remote-agents/afk-worker/SKILL.md)** — What each scheduled routine fires. Runs unattended in its own remote session and clone: flips the claim to `in-progress`, runs `/tdd-parallel <num> --on-review-failure=continue --max 2`, opens one integration PR, and on halt moves the offending slice to `needs-info` with an RCA. Per-PRD isolation means a stuck PRD can't take down the others. Invoked by the routine, not by hand.
- **[`/morning-review`](./skills/remote-agents/morning-review/SKILL.md)** — Run it in the morning. Reconciles the `afk-runs` ledger branch into the canonical `.scratch/` tracker (claim flips and halt RCAs that ran in isolated worker clones), then sorts integration PRs by their slices' `verify-after:` tag and walks the human through `local-run` / `staging` PRs first (the ones CI green can't fully validate), then scheduled-but-no-result PRDs, then halted slices, then batch-mergeable `ci` PRs. Does not auto-merge; does not deploy.

### Cleanup

- After children merge, manually run `git worktree remove` and `git branch -d` to clean up the parallel-tdd worktrees and branches (the next `/tdd-parallel` run also sweeps these in its pre-flight).

### Track and close

Every issue carries one category role (`bug` or `enhancement`) and one state role: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `tracking`, or `wontfix`. See [`/triage`](./skills/engineering/triage/SKILL.md) for the full state machine and transitions.

Where state is stored and how closure works depends on the backend you picked in `/setup-zsl-superpowers`:

**GitHub project dashboard** — state lives as labels on each issue and is mirrored to the project board's `Status` field via the mapping in `docs/agents/project-board.md`. `/triage` updates both. When a child issue's PR merges, GitHub closes the child; when the last child of a `tracking` PRD closes, GitHub auto-closes the parent — no manual transition needed.

**Local markdown files** — state lives as a `Status:` line near the top of each `.md` file under `.scratch/<NNN>-<feature-slug>/`, where `<NNN>` is a 3-digit feature number assigned at creation (auto-incremented from the highest existing number across active + archived). Features can be addressed by number alone — `/triage 23` and `/to-issues 45` resolve to features `023-*` and `045-*` via glob. Closure is folder-based, and nothing is deleted:

- Close an issue → on ship, [`/tdd`](./skills/engineering/tdd/SKILL.md) flips the `Status:` line to `shipped` and runs `git mv .scratch/<NNN>-<feature-slug>/issues/<NN>-<slug>.md .scratch/<NNN>-<feature-slug>/issues/done/<NN>-<slug>.md` in the same commit as the slice's code. The filename and `Status:` line are preserved so the archive records why it closed (e.g. `shipped` vs `wontfix`).
- Close a feature → move the whole `.scratch/<NNN>-<feature-slug>/` directory to `.scratch/done/<YYYYMMDD>-<NNN>-<feature-slug>/`, preserving its internal layout. The date prefix orders archived features chronologically (`ls .scratch/done/` shows close order); the feature number stays embedded so number-based lookup keeps working across the active/archive split. When an issue's close empties the feature's open `issues/`, [`/tdd`](./skills/engineering/tdd/SKILL.md) **prompts** you to run the feature-level `git mv` (never automatic — you might still want to add a follow-up issue first). You can also do it by hand if you're abandoning the feature.

### Cross-cutting

- **[`/triage`](./skills/engineering/triage/SKILL.md)** is also the entry point for **inbound issues** (bugs, feature requests from others) and re-evaluating stale ones — not just for the children you just sliced.
- **[`/diagnose`](./skills/engineering/diagnose/SKILL.md)** for hard bugs and performance regressions.
- **[`/improve-codebase-architecture`](./skills/engineering/improve-codebase-architecture/SKILL.md)** every few days to fight entropy.
- **[`/zoom-out`](./skills/engineering/zoom-out/SKILL.md)** when you need a higher-level view of unfamiliar code.

## Install

In Claude Code:

```
/plugin marketplace add ZunoSmartLabs/zsl-superpowers
/plugin install zsl@zsl-superpowers
```

Skills now surface namespaced as `/zsl:<skill-name>` (e.g. `/zsl:tdd`, `/zsl:triage`).

### Updating

```
/plugin marketplace update zsl-superpowers
```

Restart Claude Code to apply. (`/plugin update <name>` is not a real command — `/plugin` on its own opens the plugin manager UI, and any trailing argument is ignored. The marketplace update + restart is the actual update path.)

After updating, skim the [changelog](./docs/changelog.md) for version-specific upgrade notes — breaking-ish releases include an **Upgrading from X.Y** block with any migration steps.

### Hacking on the skills

To edit skills locally and see changes in Claude Code, clone and register the path instead:

```bash
git clone git@github.com:ZunoSmartLabs/zsl-superpowers.git ~/code/zsl-superpowers
```

```
/plugin marketplace add ~/code/zsl-superpowers
/plugin install zsl@zsl-superpowers
```

Pull and `/plugin marketplace update zsl-superpowers` to refresh.

### Per-repo setup

Run `/zsl:setup-zsl-superpowers` in any repo where you want to use these skills. It will:

- Ask which issue tracker you use (GitHub, GitLab, or local markdown files)
- Ask which labels you apply when triaging issues (`/triage` uses these)
- Ask where to save the per-repo docs the skills consume
- Ask which ship style the repo follows (PR or direct push)

## Why These Skills Exist

These skills are a way to fix common failure modes we see with Claude Code, Codex, and other coding agents.

### #1: The Agent Didn't Do What I Want

> "No-one knows exactly what they want"
>
> David Thomas & Andrew Hunt, [The Pragmatic Programmer](https://www.amazon.co.uk/Pragmatic-Programmer-Anniversary-Journey-Mastery/dp/B0833F1T3V)

**The Problem**. The most common failure mode in software development is misalignment. You think the dev knows what you want. Then you see what they've built - and you realize it didn't understand you at all.

This is just the same in the AI age. There is a communication gap between you and the agent. The fix for this is a **grilling session** - getting the agent to ask you detailed questions about what you're building.

**The Fix** is to use:

- [`/grill-me`](./skills/productivity/grill-me/SKILL.md) - for non-code uses
- [`/grill-with-docs`](./skills/engineering/grill-with-docs/SKILL.md) - same as [`/grill-me`](./skills/productivity/grill-me/SKILL.md), but adds more goodies (see below)

These are my most popular skills. They help you align with the agent before you get started, and think deeply about the change you're making. Use them _every_ time you want to make a change.

### #2: The Agent Is Way Too Verbose

> With a ubiquitous language, conversations among developers and expressions of the code are all derived from the same domain model.
>
> Eric Evans, [Domain-Driven-Design](https://www.amazon.co.uk/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215)

**The Problem**: At the start of a project, devs and the people they're building the software for (the domain experts) are usually speaking different languages.

I felt the same tension with my agents. Agents are usually dropped into a project and asked to figure out the jargon as they go. So they use 20 words where 1 will do.

**The Fix** for this is a shared language. It's a document that helps agents decode the jargon used in the project.

<details>
<summary>
Example
</summary>

For example, in a course-video-manager codebase, the same problem can be expressed two ways:

- **BEFORE**: "There's a problem when a lesson inside a section of a course is made 'real' (i.e. given a spot in the file system)"
- **AFTER**: "There's a problem with the materialization cascade"

This concision pays off session after session.

</details>

This is built into [`/grill-with-docs`](./skills/engineering/grill-with-docs/SKILL.md). It's a grilling session, but that helps you build a shared language with the AI, and document hard-to-explain decisions in ADR's.

It's hard to explain how powerful this is. It might be the single coolest technique in this repo. Try it, and see.

> [!TIP]
> A shared language has many other benefits than reducing verbosity:
>
> - **Variables, functions and files are named consistently**, using the shared language
> - As a result, the **codebase is easier to navigate** for the agent
> - The agent also **spends fewer tokens on thinking**, because it has access to a more concise language

### #3: The Code Doesn't Work

> "Always take small, deliberate steps. The rate of feedback is your speed limit. Never take on a task that’s too big."
>
> David Thomas & Andrew Hunt, [The Pragmatic Programmer](https://www.amazon.co.uk/Pragmatic-Programmer-Anniversary-Journey-Mastery/dp/B0833F1T3V)

**The Problem**: Let's say that you and the agent are aligned on what to build. What happens when the agent _still_ produces crap?

It's time to look at your feedback loops. Without feedback on how the code it produces actually runs, the agent will be flying blind.

**The Fix**: You need the usual tranche of feedback loops: static types, browser access, and automated tests.

For automated tests, a red-green-refactor loop is critical. This is where the agent writes a failing test first, then fixes the test. This helps give the agent a consistent level of feedback that results in far better code.

We've built a **[`/tdd`](./skills/engineering/tdd/SKILL.md) skill** you can slot into any project. It encourages red-green-refactor and gives the agent plenty of guidance on what makes good and bad tests.

For debugging, we've also built a **[`/diagnose`](./skills/engineering/diagnose/SKILL.md)** skill that wraps best debugging practices into a simple loop.

### #4: We Built A Ball Of Mud

> "Invest in the design of the system _every day_."
>
> Kent Beck, [Extreme Programming Explained](https://www.amazon.co.uk/Extreme-Programming-Explained-Embrace-Change/dp/0321278658)

> "The best modules are deep. They allow a lot of functionality to be accessed through a simple interface."
>
> John Ousterhout, [A Philosophy Of Software Design](https://www.amazon.co.uk/Philosophy-Software-Design-2nd/dp/173210221X)

**The Problem**: Most apps built with agents are complex and hard to change. Because agents can radically speed up coding, they also accelerate software entropy. Codebases get more complex at an unprecedented rate.

**The Fix** for this is a radical new approach to AI-powered development: caring about the design of the code.

This is built in to every layer of these skills:

- [`/to-prd`](./skills/engineering/to-prd/SKILL.md) quizzes you about which modules you're touching before creating a PRD
- [`/zoom-out`](./skills/engineering/zoom-out/SKILL.md) tells the agent to explain code in the context of the whole system

And crucially, [`/improve-codebase-architecture`](./skills/engineering/improve-codebase-architecture/SKILL.md) helps you rescue a codebase that has become a ball of mud. I recommend running it on your codebase once every few days.

### Summary

Software engineering fundamentals matter more than ever. These skills are my best effort at condensing these fundamentals into repeatable practices, to help you ship the best apps of your career. Enjoy.

## Reference

### Engineering

Skills we use daily for code work.

- **[diagnose](./skills/engineering/diagnose/SKILL.md)** — Disciplined diagnosis loop for hard bugs and performance regressions: reproduce → minimise → hypothesise → instrument → fix → regression-test.
- **[grill-with-docs](./skills/engineering/grill-with-docs/SKILL.md)** — Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates `CONTEXT.md` and ADRs inline.
- **[triage](./skills/engineering/triage/SKILL.md)** — Triage issues through a state machine of triage roles.
- **[improve-codebase-architecture](./skills/engineering/improve-codebase-architecture/SKILL.md)** — Find deepening opportunities in a codebase, informed by the domain language in `CONTEXT.md` and the decisions in `docs/adr/`.
- **[prototype](./skills/engineering/prototype/SKILL.md)** — Build a throwaway prototype to flush out a design before committing. Routes between a runnable terminal app for state/logic questions and several radically different UI variations for design questions.
- **[setup-zsl-superpowers](./skills/engineering/setup-zsl-superpowers/SKILL.md)** — Scaffold the per-repo config (issue tracker, triage label vocabulary, domain doc layout) that the other engineering skills consume. Run once per repo before using `to-issues`, `to-prd`, `triage`, `diagnose`, `tdd`, `improve-codebase-architecture`, or `zoom-out`.
- **[tdd](./skills/engineering/tdd/SKILL.md)** — Test-driven development with a red-green-refactor loop. Builds features or fixes bugs one vertical slice at a time.
- **[tdd-parallel](./skills/engineering/tdd-parallel/SKILL.md)** — Full-auto PRD pipeline: fanout `[AFK]` slices into parallel `/tdd` sub-agents, integrate onto the PRD branch, auto-chain `/verify-coverage --auto` and auto-fix any gaps via a re-fanout loop (capped by `--max-coverage-rounds`), then open one consolidated integration PR. Refuses up front if any `[HITL]` is open or any user story isn't expressible as an automatable test. PR-style only.
- **[human-itl](./skills/engineering/human-itl/SKILL.md)** — Walk a human through the manual-action `[HITL]` slices of a PRD (console clicks, credential rotation, sign-off), record each as an audit trail, mark them done. Must run **before** `/tdd-parallel`, which refuses with any `[HITL]` open. Hard-refuses disguised-decision slices.
- **[to-issues](./skills/engineering/to-issues/SKILL.md)** — Break any plan, spec, or PRD into independently-grabbable GitHub issues using vertical slices. Propagates the parent PRD's `acceptance:` tag and `AC<n>:` acceptance criteria into each slice body verbatim.
- **[to-prd](./skills/engineering/to-prd/SKILL.md)** — Turn the current conversation context into a PRD and submit it as a GitHub issue. No interview — just synthesizes what you've already discussed. Writes each story at value altitude with detailed assertions pushed into `AC<n>:` acceptance criteria; refuses non-automatable stories. Every story carries `acceptance: automatable` plus at least one acceptance criterion that `/verify-coverage` consumes downstream.
- **[verify-coverage](./skills/engineering/verify-coverage/SKILL.md)** — Verify every PRD user story is covered by a passing, non-vacuous behavioral test (Tier A maps to existing tests; Tier B generates one from the story's `AC<n>:` acceptance criteria and mutation-proves it). Auto-files gaps and writes a coverage receipt. Almost always chained by `/tdd-parallel --auto`; direct invocation is for auditing PRDs whose slices shipped via a different path.
- **[zoom-out](./skills/engineering/zoom-out/SKILL.md)** — Tell the agent to zoom out and give broader context or a higher-level perspective on an unfamiliar section of code.
- **[code-review](./skills/engineering/code-review/SKILL.md)** — Comprehensive pre-PR code review of the current branch with an issues-only tone and an approval gate before applying fixes.
- **[commit](./skills/engineering/commit/SKILL.md)** — Plan and create git commits with user approval, no Claude attribution, and explicit file lists (never `git add -A`).
- **[commit-push-pr](./skills/engineering/commit-push-pr/SKILL.md)** — One-shot ship for a feature branch: refuses on the default branch, delegates the commit to `/zsl:commit`, then `git push -u`, then `gh pr create`. No force-push, no `--no-verify`, no Claude attribution.
- **[git-branch](./skills/engineering/git-branch/SKILL.md)** — Create a git branch with the prefix convention (`feature/`, `fix/`, `chore/`, `refactor/`, `env/`) required by the auto-PR workflow.

### Productivity

General workflow tools, not code-specific.

- **[caveman](./skills/productivity/caveman/SKILL.md)** — Ultra-compressed communication mode. Cuts token usage ~75% by dropping filler while keeping full technical accuracy.
- **[grill-me](./skills/productivity/grill-me/SKILL.md)** — Get relentlessly interviewed about a plan or design until every branch of the decision tree is resolved.
- **[handoff](./skills/productivity/handoff/SKILL.md)** — Compact the current conversation into a handoff document so a fresh agent (or session) can continue cleanly. Saves to the OS temp dir, redacts secrets, references existing artifacts instead of duplicating them.
- **[timesheet](./skills/productivity/timesheet/SKILL.md)** — Summarize recent Claude Code session histories into timesheet-ready outcome bullets, grouped by project.
- **[write-a-skill](./skills/productivity/write-a-skill/SKILL.md)** — Create new skills with proper structure, progressive disclosure, and bundled resources.

### Misc

Tools we keep around but rarely use.

- **[edit-article](./skills/misc/edit-article/SKILL.md)** — Edit and improve articles by restructuring sections, improving clarity, and tightening prose.
- **[setup-pre-commit](./skills/misc/setup-pre-commit/SKILL.md)** — Set up Husky pre-commit hooks with lint-staged, Prettier, type checking, and tests.
- **[steampipe](./skills/misc/steampipe/SKILL.md)** — AWS infrastructure query reference for `steampipe query`. Auto-triggered (not user-invocable); provides table names, column schemas, and JSONB query patterns.

### Remote Agents

The overnight loop — fan work out to dedicated remote claude.ai sessions, then review the results in the morning.

- **[afk-fanout](./skills/remote-agents/afk-fanout/SKILL.md)** — Interactive local-session scheduler. Reviews the queue of `tracking` PRDs with `ready-for-agent` children, lets you pick which to run overnight and in what order, then schedules one one-shot remote routine per PRD a fixed 2h apart (a throttle for the per-5h-window token cap), each running `/afk-worker`. Places a light `scheduled` claim so a re-run won't double-book.
- **[afk-worker](./skills/remote-agents/afk-worker/SKILL.md)** — Remote per-PRD executor fired by an `/afk-fanout`-scheduled routine. Runs unattended in its own clone: flips the claim to `in-progress`, runs `/tdd-parallel <num> --on-review-failure=continue --max 2`, opens one integration PR, and on halt records the offending slice + RCA. Reports its outcome on the shared `afk-runs` ledger branch (reconciled by `/morning-review`) and fires a best-effort Telegram heads-up. Invoked by the routine, not by hand.
- **[morning-review](./skills/remote-agents/morning-review/SKILL.md)** — Walk a human through the overnight artifacts. Reconciles the `afk-runs` ledger into the canonical `.scratch/` tracker across every un-reconciled run, then surfaces integration PRs to verify and merge, halted slices to re-triage, and any scheduled PRD that produced no result. Sorts PRs by their brief's `verify-after:` tag so `local-run` and `staging` slices surface first; `ci` slices are batch-mergeable after a diff skim. Does not auto-merge; does not deploy.

## Engineering-book rules

Eight skills (`/tdd`, `/improve-codebase-architecture`, `/diagnose`, `/grill-with-docs`, `/to-prd`, `/code-review`, `/verify-coverage`, `/prototype`) bundle decision-pressure rules distilled from classic engineering books — Refactoring, Working Effectively with Legacy Code, A Philosophy of Software Design, Clean Architecture, Release It!, Domain-Driven Design Distilled, Implementing DDD, Clean Code, The Pragmatic Programmer. The rules are sourced from [ciembor/agent-rules-books](https://github.com/ciembor/agent-rules-books) by Maciej Ciemborowicz (MIT, pinned to v0.5). We embed `mini` rule sets (and `nano` for the high-frequency `/tdd`) inline-appended into each `SKILL.md` between `BEGIN`/`END` markers. Always-on, no opt-out; per-repo override via `CLAUDE.md` if needed.

The vendored snapshot lives in [`vendor/agent-rules-books/`](./vendor/agent-rules-books/). Upstream tracking is hand-picked — run `make check-upstream-books` to diff the snapshot against the latest tag, then `make sync-books` to re-render the `BEGIN`/`END` fences after a vendor bump.

## Drift from upstream

This started as a fork of [`mattpocock/skills`](https://github.com/mattpocock/skills) and has diverged substantially. The end-to-end workflow (PRD → vertical-slice issues → parallel TDD → consolidated PR), the triage state machine with project-board sync, the local-markdown issue-tracker option, and the per-repo `/setup-zsl-superpowers` config are all ZSL additions. Several upstream skills have been removed or rewritten, and the bucket-folder layout under `skills/` is our own.

We don't pull from upstream automatically — expect hand-picked cherry-picks at most. Credit and thanks to Matt for the original repo and the bones of the approach.
