# [AFK] 6 — Add ask-zsl router; pair with decision tree in sync contract

Status: ready-for-agent
github: 20

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

Add a **user-invoked** `ask-zsl` interactive router so a user can find the right
skill mid-session without leaving their work. It is a thin router (routing logic
only, deferring skill descriptions to existing docs): it encodes situational
routing questions and routes over the whole ZSL loop —
`afk-fanout`/`afk-worker`/`morning-review`, `tdd` vs `tdd-parallel`,
`verify-coverage`, `human-itl`, and `decision-mapping`. Authored **last**, against
the final skill inventory, so its routing reflects every other change in this
PRD. Flag it `disable-model-invocation: true`, sync across all five places, and
add the `ask-zsl` ↔ decision-tree pairing to the `CLAUDE.md` sync contract.

## Acceptance criteria

- [ ] `skills/engineering/ask-zsl/SKILL.md` exists and is
      `disable-model-invocation: true`.
- [ ] It encodes situational routing questions and routes over the ZSL loop
      including `afk-fanout`/`afk-worker`/`morning-review`, `tdd` vs
      `tdd-parallel`, `verify-coverage`, `human-itl`, and `decision-mapping`.
- [ ] `CLAUDE.md` names `ask-zsl` and `docs/skills/index.md`'s decision tree as
      a routing pair that must move together.
- [ ] The five-place skill sync is updated.
- [ ] `make lint test docs` exit 0.

## User stories covered

- 15 — `ask-zsl` interactive router.
  - acceptance: automatable
  - observable: `skills/engineering/ask-zsl/SKILL.md` exists, is
    `disable-model-invocation: true`, encodes situational routing questions,
    and routes over the ZSL loop including `afk-fanout`/`afk-worker`/
    `morning-review`, `tdd` vs `tdd-parallel`, `verify-coverage`, `human-itl`,
    and `decision-mapping`.
- 16 — Sync contract pairs `ask-zsl` with the decision tree.
  - acceptance: automatable
  - observable: `CLAUDE.md` names `ask-zsl` and `docs/skills/index.md`'s
    decision tree as a routing pair that must move together.

## Blocked by

- #12 ([AFK] 2a — Extract codebase-design)
- #13 ([AFK] 2b — writing-great-skills)
- #14 ([AFK] 2c — Remove caveman)
- #15 ([AFK] 2d — Remove zoom-out)
- #16 ([AFK] 3 — Extract domain-modeling)
- #17 ([AFK] 4a — Extract grilling)
- #18 ([AFK] 4b — Add teach-me-the-codebase)
- #19 ([AFK] 5 — Add decision-mapping)

(Authored last against the final inventory.)
