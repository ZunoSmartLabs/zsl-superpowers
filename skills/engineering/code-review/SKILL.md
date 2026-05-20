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
