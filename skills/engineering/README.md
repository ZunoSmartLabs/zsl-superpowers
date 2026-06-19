# Engineering

Skills I use daily for code work.

- **[diagnose](./diagnose/SKILL.md)** — Disciplined diagnosis loop for hard bugs and performance regressions: reproduce → minimise → hypothesise → instrument → fix → regression-test.
- **[grill-with-docs](./grill-with-docs/SKILL.md)** — Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates `CONTEXT.md` and ADRs inline.
- **[triage](./triage/SKILL.md)** — Triage issues through a state machine of triage roles.
- **[improve-codebase-architecture](./improve-codebase-architecture/SKILL.md)** — Find deepening opportunities in a codebase, informed by the domain language in `CONTEXT.md` and the decisions in `docs/adr/`.
- **[prototype](./prototype/SKILL.md)** — Build a throwaway prototype to flush out a design before committing. Routes to a runnable terminal app for state/logic questions, or several radically different UI variations for design questions.
- **[setup-zsl-superpowers](./setup-zsl-superpowers/SKILL.md)** — Scaffold the per-repo config (issue tracker, triage label vocabulary, domain doc layout) that the other engineering skills consume.
- **[tdd](./tdd/SKILL.md)** — Test-driven development with a red-green-refactor loop. Builds features or fixes bugs one vertical slice at a time.
- **[tdd-parallel](./tdd-parallel/SKILL.md)** — Full-auto PRD pipeline: fanout `[AFK]` slices into parallel `/tdd` sub-agents, integrate onto the PRD branch, auto-chain `/verify-coverage --auto` and auto-fix any gaps via re-fanout (capped by `--max-coverage-rounds`), then open one consolidated integration PR. Refuses up front if any `[HITL]` is open or any user story isn't expressible as an automatable test. PR-style only.
- **[human-itl](./human-itl/SKILL.md)** — Walk a human through the manual-action `[HITL]` slices of a PRD — console clicks, credential rotation, sign-off — record each as an audit trail, mark them done. Must run **before** `/tdd-parallel`, which refuses with any `[HITL]` open. Hard-refuses disguised-decision slices.
- **[to-issues](./to-issues/SKILL.md)** — Break any plan, spec, or PRD into independently-grabbable GitHub issues using vertical slices. Propagates the parent PRD's `acceptance:` tag and `AC<n>:` acceptance criteria into each slice body verbatim.
- **[verify-coverage](./verify-coverage/SKILL.md)** — Verify every PRD user story is covered by a passing, non-vacuous behavioral test (Tier A maps to existing tests; Tier B generates one from the story's `AC<n>:` acceptance criteria and mutation-proves it); auto-files gaps and writes a coverage receipt. Almost always chained by `/tdd-parallel --auto`; direct invocation is for auditing PRDs whose slices shipped via a different path.
- **[to-prd](./to-prd/SKILL.md)** — Turn the current conversation context into a PRD and submit it as a GitHub issue. Writes each story at value altitude with detailed assertions in `AC<n>:` acceptance criteria; refuses non-automatable stories. Every story carries `acceptance: automatable` + at least one acceptance criterion.
- **[zoom-out](./zoom-out/SKILL.md)** — Tell the agent to zoom out and give broader context or a higher-level perspective on an unfamiliar section of code.
- **[code-review](./code-review/SKILL.md)** — Comprehensive pre-PR code review of the current branch with an issues-only tone and an approval gate before applying fixes.
- **[commit](./commit/SKILL.md)** — Plan and create git commits with user approval, no Claude attribution, and explicit file lists (never `git add -A`).
- **[commit-push-pr](./commit-push-pr/SKILL.md)** — One-shot ship: refuse on the default branch, delegate to `/zsl:commit`, then `git push -u`, then `gh pr create`.
- **[git-branch](./git-branch/SKILL.md)** — Create a git branch with the prefix convention (`feature/`, `fix/`, `chore/`, `refactor/`, `env/`) required by the auto-PR workflow.
