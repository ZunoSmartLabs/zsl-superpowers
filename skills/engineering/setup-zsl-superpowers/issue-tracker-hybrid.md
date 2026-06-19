# Issue tracker: Hybrid local-markdown ⇄ GitHub mirror

Issues and PRDs live as markdown files in `.scratch/` (the source of truth).
Each issue is mirrored to a linked GitHub issue **purely so it can be tracked on
the project board** (`docs/agents/project-board.md`). The markdown file owns
status; the GitHub issue follows.

Repo: `<owner>/<repo>`.

## The link

- The markdown file records its mirror in frontmatter: `github: <issue-number>`.
- The GitHub issue body opens with `Mirror of .scratch/<NNN>-<slug>/issues/<NN>-<slug>.md`.
- Matched up by storing each side's identifier on the other. No node ID lives in
  the file; the `github:` number is enough to resolve the issue (and thus its
  board card) on demand.

## Source of truth: the `.scratch` file

The file's `Status:` line is authoritative. The GitHub issue's label and the
board's Status column are **mirrors** — every status change is pushed outward,
never inward. If they ever disagree, the file wins; re-push to reconcile.

## Conventions (local markdown)

- One feature per directory: `.scratch/<NNN>-<feature-slug>/`, `<NNN>` a 3-digit
  zero-padded feature number assigned at creation. Address by number alone —
  `/zsl:triage 23` resolves `023-*` via glob.
- PRD: `.scratch/<NNN>-<feature-slug>/PRD.md`
- Open issues: `.scratch/<NNN>-<feature-slug>/issues/<NN>-<slug>.md`, numbered
  from `01` per-feature. Issue numbers are scoped to their feature, not globally.
- Closed issues archive to `.../issues/_done/<NN>-<slug>.md` — same filename, one
  directory deeper.
- Closed features archive to `.scratch/_done/<YYYYMMDD>-<NNN>-<feature-slug>/` —
  the whole feature dir moves under `_done/` with the close date stamped before
  the feature number, preserving its internal structure.
- Feature numbers are permanent and unique across active + archived. Never
  renumber — references in commit history, PRD bodies, and the GitHub mirror
  depend on them.
- Triage state is the `Status:` line near the top of each file (roles in
  `triage-labels.md`).
- Comments and conversation history append under a `## Comments` heading.

### Next feature number

The highest existing number across both active and archived features, plus one.
First feature is `001`.

```bash
next=$(
  ls -d .scratch/[0-9][0-9][0-9]-*/ .scratch/_done/[0-9]*-[0-9][0-9][0-9]-*/ 2>/dev/null \
    | sed -E 's,^\.scratch/(_done/[0-9]{8}-)?([0-9]{3})-.*/$,\2,' \
    | sort -n | tail -1
)
printf '%03d' $((${next:-0} + 1))
```

## When a skill says "publish to the issue tracker" (create an issue)

1. Create/locate the feature dir (assign the next `<NNN>` per "Next feature
   number" above; first is `001`).
2. Write the issue file under `.../issues/<NN>-<slug>.md` with a
   `Status: needs-triage` line near the top.
3. **Mirror to GitHub** so the board can track it:
   ```bash
   gh issue create --title "<title>" \
     --body "Mirror of .scratch/<NNN>-<slug>/issues/<NN>-<slug>.md" \
     --label needs-triage,backlog
   ```
4. Record the returned number in the file's frontmatter: `github: <N>`.
5. The repo's "Auto-add to project" board workflow adds the issue to the board at
   `Backlog`; if that workflow is off, add it and set Status per
   `docs/agents/project-board.md`.

## When a skill says "change triage state"

1. Edit the `Status:` line in the markdown file (the source of truth).
2. Swap the GitHub label on the mirror issue (`github:` frontmatter) to the
   matching role string — `gh issue edit <N> --add-label <role> --remove-label <prior>`.
3. Set the board card's Status option per `docs/agents/project-board.md`.

Steps 2–3 are best-effort mirrors; step 1 is authoritative. If a mirror push
fails, the file is still correct — re-push later to reconcile.

## When a skill says "fetch the relevant ticket"

Resolve from `.scratch` — the user normally passes a path, a per-feature issue
number, or a feature number.

For **feature-number references** (e.g. `/zsl:triage 23`), normalise to 3 digits
(`printf '%03d' 23` → `023`) then glob:

- Active: `.scratch/023-*/`
- Archive: `.scratch/_done/*-023-*/`

Numbers are unique, so at most one match. Read the file — it is canonical. The
`github:` frontmatter only matters when pushing state outward. If a file isn't
where expected, check the archive locations; nothing is deleted.

## When a skill says "close the issue"

1. Move the file `issues/<NN>-<slug>.md` → `issues/_done/<NN>-<slug>.md`, keeping
   the final `Status:` line intact so the archive preserves why it closed.
2. Close the mirror issue — `/tdd`'s PR carries `Closes #<github>`, so merge
   closes it (and lands the card on `Done` via the Auto-close board workflow). If
   closing outside a PR, `gh issue close <github>`.

## When a skill says "close the feature"

Move `.scratch/<NNN>-<feature-slug>/` →
`.scratch/_done/<YYYYMMDD>-<NNN>-<feature-slug>/` (today's date,
`$(date +%Y%m%d)`), preserving internal layout exactly. Close any still-open
mirror issues. The feature number stays embedded, so number-based lookup keeps
working across the active/archive split.
