# Skills

Every skill in the plugin, grouped by bucket. Each entry links to the skill's own
page — auto-generated from its `SKILL.md` so the site stays in lockstep with the
plugin source. Click any skill to see what triggers it, what it does, and the full
spec.

You can always invoke a skill explicitly with `/zsl:<name>`. Skills without
`disable-model-invocation: true` also auto-trigger when Claude Code matches your
prompt against the trigger phrases shown on each skill's page.

## Engineering

Daily code work.

- [setup-zsl-superpowers](setup-zsl-superpowers.md) — scaffold the per-repo config the engineering skills consume. Run once per repo.
- [grill-with-docs](grill-with-docs.md) — interview-driven planning, sharpens terminology against `CONTEXT.md` and ADRs inline.
- [to-prd](to-prd.md) — turn the current conversation into a PRD on the issue tracker.
- [to-issues](to-issues.md) — break a PRD into vertical-slice sub-issues with explicit `Blocked by` graphs.
- [triage](triage.md) — move issues through the state machine; entry point for inbound bug reports and feature requests too.
- [tdd](tdd.md) — single-issue red-green-refactor loop.
- [tdd-parallel](tdd-parallel.md) — fan AFK slices out into worktrees, merge in wave order, open one integration PR. ([Deep-dive](../tdd-parallel.md).)
- [diagnose](diagnose.md) — disciplined bug/perf-regression loop: reproduce → minimise → hypothesise → instrument → fix → regression-test.
- [improve-codebase-architecture](improve-codebase-architecture.md) — find deepening opportunities; run every few days to fight entropy.
- [zoom-out](zoom-out.md) — broader context on unfamiliar code.
- [prototype](prototype.md) — throwaway terminal app or radically-different UI variations to flush out a design before committing.
- [code-review](code-review.md) — pre-PR review of the current branch with an issues-only tone.
- [commit](commit.md) — explicit-file-list commits, no `git add -A`, no Claude attribution.
- [git-branch](git-branch.md) — branch with the prefix convention required by GitHub auto-PR workflows.

## Productivity

General workflow tools, not code-specific.

- [grill-me](grill-me.md) — get relentlessly interviewed about a plan or design until every branch resolves.
- [timesheet](timesheet.md) — turn recent Claude Code session histories into copy/paste timesheet bullets.
- [write-a-skill](write-a-skill.md) — author a new skill with progressive disclosure and bundled resources.
- [caveman](caveman.md) — ultra-compressed reply mode (~75% token cut, full technical accuracy).

## Misc

Tools we keep around but rarely reach for.

- [edit-article](edit-article.md) — restructure and tighten article drafts.
- [setup-pre-commit](setup-pre-commit.md) — Husky + lint-staged + Prettier + type-check + tests pre-commit setup.
- [steampipe](steampipe.md) — reference for AWS infra queries via Steampipe (auto-triggered, not user-invocable).
