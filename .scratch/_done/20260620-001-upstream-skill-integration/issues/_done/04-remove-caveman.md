# [AFK] 2c — Remove caveman everywhere

Status: ready-for-agent
github: 14

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

Sweep the `caveman` skill off every parallel surface so no surface advertises a
gone command. Delete the skill directory and remove its entry from all five sync
places (plugin.json, top README, bucket README, docs/skills/index.md role table
+ decision tree node, mkdocs.yml nav). The only place `caveman` may still be
named is the changelog (which records its removal).

## Acceptance criteria

- [ ] `skills/productivity/caveman/` is absent.
- [ ] A repo-wide grep for `caveman` returns no hits outside `docs/changelog.md`.
- [ ] The five-place sync is updated and the decision-tree node is dropped.
- [ ] `make lint test docs` exit 0.

## User stories covered

- 20 — `caveman` removed everywhere.
  - acceptance: automatable
  - observable: `skills/productivity/caveman/` is absent and a repo-wide grep
    for `caveman` returns no hits outside `docs/changelog.md`.

## Blocked by

- #11 ([AFK] 1 — Establish invocation taxonomy)

## Verification

Ran on the feature branch — observable PASS, `make lint test docs` exit 0.

- Story 20: `skills/productivity/caveman/` is absent (git rm). `grep -rn caveman` over the repo excluding `docs/changelog.md`, `.scratch/` (the PRD/issue spec that describes the removal), and `site/` (build output) → no hits. Swept from all parallel surfaces: plugin.json, top README, bucket README, docs/skills/index.md role table + decision-tree node, mkdocs.yml nav, plus docs/architecture.md, docs/workflow.md (mermaid node + table link), docs/faq.md, docs/quickstart.md.
