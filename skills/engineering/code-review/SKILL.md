---
name: code-review
description: Comprehensive pre-PR code review of the current branch with an issues-only tone and an approval gate before applying fixes. Use when user wants a code review, mentions /code-review, or asks to scan the branch before opening a PR.
model: opus
---

# Pre-PR Code Review

Review like Uncle Bob would. Clean code is **simple, correct, and minimal** — single responsibility, small functions with names that don't lie, no dead code, no defensive padding, no premature abstraction. The diff should leave the codebase clearer than it found it.

Focus the review on:
- Clean-code principles (see below)
- Bugs and correctness
- Performance
- Security
- Test coverage — every behavior change should ship with a test change
- Scope — flag PRs that mix unrelated changes

Use the repository's CLAUDE.md for project-specific style and conventions.

## Clean code lens

Apply these standards to every diff. They are what "issues" means.

- **Single responsibility violated** — Functions or classes doing multiple unrelated things. Name the seams and suggest a split.
- **Names that lie or obscure** — `data`, `handleStuff`, `processItem`, getters that mutate, queries with side effects, booleans named for the wrong default. Rename.
- **Functions too large to hold in your head** — Long bodies, deep nesting, many parameters. Suggest extraction along a natural seam.
- **Dead code** — Commented-out blocks, unused imports, unreachable branches, debug statements (`console.log`, `print`, `dbg!`). Delete.
- **Comments compensating for unclear code** — A comment that explains *what* the code does (rather than *why*) usually signals the code itself should be rewritten.
- **Mixed concerns** — Happy-path and error-recovery logic deeply intertwined, or unrelated changes bundled in one diff. Separate.
- **Behavior change without test change** — A diff that alters logic but touches no test file. Flag and ask which test should cover it.
- **ENV files modified** — `.env`, `.env.local`, etc. typically contain secrets and shouldn't be in version control. Always call out.

Carry this lens into every sub-agent prompt below.

## Do not flag

These are noise — never include in findings:

- **Pre-existing issues** — bugs on lines this branch didn't touch. Verify with `git blame` before flagging.
- **Issues the CI catches** — type errors, lint violations, formatting, import order, broken tests. CI handles these.
- **Pedantic nitpicks** — style preferences not codified in CLAUDE.md, "I would have written this differently."
- **Intentional functionality changes** — the diff is the spec; don't flag behavior changes as bugs.
- **Issues silenced by escape hatches** — `// eslint-disable`, `// @ts-expect-error`, `# noqa` mean the author already considered it.
- **Generic code-quality wishes** — "this could be more testable", "consider adding documentation" — unless CLAUDE.md explicitly requires it.

When in doubt, drop it.

## Before suggesting changes

A few patterns produce most false-positive review comments. Apply these before flagging:

1. **Match existing conventions** — Search the codebase before flagging style, naming, or structural choices. If the project does it one way fifty times, suggesting a different way is noise unless CLAUDE.md explicitly requires it.

2. **Trust enforcement layers** — Don't suggest runtime validation for states the database (CHECK / FK / NOT NULL / enum types), the type system (discriminated unions, branded types), or the input-validation layer (schema validation, form validation) already prevents. Defensive code for impossible states adds noise.

3. **Don't push abstraction prematurely** — Constants are not env vars; use env vars only for values that must differ per environment. Inline code is not a service. Suggest extraction or configurability only when there's a concrete second caller or a real runtime-configuration need.

## Parallel multi-lens scan

Before writing findings, launch six parallel sub-agents — each gets the diff and one job. Issue all six Agent calls in a single message so they run concurrently.

1. **CLAUDE.md compliance** — Read root `CLAUDE.md` and any `CLAUDE.md` in modified directories. Audit changes against codified rules. Skip rules that are about code generation but not review.
2. **Shallow bug scan** — Read the diff only (no extra context). Surface obvious bugs in the changes themselves. Ignore nitpicks.
3. **Git history** — Run `git blame` / `git log` on modified hunks. Flag bugs visible only in historical context ("this line was added in PR #X to handle Y; the new change breaks that").
4. **Prior PR comments** — Use `gh pr list --search` to find previous PRs touching these files. Read review comments. Surface guidance that also applies here.
5. **Inline code comments** — Read comments in modified files. Surface any guidance the changes contradict.
6. **Spec alignment** — Find the originating spec for this branch, then check the diff against it. Lookup order: (a) issue references in commit messages (`#123`, `Closes #45`, `Closes <path-to-md>`, GitLab `!67`) — fetch via the workflow in `docs/agents/issue-tracker.md`; (b) a PRD/spec path the user passed as an argument; (c) a PRD or AGENT-BRIEF under `docs/`, `specs/`, or `.scratch/` matching the branch slug or feature name. If nothing is found, this lens returns "no spec available" and is skipped. Otherwise report: (i) requirements the spec asked for that are missing or partial, with the spec line quoted; (ii) behaviour in the diff that wasn't asked for (scope creep); (iii) requirements that look implemented but where the implementation looks wrong relative to the spec.

Each agent returns a list of issues with `file:line` references and a one-line reason per issue. The Spec lens additionally quotes the relevant spec line (file:line or section heading).

## Confidence scoring

Score every collected finding 0–100 before presenting:

- **0–25** — Doesn't survive light scrutiny, or it's a pre-existing issue on lines this branch didn't touch.
- **50** — Real but low-impact. Nitpicky relative to the rest of the diff.
- **75** — Verified real, will hit in practice, or directly violates CLAUDE.md.
- **100** — Concrete evidence the issue is real and frequent.

**Drop everything below 60.** The approval gate catches the rest — but the scoring filter is what keeps the gate from drowning in noise.

## Autonomous mode (`--auto`)

When invoked with `--auto`, the approval gate is dropped and high-confidence findings auto-apply. Designed for AFK contexts — `/tdd` calls this under `--no-ship`, and `/tdd-parallel` calls it at integration time.

- **≥80** — auto-apply as a single follow-up commit (subject: `review: <one-line summary>`). Revertible with one `git revert`.
- **60–79** — report in the return summary with `file:line` references. Do not apply.
- **<60** — dropped, per the standard confidence rule.

After auto-applying, run lint (and tests if the project exposes them — `make test` or equivalent). If either fails, `git revert` the review commit and halt with the failure surfaced in the return summary.

Return a single message: auto-applied count, deferred (60–79) list with `file:line` refs, lint/test status. No follow-up questions.

## Workflow

1. Run `git diff main...HEAD` (or the project's base branch) to identify the diff.
2. Read modified files in full before judging changes against them.
3. Launch the six-agent parallel scan above. Collect and dedupe findings.
4. Score each finding 0–100. Drop everything below 60.
5. Branch on mode:
   - **Interactive (default)** — Group survivors by severity (Critical / Important / Minor) and present as a numbered list with `file:line` references and confidence scores. Search for similar patterns in the codebase before flagging style issues. Propose a fix plan: which findings you'll fix, which to skip and why, marking suspected false positives. Ask: "Shall I proceed with these fixes?" Wait for explicit approval before editing. After fixes, run `make lint` (or the project's equivalent).
   - **Autonomous (`--auto`)** — Apply each ≥80 finding, then commit them as a single follow-up. Run lint and tests; revert the commit and halt if either fails. Return the summary described in *Autonomous mode* above. Do not stay in conversation.

**Tone: issues only.** Never praise or summarize what went well. If nothing survives scoring, say "No issues found." and stop.

The approval gate is the differentiator versus `/review`: in interactive mode you stay in the loop and decide what's worth fixing. `--auto` is for AFK contexts only.

<!-- BEGIN bundled-book-rules -->

## Bundled book rules

Do not hand-edit content between the `BEGIN`/`END` markers — `scripts/sync_book_rules.py` overwrites it from `vendor/agent-rules-books/`.

### Rules from "Clean Code" by Robert C. Martin

<!-- BEGIN clean-code.mini.md v0.5 -->

# OBEY Clean Code by Robert C. Martin

## When to use

Use when readability, local reasoning, and maintainable code shape are the main concerns, especially during everyday implementation and review.

## Primary bias to correct

Working code is not automatically clean code.

## Decision rules

- Treat cleanliness as part of delivery. Preserve behavior, leave touched code cleaner within scope, and do not add mess because the schedule is tight or a rewrite is promised.
- Write for local reasoning. A reader should understand the path without reconstructing hidden state, wide jumps, or naming trivia.
- Use precise names and one term per concept. Rename code when vocabulary hides intent, overloads meaning, or forces comments to compensate.
- Keep functions small, focused, and at one level of abstraction. Tell the story top-down so intent appears before detail.
- Keep parameters few and meaningful. Avoid boolean flags, output parameters, and grab-bag argument lists; model the concept instead.
- Separate commands from queries and eliminate hidden side effects. A function that answers should not also mutate behind the reader's back.
- Keep the happy path readable. Isolate error handling, invalid-state handling, and cleanup; prefer explicit optionality or typed results over null-like sentinel flow when the language supports it.
- Expose behavior rather than raw representation. Avoid train-wreck access, utility dumping grounds, and classes or modules with mixed responsibilities.
- Keep construction, framework, persistence, transaction, security, and vendor details outside business behavior.
- Make public APIs small, explicit, and hard to misuse. Encode boundary logic, required order, and likely changes where readers can see them.
- Use comments only for rationale, constraints, warnings, or external contracts. Do not narrate code instead of improving it.
- Treat tests as production code: readable, deterministic, aligned with the behavior or contract they protect, and backed by proportionate validation before calling the change done.
- Let design emerge through tests, duplication removal, expressiveness, and minimal structure; do not add needless abstractions or infrastructure.
- When touching code, remove the smell that most increases change cost, but do not silently broaden the task beyond the smallest cleanup that makes the requested change safe.

## Trigger rules

- When a function mixes setup, validation, computation, and side effects, split the phases.
- When a comment explains control flow, simplify names or structure before keeping the comment.
- When a function both mutates and answers, or hides a mode switch behind a flag, separate the responsibilities.
- When duplication, repeated switches, or primitive clusters appear, name the concept with an argument object, polymorphism, special case, or other small abstraction.
- When a boundary leaks framework, vendor, or persistence quirks inward, add or strengthen a local adapter.
- When async or concurrency enters, isolate threading policy, minimize shared mutable state, define shutdown, and test timing-sensitive behavior.
- When fixing a bug or changing behavior, add or update the test that protects the intended contract.
- When cleanup starts spreading into unrelated areas, cut back to the smallest refactor that keeps the requested change safe and readable.

## Final checklist

- Can a reader follow the change locally?
- Are names and APIs carrying the meaning without narration?
- Is mutation explicit and the happy path still clear?
- Did framework, persistence, vendor, and construction details stay behind boundaries?
- Did I remove at least one smell from the touched area?
- Do tests protect the changed behavior or contract?
- Did I actually run the relevant tests or checks for this change?

<!-- END clean-code.mini.md -->

### Rules from "Refactoring" by Martin Fowler

<!-- BEGIN refactoring.mini.md v0.5 -->

# OBEY Refactoring by Martin Fowler

## When to use

Use when changing existing code, preparing a feature or bug fix, reviewing cleanup, or reducing structural friction without intending to change observable behavior.

## Primary bias to correct

Refactoring is behavior-preserving design work in small steps. Do not turn cleanup into a rewrite, a hidden feature change, or speculative architecture.

## Decision rules

- Preserve observable behavior during refactoring. Isolate behavior changes from structural changes and never disguise a feature, migration, or redesign as cleanup.
- Work in small, reversible, buildable, testable, reviewable steps. Split a patch when it is too large to reason about locally.
- Establish or identify a safety net before risky refactoring. Use characterization tests for unclear behavior, keep test updates aligned with intended behavior, and never delete a failing test to finish cleanup.
- Use preparatory and follow-up refactoring around feature work: identify what makes the requested change awkward, reshape that local structure first when useful, make the behavior change, then clean debt introduced by the change.
- Refactor the current blocking smell, not every smell in sight: duplication, long functions, long parameter lists, globals, divergent change, shotgun surgery, feature envy, primitive obsession, repeated conditionals, temporary fields, middle men, or speculative generality.
- Prefer the simplest named move that helps: rename, extract, inline, move, split meanings, introduce a parameter or value object, encapsulate a field or collection, decompose conditionals, use guard clauses, or substitute a clearer algorithm.
- Make names and functions reveal intent. Rename before deeper work when bad names block understanding; keep functions coherent, at one abstraction level, with tight variable scope and separated phases.
- Put behavior and state with the concept that owns them. Split classes or modules with multiple reasons to change; separate business policy from formatting, transport, persistence, I/O, frameworks, and integration details.
- Keep data, mutation, and call contracts explicit. Avoid behavior-switching boolean flags, confusing argument order, parameter reassignment, exposed mutable collections, unnecessary setters, public fields, and duplicated state-transition logic.
- Simplify conditionals honestly. Use guard clauses, extracted predicates, lookup tables, consolidated duplicate fragments, state, strategy, polymorphism, or null objects only when they reduce repeated branching or clarify variation.
- Use abstraction and generalization only when current evidence justifies them. Remove pass-through layers, vague utilities, middle men, unused hierarchy, and just-in-case interfaces that do not improve changeability.
- Preserve error semantics unless intentionally changing behavior. Refactor error handling to reveal the main path and consolidate duplicate validation, cleanup, recovery, or error structures.
- Keep patch intent reviewable. Group related refactorings, separate structural edits from behavior where practical, and avoid giant patches that rename, move, redesign, and change logic together.
- Stop when the requested change is easy, the blocking smell is gone, readability and local changeability are clearly better, and the next cleanup would be speculative.

## Trigger rules

- When adding behavior, first ask what structural friction blocks the change; refactor before the feature only when it makes the feature safer or simpler.
- When fixing a bug in unclear code, characterize the current failure and refactor only enough to make the fix visible before changing behavior.
- When tests are absent or weak, make the smallest possible structural move and improve testability before attempting broader cleanup.
- When the same edit appears for a third time, remove duplication through clearer ownership instead of copying again.
- When a function mixes responsibilities, abstraction levels, phases, or hidden side effects, rename, extract, split phases, or isolate side effects before adding more logic.
- When one change forces edits across many files, centralize the knowledge or introduce a clearer boundary.
- When repeated conditionals or type codes grow, decompose intent first; introduce polymorphism, state, strategy, or a table only when the variation is real.
- When UI and domain behavior mix, move rules toward domain objects and verify any required presentation synchronization.
- When a patch mixes intents or code motion makes review hard, split the change unless context makes that impractical.
- When tempted to rewrite, choose the next small behavior-preserving transformation that recovers control.

## Final checklist

- Observable behavior preserved?
- Structural change, behavior change, and test updates separated where practical?
- Safety net, characterization, or verification gap recorded?
- At least one real source of friction removed?
- Names, responsibilities, control flow, data ownership, and interfaces clearer?
- Patch still reviewable and runnable?
- Cleanup stopped before speculative abstraction or rewrite pressure took over?

<!-- END refactoring.mini.md -->

<!-- END bundled-book-rules -->
