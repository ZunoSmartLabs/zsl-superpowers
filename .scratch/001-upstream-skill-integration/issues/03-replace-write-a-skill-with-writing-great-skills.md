# [AFK] 2b — Replace write-a-skill with writing-great-skills; relocate description-length gate; repoint make targets

Status: ready-for-agent
github: 13

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

Replace the old `write-a-skill` process skill with `writing-great-skills` (a
principles/vocabulary reference, upstream SKILL + GLOSSARY verbatim) while
preserving the description-length deterministic gate end-to-end. Relocate
`check-description-length.py` and its tests into the new skill's `scripts/`,
re-add the deterministic-gate callout with the three-environment resolver and a
Fallback heading, repoint the `make lint`/`make test` targets at the new path,
and set `disable-model-invocation: true` (the skill is a pure orchestrator).
Sync the add/remove across all five places.

## Acceptance criteria

- [ ] `skills/productivity/writing-great-skills/{SKILL.md,GLOSSARY.md}` exist;
      `skills/productivity/write-a-skill/` does not.
- [ ] `writing-great-skills/SKILL.md` frontmatter contains
      `disable-model-invocation: true` (contributes to story 2).
- [ ] `writing-great-skills/scripts/check-description-length.py` and its
      `scripts/tests/test_*.py` exist; `pytest` on them passes (including the
      fails-the-prose-way case, e.g. a 1025-char description).
- [ ] `writing-great-skills/SKILL.md` has a deterministic-gate callout with the
      three-environment resolver and a **Fallback** heading.
- [ ] The `basedpyright` line in `make lint` and the test runner in `make test`
      reference the `writing-great-skills/scripts/` path, not
      `write-a-skill/scripts/`.
- [ ] The five-place skill sync is updated (plugin.json, top README, bucket
      README, docs/skills/index.md role table, mkdocs.yml nav).
- [ ] `make lint test docs` exit 0.

## User stories covered

- 17 — `writing-great-skills` replaces the old process skill.
  - acceptance: automatable
  - observable: `skills/productivity/writing-great-skills/{SKILL.md,GLOSSARY.md}`
    exist; `skills/productivity/write-a-skill/` does not.
- 18 — Description-length gate preserved.
  - acceptance: automatable
  - observable: `writing-great-skills/scripts/check-description-length.py` and
    its `scripts/tests/test_*.py` exist, `pytest` on them passes (including the
    fails-the-prose-way case), and `writing-great-skills/SKILL.md` has a
    deterministic-gate callout with the three-environment resolver and a
    Fallback heading.
- 19 — Make targets repointed.
  - acceptance: automatable
  - observable: the `basedpyright` line in `make lint` and the test runner in
    `make test` reference the `writing-great-skills/scripts/` path, not
    `write-a-skill/scripts/`; `make lint test` pass.

## Blocked by

- #11 ([AFK] 1 — Establish invocation taxonomy)
