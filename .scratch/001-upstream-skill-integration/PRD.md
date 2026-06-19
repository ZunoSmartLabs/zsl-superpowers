# PRD: Upstream skill integration (mattpocock/skills) → v2.0.0

Status: tracking
github: 10
Labels: tracking, backlog

## Problem Statement

Upstream `mattpocock/skills` (now at 1.0.x, after the `47bde84` "Commands and
Skills" refactor) has diverged from this repo. As a maintainer I want to pull in
the changes that fit ZSL's engineering-delivery loop without importing what's
personal to Matt or what conflicts with our autonomous/overnight machinery — and
to do it in a way that respects this repo's parallel-surface sync contracts so a
single push doesn't break the marketplace version, the strict docs deploy, or a
remote routine.

Three of the upstream additions are not new features but *extraction refactors*
of guidance we already carry inline (the deep-module vocabulary, the ADR/CONTEXT
formats, the grilling loop). Today that guidance is duplicated across multiple
skills and drifts. Separately, we carry two skills upstream deliberately removed
(`caveman`, `zoom-out`) and a `write-a-skill` that upstream replaced.

## Solution

Ship one `2.0.0` release that:

- Adopts a lightweight **User-invoked / Model-invoked** taxonomy and uses it to
  extract the duplicated guidance into three shared **model-invoked** skills
  (`codebase-design`, `domain-modeling`, `grilling`) that other skills compose
  instead of copy — net deletion-positive.
- Adds three **user-invoked** skills that fit our loop: `decision-mapping`
  (front-of-loop, pre-PRD idea maturation), `teach-me-the-codebase` (on-the-fly
  codebase onboarding tutor), and `ask-zsl` (thin interactive router).
- Removes `caveman` and `zoom-out`; replaces `write-a-skill` with
  `writing-great-skills` while preserving the description-length deterministic
  gate.
- Keeps every parallel surface in sync and lands the breaking changes behind one
  combined "Upgrading from 1.4" changelog note.

Net skill count: 29 → 32 (+6 added, −3 removed). Decisions recorded in
`docs/adr/0001-user-invoked-model-invoked-taxonomy.md`.

## User Stories

### Taxonomy groundwork

1. As a maintainer, I want a documented definition of the user/model-invoked
   split, so that the taxonomy is discoverable and enforceable.
   - acceptance: automatable
   - observable: `docs/invocation.md` exists and contains the rule that a
     user-invoked skill may invoke model-invoked skills but never another
     user-invoked skill.

2. As a maintainer, I want pure orchestrators flagged so they never auto-fire,
   so that only-when-typed skills behave predictably.
   - acceptance: automatable
   - observable: the SKILL.md frontmatter of each pure orchestrator (`commit`,
     `commit-push-pr`, `afk-fanout`, `tdd-parallel`, `decision-mapping`,
     `teach-me-the-codebase`, `ask-zsl`, `writing-great-skills`) contains
     `disable-model-invocation: true`.

3. As a maintainer, I want the sync contract to describe the model-invoked lane,
   so that future model-invoked skills get the right (lighter) treatment.
   - acceptance: automatable
   - observable: `CLAUDE.md` contains a sixth lane stating model-invoked-only
     skills are registered in `plugin.json` + a "Shared / model-invoked" doc
     subsection but omitted from the decision tree and user-command lists.

### codebase-design extraction

4. As a skill author, I want a shared `codebase-design` model-invoked skill, so
   that the deep-module vocabulary has one home.
   - acceptance: automatable
   - observable: `skills/engineering/codebase-design/SKILL.md` exists, its
     frontmatter has no `disable-model-invocation` flag, and its body defines
     module/interface/depth/seam/adapter plus the deletion-test and
     two-adapters-real-seam refinements.

5. As a maintainer, I want the duplicated deep-module files deleted, so that the
   vocabulary stops drifting across skills.
   - acceptance: automatable
   - observable: none of
     `improve-codebase-architecture/{LANGUAGE,INTERFACE-DESIGN}.md` or
     `tdd/{deep-modules,interface-design}.md` exist; a repo-wide grep finds no
     surviving links to them.

6. As a maintainer, I want `improve-codebase-architecture` and `tdd` to point at
   `codebase-design`, so that both draw from the shared source.
   - acceptance: automatable
   - observable: `improve-codebase-architecture/SKILL.md` and `tdd/SKILL.md`
     each reference `codebase-design` and contain no inline deep-module glossary
     body.

### domain-modeling extraction

7. As a skill author, I want a `domain-modeling` model-invoked skill that owns
   the ADR and CONTEXT formats, so that the domain-doc formats have one home.
   - acceptance: automatable
   - observable: `skills/engineering/domain-modeling/` contains the ADR-format
     and CONTEXT-format guidance, and `grill-with-docs/{ADR-FORMAT,CONTEXT-FORMAT}.md`
     no longer exist.

8. As a maintainer, I want `grill-with-docs` and `improve-codebase-architecture`
   to consume `domain-modeling`, so that domain reasoning is shared not inlined.
   - acceptance: automatable
   - observable: both SKILL.md files reference `domain-modeling` and contain no
     inline ADR/CONTEXT format definition.

9. As a maintainer, I want the DDD book-rules embedded on `domain-modeling`, so
   that the rules follow the reasoning into every consumer.
   - acceptance: automatable
   - observable: `scripts/sync_book_rules.py` MAPPING keys `domain-modeling`
     (not `grill-with-docs`) to the two DDD embeds; running the sync leaves
     `domain-modeling/SKILL.md` with the DDD `BEGIN/END` block and
     `grill-with-docs/SKILL.md` without it; `make docs` passes.

### grilling extraction

10. As a skill author, I want a `grilling` model-invoked skill owning the rich
    design-tree protocol, so that the interview loop lives in one place.
    - acceptance: automatable
    - observable: `skills/productivity/grilling/SKILL.md` exists and contains the
      design-tree markers, the example tree, the reprint rules, and the mermaid
      status-lifecycle diagram.

11. As a maintainer, I want `grill-me` and `grill-with-docs` thinned to compose
    `grilling`, so that the design-tree block stops being duplicated.
    - acceptance: automatable
    - observable: both SKILL.md files reference `grilling`; neither contains its
      own copy of the design-tree example/lifecycle block.

### decision-mapping

12. As a planner, I want a `decision-mapping` skill that turns a loose idea into a
    sequenced ticket map, so that multi-session ideas mature before a PRD.
    - acceptance: automatable
    - observable: `skills/engineering/decision-mapping/SKILL.md` exists, is
      `disable-model-invocation: true`, and references `grilling`,
      `domain-modeling`, `prototype`, and `to-prd` (never `grill-with-docs`).

13. As a maintainer, I want the map stored under `.scratch/` and the upstream typo
    fixed, so that it matches our state convention and the references resolve.
    - acceptance: automatable
    - observable: `decision-mapping/SKILL.md` writes maps to
      `.scratch/decision-maps/`, contains no `domain-modelling` (double-L)
      spelling, and declares being AFK-wired an explicit non-goal.

### teach-me-the-codebase

14. As a developer new to a repo, I want a `teach-me-the-codebase` tutor, so that
    I can learn the repo's domain/architecture/conventions interactively.
    - acceptance: automatable
    - observable: `skills/engineering/teach-me-the-codebase/SKILL.md` exists, is
      `disable-model-invocation: true`, has no `lessons/`/`learning-records/`
      workspace directories, states it reads `CONTEXT.md`/ADRs/`CLAUDE.md`/code
      and hands undocumented terms to `domain-modeling`/`grill-with-docs`, and
      offers an optional `md-to-html` cheat-sheet rather than persisting one.

### ask-zsl

15. As a user, I want an `ask-zsl` interactive router, so that I can find the
    right skill mid-session without leaving my work.
    - acceptance: automatable
    - observable: `skills/engineering/ask-zsl/SKILL.md` exists, is
      `disable-model-invocation: true`, encodes situational routing questions,
      and routes over the ZSL loop including `afk-fanout`/`afk-worker`/
      `morning-review`, `tdd` vs `tdd-parallel`, `verify-coverage`, `human-itl`,
      and `decision-mapping`.

16. As a maintainer, I want the sync contract to pair `ask-zsl` with the decision
    tree, so that adding/removing a loop skill updates both.
    - acceptance: automatable
    - observable: `CLAUDE.md` names `ask-zsl` and `docs/skills/index.md`'s
      decision tree as a routing pair that must move together.

### writing-great-skills (replaces write-a-skill)

17. As a skill author, I want `writing-great-skills`, so that the principles/
    vocabulary reference replaces the old process skill.
    - acceptance: automatable
    - observable: `skills/productivity/writing-great-skills/{SKILL.md,GLOSSARY.md}`
      exist; `skills/productivity/write-a-skill/` does not.

18. As a maintainer, I want the description-length gate preserved, so that the
    deterministic check survives the replace.
    - acceptance: automatable
    - observable: `writing-great-skills/scripts/check-description-length.py` and
      its `scripts/tests/test_*.py` exist, `pytest` on them passes (including the
      fails-the-prose-way case), and `writing-great-skills/SKILL.md` has a
      deterministic-gate callout with the three-environment resolver and a
      Fallback heading.

19. As a maintainer, I want the make targets repointed, so that lint/test cover
    the moved gate.
    - acceptance: automatable
    - observable: the `basedpyright` line in `make lint` and the test runner in
      `make test` reference the `writing-great-skills/scripts/` path, not
      `write-a-skill/scripts/`; `make lint test` pass.

### Removals

20. As a maintainer, I want `caveman` removed everywhere, so that no surface
    advertises a gone command.
    - acceptance: automatable
    - observable: `skills/productivity/caveman/` is absent and a repo-wide grep
      for `caveman` returns no hits outside `docs/changelog.md`.

21. As a maintainer, I want `zoom-out` removed everywhere, so that no surface
    advertises a gone command.
    - acceptance: automatable
    - observable: `skills/engineering/zoom-out/` is absent and a repo-wide grep
      for `zoom-out` returns no hits outside `docs/changelog.md`.

### Release plumbing & sync

22. As a maintainer, I want `plugin.json` to reflect the new inventory, so that
    the right skills are provisioned.
    - acceptance: automatable
    - observable: `plugin.json` `skills` array lists `codebase-design`,
      `domain-modeling`, `grilling`, `decision-mapping`, `teach-me-the-codebase`,
      `ask-zsl`, `writing-great-skills` and omits `caveman`, `zoom-out`,
      `write-a-skill`.

23. As a maintainer, I want the version bumped in lockstep, so that the
    marketplace advertises what's installed.
    - acceptance: automatable
    - observable: `plugin.json` `version` and `marketplace.json` `version` both
      equal `2.0.0`.

24. As a user upgrading, I want a changelog entry with migration notes, so that I
    know what broke.
    - acceptance: automatable
    - observable: `docs/changelog.md` has a top `2.0.0` section that names the six
      added skills, the three removals/renames, and an "Upgrading from 1.4"
      sub-block covering `caveman`, `zoom-out`, and `write-a-skill →
      writing-great-skills`.

25. As a maintainer, I want every added/removed skill synced across all surfaces,
    so that the deploy gate and references stay consistent.
    - acceptance: automatable
    - observable: each added user-invoked skill appears in the top `README.md`
      bucket list, its bucket `README.md`, the `docs/skills/index.md` role table,
      and `mkdocs.yml` nav; each removed skill is gone from all four; model-invoked
      skills appear only in `plugin.json` + a "Shared / model-invoked" doc
      subsection.

26. As a maintainer, I want the decision tree updated, so that the router diagram
    matches the inventory.
    - acceptance: automatable
    - observable: the `docs/skills/index.md` "Which skill do I want?" mermaid tree
      drops `caveman`/`zoom-out`/`write-a-skill`, adds `decision-mapping` (Plan)
      and `teach-me-the-codebase`, and contains no node for any model-invoked
      skill.

27. As a maintainer, I want the full gate green, so that the release is landable.
    - acceptance: automatable
    - observable: `make lint`, `make test`, and `make docs` all exit 0 on the
      final branch.

28. As a maintainer, I want the taxonomy ADR present but unpublished, so that the
    decision is recorded without breaking the strict docs build.
    - acceptance: automatable
    - observable: `docs/adr/0001-user-invoked-model-invoked-taxonomy.md` exists,
      `mkdocs.yml` has top-level `not_in_nav: adr/*`, and `make docs` passes.

## Implementation Decisions

- **Taxonomy is lightweight.** Introduce User-invoked / Model-invoked via
  `disable-model-invocation` frontmatter flags + `docs/invocation.md` + a sixth
  CLAUDE.md sync lane. Do not rename existing doc framing wholesale.
- **Three extractions, adopt-shape-keep-refinements.** `codebase-design`,
  `domain-modeling`, `grilling` take upstream's shared-skill *shape* but are
  seeded from the union of our existing inline files so no local phrasing
  regresses. All three are model-invoked.
- **Book-rules ownership moves with the reasoning.** The two DDD embeds move from
  `grill-with-docs` to `domain-modeling` by re-keying `sync_book_rules.py`'s
  MAPPING dict; `make docs`/the sync regenerates the `BEGIN/END` blocks.
- **`grill-me`/`grill-with-docs` become thin composers** over `grilling`
  (+`domain-modeling` for `grill-with-docs`).
- **`decision-mapping`** is user-invoked, composes the model-invoked primitives
  directly (taxonomy forbids calling `grill-with-docs`), stores maps in
  `.scratch/decision-maps/`, is local-only (AFK-wiring is a stated non-goal),
  and hands off to `to-prd`.
- **`teach-me-the-codebase`** is an on-the-fly conversational tutor with zero
  persisted artefacts (optional `md-to-html` cheat-sheet on demand). Teacher-only
  boundary: it reads the canonical `CONTEXT.md`/ADRs/code and hands gaps to
  `domain-modeling`/`grill-with-docs`; it never writes `CONTEXT.md` or a parallel
  glossary.
- **`ask-zsl`** is a thin interactive router (routing logic only, defers skill
  descriptions to existing docs) and joins the sync contract paired with the
  decision tree.
- **`writing-great-skills`** is a pure replace of `write-a-skill`'s content
  (upstream SKILL + GLOSSARY verbatim) with the `check-description-length.py`
  deterministic gate merged in (scripts + tests relocated, gate callout +
  resolver + Fallback added, make targets repointed).
- **Removals** of `caveman` and `zoom-out` sweep all ~14 parallel surfaces.
- **Single `2.0.0` release.** Breaking (public commands removed) → major bump;
  `plugin.json` + `marketplace.json` in lockstep; one changelog entry + combined
  Upgrading note. The push to `main` triggers `.github/workflows/release.yml`,
  which validates the changelog/marketplace rules.

## Testing Decisions

- Good tests assert external/public behaviour, not implementation detail. For a
  skills-content repo, the public surface is the repo's structure and the build
  gates, so most stories are pinned by structural assertions (file present/absent,
  frontmatter/grep checks, JSON field equality) plus `make lint test docs`.
- The only script module with a behavioural test suite is
  `check-description-length.py`; its existing `pytest` tests (including a
  fails-the-prose-way case, e.g. a 1025-char description) travel with it to
  `writing-great-skills/scripts/` and must pass at the new path. Prior art: the
  existing `scripts/tests/test_check_description_length.py`.
- The `sync_book_rules.py` MAPPING change is verified by running the sync and
  `make docs`; no new unit test is added.
- No additional structural-invariant test is added this PRD (confirmed with the
  maintainer); the existing `make` gates and per-story grep/JSON assertions are
  the verification surface.

## Out of Scope

- Upstream skills deliberately **not** adopted: `resolving-merge-conflicts`,
  `review`, `git-guardrails-claude-code`, `implement` (overlap or conflict with
  existing machinery); and the personal/course-specific `ask-matt`,
  `obsidian-vault`, `migrate-to-shoehorn`, `scaffold-exercises`, `teach` (whole),
  and the writing trio.
- Wiring `decision-mapping` tickets into the `afk-fanout`/`afk-worker` remote loop
  (deferred; investigation tickets have no automatable acceptance gate).
- Folding `review`'s Spec-vs-PRD axis into `code-review` (noted as a possible
  future enhancement, not this release).
- Promoting any `teach-me-the-codebase` output to committed `docs/onboarding/`
  (it stays ephemeral).

## Further Notes

- The taxonomy decision is recorded in `docs/adr/0001`; `mkdocs.yml` already
  carries `not_in_nav: adr/*` and `make docs` was verified green with the ADR in
  place.
- The five-place skill-sync contract and the deterministic-gate contract in
  `CLAUDE.md` both apply to every add/remove here — treat them as the acceptance
  backbone when slicing into issues.
- `ask-zsl` should be authored last, against the final skill inventory, so its
  routing reflects every other change in this PRD.
