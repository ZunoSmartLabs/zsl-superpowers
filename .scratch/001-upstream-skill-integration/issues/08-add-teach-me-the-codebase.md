# [AFK] 4b — Add teach-me-the-codebase (user-invoked)

Status: ready-for-agent
github: 18

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

Add a **user-invoked** `teach-me-the-codebase` tutor: an on-the-fly
conversational onboarding skill with zero persisted artefacts. It reads the
canonical `CONTEXT.md`/ADRs/`CLAUDE.md`/code and hands undocumented terms to
`domain-modeling`/`grill-with-docs` (teacher-only boundary — it never writes
`CONTEXT.md` or a parallel glossary), and offers an optional `md-to-html`
cheat-sheet on demand rather than persisting one. Flag it
`disable-model-invocation: true` and sync it across all five places.

## Acceptance criteria

- [ ] `skills/engineering/teach-me-the-codebase/SKILL.md` exists and is
      `disable-model-invocation: true`.
- [ ] It has no `lessons/` or `learning-records/` workspace directories.
- [ ] It states it reads `CONTEXT.md`/ADRs/`CLAUDE.md`/code and hands
      undocumented terms to `domain-modeling`/`grill-with-docs`.
- [ ] It offers an optional `md-to-html` cheat-sheet rather than persisting one.
- [ ] The five-place skill sync is updated (plugin.json, top README, bucket
      README, docs/skills/index.md role table + decision-tree node, mkdocs.yml).
- [ ] `make lint test docs` exit 0.

## User stories covered

- 14 — `teach-me-the-codebase` tutor.
  - acceptance: automatable
  - observable: `skills/engineering/teach-me-the-codebase/SKILL.md` exists, is
    `disable-model-invocation: true`, has no `lessons/`/`learning-records/`
    workspace directories, states it reads `CONTEXT.md`/ADRs/`CLAUDE.md`/code
    and hands undocumented terms to `domain-modeling`/`grill-with-docs`, and
    offers an optional `md-to-html` cheat-sheet rather than persisting one.

## Blocked by

- #16 ([AFK] 3 — Extract domain-modeling) — references `domain-modeling`.
