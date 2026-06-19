---
name: commit-push-pr
description: Commit session changes, push the branch, and open a PR — in one shot. Refuses to run on the repo's default branch (main/master) so the PR step can't fail. Delegates the commit step to `/zsl:commit`, then pushes with `-u`, then opens the PR via `gh`. Use when user wants to ship a feature branch end-to-end, says "/commit-push-pr", or asks to commit, push, and open a PR.
disable-model-invocation: true
---

# Commit, Push, Open PR

One-shot shipping for a feature branch: commit → push → PR.

The commit step is delegated wholesale to [`/zsl:commit`](../commit/SKILL.md) — same rules (autonomous for session changes, explicit file lists, no Claude attribution). The novel work here is the **pre-flight branch check** and the **push + PR open** after the commit lands.

## Pre-flight: not on the default branch

The PR step would fail on `main`/`master` — you can't open a PR from a branch into itself. Check **before** committing so the user isn't left committed-but-undeliverable.

1. `git rev-parse --abbrev-ref HEAD` → current branch.
2. `git symbolic-ref refs/remotes/origin/HEAD --short 2>/dev/null | sed 's|^origin/||'` → remote default branch. Fall back to `main`, then `master`, if that returns nothing.
3. If current branch equals the default branch, **stop immediately**. Surface the mistake and suggest `/zsl:git-branch <description>` to create a properly-prefixed feature branch. Do not proceed to the commit.

If the working tree is clean *and* the branch has no unpushed commits, also stop — there's nothing to ship.

## Process

1. **Run the pre-flight branch check.** Stop if on the default branch.

2. **Delegate to [`/zsl:commit`](../commit/SKILL.md).** Follow that skill's full process: classify session vs other-origin changes, confirm only the other-origin bucket, plan the commit(s), execute with explicit file lists. If `/zsl:commit` halts (user declines an other-origin file, hook fails, etc.), halt here too — don't push a half-shipped state.

   Skip this step if the working tree is clean but the branch has unpushed commits — go straight to push.

3. **Push with upstream.**
   ```bash
   git push -u origin <current-branch>
   ```
   `-u` sets the upstream so subsequent `git push`/`git pull` work without arguments. Harmless if the branch already tracks.

   If push fails (non-fast-forward, hook reject, auth), surface the error verbatim and stop. **Never `--force`. Never `--no-verify`.**

4. **Open the PR.**
   ```bash
   gh pr create --title "<title>" --body "<body>"
   ```
   - **Title**: derive from the branch name (strip the `feature/`/`fix/`/etc. prefix, replace hyphens with spaces, sentence-case) or the latest commit subject, whichever reads better. Keep under 72 chars.
   - **Body**: short *why* summary (1–3 bullets) plus a `## Test plan` checklist. Multi-line via heredoc. If `.github/pull_request_template.md` exists, follow its shape.
   - **No Claude attribution.** No `🤖 Generated with…`, no `Co-Authored-By:`. Same rule as `/zsl:commit`.
   - If a PR for this branch already exists, `gh pr create` fails; fall back to `gh pr view --json url -q .url` and report the existing PR URL.
   - If the repo has an auto-PR workflow (`.github/workflows/auto-pr.yml`) and the push already created the PR, skip the `gh pr create` and just resolve the URL.

5. **Report.** One line: PR URL. Done.

## Safety rails

- **Never force-push.** If the remote rejects, stop and let the user resolve.
- **Never `--no-verify`.** Pre-push hooks exist for a reason — fix the issue, re-run.
- **Don't open against a release branch by accident.** `gh pr create` defaults to the repo's base; if that's `main` but the user's flow uses `develop` or a release branch, ask before opening.
- **Don't re-litigate the commit grouping.** `/zsl:commit` owns that decision.

## When to use a different skill

- Just committing, no push/PR? → [`/zsl:commit`](../commit/SKILL.md).
- Need a branch first? → [`/zsl:git-branch`](../git-branch/SKILL.md), then this skill.
- Pre-PR review pass? → [`/zsl:code-review`](../code-review/SKILL.md) before this; fix findings, then run this.

## Why this shape

- **Pre-flight before commit** because committing on `main` is harder to unwind than refusing up front. One `git rev-parse` saves a future `git reset`.
- **Delegate to `/zsl:commit`** rather than re-implementing the commit rules — keeps the no-`-A`, no-attribution, other-origin-confirmation logic in one place.
- **`-u origin` on push** because half of "push failed" reports trace back to a branch with no upstream. Setting it once costs nothing.
