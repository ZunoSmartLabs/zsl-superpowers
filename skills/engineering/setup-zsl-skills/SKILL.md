---
name: setup-zsl-skills
description: Sets up an `## Agent skills` block in AGENTS.md/CLAUDE.md and `docs/agents/` so the engineering skills know this repo's issue tracker (GitHub or local markdown), triage label vocabulary, domain doc layout, and ship style (PR vs direct push). Run before first use of `to-issues`, `to-prd`, `triage`, `diagnose`, `tdd`, `improve-codebase-architecture`, or `zoom-out` — or if those skills appear to be missing context about the issue tracker, triage labels, domain docs, or ship style.
disable-model-invocation: true
---

# Setup ZSL Skills

Scaffold the per-repo configuration that the engineering skills assume:

- **Issue tracker** — where issues live (GitHub by default; local markdown is also supported out of the box)
- **Triage labels** — the strings used for the six canonical triage roles
- **Domain docs** — where `CONTEXT.md` and ADRs live, and the consumer rules for reading them
- **Ship style** — how changes reach the default branch (pull request or direct push)
- **Project board** *(optional)* — a GitHub Projects v2 board whose `Status` column should mirror triage labels and tdd lifecycle

This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm with the user, then write.

## Process

### 1. Explore

Look at the current repo to understand its starting state. Read whatever exists; don't assume:

- `git remote -v` and `.git/config` — is this a GitHub repo? Which one?
- `AGENTS.md` and `CLAUDE.md` at the repo root — does either exist? Is there already an `## Agent skills` section in either?
- `CONTEXT.md` and `CONTEXT-MAP.md` at the repo root
- `docs/adr/` and any `src/*/docs/adr/` directories
- `docs/agents/` — does this skill's prior output already exist?
- `.scratch/` — sign that a local-markdown issue tracker convention is already in use

### 2. Present findings and ask

Summarise what's present and what's missing. Then walk the user through the five decisions **one at a time** — present a section, get the user's answer, then move to the next. Don't dump them all at once.

Assume the user does not know what these terms mean. Each section starts with a short explainer (what it is, why these skills need it, what changes if they pick differently). Then show the choices and the default.

**Section A — Issue tracker.**

> Explainer: The "issue tracker" is where issues live for this repo. Skills like `to-issues`, `triage`, `to-prd`, and `qa` read from and write to it — they need to know whether to call `gh issue create`, write a markdown file under `.scratch/`, or follow some other workflow you describe. Pick the place you actually track work for this repo.

Default posture: these skills were designed for GitHub. If a `git remote` points at GitHub, propose that. If a `git remote` points at GitLab (`gitlab.com` or a self-hosted host), propose GitLab. Otherwise (or if the user prefers), offer:

- **GitHub** — issues live in the repo's GitHub Issues (uses the `gh` CLI)
- **GitLab** — issues live in the repo's GitLab Issues (uses the [`glab`](https://gitlab.com/gitlab-org/cli) CLI)
- **Local markdown** — issues live as files under `.scratch/<feature>/` in this repo (good for solo projects or repos without a remote)
- **Other** (Jira, Linear, etc.) — ask the user to describe the workflow in one paragraph; the skill will record it as freeform prose

**Section B — Triage label vocabulary.**

> Explainer: When the `triage` skill processes an incoming issue, it moves it through a state machine — needs evaluation, waiting on reporter, ready for an AFK agent to pick up, ready for a human, a tracking container for sub-issues, or won't fix. To do that, it needs to apply labels (or the equivalent in your issue tracker) that match strings *you've actually configured*. If your repo already uses different label names (e.g. `bug:triage` instead of `needs-triage`), map them here so the skill applies the right ones instead of creating duplicates.

The six canonical roles:

- `needs-triage` — maintainer needs to evaluate
- `needs-info` — waiting on reporter
- `ready-for-agent` — fully specified, AFK-ready (an agent can pick it up with no human context)
- `ready-for-human` — needs human implementation
- `tracking` — container/parent issue (e.g. PRD) — work lives in sub-issues
- `wontfix` — will not be actioned

Default: each role's string equals its name. Ask the user if they want to override any. If their issue tracker has no existing labels, the defaults are fine.

**Section C — Domain docs.**

> Explainer: Some skills (`improve-codebase-architecture`, `diagnose`, `tdd`) read a `CONTEXT.md` file to learn the project's domain language, and `docs/adr/` for past architectural decisions. They need to know whether the repo has one global context or multiple (e.g. a monorepo with separate frontend/backend contexts) so they look in the right place.

Confirm the layout:

- **Single-context** — one `CONTEXT.md` + `docs/adr/` at the repo root. Most repos are this.
- **Multi-context** — `CONTEXT-MAP.md` at the root pointing to per-context `CONTEXT.md` files (typically a monorepo).

**Section D — Ship style.**

> Explainer: When a skill like `tdd` finishes a change, it needs to know how to get that change to the default branch. Team projects almost always go through pull requests; solo projects often push direct. This affects whether the skill creates a feature branch, opens a PR with a closing keyword, or commits straight to the default branch and closes the issue explicitly.

- **Pull request** — every change goes through a PR. Skills create a feature branch, push, and open a PR with `Closes #<issue>` in the body. The human merges.
- **Direct push** — changes go straight to the default branch. Skills commit, push, and close the related issue explicitly.

Default: pull request, unless the user specifies otherwise.

**Section E — Project board sync (optional, GitHub only).**

> Explainer: If you're using GitHub Projects v2 to track your issues on a board — or want to start — the `triage`, `to-issues`, and `tdd` skills can update a card's `Status` column whenever they change the issue's lifecycle (e.g. triaged to `ready-for-agent` → Status `Ready`; `tdd` starts work → `In progress`; PR opened → `In review`). Without this, the board stays static and you have to drag cards across columns manually. The skill can wire up either an existing board or create a fresh one. Skip this section if you don't want a project board, or if you'd rather wire the sync up via GitHub Actions yourself.

If the user opts in, walk them through:

1. **Identify or create the project.** Ask whether an existing Projects v2 board should be wired up, or whether to create a new one.

   - **Existing board.** Ask for the project URL (e.g. `https://github.com/users/<owner>/projects/<number>` or `https://github.com/orgs/<org>/projects/<number>`) or an `owner/number` pair. Parse out the owner and number.
   - **New board.** Ask for a title (default: the repo name). Determine the owner — for org-owned repos default to the org; for user repos default to the user — and confirm before creating. Then:
     ```bash
     gh project create --owner <owner> --title "<title>" --format json
     ```
     Capture the returned `number`, `url`, and node ID. Two follow-ups, both optional but worth offering:
     - **Link the repo** so issue/PR pickers know about the board: `gh project link <number> --owner <owner> --repo <owner>/<repo>`.
     - **Enable built-in workflows** at `<url>/workflows` — at minimum **Auto-add to project** (filter `repo:<owner>/<repo> is:issue,pr is:open`) and **Auto-close issue** (so closing an issue lands its card on `Done` without the skills having to). These workflows can't yet be toggled via `gh`; point the user at the URL.

2. **Fetch the project's structure.** Run:
   ```bash
   gh project view <number> --owner <owner> --format json
   gh project field-list <number> --owner <owner> --format json
   ```
   Capture the project's node ID (`PVT_…`), find the single-select field named `Status` (or whatever the user calls their lifecycle column — confirm with them), and capture its field ID (`PVTSSF_…`) and option IDs.

3. **Customise Status options if needed.** New projects ship with `Todo` / `In Progress` / `Done`. These skills work best with five canonical options — `Backlog`, `Ready`, `In progress`, `In review`, `Done` — because they map cleanly onto the triage and tdd lifecycle. Compare the option list from step 2 against the canonical five. If any are missing, ask the user which approach they'd prefer:

   - **Replace** the Status options with the canonical five (recommended for new boards, or older boards with no cards yet). Run the mutation:
     ```bash
     gh api graphql -f query='
       mutation($projectId: ID!, $fieldId: ID!) {
         updateProjectV2Field(input: {
           projectId: $projectId
           fieldId: $fieldId
           singleSelectOptions: [
             {name: "Backlog",     color: GRAY,   description: ""}
             {name: "Ready",       color: BLUE,   description: ""}
             {name: "In progress", color: YELLOW, description: ""}
             {name: "In review",   color: PURPLE, description: ""}
             {name: "Done",        color: GREEN,  description: ""}
           ]
         }) {
           projectV2Field {
             ... on ProjectV2SingleSelectField {
               id
               options { id name }
             }
           }
         }
       }
     ' -f projectId=<PVT_…> -F fieldId=<PVTSSF_…>
     ```
     Re-run `gh project field-list` to capture the new option IDs. Note: `updateProjectV2Field` replaces the option set wholesale; any cards assigned to a removed option (e.g. `Todo`) become unassigned and need manual remapping. Don't run this on a board with live cards without warning the user first.
   - **Map** existing options onto the canonical states (recommended when the board already has live cards). Confirm a mapping with the user — e.g. `Todo → Backlog`, `In Progress → In progress` — and record it in `docs/agents/project-board.md` so the skills emit the right option IDs without mutating the field.

4. **Map canonical states to Status options.** Default mapping (override per user preference, or per the mapping agreed in step 3):

   | Skill action                                                      | Status option |
   |-------------------------------------------------------------------|---------------|
   | `/triage` → `needs-triage` / `needs-info`                         | Backlog       |
   | `/triage` → `ready-for-agent` / `ready-for-human`                 | Ready         |
   | `/triage` → `tracking` / `/to-issues` parent                      | In progress   |
   | `/tdd` step 1 (work begins)                                       | In progress   |
   | `/tdd` ship in PR-style (PR opened)                               | In review     |
   | `/tdd-parallel` step 4 (integration PR opened) — bulk parent + every integrated sub-issue | In review     |
   | `/triage` → `wontfix`                                             | Done          |

   `/tdd` invoked with `--no-ship` (used by `/tdd-parallel` sub-agents) skips the per-slice "In review" update; the orchestrator handles the bulk transition when the consolidated integration PR opens.

   Issue closure (PR merged, direct-push commit, manual close) lands at `Done` automatically via the project's built-in **Auto-close issue** workflow — skills don't write `Done` themselves.
5. If the user's Status options don't include some of these labels (e.g. their column is named `In Review` not `In review`, or they have no `In progress`), confirm the substitutions before writing.

If the user opts out, do not write `docs/agents/project-board.md` — the skills detect its absence and silently skip the sync.

### 3. Confirm and edit

Show the user a draft of:

- The `## Agent skills` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is being edited (see step 4 for selection rules)
- The contents of `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/agents/domain.md`, `docs/agents/ship-style.md`, and (if Section E was answered yes) `docs/agents/project-board.md`

Let them edit before writing.

### 4. Write

**Pick the file to edit:**

- If `CLAUDE.md` exists, edit it.
- Else if `AGENTS.md` exists, edit it.
- If neither exists, ask the user which one to create — don't pick for them.

Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa) — always edit the one that's already there.

If an `## Agent skills` block already exists in the chosen file, update its contents in-place rather than appending a duplicate. Don't overwrite user edits to the surrounding sections.

The block:

```markdown
## Agent skills

### Issue tracker

[one-line summary of where issues are tracked]. See `docs/agents/issue-tracker.md`.

### Triage labels

[one-line summary of the label vocabulary]. See `docs/agents/triage-labels.md`.

### Domain docs

[one-line summary of layout — "single-context" or "multi-context"]. See `docs/agents/domain.md`.

### Ship style

[one-line summary — "pull request" or "direct push"]. See `docs/agents/ship-style.md`.
```

If Section E was answered yes, also append:

```markdown
### Project board

[one-line summary — project name and URL]. See `docs/agents/project-board.md`.
```

Then write the docs files using the seed templates in this skill folder as a starting point:

- [issue-tracker-github.md](./issue-tracker-github.md) — GitHub issue tracker
- [issue-tracker-gitlab.md](./issue-tracker-gitlab.md) — GitLab issue tracker
- [issue-tracker-local.md](./issue-tracker-local.md) — local-markdown issue tracker
- [triage-labels.md](./triage-labels.md) — label mapping
- [domain.md](./domain.md) — domain doc consumer rules + layout
- [ship-style-pr.md](./ship-style-pr.md) — pull-request workflow
- [ship-style-direct.md](./ship-style-direct.md) — direct push to default branch
- [project-board.md](./project-board.md) — GitHub Projects v2 sync (only when Section E was answered yes)

For "other" issue trackers, write `docs/agents/issue-tracker.md` from scratch using the user's description. For `docs/agents/project-board.md`, fill the template placeholders with the project node ID, Status field ID, and option IDs you discovered in Section E.

### 5. Done

Tell the user the setup is complete and which engineering skills will now read from these files. Mention they can edit `docs/agents/*.md` directly later — re-running this skill is only necessary if they want to switch issue trackers or restart from scratch.
