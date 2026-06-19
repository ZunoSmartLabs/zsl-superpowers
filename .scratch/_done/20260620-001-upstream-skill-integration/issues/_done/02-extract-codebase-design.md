# [AFK] 2a — Extract codebase-design (model-invoked); repoint improve-codebase-architecture + tdd

Status: ready-for-agent
github: 12

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

Give the deep-module vocabulary one home. Create a new **model-invoked**
`codebase-design` skill seeded from the union of the existing inline deep-module
files so no local phrasing regresses, delete those duplicated files, and repoint
`improve-codebase-architecture` and `tdd` to compose the shared skill instead of
carrying their own copies. Sync the new model-invoked skill across its (lighter)
surfaces: `plugin.json` + a "Shared / model-invoked" doc subsection only — no
decision-tree node, no user-command listing.

## Acceptance criteria

- [ ] `skills/engineering/codebase-design/SKILL.md` exists, its frontmatter has
      **no** `disable-model-invocation` flag, and its body defines
      module/interface/depth/seam/adapter plus the deletion-test and
      two-adapters-real-seam refinements.
- [ ] None of `improve-codebase-architecture/{LANGUAGE,INTERFACE-DESIGN}.md` or
      `tdd/{deep-modules,interface-design}.md` exist; a repo-wide grep finds no
      surviving links to them.
- [ ] `improve-codebase-architecture/SKILL.md` and `tdd/SKILL.md` each reference
      `codebase-design` and contain no inline deep-module glossary body.
- [ ] `codebase-design` is registered in `plugin.json` and listed in a "Shared /
      model-invoked" doc subsection; it is absent from the decision tree and
      user-command lists.
- [ ] `make lint test docs` exit 0.

## User stories covered

- 4 — Shared `codebase-design` model-invoked skill.
  - acceptance: automatable
  - observable: `skills/engineering/codebase-design/SKILL.md` exists, its
    frontmatter has no `disable-model-invocation` flag, and its body defines
    module/interface/depth/seam/adapter plus the deletion-test and
    two-adapters-real-seam refinements.
- 5 — Duplicated deep-module files deleted.
  - acceptance: automatable
  - observable: none of
    `improve-codebase-architecture/{LANGUAGE,INTERFACE-DESIGN}.md` or
    `tdd/{deep-modules,interface-design}.md` exist; a repo-wide grep finds no
    surviving links to them.
- 6 — `improve-codebase-architecture` and `tdd` point at `codebase-design`.
  - acceptance: automatable
  - observable: `improve-codebase-architecture/SKILL.md` and `tdd/SKILL.md` each
    reference `codebase-design` and contain no inline deep-module glossary body.

## Blocked by

- #11 ([AFK] 1 — Establish invocation taxonomy)

## Verification

Ran on the feature branch — all observables PASS, `make lint test docs` exit 0.

- Story 4: `skills/engineering/codebase-design/SKILL.md` exists, frontmatter has no `disable-model-invocation` flag, body defines module/interface/depth/seam/adapter + deletion-test + "Two adapters = real" → PASS.
- Story 5: none of `improve-codebase-architecture/{LANGUAGE,INTERFACE-DESIGN}.md` or `tdd/{deep-modules,interface-design}.md` exist; `grep -rnE '\]\((…)(LANGUAGE|INTERFACE-DESIGN|deep-modules|interface-design)\.md\)'` over skills/ docs/ README.md → no surviving links.
- Story 6: `improve-codebase-architecture/SKILL.md` and `tdd/SKILL.md` both reference `codebase-design`; the inline deep-module glossary body was removed from ICA → PASS.
- Sync (model-invoked lane): registered in `plugin.json`; listed in the new "Shared / model-invoked" subsection of `docs/skills/index.md`; `skills/codebase-design.md` added to `not_in_nav`; absent from top/bucket README, role tables, decision tree → PASS.
