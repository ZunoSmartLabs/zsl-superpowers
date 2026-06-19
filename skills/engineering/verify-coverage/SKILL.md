---
name: verify-coverage
description: Verify every PRD user story is covered by a passing, non-vacuous behavioral test — Tier A maps to an existing test; Tier B generates one, mutation-proves it, and runs it. Auto-files gaps as new sub-issues and writes a coverage receipt. Used as `/tdd-parallel`'s step-4b subroutine in `--auto` mode (the common path), or invoked directly against any PRD whose slices have shipped.
---

# Verify Coverage

`/to-issues` slices a PRD into issues and `/tdd` builds them, but the
only post-implementation completeness signal is *structural*: the tracker
auto-closes the parent when every child closes. "All slices shipped" is
not "all user stories covered" — those come apart exactly when slicing
drops or misframes a story.

This skill closes that loop. It uses the PRD's `## User Stories` section
as an **acceptance oracle** (not as implementation context — `/tdd`
deliberately never sees it) and answers, per story, *is there a passing
behavioral test that proves this is built?* It does **not** trust
prose-vs-prose or code-search judgement — a story is covered only when an
executable, non-vacuous test says so.

It is also the **termination oracle** for `/tdd-parallel`'s auto-loop:
the loop iterates fanout → integration review → verify-coverage until
this skill returns zero gaps (or a circuit breaker fires). Without it,
`/tdd-parallel` has no semantic completeness signal — only the
structural "all slices merged" one, which is exactly the signal that's
insufficient.

## Role in the pipeline

This is a verification primitive, almost always chained by an
orchestrator (`/tdd-parallel` step 4b, in `--auto` mode). Direct user
invocation is supported for two cases:

- Auditing a PRD whose slices shipped via a different path (hotfix
  merged by hand, legacy work).
- Re-verifying after a manual edit of the integrated branch.

Three human gates that earlier versions of this skill held — story
classification, HITL human-attestation, and a matrix-confirmation
review — have all moved upstream:

- **Classification** moved to `/to-prd`: every story carries
  one or more `AC<n>:` acceptance-criteria sub-bullets written at
  PRD-authoring time. This skill reads them instead of judging.
- **HITL human-attestation** is gone. Non-automatable stories
  (visual/UX, "feels welcoming", real external systems) are refused at
  `/to-prd` time — they don't enter this pipeline.
- **Matrix confirmation** is gone in `--auto` mode. Auto-filed gap
  issues land as `ready-for-agent` so `/tdd-parallel` can fanout the
  remediation directly; the human review surface moves to `/triage`
  (which is where false-positive gaps get caught, no different from any
  other triage-able backlog item).

What remains is the load-bearing core: Tier A finds an existing passing
test; Tier B generates one, mutation-proves it non-vacuous, runs it;
gaps get filed and quarantined; a receipt is written.

## Usage

```
/zsl:verify-coverage <parent-prd-issue>           # default mode
/zsl:verify-coverage <parent-prd-issue> --auto    # for orchestrator chaining
/zsl:verify-coverage                              # no arg → picker of tracking PRDs
```

Flags:

- `--auto` — orchestrator mode. Skips the matrix-confirmation step (no
  user prompt before filing), files gap issues as `ready-for-agent`
  directly (no `needs-triage` hop), and emits a structured terminal
  block the orchestrator parses. Use this when `/tdd-parallel` chains
  the skill; direct user invocations should usually omit it.
- `--no-file` — produce the matrix and quarantined failing tests, but
  do **not** auto-file gap issues. Report-only. Still a full run —
  writes a gate-satisfying receipt (verification happened; you chose
  not to file). No effect on `deferred`: deferred stories are never
  filed in any mode (there's nothing to fix yet), so the `deferred`
  count is identical with or without `--no-file`.
- `--no-generate` — Tier A only. Stories without an existing passing
  test are reported as `unverified` rather than driven through Tier B.
  Fast pass for a quick read; no tests are written. Writes a **partial**
  receipt; **does not satisfy `/tdd-parallel`'s auto-loop termination**
  — unverified rows mean those stories weren't actually checked.
  Deferral is computed from tracker state *before* Tier A, so a story
  claimed only by open slices is classified `deferred`, not
  `unverified`, even under `--no-generate` (deferral takes precedence —
  it's a known not-yet, not an unchecked unknown).

## Pre-flight

Refuse with a clear message if any fails:

- `docs/agents/issue-tracker.md` exists (run `/setup-zsl-superpowers`
  if not). `docs/agents/triage-labels.md` exists.
- The input resolves to a PRD: an issue with a `## User Stories`
  section. No argument → present a numbered picker of issues in the
  `tracking` state. If the resolved issue has no `## User Stories`
  section it is not a PRD — refuse and say so.
- **Every user story has at least one `AC<n>:` acceptance-criterion
  sub-bullet.** Any story carrying no `AC<n>:` criterion is invalid —
  the PRD must be reworked in `/to-prd` or split. Refuse with the
  offending story numbers and a pointer to `/to-prd`'s story format.
  **Back-compat:** a legacy `observable:` sub-bullet (PRDs authored
  before the AC split) counts as a single acceptance criterion — accept
  it in place of an `AC<n>:` bullet; a legacy `acceptance:` tag, if
  present, is ignored.
- The working tree is on the branch carrying the integrated work (the
  PRD/integration branch for a `/tdd-parallel` run, or wherever the
  shipped slices live). Refuse if dirty (`git status --porcelain`
  non-empty) — Tier B writes and runs tests, and a dirty tree makes
  the non-vacuity mutation unsafe to revert cleanly.

Use the project domain glossary so story vocabulary maps onto the
codebase's and test suite's vocabulary; respect ADRs in the touched
area. See `engineering/tdd/tests.md` for what a behavioural test is and
`engineering/tdd/mocking.md` for what disqualifies one.

## Process

### 1. Build the story inventory

Parse the PRD's `## User Stories` into a numbered list, verbatim. For
each story, capture its `AC<n>:` acceptance criteria (or, on a legacy
PRD, its single `observable:` line treated as one criterion) — Tier B
uses them as the test-generation hint. Parse `## Out of Scope`: any story (or
behaviour) that `## Out of Scope` excludes is marked `out-of-scope` now
and never verified — record the PRD line that excludes it as the
evidence.

The pre-flight already validated that every story carries at least one
`AC<n>:` criterion, so there is no classification step at runtime —
every in-scope story goes through Tier A then Tier B.

### 2. Build the story → slice map

Fetch the PRD's sub-issues per `docs/agents/issue-tracker.md`. Read the
`## User stories covered` section of **both** shipped and open slices —
the mapping `/to-issues` persists into each issue body. For each
**shipped** (closed/done) slice, invert it into `story → [shipped
slices]`. For each **open** (not-shipped) slice, invert it into
`story → [open slices]` separately — this is what tells deferred apart
from a real gap.

- A slice whose section says `None — enabling/infrastructure slice`
  contributes no story coverage; that is expected, not a gap.
- Slices created before `/to-issues` persisted this section won't have
  it. Fall back to inferring the map from each slice's `## What to
  build` + (for shipped slices) its merged diff, and **warn** that the
  map is inferred and lower-confidence for those slices. Apply the same
  inference to open slices so the shipped-vs-open split still holds.
- A story claimed **only by still-open slices** (none shipped) is
  **deferred**, not a gap — the work to cover it hasn't landed yet
  (typically the covering slice is gated behind an open `[HITL]` and
  `/tdd-parallel` deferred it to a partial run). Record the blocking
  open slice ref as evidence. Deferred stories are **not** driven
  through Tier B and **not** filed as gaps (see steps 4–7).
- A story with **no claiming slice at all** (neither shipped nor open)
  is a strong gap candidate — a real hole — but absence of a claim is
  not proof of absence, and presence of a claim is not proof of
  coverage. Every non-deferred in-scope story is still verified by test
  below regardless of what the map says; the map only decides Tier A
  search order, separates deferred from gap, and surfaces suspicious
  holes early.

This deferral derivation is **always on** — it's a function of tracker
state (shipped vs open slices), not a flag. When every slice is
shipped, no story is deferred and the run is identical to before.

### 3. Tier A — map to an existing passing test

Set aside the `deferred` stories from step 2 (claimed only by still-open
slices) and the `out-of-scope` stories — neither is verified this run. A
deferred story has no shipped code to test yet; driving it through Tier A
would always miss and Tier B would manufacture a spurious gap. The
remaining in-scope, not-deferred stories go through Tier A then Tier B.

For each such story, search the test suite for the behavioural
test(s) that exercise it (the story → slice map narrows where to look;
the glossary aligns naming; the story's `AC<n>:` criteria name the
behaviour). A story is **covered** only when:

- mapped test(s) covering its acceptance criteria **pass** when run
  now, **and**
- reading the test body confirms it exercises *this story's*
  behaviour through a public interface — not a name coincidence, not
  an implementation-detail assertion (`tests.md` rules apply).

Run the mapped tests (scope to the relevant suite/files; a full run
is fine if cheap). Record the passing test's path + name as the
evidence. Anything not satisfied here falls through to Tier B.

### 4. Tier B — generate, prove non-vacuous, run

Skip this step entirely under `--no-generate` (such stories →
`unverified`).

For each story Tier A did not satisfy:

1. **Write acceptance test(s) covering the story's acceptance
   criteria** through the public interface. The story's `AC<n>:`
   lines are the contract — turn each into an assertion against the
   public interface (one test may cover several closely-related
   criteria, or one test per criterion where they're independent).
   Behaviour, not implementation — it must read like the story
   (`tdd/SKILL.md` philosophy).
2. **Prove it is non-vacuous by mutation.** A test that passes
   against broken code proves nothing. Perturb the implementing code
   path (force a wrong return / comment out the effect), run the
   test, and confirm it goes **RED**. Then revert the perturbation
   exactly (the pre-flight clean-tree check makes this safe). A test
   that stays GREEN under perturbation is vacuous — discard it and
   re-derive against the criterion it should pin (re-read the
   `AC<n>:` line — it should pin the behaviour precisely).
3. **Run it against the real integrated code:**
   - GREEN + proven non-vacuous → the criterion is exercised. A story
     is **covered** when *every* one of its acceptance criteria has a
     passing, non-vacuous test. The generated tests are durable
     regression artifacts — keep them.
   - RED → genuine **gap**. Keep the failing test as the receipt; it
     is dispositioned in step 7.

Work one story at a time — write its test(s), prove each non-vacuous,
run them, move on; never batch-write Tier B tests across stories (same
anti-horizontal-slicing reason as `tdd/SKILL.md`).

### 5. Coverage matrix

Render one row per story:

| State | Meaning | Evidence |
|---|---|---|
| `covered` | Tier A or Tier B GREEN | test path+name |
| `gap` | Tier B RED, **or** no claiming slice at all (real hole) | failing test path / "no claiming slice" |
| `deferred` | claimed only by still-open slice(s); none shipped yet | the blocking open slice ref |
| `unverified` | `--no-generate`, no existing test | — |
| `out-of-scope` | excluded by PRD `## Out of Scope` | the excluding PRD line |

`deferred` is distinct from both `gap` (a hole to fix now) and
`out-of-scope` (a permanent exclusion): it's a *temporary* not-yet —
the covering slice is open and will land on a later `/tdd-parallel` run.
Deferred stories never become gaps and are never filed.

Print aggregate counts.

**Default mode (no `--auto`)**: before filing anything, **confirm with
the user** — this matrix is a review surface. The user can override any
row (e.g. accept a gap as out-of-scope, or reclassify).

**`--auto` mode**: skip the confirmation; proceed directly to step 6.
The human review surface moves downstream to `/triage` (for filed gap
issues) — if Tier B misjudged an acceptance criterion and filed a bogus gap, the
triage step is where it's caught and dropped.

### 6. Disposition the failing Tier B tests

A red test cannot land on a green suite. For each `gap` with a failing
test, quarantine it with the project's skip/xfail marker (infer from
the test framework — `@pytest.mark.skip`, `it.skip`, `t.Skip`,
`xit`, …), and put the gap issue reference in the skip reason:

```
skip("gap: PRD story <N> — see <issue-ref>; un-skip when implemented")
```

Commit the quarantined tests via `/commit` (never craft commits
yourself). This makes every gap traceable from the suite itself, and
the remediation slice's acceptance criterion becomes literally
"un-skip this test and make it green." Under `--no-file` there is no
issue ref yet — use `gap: PRD story <N> — unfiled` and tell the user.

### 7. Auto-file the gaps

Skip under `--no-file`. For each `gap` (Tier B RED), publish one issue
per `docs/agents/issue-tracker.md`:

- **Title:** `Cover PRD story <N>: <short description>`. Do **not**
  pre-assign an `[AFK]`/wave-number prefix — these are un-sliced work
  items, not slices. If the auto-loop later re-sliced them, that
  prefix would conflict.
- **Body** (issue template below).
- **Labels:**
  - **Default mode**: `needs-triage` + `backlog` (same convention
    `/to-issues` uses) so each enters normal triage.
  - **`--auto` mode**: `ready-for-agent` + `backlog`. The acceptance
    criterion is fully specified (the quarantined test is the
    contract), the work is definitionally AFK (manual stories were
    refused at PRD ingestion), and the orchestrator is about to
    fanout these issues in its next loop iteration — going through
    `/triage` first would just stall the loop. Quality risk (a
    false-positive gap getting auto-fixed) is bounded: the
    remediation slice will write code to make the (potentially
    wrong) test green; a subsequent verify-coverage round will either
    declare the story covered or surface the inconsistency. The
    circuit breakers in `/tdd-parallel` cap the worst case.
- **Link as a sub-issue of the PRD** using the same mechanism
  `/to-issues` uses, so the PRD stays the tracking container and does
  not spuriously auto-close while gaps are open:

  ```bash
  PARENT_ID=$(gh api graphql -f query='query{repository(owner:"OWNER",name:"REPO"){issue(number:PARENT){id}}}' -q .data.repository.issue.id)
  CHILD_ID=$(gh api graphql -f query='query{repository(owner:"OWNER",name:"REPO"){issue(number:CHILD){id}}}' -q .data.repository.issue.id)
  gh api graphql -f query='mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){subIssue{number}}}' -f p="$PARENT_ID" -f c="$CHILD_ID"
  ```

  Linear: set `parentId`. GitLab / local-markdown / unsupported: the
  `## Parent` text reference is the only link.

<issue-template>
## Parent

A reference to the PRD issue on the issue tracker.

## What to build

The PRD user story this gap leaves uncovered, quoted verbatim
(including its `AC<n>:` acceptance criteria), plus a one-line
statement of the observed gap (Tier B test RED against
the integrated branch).

## Acceptance criteria

- [ ] The quarantined test `<path::name>` is un-skipped and passes
- [ ] Behaviour is reachable through the public interface, not an
  implementation-detail assertion

## Blocked by

None - can start immediately
</issue-template>

If `docs/agents/project-board.md` exists, newly filed issues are
auto-added to the project by the user's existing workflow; do not
move the PRD's own card (it remains a tracking container).

### 8. Post the coverage receipt

This is the artifact `/tdd-parallel`'s auto-loop consumes — write it
on **every** completed run (including `--no-file` and `--no-generate`),
after the matrix is computed and any filing/disposition is done.

Capture `git rev-parse HEAD` as the **verified-sha** — the receipt
asserts "coverage was checked against *this* tree." Write the receipt
per `docs/agents/issue-tracker.md` conventions:

- **GitHub / GitLab:** post a comment on the PRD issue, led by the
  literal marker line `## Coverage receipt — verify-coverage` so the
  orchestrator can find the latest one.
- **Local markdown:** write/overwrite
  `.scratch/<NNN>-<feature-slug>/verify-coverage-receipt.md` and
  include it in the same commit as the quarantined tests.

Receipt body (stable fields the orchestrator parses):

```
## Coverage receipt — verify-coverage
- prd: <PRD ref>
- branch: <branch name>
- verified-sha: <full git sha>
- mode: full | partial (--no-generate)
- invocation: auto | manual
- matrix: covered=<n> gap=<n> deferred=<n> unverified=<n> out-of-scope=<n>
- deferred-stories: <story N → blocking open slice ref, … | none>
- gaps-filed: <#a, #b | none (--no-file) | none (no gaps)>
- ts: <ISO-8601 UTC>
```

`mode: partial` (a `--no-generate` run) is recorded honestly and will
**not** terminate `/tdd-parallel`'s auto-loop — the orchestrator wants
every story actually exercised, not skipped as `unverified`.
`invocation` records whether this run was chained by an orchestrator
(`auto`) or invoked directly by a human (`manual`) — useful for audit
("when did this story start failing?").

### 9. Terminal report

Print the structured terminal block the orchestrator parses:

```
verify-coverage: matrix covered=<n> gap=<n> deferred=<n> unverified=<n> out-of-scope=<n>
gaps-filed: <#a, #b | none>
deferred-stories: <story N → open slice ref, … | none>
quarantined-tests-commit: <sha | none>
receipt: <comment URL or file path>
verified-sha: <full git sha>
```

`/tdd-parallel`'s step 4b reads `deferred=<n>` here: `gap=0 deferred>0`
is its partial-complete signal (proceed to the `[partial]` PR, don't
loop), while `gap>0` still drives the auto-fix loop. The two counts are
independent — a run can report both (some stories have a real gap to fix
now, others are deferred behind an open `[HITL]`).

Plus, for direct invocation (no `--auto`), a one-line next-step hint:

> Filed N gap issues as sub-issues of #PRD. Run `/triage` to walk them
> to `ready-for-agent`, then `/tdd-parallel <PRD>` to clear them — the
> remediation slices un-skip the quarantined tests.

Under `--auto`, omit the hint — the orchestrator is the next step.

Do not chain — this skill ends here.

## Not in scope

- Implementing the gaps — that's `/tdd` / `/tdd-parallel`.
- Triaging or slicing the filed gap issues — that's `/triage` /
  `/to-issues`. (In `--auto` mode, the orchestrator fanouts them
  directly without a triage hop because the gap is fully specified by
  its quarantined test.)
- Verifying anything against a PRD that has no `## User Stories`
  section, or whose stories lack an `AC<n>:` acceptance criterion —
  refuse in pre-flight.

## Constraints

- **Test, don't assess.** No story reaches `covered` on prose or
  code-search judgement alone — only a passing, non-vacuous
  behavioural test (Tier A/B).
- **Every Tier B test must survive the mutation check** before its
  result is trusted. Vacuous tests are worse than no test.
- **The matrix outcome is advisory in default mode, automatic in
  `--auto`.** In default mode, ends in user confirmation. In `--auto`,
  the human review surface moves to `/triage` (for filed gaps);
  `/tdd-parallel`'s circuit breakers (round limit, per-story retry
  limit, no-progress halt) cap the worst case of a misjudged
  acceptance criterion looping.

<!-- BEGIN bundled-book-rules -->

## Bundled book rules

Do not hand-edit content between the `BEGIN`/`END` markers — `scripts/sync_book_rules.py` overwrites it from `vendor/agent-rules-books/`.

### Rules from "Working Effectively with Legacy Code" by Michael Feathers

<!-- BEGIN working-effectively-with-legacy-code.mini.md v0.5 -->

# OBEY Working Effectively with Legacy Code by Michael Feathers

## When to use

Use when changing code that is expensive to change safely because behavior is unclear, tests are weak or missing, dependencies are hidden, or runtime/framework setup blocks local feedback.

## Primary bias to correct

Gain control before improving design. Understand current behavior, protect what must stay, create the smallest useful seam, break the dependency that blocks feedback, make the requested change, then leave the area more testable.

## Decision rules

- Treat any area without trustworthy tests as legacy code; do not start with rewrite or module-wide cleanup unless that is explicitly required or clearly safer.
- Before editing, state the requested behavior change and the current behavior that must remain; characterize uncertain or suspicious behavior instead of silently fixing it.
- Follow the legacy loop: identify the change point, check existing protection, add characterization where possible, find or create a seam, break the blocking dependency, change behavior, then refactor locally.
- Prefer fast, focused tests around the slice being changed; use broader interception or integration tests only when they are the safest first observation point.
- Choose test points by tracing effects outward from the change point through values, calls, fields, outputs, collaborators, interception points, and pinch points.
- Use the smallest seam that allows substitution, observation, or interception; make clear whether the seam is for sensing, separation, or both.
- Break dependencies deliberately: expose hidden inputs, hard outputs, hard construction, globals, statics, ambient context, and framework callbacks only where they block testing or safe change.
- Keep behavior changes, structural refactorings, and cleanup separate; verify small steps and avoid checking in exploratory restructuring used only for understanding.
- When direct edits are risky, add behavior with sprout method, sprout class, wrap method, wrap class, or extract-and-override style moves, then fold the temporary structure into better design when tests support it.
- For hard-to-test methods, split construction from use, extract side effects behind collaborators, carve pure computation first, and isolate policy from runtime, persistence, UI, or framework mechanisms.
- Use dependency-breaking techniques according to the actual barrier: adapt narrow parameters, extract interfaces or implementers, parameterize constructors or methods, encapsulate globals, introduce instance delegators, override factories/calls, or use link/preprocessing seams only when ordinary object seams are impractical.
- In large code, sketch effects and group responsibilities before moving behavior; let excessive setup, impossible observation, and repeated changes point to smaller extracted responsibilities.
- During review, treat no tests around modified logic, mixed structural and behavioral edits, broad edits in poorly understood modules, hard-coded collaborators, global/static reach-through, constructor side effects, and business logic trapped in framework entry points as legacy-change risks.
- Reject changes that expand hidden dependencies, mock around untestable structure without improving it, rename or format while leaving the real dependency knots intact, or introduce large architecture before basic seams exist.
- Leave the touched area easier to understand, test, or change; do not mistake test-only seams, wrappers, subclass tricks, or build tricks for design improvement by themselves.

## Trigger rules

- When behavior is uncertain, consumers may rely on ugly behavior, or a branch/path is hard to prove, add characterization or another explicit observation path before changing semantics.
- When tests require too much setup or a class cannot be instantiated cheaply, break the first real barrier: constructor work, hidden allocation, factory call, global state, static construction, framework object, or hard parameter.
- When time, randomness, environment, thread-local state, current user/request, files, network, process exits, database writes, messages, or control-flow logging block repeatable tests, wrap or inject that boundary.
- When a large method or class defeats local reasoning, sketch effects, find interception or pinch points, extract pure computation first, and avoid editing many branches at once.
- When changing database-heavy, UI, framework, or API-boundary code, separate policy from query/mapping/persistence, handlers/callbacks, adapters, and runtime setup; keep real-boundary integration tests where they matter.
- When a seam is magical, temporary, public-for-test, subclass-only, link/preprocessor-based, or probe/sensing-variable-based, add a cleanup obligation and remove it once safer structure exists.
- When repeated edits cluster across several places, remove duplication incrementally under tests instead of launching a broad redesign.
- When rewrite or heroic cleanup feels tempting, choose the smallest sprout, wrap, seam, characterization, or refactoring step that makes today's requested change safer.

## Final checklist

- Untested or weakly tested area treated as legacy risk?
- Behavior delta and behavior-to-preserve stated?
- Uncertain current behavior characterized or explicitly observed?
- Tests close enough and fast enough to diagnose the change?
- Smallest useful seam chosen, with sensing vs separation clear?
- Blocking dependency reduced without expanding hidden dependencies?
- Behavior change, refactoring, and cleanup kept separate?
- Temporary seam or dependency-breaking trick has a cleanup path?
- Touched area is more understandable, testable, or changeable?

<!-- END working-effectively-with-legacy-code.mini.md -->

<!-- END bundled-book-rules -->
