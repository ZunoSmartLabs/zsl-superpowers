# [AFK] 3 — Extract domain-modeling (model-invoked); repoint grill-with-docs + improve-codebase-architecture; re-key sync_book_rules.py

Status: ready-for-agent
github: 16

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

Give the ADR and CONTEXT formats one home. Create a **model-invoked**
`domain-modeling` skill that owns the ADR-format and CONTEXT-format guidance
(seeded from the existing inline files so no phrasing regresses), delete those
format files from `grill-with-docs`, and repoint `grill-with-docs` and
`improve-codebase-architecture` to consume the shared skill. Move the two DDD
book-rule embeds to follow the reasoning: re-key `sync_book_rules.py`'s MAPPING
from `grill-with-docs` to `domain-modeling`, then run the sync so the
`BEGIN/END` blocks regenerate in the new home. Sync the model-invoked skill
across its lighter surfaces (plugin.json + "Shared / model-invoked" subsection).

## Acceptance criteria

- [ ] `skills/engineering/domain-modeling/` contains the ADR-format and
      CONTEXT-format guidance; `grill-with-docs/{ADR-FORMAT,CONTEXT-FORMAT}.md`
      no longer exist.
- [ ] `grill-with-docs/SKILL.md` and `improve-codebase-architecture/SKILL.md`
      both reference `domain-modeling` and contain no inline ADR/CONTEXT format
      definition.
- [ ] `scripts/sync_book_rules.py` MAPPING keys `domain-modeling` (not
      `grill-with-docs`) to the two DDD embeds; running the sync leaves
      `domain-modeling/SKILL.md` with the DDD `BEGIN/END` block and
      `grill-with-docs/SKILL.md` without it.
- [ ] `domain-modeling` is registered in `plugin.json` and the "Shared /
      model-invoked" doc subsection (no decision-tree node / user-command entry).
- [ ] `make lint test docs` exit 0.

## User stories covered

- 7 — `domain-modeling` model-invoked skill owns the ADR/CONTEXT formats.
  - acceptance: automatable
  - observable: `skills/engineering/domain-modeling/` contains the ADR-format
    and CONTEXT-format guidance, and
    `grill-with-docs/{ADR-FORMAT,CONTEXT-FORMAT}.md` no longer exist.
- 8 — `grill-with-docs` and `improve-codebase-architecture` consume it.
  - acceptance: automatable
  - observable: both SKILL.md files reference `domain-modeling` and contain no
    inline ADR/CONTEXT format definition.
- 9 — DDD book-rules embedded on `domain-modeling`.
  - acceptance: automatable
  - observable: `scripts/sync_book_rules.py` MAPPING keys `domain-modeling`
    (not `grill-with-docs`) to the two DDD embeds; running the sync leaves
    `domain-modeling/SKILL.md` with the DDD `BEGIN/END` block and
    `grill-with-docs/SKILL.md` without it; `make docs` passes.

## Blocked by

- #12 ([AFK] 2a — Extract codebase-design) — shares
  `improve-codebase-architecture/SKILL.md`; serialized to avoid integration
  conflicts.

## Verification

Ran on the feature branch — all observables PASS, `make lint test docs` exit 0.

- Story 7: `skills/engineering/domain-modeling/` contains ADR-FORMAT.md + CONTEXT-FORMAT.md (git mv from grill-with-docs); SKILL.md has no `disable-model-invocation` flag (model-invoked); `grill-with-docs/{ADR-FORMAT,CONTEXT-FORMAT}.md` no longer exist → PASS.
- Story 8: `grill-with-docs/SKILL.md` and `improve-codebase-architecture/SKILL.md` both reference `domain-modeling`; neither carries an inline ADR/CONTEXT format definition → PASS.
- Story 9: `sync_book_rules.py` MAPPING keys `engineering/domain-modeling` (not `grill-with-docs`); `make sync-books` left the DDD `BEGIN/END` block on `domain-modeling/SKILL.md` and removed it from `grill-with-docs/SKILL.md`; sync is idempotent ("All SKILL.md files already in sync."); `make docs` passes → PASS.
- Model-invoked sync: plugin.json + "Shared / model-invoked" subsection row + `not_in_nav: skills/domain-modeling.md`; absent from READMEs / role tables / decision tree.
