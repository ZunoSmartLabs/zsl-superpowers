---
name: verify-coverage
description: Verify every PRD user story is covered by a passing behavioral test, generate-and-prove tests for the gaps, route non-automatable stories to a human-attestation lane, and auto-file genuine gaps as triage issues. Use after /tdd-parallel integrates a PRD's slices, when the user wants to check a PRD is fully covered, or invokes /verify-coverage directly.
disable-model-invocation: true
---

# Verify Coverage

`/to-issues` slices a PRD into issues and `/tdd` builds them, but the only
post-implementation completeness signal is *structural*: the tracker
auto-closes the parent when every child closes. "All slices shipped" is
not "all user stories covered" — those come apart exactly when slicing
drops or misframes a story.

This skill closes that loop. It uses the PRD's `## User Stories` section
as an **acceptance oracle** (not as implementation context — `/tdd`
deliberately never sees it) and answers, per story, *is there a passing
behavioral test that proves this is built?* It does **not** trust
prose-vs-prose or code-search judgement — a story is covered only when an
executable, non-vacuous test says so.

Run it on the integration/PRD branch after a `/tdd-parallel` fanout
completes. This is no longer optional: `/tdd-parallel` step 4a is an
**execution gate** that refuses to open the integration PR until a valid
coverage receipt for the integrated tip exists (step 10 writes it). The
gate enforces that the check *ran*, never that the matrix came back
clean — gaps are allowed; skipping the check is not. You can also run it
any time against a parent PRD whose slices have shipped.

## The oracle, weakest to strongest

1. Prose vs prose — LLM reads PRD + issues and judges. Fuzzy; rejected.
2. Prose vs code search — grep for code that *looks* related. Confirms
   code exists, not that behaviour is correct. Demoted to a *hint* only.
3. **Prose vs existing passing test** (Tier A) — a behavioural test that
   exercises the story's observable behaviour and is green.
4. **Prose vs generated-and-proven test** (Tier B) — for stories with no
   such test, write one, prove it is non-vacuous, then run it.

Stories that are not expressible as an automated test (visual/UX, "feels
welcoming", real external systems) cannot reach Tier A/B — they go to the
**HITL lane** for human attestation, the same AFK/HITL split the rest of
the loop uses.

## Usage

```
/zsl:verify-coverage <parent-prd-issue>   # verify all of a PRD's stories
/zsl:verify-coverage                      # no arg → picker of tracking PRDs
```

Flags:

- `--no-file` — produce the matrix and the quarantined failing tests, but
  do **not** auto-file gap issues. Report-only. Still a **full** run —
  writes a gate-satisfying receipt (verification happened; you chose not
  to file).
- `--no-generate` — Tier A only. Stories without an existing passing test
  are reported as `unverified` rather than driven through Tier B. Fast
  pass for a quick read; no tests are written. Writes a **partial**
  receipt, which does **not** satisfy `/tdd-parallel`'s coverage gate —
  unverified rows mean those stories weren't actually checked.

## Pre-flight

Refuse with a clear message if any fails:

- `docs/agents/issue-tracker.md` exists (run `/setup-zsl-superpowers` if
  not). `docs/agents/triage-labels.md` exists.
- The input resolves to a PRD: an issue with a `## User Stories` section.
  No argument → present a numbered picker of issues in the `tracking`
  state (PRDs whose children are in flight). If the resolved issue has no
  `## User Stories` section it is not a PRD — refuse and say so.
- The working tree is on the branch carrying the integrated work (the
  PRD/integration branch for a `/tdd-parallel` run, or wherever the
  shipped slices live). Refuse if dirty (`git status --porcelain`
  non-empty) — Tier B writes and runs tests, and a dirty tree makes the
  non-vacuity mutation unsafe to revert cleanly.

Use the project domain glossary so story vocabulary maps onto the
codebase's and test suite's vocabulary; respect ADRs in the touched area.
See `engineering/tdd/tests.md` for what a behavioural test is and
`engineering/tdd/mocking.md` for what disqualifies one.

## Process

### 1. Build the story inventory

Parse the PRD's `## User Stories` into a numbered list, verbatim. Parse
`## Out of Scope`: any story (or behaviour) that `## Out of Scope`
excludes is marked `out-of-scope` now and never verified — record the
PRD line that excludes it as the evidence.

### 2. Build the story → slice map

Fetch the PRD's sub-issues per `docs/agents/issue-tracker.md`. For each
**shipped** (closed/done) slice, read its `## User stories covered`
section — the mapping `/to-issues` now persists into each issue body.
Invert it into `story → [slices]`.

- A slice whose section says `None — enabling/infrastructure slice`
  contributes no story coverage; that is expected, not a gap.
- Slices created before `/to-issues` persisted this section won't have
  it. Fall back to inferring the map from each slice's `## What to build`
  + its merged diff, and **warn** the user the map is inferred and
  lower-confidence for those slices.
- A story with no claiming slice is a strong gap candidate — but absence
  of a claim is not proof of absence, and presence of a claim is not
  proof of coverage. Every story is still verified by test below
  regardless of what the map says; the map only decides Tier A search
  order and surfaces suspicious holes early.

### 3. Classify each story: AFK-testable vs HITL-verifiable

For each in-scope story, decide whether its acceptance is expressible as
an automated test through a public interface:

- **AFK-testable** — observable behaviour (an API result, a state
  transition, a rendered value, an emitted event). Goes to Tier A/B.
- **HITL-verifiable** — requires human judgement, a real external system,
  or a visual/UX assessment no assertion captures. Goes to the HITL lane.

This classification is LLM judgement, so surface it as a list and let the
user re-classify any story before tests are written. Err toward
AFK-testable: if a story *can* be pinned by an assertion, it should be.

### 4. Tier A — map to an existing passing test

For each AFK-testable story, search the test suite for the behavioural
test(s) that exercise it (the story → slice map narrows where to look;
the glossary aligns naming). A story is **covered** only when:

- a mapped test **passes** when run now, **and**
- reading the test body confirms it exercises *this story's* behaviour
  through a public interface — not a name coincidence, not an
  implementation-detail assertion (`tests.md` rules apply).

Run the mapped tests (scope to the relevant suite/files; a full run is
fine if cheap). Record the passing test's path + name as the evidence.
Anything not satisfied here falls through to Tier B.

### 5. Tier B — generate, prove non-vacuous, run

Skip this step entirely under `--no-generate` (such stories → `unverified`).

For each AFK-testable story Tier A did not satisfy:

1. **Write one acceptance test** expressing the story's observable
   behaviour through the public interface. Behaviour, not implementation
   — it must read like the story (`tdd/SKILL.md` philosophy).
2. **Prove it is non-vacuous by mutation.** A test that passes against
   broken code proves nothing. Perturb the implementing code path
   (force a wrong return / comment out the effect), run the test, and
   confirm it goes **RED**. Then revert the perturbation exactly (the
   pre-flight clean-tree check makes this safe). A test that stays GREEN
   under perturbation is vacuous — discard it and re-derive against a
   different observable.
3. **Run it against the real integrated code:**
   - GREEN + proven non-vacuous → story **covered**. The generated test
     is a durable regression artifact — keep it.
   - RED → genuine **gap**. Keep the failing test as the receipt; it is
     dispositioned in step 8.

Generate one test, prove it, run it, move on — never batch-write Tier B
tests (same anti-horizontal-slicing reason as `tdd/SKILL.md`).

### 6. HITL lane

For each HITL-verifiable story, present an attestation prompt: the story
verbatim, what to check, and where (URL / console / screen). The user
attests **covered** (with a one-line note → recorded as the evidence) or
**not-covered**. No test is written. A not-covered attestation becomes a
gap in step 7; a covered one is recorded with the user's note.

### 7. Coverage matrix

Render one row per story:

| State | Meaning | Evidence |
|---|---|---|
| `covered` | Tier A/B GREEN, or HITL attested | test path+name, or attestation note |
| `gap` | Tier B RED, or HITL not-covered | failing test path, or "HITL not-covered" |
| `unverified` | `--no-generate`, no existing test | — |
| `out-of-scope` | excluded by PRD `## Out of Scope` | the excluding PRD line |

Print aggregate counts and, before filing anything, **confirm with the
user** — this matrix is a review surface, not an auto-gate. The user can
override any row (e.g. accept a gap as out-of-scope, or reclassify).

### 8. Disposition the failing Tier B tests

A red test cannot land on a green suite. For each `gap` with a failing
test, quarantine it with the project's skip/xfail marker (infer from the
test framework — `@pytest.mark.skip`, `it.skip`, `t.Skip`, `xit`, …),
and put the gap issue reference in the skip reason:

```
skip("gap: PRD story <N> — see <issue-ref>; un-skip when implemented")
```

Commit the quarantined tests via `/commit` (never craft commits
yourself). This makes every gap traceable from the suite itself, and the
remediation slice's acceptance criterion becomes literally "un-skip this
test and make it green." Under `--no-file` there is no issue ref yet —
use `gap: PRD story <N> — unfiled` and tell the user.

### 9. Auto-file the gaps

Skip under `--no-file`. For each `gap` (Tier B RED, or HITL not-covered),
publish one issue per `docs/agents/issue-tracker.md`:

- **Title:** `Cover PRD story <N>: <short description>`. Do **not**
  pre-assign an `[AFK]`/`[HITL]` prefix or a wave number — these are
  un-sliced work items, not slices. They re-enter the loop through
  `/triage` (and `/to-issues` if they need slicing), which assigns those.
- **Body** (issue template below).
- **Labels:** `needs-triage` + `backlog` (same convention `/to-issues`
  uses) so each enters normal triage and shows on the board.
- **Link as a sub-issue of the PRD** using the same mechanism
  `/to-issues` uses, so the PRD stays the tracking container and does not
  spuriously auto-close while gaps are open:

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

The PRD user story this gap leaves uncovered, quoted verbatim, plus a
one-line statement of the observed gap (Tier B test RED / HITL attested
not-covered).

## Acceptance criteria

- [ ] The quarantined test `<path::name>` is un-skipped and passes
  (for HITL gaps: the manual check in the PRD story is satisfied and
  attested)
- [ ] Behaviour is reachable through the public interface, not an
  implementation-detail assertion

## Blocked by

None - can start immediately
</issue-template>

If `docs/agents/project-board.md` exists, newly filed issues are
auto-added to the project by the user's existing workflow; do not move
the PRD's own card (it remains a tracking container).

### 10. Post the coverage receipt

This is the artifact `/tdd-parallel`'s coverage gate consumes — write it
on **every** completed run (including `--no-file` and `--no-generate`),
after the matrix is confirmed and any filing/disposition is done.

Capture `git rev-parse HEAD` as the **verified-sha** — the receipt
asserts "coverage was checked against *this* tree." Write the receipt per
`docs/agents/issue-tracker.md` conventions:

- **GitHub / GitLab:** post a comment on the PRD issue (same audit-trail
  mechanism `/human-itl` uses), led by the literal marker line
  `## Coverage receipt — verify-coverage` so the gate can find the
  latest one.
- **Local markdown:** write/overwrite `.scratch/<NNN>-<feature-slug>/verify-coverage-receipt.md`
  and include it in the same commit as the quarantined tests.

Receipt body (stable fields the gate parses):

```
## Coverage receipt — verify-coverage
- prd: <PRD ref>
- branch: <branch name>
- verified-sha: <full git sha>
- mode: full | partial (--no-generate)
- matrix: covered=<n> gap=<n> unverified=<n> out-of-scope=<n>
- gaps-filed: <#a, #b | none (--no-file) | none (no gaps)>
- ts: <ISO-8601 UTC>
```

`mode: partial` (a `--no-generate` run) is recorded honestly and will
**not** satisfy the gate — the gate wants every AFK story actually
exercised, not skipped as `unverified`.

### 11. Summary

Print: PRD + branch verified, coverage matrix counts
(`covered / gap / unverified / out-of-scope`), the filed gap issue
numbers (or "report-only — `--no-file`"), the commit sha of the
quarantined tests, the receipt location (PRD comment or receipt file)
and its verified-sha, and the explicit next step:

> Filed N gap issues as sub-issues of #PRD. Run `/triage` to walk them
> to `ready-for-agent`, then `/tdd-parallel <PRD>` to clear them — the
> remediation slices un-skip the quarantined tests.

Do not chain — this skill ends with the hint.

## Not in scope

- Implementing the gaps — that's `/tdd` / `/tdd-parallel`.
- Triaging or slicing the filed gap issues — that's `/triage` /
  `/to-issues`.
- Verifying anything against a PRD that has no `## User Stories` section —
  there is no oracle; refuse in pre-flight.
- Auto-gating a merge on the matrix. The matrix terminates in a human
  decision (step 7); a silent pass/fail would manufacture false
  confidence.

## Constraints

- **Test, don't assess.** No story reaches `covered` on prose or
  code-search judgement alone — only a passing, non-vacuous behavioural
  test (Tier A/B) or an explicit human attestation (HITL).
- **Every Tier B test must survive the mutation check** before its
  result is trusted. Vacuous tests are worse than no test.
- **The matrix outcome is advisory, never an auto-gate** — it ends in
  user confirmation. `/tdd-parallel`'s gate is an *execution* gate (did
  the check run against this tip?), not an *outcome* gate (did it pass?).
  A receipt with open gaps still satisfies it; the two notions never
  collapse into "block the PR until coverage is clean."
