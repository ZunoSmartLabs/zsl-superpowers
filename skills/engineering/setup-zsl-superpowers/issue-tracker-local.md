# Issue tracker: Local Markdown

Issues and PRDs for this repo live as markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<NNN>-<feature-slug>/` where `<NNN>` is a 3-digit zero-padded feature number assigned at creation (e.g. `.scratch/023-auth/`). Features can be addressed by number alone — `/zsl:triage 23` and `/zsl:to-issues 45` resolve to features `023-*` and `045-*` via glob.
- The PRD is `.scratch/<NNN>-<feature-slug>/PRD.md`
- Open implementation issues are `.scratch/<NNN>-<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` per-feature. Issue numbers are scoped to their feature, not globally — feature `023`'s issue `01` and feature `045`'s issue `01` are unrelated.
- Closed issues are archived to `.scratch/<NNN>-<feature-slug>/issues/_done/<NN>-<slug>.md` — same filename, just one directory deeper
- Closed features are archived to `.scratch/_done/<YYYYMMDD>-<NNN>-<feature-slug>/` — the whole feature directory moves under `.scratch/_done/` with the close date stamped before the feature number, preserving its internal structure (`PRD.md`, `issues/`, `issues/_done/`). The date prefix orders archived features chronologically (`ls .scratch/_done/` shows close order); the feature number stays embedded so number-based lookup keeps working across the active/archive split.
- Feature numbers are permanent and unique across active and archived features. Never renumber — references in commit history, PRD bodies, and external trackers depend on them.
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "create a new feature"

1. Determine the next feature number — the highest existing number across both active and archived features, plus one. First feature is `001`.
2. Use that `<NNN>` (3-digit, zero-padded) when creating `.scratch/<NNN>-<feature-slug>/`.

Reference snippet:

```bash
next=$(
  ls -d .scratch/[0-9][0-9][0-9]-*/ .scratch/_done/[0-9]*-[0-9][0-9][0-9]-*/ 2>/dev/null \
    | sed -E 's,^\.scratch/(_done/[0-9]{8}-)?([0-9]{3})-.*/$,\2,' \
    | sort -n | tail -1
)
printf '%03d' $((${next:-0} + 1))
```

The `sed` anchors the capture to either `^.scratch/<NNN>-` (active) or `^.scratch/_done/<DATE>-<NNN>-` (archive) so digits inside the slug itself don't get picked up.

## When a skill says "publish to the issue tracker"

If the feature directory doesn't exist yet, first create it per "When a skill says 'create a new feature'" above (which assigns the next number). Then create the issue file under `.scratch/<NNN>-<feature-slug>/issues/`.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user normally passes a path, an issue number, or a feature number directly.

For **feature-number references** (e.g. `/zsl:triage 23`), normalise the input to 3 digits (`printf '%03d' 23` → `023`) then glob:

- Active: `.scratch/023-*/`
- Archive: `.scratch/_done/*-023-*/`

Numbers are unique, so at most one match across the two locations. Error if zero matches; the user typed a number that doesn't exist.

For **path or per-feature issue references**, read the file directly. If the file isn't where expected, also check the archive locations — closed issues live in `issues/_done/`, and closed features live under `.scratch/_done/<YYYYMMDD>-<NNN>-<feature-slug>/` (resolve with the same `.scratch/_done/*-<NNN>-*/` glob).

Nothing is deleted — anything missing is in the archive.

## When a skill says "close the issue"

Move the file from `issues/<NN>-<slug>.md` to `issues/_done/<NN>-<slug>.md`. Keep the filename and the final `Status:` line intact so the archive preserves why it closed (e.g. `wontfix`, or whatever state it shipped from). Numbering does not reset — the `NN` prefix is permanent and unique across both folders.

## When a skill says "close the feature"

Move the entire feature directory from `.scratch/<NNN>-<feature-slug>/` to `.scratch/_done/<YYYYMMDD>-<NNN>-<feature-slug>/`, using today's date as the prefix (`$(date +%Y%m%d)`). Preserve its internal layout exactly — do not flatten `issues/_done/` or rewrite anything. A feature is typically closed once all its issues are in `issues/_done/`, but the maintainer may also archive a feature that was abandoned; the move is the signal either way. After the move, looking up a path under `.scratch/<NNN>-<feature-slug>/...` should fall through to `.scratch/_done/*-<NNN>-<feature-slug>/...` — the date prefix is unknown at lookup time, but the glob resolves it. The feature number stays embedded throughout, so number-based lookup keeps working.
