---
name: code-review
description: Do a comprehensive code review of the current branch
model: opus
---

# Pre-PR Code Review

Please review this pull request and provide feedback on:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security concerns
- Test coverage (see coverage analysis below)

Use the repository's CLAUDE.md for guidance on style and conventions. Be constructive and helpful in your feedback.

## Sentry / Error Handling Analysis

Before suggesting Sentry additions:

1. **Check existing patterns** — Search for similar code in the codebase. If 5+ routes handle 401s without Sentry, that's the project pattern.

2. **Distinguish error types**:
   - **DO log to Sentry**: Unexpected exceptions, external API failures, missing configuration, data corruption, catch blocks
   - **DO NOT log to Sentry**: Expected HTTP responses (401 unauthenticated, 403 forbidden, 400 validation errors, 404 not found for user input)

3. **Apply the "would this wake someone up?" test**: If this condition happening at 3am shouldn't trigger an alert, don't log it as an exception.

4. **Expected conditions are not exceptions**:
   - User not authenticated → 401 (expected, don't log)
   - Invalid input → 400 (expected, don't log)
   - External API down → 503 (unexpected, DO log)
   - Database query fails → (unexpected, DO log)

**If suggesting Sentry, verify the codebase doesn't already handle similar cases differently.**

## Coverage Exclusion Analysis

Before suggesting coverage exclusions:

1. **Read existing config** — `jest.config.ts` (`collectCoverageFrom`) and `codecov.yml` (`ignore`). Skip files already excluded or outside collection scope.

2. **Analyze file content** (don't pattern-match paths):
   - **SHOULD HAVE UNIT TESTS**: Exports pure functions (no Supabase/React/fetch imports, input→output, no side effects). Examples: `validation.ts`, `*-utils.ts`, `mock-data.ts` with logic.
   - **SHOULD BE EXCLUDED**: Direct `createClient()` usage, route handlers, React components with `useEffect`/`useState`.

3. **Verify before suggesting**: Is file in collection scope? Does existing pattern cover it? Does file contain ANY pure functions?

**If pure functions exist → suggest unit tests, not exclusion.**

## SQL Migration Analysis

Before suggesting SQL changes:

1. **Check existing comments** — Inline SQL comments (`-- comment`) are valid documentation. Don't suggest `COMMENT ON` statements if inline comments already explain the logic.

2. **COMMENT ON is for tooling** — Use `COMMENT ON` when database documentation tools need metadata. Use inline comments for developer readability. Both are valid; don't require both.

3. **Index comments** — Partial indexes with `WHERE` clauses benefit from inline comments explaining the filtering logic. `COMMENT ON INDEX` is optional and only useful if you use database documentation generators.

## Type Safety / Runtime Validation Analysis

Before suggesting runtime type checks or validation:

1. **Check database constraints first** — If a column has `CHECK`, `FOREIGN KEY`, `NOT NULL`, or enum type constraints, the database already enforces valid values. Runtime validation is redundant.

2. **Type casts from DB are often necessary** — Supabase generates `string` for constrained columns (e.g., `country: string` even with `CHECK (country IN ('NZ', 'AU'))`). A type cast like `as "NZ" | "AU"` is correct—it tells TypeScript what the DB guarantees.

3. **Don't add validation for impossible states**:
   - **Redundant**: `if (country !== "NZ" && country !== "AU") throw` when DB has CHECK constraint
   - **Appropriate**: Validation at API boundaries where user input hasn't been validated yet

4. **If suggesting runtime checks**, verify the constraint isn't already enforced at:
   - Database level (CHECK, FK, NOT NULL, enum types)
   - API/form validation layer (zod schemas, form validation)
   - Type system (discriminated unions, branded types)

**Defensive code for impossible states adds noise without value.**

## Documentation Convention Analysis

Before suggesting JSDoc, comments, or documentation:

1. **Check existing conventions** — Search for `@param`, `@returns`, `/**` patterns in the codebase. If <5% of functions have JSDoc, don't suggest adding it to one file.

2. **Self-documenting code is preferred** — Clear prop names, TypeScript interfaces, and descriptive function names often eliminate the need for JSDoc.

3. **Don't suggest inconsistent documentation**:
   - **Wrong**: Add JSDoc to one component when 50 others have none
   - **Right**: Note that documentation is sparse project-wide (if it's actually a problem)

4. **CLAUDE.md guidance**: "Don't add docstrings, comments, or type annotations to code you didn't change"

**Documentation suggestions should match codebase conventions, not ideal-world standards.**

## Over-Engineering Analysis

Before suggesting configurability or abstraction:

1. **Constants vs environment variables**:
   - **Use constants**: Values that rarely change and have sensible defaults (cache TTLs, timeouts, retry counts)
   - **Use env vars**: Values that MUST differ per environment (API keys, URLs, feature flags for A/B tests)

2. **Apply the "how often would this change?" test**: If the answer is "rarely" or "never in production," a constant is sufficient. Environment variables add deployment complexity for no benefit.

3. **DRY without over-abstracting**:
   - **DO suggest**: Extracting magic numbers to named constants (improves readability)
   - **DO NOT suggest**: Environment variables for internal implementation details

4. **Examples**:
   - Cache duration `300` → `CACHE_MAX_AGE_SECONDS = 300` (good)
   - Cache duration → `process.env.CACHE_MAX_AGE` (over-engineering unless proven need)
   - Debounce delay `150` → `BLUR_DELAY_MS = 150` (good)
   - Creating a `ConfigService` for 3 constants (over-engineering)

**If suggesting configurability, explain the concrete use case requiring runtime changes.**

## Instructions

1. Use `git diff main...HEAD` (or `staging...HEAD` depending on the project's base branch) to see changes since branching
2. Read all modified files completely (minimum 1500 lines)
3. **Before suggesting any change**, search for similar patterns in the codebase to understand existing conventions
4. Review against the checklist above
5. Provide specific, actionable feedback with file:line references
6. Highlight any issues that should be fixed before creating a PR
7. Note any validation that should be run (`make lint`)
8. **Tone: issues only** — Do not praise code or summarize what was done well. Only report things that should be improved, fixed, or reconsidered. If there are no issues, state "No issues found." and nothing else.

## Workflow (IMPORTANT)

1. **Present findings first** — After reviewing, present ALL findings as a numbered list with file:line references and confidence levels. Group by severity (Critical / Important / Minor).
2. **Propose a fix plan** — List which findings you plan to fix and which you recommend skipping (with reasoning). For any findings you believe are false positives, mark them and explain why.
3. **Ask for approval** — End with: "Shall I proceed with these fixes?" Wait for explicit approval.
4. **Only then apply fixes** — Do not edit files until the user approves the plan.

This approval gate prevents applying incorrect fixes based on false positives and lets the user decide which issues are worth addressing.

Be thorough and critical - this review should catch issues before they reach the PR stage.
