# [AFK] 7 — Release 2.0.0: version bump, changelog + Upgrading-from-1.4, final decision tree, full sync audit, green gate

Status: ready-for-agent
github: 21

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

The final release slice — runs alone, last, because the version-bump push to
`main` triggers `.github/workflows/release.yml`. Reconcile and verify the whole
release in lockstep: confirm `plugin.json`'s `skills` array reflects the final
inventory (the six adds, the three removals/renames); bump `plugin.json` and
`marketplace.json` both to `2.0.0`; add a top changelog `2.0.0` section naming
the six added skills, the three removals/renames, and an "Upgrading from 1.4"
sub-block; finalize the decision tree; audit the full cross-surface sync; and
get the entire gate green so the release is landable.

## Acceptance criteria

- [ ] `plugin.json` `skills` array lists `codebase-design`, `domain-modeling`,
      `grilling`, `decision-mapping`, `teach-me-the-codebase`, `ask-zsl`,
      `writing-great-skills` and omits `caveman`, `zoom-out`, `write-a-skill`.
- [ ] `plugin.json` `version` and `marketplace.json` `version` both equal
      `2.0.0`.
- [ ] `docs/changelog.md` has a top `2.0.0` section naming the six added skills,
      the three removals/renames, and an "Upgrading from 1.4" sub-block covering
      `caveman`, `zoom-out`, and `write-a-skill → writing-great-skills`.
- [ ] Each added user-invoked skill appears in the top README bucket list, its
      bucket README, the docs/skills/index.md role table, and mkdocs.yml nav;
      each removed skill is gone from all four; model-invoked skills appear only
      in `plugin.json` + the "Shared / model-invoked" doc subsection.
- [ ] The `docs/skills/index.md` "Which skill do I want?" mermaid tree drops
      `caveman`/`zoom-out`/`write-a-skill`, adds `decision-mapping` (Plan) and
      `teach-me-the-codebase`, and contains no node for any model-invoked skill.
- [ ] `make lint`, `make test`, and `make docs` all exit 0 on the final branch.

## User stories covered

- 22 — `plugin.json` reflects the new inventory.
  - acceptance: automatable
  - observable: `plugin.json` `skills` array lists `codebase-design`,
    `domain-modeling`, `grilling`, `decision-mapping`, `teach-me-the-codebase`,
    `ask-zsl`, `writing-great-skills` and omits `caveman`, `zoom-out`,
    `write-a-skill`.
- 23 — Version bumped in lockstep.
  - acceptance: automatable
  - observable: `plugin.json` `version` and `marketplace.json` `version` both
    equal `2.0.0`.
- 24 — Changelog entry with migration notes.
  - acceptance: automatable
  - observable: `docs/changelog.md` has a top `2.0.0` section that names the six
    added skills, the three removals/renames, and an "Upgrading from 1.4"
    sub-block covering `caveman`, `zoom-out`, and `write-a-skill →
    writing-great-skills`.
- 25 — Every added/removed skill synced across all surfaces.
  - acceptance: automatable
  - observable: each added user-invoked skill appears in the top `README.md`
    bucket list, its bucket `README.md`, the `docs/skills/index.md` role table,
    and `mkdocs.yml` nav; each removed skill is gone from all four; model-invoked
    skills appear only in `plugin.json` + a "Shared / model-invoked" doc
    subsection.
- 26 — Decision tree updated.
  - acceptance: automatable
  - observable: the `docs/skills/index.md` "Which skill do I want?" mermaid tree
    drops `caveman`/`zoom-out`/`write-a-skill`, adds `decision-mapping` (Plan)
    and `teach-me-the-codebase`, and contains no node for any model-invoked
    skill.
- 27 — Full gate green.
  - acceptance: automatable
  - observable: `make lint`, `make test`, and `make docs` all exit 0 on the
    final branch.

## Blocked by

- #20 ([AFK] 6 — Add ask-zsl router) — and transitively every other slice.
