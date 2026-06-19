# [AFK] 5 — Add decision-mapping (user-invoked)

Status: ready-for-agent
github: 19

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

Add a **user-invoked** `decision-mapping` skill that turns a loose idea into a
sequenced ticket map so multi-session ideas mature before a PRD. It composes the
model-invoked primitives directly (`grilling`, `domain-modeling`, `prototype`)
and hands off to `to-prd` — never calling `grill-with-docs` (the taxonomy
forbids a user-invoked skill calling another user-invoked skill). Store maps
under `.scratch/decision-maps/` to match our state convention, fix the upstream
`domain-modelling` (double-L) typo, and declare being AFK-wired an explicit
non-goal. Flag it `disable-model-invocation: true` and sync across all five
places.

## Acceptance criteria

- [ ] `skills/engineering/decision-mapping/SKILL.md` exists and is
      `disable-model-invocation: true`.
- [ ] It references `grilling`, `domain-modeling`, `prototype`, and `to-prd`,
      and never references `grill-with-docs`.
- [ ] It writes maps to `.scratch/decision-maps/`.
- [ ] It contains no `domain-modelling` (double-L) spelling.
- [ ] It declares being AFK-wired an explicit non-goal.
- [ ] The five-place skill sync is updated (incl. a `decision-mapping` node in
      the Plan branch of the decision tree).
- [ ] `make lint test docs` exit 0.

## User stories covered

- 12 — `decision-mapping` skill turns a loose idea into a sequenced ticket map.
  - acceptance: automatable
  - observable: `skills/engineering/decision-mapping/SKILL.md` exists, is
    `disable-model-invocation: true`, and references `grilling`,
    `domain-modeling`, `prototype`, and `to-prd` (never `grill-with-docs`).
- 13 — Map stored under `.scratch/` and the upstream typo fixed.
  - acceptance: automatable
  - observable: `decision-mapping/SKILL.md` writes maps to
    `.scratch/decision-maps/`, contains no `domain-modelling` (double-L)
    spelling, and declares being AFK-wired an explicit non-goal.

## Blocked by

- #16 ([AFK] 3 — Extract domain-modeling) — references `domain-modeling`.
- #17 ([AFK] 4a — Extract grilling) — references `grilling`.

## Verification

Ran on the feature branch — all observables PASS, `make lint test docs` exit 0.

- Story 12: `skills/engineering/decision-mapping/SKILL.md` exists, `disable-model-invocation: true`; references `grilling`, `domain-modeling`, `prototype`, and `to-prd`; grep for `grill-with-docs` → no hits (never references it) → PASS.
- Story 13: writes maps to `.scratch/decision-maps/`; grep for `domain-modelling` (double-L) → no hits; declares being AFK-wired an explicit non-goal → PASS.
- Five-place sync: plugin.json, top README (Plan workflow section + Reference Engineering), engineering bucket README, docs/skills/index.md Plan role table + a `decision_mapping` node in the **Plan** branch of the decision tree, mkdocs.yml Plan nav.
