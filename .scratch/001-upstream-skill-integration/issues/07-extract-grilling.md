# [AFK] 4a — Extract grilling (model-invoked); thin grill-me + grill-with-docs

Status: ready-for-agent
github: 17

## Parent

PRD: Upstream skill integration (mattpocock/skills) → v2.0.0 —
`.scratch/001-upstream-skill-integration/PRD.md` (#10)

## What to build

Give the rich design-tree interview protocol one home. Create a **model-invoked**
`grilling` skill containing the design-tree markers, the example tree, the
reprint rules, and the mermaid status-lifecycle diagram (seeded from the existing
inline copies). Thin `grill-me` and `grill-with-docs` so they compose `grilling`
rather than each carrying their own copy of the design-tree block. Sync the
model-invoked skill across its lighter surfaces (plugin.json + "Shared /
model-invoked" subsection).

## Acceptance criteria

- [ ] `skills/productivity/grilling/SKILL.md` exists and contains the
      design-tree markers, the example tree, the reprint rules, and the mermaid
      status-lifecycle diagram.
- [ ] `grill-me/SKILL.md` and `grill-with-docs/SKILL.md` both reference
      `grilling`; neither contains its own copy of the design-tree
      example/lifecycle block.
- [ ] `grilling` is registered in `plugin.json` and the "Shared / model-invoked"
      doc subsection (no decision-tree node / user-command entry).
- [ ] `make lint test docs` exit 0.

## User stories covered

- 10 — `grilling` model-invoked skill owns the design-tree protocol.
  - acceptance: automatable
  - observable: `skills/productivity/grilling/SKILL.md` exists and contains the
    design-tree markers, the example tree, the reprint rules, and the mermaid
    status-lifecycle diagram.
- 11 — `grill-me` and `grill-with-docs` thinned to compose `grilling`.
  - acceptance: automatable
  - observable: both SKILL.md files reference `grilling`; neither contains its
    own copy of the design-tree example/lifecycle block.

## Blocked by

- #16 ([AFK] 3 — Extract domain-modeling) — shares `grill-with-docs/SKILL.md`;
  serialized to avoid integration conflicts.
