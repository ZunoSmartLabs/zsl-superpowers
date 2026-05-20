# The end-to-end loop

The skills compose into one engineering loop. Most days you only touch a few of them. Run [`/zsl:setup-zsl-superpowers`](setup.md) once per repo before any of this; from then on it's the loop:

```mermaid
flowchart LR
    plan["`**Plan**
    grill-me · grill-with-docs · to-prd`"]
    breakdown["`**Break down**
    to-issues · triage`"]
    build["`**Build**
    tdd-parallel · tdd · diagnose`"]
    ship["`**Ship**
    code-review · commit`"]
    track["`**Track & close**
    state machine · project board`"]

    plan --> breakdown --> build --> ship --> track --> plan

    classDef phase stroke:#3f51b5,stroke-width:1.5px,rx:6,ry:6;
    class plan,breakdown,build,ship,track phase;
```

!!! tip "Looking for the conceptual map?"
    This page is the walkthrough with slash-command examples. For the
    conceptual map — what each phase produces, what flows between them,
    the cross-cutting band — read [The loop](concepts/the-loop.md) in
    the Concepts section.

## Loop skills vs cross-cutting helpers

Some skills sit *on* the loop arrow; others run *across* it. The lane
diagram below shows which is which — the second lane is the band of
skills you can reach for at any time, regardless of which phase you're
in.

```mermaid
flowchart TB
    subgraph loop["📦 On the loop"]
        direction LR
        a["**Plan**<br/>grill-me<br/>grill-with-docs<br/>to-prd"] --> b["**Break down**<br/>to-issues<br/>triage"]
        b --> c["**Build**<br/>tdd-parallel<br/>tdd"]
        c --> d["**Ship**<br/>git-branch<br/>commit<br/>code-review"]
        d --> e["**Track**<br/>state machine"]
        e --> a
    end
    subgraph cross["🧭 Cross-cutting"]
        direction LR
        x1["diagnose<br/><i>bugs / perf</i>"]
        x2["improve-codebase-architecture<br/><i>fight entropy</i>"]
        x3["zoom-out<br/><i>find your footing</i>"]
        x4["triage<br/><i>inbound issues</i>"]
    end
    subgraph offloop["✋ Off-loop"]
        direction LR
        o1["prototype<br/><i>throwaway exploration</i>"]
        o2["timesheet<br/><i>standup notes</i>"]
        o3["caveman<br/><i>compressed mode</i>"]
        o4["write-a-skill<br/><i>meta</i>"]
    end
    cross -.-> loop
```

## One-time setup

[`/zsl:setup-zsl-superpowers`](setup.md)
:   Configure the issue tracker, triage label vocabulary, domain doc layout, and ship style for the repo. Run once before anything else.

## Plan

[`/zsl:grill-me`](skills/grill-me.md) or [`/zsl:grill-with-docs`](skills/grill-with-docs.md)
:   Interview yourself to surface what you're actually building. `grill-with-docs` also updates `CONTEXT.md` and ADRs inline.

[`/zsl:to-prd`](skills/to-prd.md)
:   Synthesise that conversation into a PRD on the issue tracker.

## Break down

[`/zsl:to-issues`](skills/to-issues.md)
:   Break the PRD into vertical-slice sub-issues. Children are labeled `needs-triage`; the PRD parent is auto-relabeled to `tracking`. Slice titles use the `[AFK|HITL] <wave>[<letter>] — <description>` format so the dependency graph reads at a glance (same wave = runnable in parallel).

[`/zsl:triage`](skills/triage.md)
:   Triage **each child** to `ready-for-agent` (with an agent brief), `ready-for-human`, or `needs-info`. Skip triaging the PRD itself; you just wrote it.

## Build

[`/zsl:tdd-parallel`](tdd-parallel.md) `<PRD>`
:   Fan out the unblocked **`[AFK]`** `ready-for-agent` children into parallel `/tdd` sub-agents in worktrees. Sub-agents commit but do **not** push (`/tdd --no-ship`). The orchestrator merges every slice branch onto the PRD branch in wave order with `--no-ff`, runs an integration `/zsl:code-review --auto` against the merged tip (step 4a, catching cross-slice issues per-slice reviews can't see), then — gated on a valid `/zsl:verify-coverage` receipt for the integrated tip (step 4b; see **Verify** below) — opens **one consolidated integration PR** (step 4c). Halts with a structured RCA on agent failure, merge conflict, zero-progress cycles, an integration review failure, or a declined coverage gate. PR-style repos only; `[HITL]`, container, and blocked items are skipped.

[`/zsl:human-itl`](skills/human-itl.md) `<PRD>`
:   Clear the `[HITL]` slices `/tdd-parallel` skipped — the manual actions a coding agent can't perform (console clicks, credential rotation, sign-off). Records each as an audit-trail comment, marks them done so the dependent `[AFK]` slices unblock, then hands back; re-run `/zsl:tdd-parallel` after. Hard-refuses slices that are really decisions in disguise — those belong upstream in `/zsl:grill-with-docs` + an ADR.

[`/zsl:tdd`](skills/tdd.md) `<child>`
:   Single-issue red-green-refactor. Refuses if you point it at a container. **On local-markdown trackers, you can also run `/zsl:tdd` with no argument** — it scans `.scratch/`, resolves each open issue's `## Blocked by` against the `issues/done/` archive, and lets you pick from the unblocked ones. The picker also surfaces "features fully archived but not closed" so you can run the feature-level close before grabbing more work.

## Verify

[`/zsl:verify-coverage`](skills/verify-coverage.md) `<PRD>`
:   After the fanout integrates, check every PRD `## User Stories` entry against the *implemented code via tests*, not prose. Tier A maps each story to an existing passing behavioral test; Tier B generates one for the rest, proves it non-vacuous by mutation, and runs it; visual/UX/external stories go to a human-attestation lane (HITL). Quarantines failing tests, auto-files genuine gaps as `needs-triage` sub-issues of the PRD, and writes a coverage receipt against the verified sha. `/zsl:tdd-parallel` **enforces** this at step 4b: it refuses to open the integration PR until a valid receipt for the integrated tip exists. It's an *execution* gate (did the check run?), not an *outcome* gate — open gaps still pass; only skipping the check is blocked. The matrix outcome itself stays a review surface, never an auto-gate.

## Ship

Each `/zsl:tdd` reads `docs/agents/ship-style.md`. PR-style opens a PR per slice; direct-push pushes the feature branch and you merge by hand. Review happens automatically inside `/zsl:tdd` step 5, between Refactor (step 4) and Ship (step 6) — by the time you reach the PR-open step the slice has already been reviewed.

[`/zsl:commit`](skills/commit.md) for clean, attribution-free commits — fully autonomous for session changes (no per-commit approval prompt); confirms only "other-origin" dirty files before including.

[`/zsl:code-review`](skills/code-review.md) runs automatically as `/zsl:tdd` step 5 (interactive mode with an approval gate) or in `--auto` mode under `/zsl:tdd --no-ship` and `/zsl:tdd-parallel` step 4a. You can also invoke it standalone before opening a PR — same scan, same scoring.

## Cleanup

After children merge, manually run `git worktree remove` and `git branch -d` to clean up the parallel-tdd worktrees and branches (the next `/zsl:tdd-parallel` run also sweeps these in its pre-flight).

## Track and close

Every issue carries one **category role** (`bug` or `enhancement`) and one **state role**:

```mermaid
stateDiagram-v2
    direction LR
    [*] --> needs_triage: created
    needs_triage: needs-triage
    needs_info: needs-info
    ready_agent: ready-for-agent
    ready_human: ready-for-human
    tracking: tracking
    wontfix: wontfix
    done: closed

    needs_triage --> needs_info: ask reporter
    needs_info --> needs_triage: reporter replied
    needs_triage --> ready_agent: agent brief written
    needs_triage --> ready_human: needs human judgment
    needs_triage --> tracking: /to-issues sliced it
    needs_triage --> wontfix: declined
    ready_agent --> done: PR merged
    ready_human --> done: PR merged
    tracking --> done: last child closed
    wontfix --> done: closed with reason

    note right of tracking
        Auto-set by /to-issues.
        Auto-closes when the last
        child closes (GitHub) or
        when you move the folder
        to .scratch/done/ (local).
    end note
```

See [`/zsl:triage`](skills/triage.md) for transition policy and brief templates.

Where state lives, and how closure works, depends on the backend you picked in [`/zsl:setup-zsl-superpowers`](setup.md):

**GitHub project dashboard** — state lives as labels on each issue and is mirrored to the project board's `Status` field via the mapping in `docs/agents/project-board.md`. `/zsl:triage` updates both. When a child issue's PR merges, GitHub closes the child; when the last child of a `tracking` PRD closes, GitHub auto-closes the parent — no manual transition needed.

**Local markdown files** — state lives as a `Status:` line near the top of each `.md` file under `.scratch/<NNN>-<feature-slug>/`, where `<NNN>` is a 3-digit feature number assigned at creation (auto-incremented from the highest existing number across active + archived). Features can be addressed by number alone — `/zsl:triage 23` and `/zsl:to-issues 45` resolve to features `023-*` and `045-*` via glob. Closure is folder-based, and nothing is deleted:

- Close an issue → on ship, [`/zsl:tdd`](skills/tdd.md) flips the `Status:` line to `shipped` and runs `git mv .scratch/<NNN>-<feature-slug>/issues/<NN>-<slug>.md .scratch/<NNN>-<feature-slug>/issues/done/<NN>-<slug>.md` in the same commit as the slice's code, so the close is atomic with the work that earned it. The filename and `Status:` line are preserved so the archive records why it closed (e.g. `shipped` vs `wontfix`).
- Close a feature → move the whole `.scratch/<NNN>-<feature-slug>/` directory to `.scratch/done/<YYYYMMDD>-<NNN>-<feature-slug>/`, preserving its internal layout. The date prefix orders archived features chronologically (`ls .scratch/done/` shows close order); the feature number stays embedded so number-based lookup keeps working across the active/archive split. There's no auto-close: when an issue's close empties the feature's open `issues/`, [`/zsl:tdd`](skills/tdd.md) **prompts** you to run the feature-level `git mv` (never automatic — you might still want to add a follow-up issue). You can also do it by hand if you're abandoning the feature.

## Cross-cutting

[`/zsl:triage`](skills/triage.md) is also the entry point for **inbound issues** (bugs, feature requests from others) and re-evaluating stale ones — not just for the children you just sliced.

[`/zsl:diagnose`](skills/diagnose.md) for hard bugs and performance regressions.

[`/zsl:improve-codebase-architecture`](skills/improve-codebase-architecture.md) every few days to fight entropy.

[`/zsl:zoom-out`](skills/zoom-out.md) when you need a higher-level view of unfamiliar code.

## Catalogue at a glance

For the full per-skill descriptions and decision tree, see the
[Skills overview](skills/index.md).

| Phase | Skill | What it does |
|---|---|---|
| Setup | [setup-zsl-superpowers](skills/setup-zsl-superpowers.md) | One-time per-repo scaffold: tracker, label vocab, ship style |
| Plan | [grill-with-docs](skills/grill-with-docs.md) | Interview + updates `CONTEXT.md` and ADRs |
| Plan | [grill-me](skills/grill-me.md) | Interview only (non-code) |
| Plan | [to-prd](skills/to-prd.md) | Conversation → PRD on tracker |
| Break down | [to-issues](skills/to-issues.md) | PRD → vertical-slice children with wave/letter dependency graph |
| Break down | [triage](skills/triage.md) | Walk each child through the [state machine](concepts/state-machine.md) |
| Build | [tdd](skills/tdd.md) | Single-issue red-green-refactor |
| Build | [tdd-parallel](skills/tdd-parallel.md) | Worktree fanout + wave-ordered merges + one PR |
| Build | [diagnose](skills/diagnose.md) | Reproduce → minimise → hypothesise → fix |
| Verify | [verify-coverage](skills/verify-coverage.md) | PRD-story coverage via tests; gates the fanout's integration PR |
| Ship | [git-branch](skills/git-branch.md) | Branch with the prefix convention |
| Ship | [commit](skills/commit.md) | Explicit-file-list commits, autonomous for session changes |
| Ship | [code-review](skills/code-review.md) | Multi-lens scan with confidence scoring; interactive approval gate or `--auto` |
| Cross-cut | [improve-codebase-architecture](skills/improve-codebase-architecture.md) | Find deepening opportunities |
| Cross-cut | [zoom-out](skills/zoom-out.md) | Broader context on unfamiliar code |
| Off-loop | [prototype](skills/prototype.md) | Throwaway exploration |
| Off-loop | [timesheet](skills/timesheet.md), [caveman](skills/caveman.md), [write-a-skill](skills/write-a-skill.md) | Productivity helpers |
