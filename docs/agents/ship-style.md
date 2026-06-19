# Ship style: pull request

Every change reaches the default branch through a pull request — never push
directly.

## Conventions

- Create a feature branch before committing if on the default branch. Branch
  names follow the prefix convention (`feature/`, `fix/`, `chore/`, `refactor/`,
  `env/`) the repo's auto-PR workflows expect, and should reference the work.
- Open a PR with a closing keyword referencing the **GitHub mirror issue** this
  work resolves (e.g. `Closes #<github>` in the PR body, where `<github>` is the
  `github:` frontmatter number from the `.scratch` issue file). The mirror issue
  closes on merge — and its board card lands on `Done` via the Auto-close
  workflow.
- Confirm the PR title and body with the user before creating.
- Do not merge. Leave that to the human.

## When a skill says "ship the change"

1. Create a feature branch (if on the default branch).
2. Commit and push.
3. Open a PR with `Closes #<github>` in the body (the mirror issue number).
4. On merge: the mirror issue closes automatically. The skill then moves the
   `.scratch` issue file from `issues/<NN>-<slug>.md` to
   `issues/_done/<NN>-<slug>.md` (per `docs/agents/issue-tracker.md`), since the
   GitHub close does not move the local source-of-truth file.
5. Stop — do not merge.
