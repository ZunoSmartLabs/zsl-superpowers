# Ship style: direct push

Changes go straight to the default branch — no pull request workflow.

## Conventions

- Pull latest before committing.
- Commit and push to the default branch.
- Close the related issue explicitly with a reference to the commit (`gh issue close <num> --comment "<sha>"` for GitHub; equivalent for other trackers). If the issue is a sub-issue, closing it lets the parent auto-close once its last child closes.
- Confirm the commit message with the user before pushing.

## When a skill says "ship the change"

1. Pull latest.
2. Commit and push.
3. Close the related issue with a reference to the commit.
