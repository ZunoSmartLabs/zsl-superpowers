# Issue tracker: Local Markdown

Issues and PRDs for this repo live as markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The PRD is `.scratch/<feature-slug>/PRD.md`
- Open implementation issues are `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Closed issues are archived to `.scratch/<feature-slug>/issues/done/<NN>-<slug>.md` — same filename, just one directory deeper
- Closed features are archived to `.scratch/done/<feature-slug>/` — the whole feature directory moves under `.scratch/done/`, preserving its internal structure (`PRD.md`, `issues/`, `issues/done/`)
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/issues/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly. If the file isn't where expected, also check the archive locations — closed issues live in `issues/done/`, and closed features live under `.scratch/done/<feature-slug>/`. Nothing is deleted.

## When a skill says "close the issue"

Move the file from `issues/<NN>-<slug>.md` to `issues/done/<NN>-<slug>.md`. Keep the filename and the final `Status:` line intact so the archive preserves why it closed (e.g. `wontfix`, or whatever state it shipped from). Numbering does not reset — the `NN` prefix is permanent and unique across both folders.

## When a skill says "close the feature"

Move the entire feature directory from `.scratch/<feature-slug>/` to `.scratch/done/<feature-slug>/`. Preserve its internal layout exactly — do not flatten `issues/done/` or rewrite anything. A feature is typically closed once all its issues are in `issues/done/`, but the maintainer may also archive a feature that was abandoned; the move is the signal either way. After the move, looking up a path under `.scratch/<feature-slug>/...` should fall through to `.scratch/done/<feature-slug>/...`.
