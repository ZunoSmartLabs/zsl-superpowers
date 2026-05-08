# Skills reference

Every skill in the plugin, grouped by bucket. Trigger phrases are listed in each skill's `description:` frontmatter; you can also invoke any skill by its slash command (`/zsl:<name>`).

## Engineering

Daily code work.

### diagnose
Disciplined diagnosis loop for hard bugs and performance regressions: reproduce → minimise → hypothesise → instrument → fix → regression-test.

### grill-with-docs
Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates `CONTEXT.md` and ADRs inline.

### improve-codebase-architecture
Find deepening opportunities in a codebase, informed by the domain language in `CONTEXT.md` and the decisions in `docs/adr/`.

### prototype
Build a throwaway prototype to flush out a design before committing. Routes between a runnable terminal app for state/logic questions and several radically different UI variations for design questions.

### setup-zsl-superpowers
Scaffold the per-repo config (issue tracker, triage label vocabulary, domain doc layout, ship style) that the other engineering skills consume. Run once per repo before using `to-issues`, `to-prd`, `triage`, `diagnose`, `tdd`, `improve-codebase-architecture`, or `zoom-out`. See [Per-repo setup](setup.md).

### tdd
Test-driven development with a red-green-refactor loop. Builds features or fixes bugs one vertical slice at a time.

### tdd-parallel
Fan out the unblocked `[AFK]` sub-tasks of a parent issue into parallel `/zsl:tdd` sub-agents in worktrees; sub-agents commit but don't push. The orchestrator merges every slice branch onto the PRD branch in wave order, then opens a single consolidated integration PR. PR-style repos only.

### to-issues
Break any plan, spec, or PRD into independently-grabbable issues using vertical slices.

### to-prd
Turn the current conversation context into a PRD and submit it as an issue. No interview — just synthesises what you've already discussed.

### triage
Triage issues through a state machine of triage roles. Also handles inbound bug reports / feature requests, not just newly-sliced children.

### zoom-out
Tell the agent to zoom out and give broader context or a higher-level perspective on an unfamiliar section of code.

### code-review
Comprehensive pre-PR code review of the current branch with an issues-only tone and an approval gate before applying fixes.

### commit
Plan and create git commits with explicit file lists (never `git add -A`), user approval before each commit, and no Claude attribution lines.

### git-branch
Create a git branch with the prefix convention (`feature/`, `fix/`, `chore/`, `refactor/`, `env/`) required by GitHub auto-PR workflows.

## Productivity

General workflow tools, not code-specific.

### caveman
Ultra-compressed communication mode. Cuts token usage ~75% by dropping filler while keeping full technical accuracy.

### grill-me
Get relentlessly interviewed about a plan or design until every branch of the decision tree is resolved.

### timesheet
Summarize recent Claude Code session histories into copy/paste-ready timesheet bullets, grouped by project. Filters by repo and time window; offers to copy to clipboard.

### write-a-skill
Create new skills with proper structure, progressive disclosure, and bundled resources.

## Misc

Tools we keep around but rarely use.

### edit-article
Edit and improve articles by restructuring sections, improving clarity, and tightening prose.

### git-guardrails-claude-code
Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, etc.) before they execute.

### setup-pre-commit
Set up Husky pre-commit hooks with lint-staged, Prettier, type checking, and tests.

### steampipe
AWS infrastructure query reference for `steampipe query`. Auto-triggered (not user-invocable); provides table names, column schemas, and JSONB query patterns.
