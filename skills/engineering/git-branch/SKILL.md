---
name: git-branch
description: Create a git branch with a name that matches the auto-PR workflow prefix convention
---

# Create Git Branch

Create a new git branch with a name that follows the project's required prefix convention so the auto-PR workflow picks it up.

## Required prefixes

Branches MUST start with one of these prefixes followed by `/`:

- `feature/` — new functionality
- `fix/` — bug fix
- `chore/` — maintenance, tooling, non-functional changes
- `refactor/` — internal restructuring without behavior change
- `env/` — environment-specific work (e.g. `env/seb-test`)

Branch names without one of these prefixes will NOT trigger the auto-PR workflow (`.github/workflows/auto-pr.yml`).

## Process

1. **Parse the user's prompt** (the argument after `/git-branch`):
   - If the user already provided a valid prefix (e.g. `fix/logout-button`), use it verbatim.
   - Otherwise, infer the most appropriate prefix from the description and the current working tree context:
     - New feature or capability → `feature/`
     - Bug fix or broken behavior → `fix/`
     - Docs, dependencies, cleanup, deletions of unused code → `chore/`
     - Rename, restructure, extract, inline (no behavior change) → `refactor/`
     - Per-developer sandbox branches → `env/`
   - **Extract a GitHub issue ID** if the prompt references one. Match any of:
     - A full issue URL: `https://github.com/<org>/<repo>/issues/<N>`
     - A shorthand reference: `#<N>` or `issue <N>` / `issue #<N>` / `gh-<N>`
     For the URL form, fetch the issue title with `gh issue view <N> --repo <org>/<repo> --json title -q .title` and use it (slugified) as the description if the user didn't also provide their own wording. For shorthand without a repo, assume the current working directory's repo.

2. **Build a slug** from the description:
   - Lowercase
   - Replace spaces and non-alphanumerics with hyphens
   - Collapse repeat hyphens
   - Trim leading/trailing hyphens
   - **Total branch name must not exceed 40 characters**. Shorten the description until it fits.
   - **If an issue ID was extracted**, prepend it to the slug so the final branch name is `<prefix>/<N>-<slug>` (e.g. `feature/22-broker-s3-persistence`). The issue number goes immediately after the prefix's `/`, before the descriptive slug.

3. **Present the proposed branch name to the user** and ask for confirmation:
   - Show the prefix you chose and why (one sentence)
   - Ask: "Create branch `<name>`? (y/n)"

4. **On confirmation**, run:
   ```bash
   git checkout -b <branch-name>
   ```

## Important

- NEVER create a branch without the required prefix
- NEVER create a branch without user confirmation
- If the user is already on a non-main branch with uncommitted changes, ask whether to carry the changes over (default) or stash them first
- If a branch with that name already exists, tell the user and suggest an alternative

## Examples

<example>
User: `/git-branch remove the broken logout button`
Assistant: Proposes `fix/remove-broken-logout-button` — "fix" because it's removing broken behavior. Asks for confirmation, then runs `git checkout -b fix/remove-broken-logout-button`.
</example>

<example>
User: `/git-branch chore/update-readme`
Assistant: Uses the provided name verbatim (already has valid prefix). Asks for confirmation, then runs `git checkout -b chore/update-readme`.
</example>

<example>
User: `/git-branch add cognito group support`
Assistant: Proposes `feature/add-cognito-group-support` — "feature" because it's new functionality.
</example>

<example>
User: `/git-branch fix https://github.com/Thundergrid149/tg-ops-portal/issues/22`
Assistant: Extracts issue number `22` from the URL, fetches the issue title via `gh issue view 22 --repo Thundergrid149/tg-ops-portal --json title -q .title` (e.g. "Get CPMS broker working in preview environments"), picks `feature/` based on the issue content, and proposes `feature/22-broker-working-in-preview`. Asks for confirmation, then creates the branch.
</example>

<example>
User: `/git-branch #14 remove logout button`
Assistant: Extracts issue number `14` from the `#14` shorthand, keeps the user's own description, and proposes `fix/14-remove-logout-button`.
</example>
