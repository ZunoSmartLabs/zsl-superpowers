# [AFK] 1 — Establish invocation taxonomy (invocation.md, CLAUDE.md sixth lane, ADR, flag existing orchestrators)

Status: ready-for-agent
github: 11

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

The taxonomy groundwork every other slice in this PRD builds on. Introduce the
lightweight **User-invoked / Model-invoked** split as repo infrastructure:
publish the rule in a new `docs/invocation.md`, add a sixth sync lane to
`CLAUDE.md` describing how model-invoked-only skills are treated, ensure the
taxonomy ADR is present and kept out of the strict docs build, and flag the
**four already-existing** pure orchestrators so they never auto-fire. The four
new orchestrators introduced later in this PRD (`decision-mapping`,
`teach-me-the-codebase`, `ask-zsl`, `writing-great-skills`) carry their own
`disable-model-invocation` flag in their own slices; the full eight-orchestrator
state is re-verified by the release slice (#21).

## Acceptance criteria

- [ ] `docs/invocation.md` exists and contains the rule that a user-invoked
      skill may invoke model-invoked skills but never another user-invoked skill.
- [ ] The SKILL.md frontmatter of `commit`, `commit-push-pr`, `afk-fanout`, and
      `tdd-parallel` each contain `disable-model-invocation: true`.
- [ ] `CLAUDE.md` contains a sixth sync lane stating model-invoked-only skills
      are registered in `plugin.json` + a "Shared / model-invoked" doc
      subsection but omitted from the decision tree and user-command lists.
- [ ] `docs/adr/0001-user-invoked-model-invoked-taxonomy.md` exists,
      `mkdocs.yml` has top-level `not_in_nav: adr/*`, and `make docs` passes.
- [ ] `make lint test docs` exit 0.

## User stories covered

- 1 — Documented definition of the user/model-invoked split.
  - acceptance: automatable
  - observable: `docs/invocation.md` exists and contains the rule that a
    user-invoked skill may invoke model-invoked skills but never another
    user-invoked skill.
- 2 — Pure orchestrators flagged so they never auto-fire.
  - acceptance: automatable
  - observable: the SKILL.md frontmatter of each pure orchestrator (`commit`,
    `commit-push-pr`, `afk-fanout`, `tdd-parallel`, `decision-mapping`,
    `teach-me-the-codebase`, `ask-zsl`, `writing-great-skills`) contains
    `disable-model-invocation: true`.
  - **Scope note:** this slice satisfies the four already-existing orchestrators
    (`commit`, `commit-push-pr`, `afk-fanout`, `tdd-parallel`). The four new
    orchestrators set the flag in their own slices (#13, #18, #19, #20); the
    full eight-skill observable is re-verified by the release slice (#21).
- 3 — Sync contract describes the model-invoked lane.
  - acceptance: automatable
  - observable: `CLAUDE.md` contains a sixth lane stating model-invoked-only
    skills are registered in `plugin.json` + a "Shared / model-invoked" doc
    subsection but omitted from the decision tree and user-command lists.
- 28 — Taxonomy ADR present but unpublished.
  - acceptance: automatable
  - observable: `docs/adr/0001-user-invoked-model-invoked-taxonomy.md` exists,
    `mkdocs.yml` has top-level `not_in_nav: adr/*`, and `make docs` passes.

## Blocked by

None - can start immediately.

## Verification

Ran on `feature/v2.0.0-upstream-skill-integration` — all observables PASS, `make lint test docs` exit 0.

- Story 1: `test -f docs/invocation.md && grep "may invoke model-invoked skills, but never another" docs/invocation.md` → PASS.
- Story 2: `grep "disable-model-invocation: true"` in `commit`, `commit-push-pr`, `afk-fanout`, `tdd-parallel` SKILL.md → all PASS (four existing orchestrators; the four new ones flagged in #13/#18/#19/#20, re-verified in #21).
- Story 3: `grep "Sixth lane"` + `grep "Shared / model-invoked"` in `CLAUDE.md` → PASS (registered in plugin.json + Shared/model-invoked subsection; omitted from decision tree + user-command lists).
- Story 28: `test -f docs/adr/0001-user-invoked-model-invoked-taxonomy.md` + `not_in_nav: adr/*` in `mkdocs.yml` + `make docs` exit 0 → PASS.
