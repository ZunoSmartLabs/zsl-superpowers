# ZSL Superpowers

A Claude Code **plugin** distributed through a marketplace: a collection of *skills* (slash-command workflows under `skills/`) plus a MkDocs documentation site (`docs/`) published to GitHub Pages. Most maintenance here is keeping parallel surfaces — plugin manifest, READMEs, docs nav, changelog — in sync.

Skills live in bucket folders under `skills/`:

- `engineering/` — daily code work
- `misc/` — kept around but rarely used
- `productivity/` — daily non-code workflow tools
- `remote-agents/` — the overnight loop: schedule unattended remote runs, run them, review the results

## Validating changes

- `make lint` — `ruff check` plus `basedpyright` over the Python (mkdocs hooks, scripts).
- `make docs` — strict MkDocs build. **This is the exact gate the GitHub Pages deploy runs on push to `main`** — run it locally before pushing any change to `docs/**`, `skills/**/SKILL.md`, `scripts/mkdocs_hooks/**`, or `mkdocs.yml`, or the deploy fails. (`make docs-serve` for live preview.)
- `make format` — `ruff format`.

## Invariants that break silently

The rest of this file is lockstep contracts: sets of files or fields that must move together. Editing one surface without the others raises no error at edit time — it surfaces later as a failed deploy, a mismatched marketplace version, or a remote routine that won't resolve. Three of them.

### Skill sync — five places

A skill in `engineering/`, `productivity/`, `misc/`, or `remote-agents/` must be cited in five places, all kept in sync. Adding or removing one means updating all five:

1. `.claude-plugin/plugin.json` — entry in the `skills` array.
2. Top-level `README.md` — one-line description in the matching bucket of the **Reference** section, skill name linked to its `SKILL.md`. Plus a workflow-section reference if it's part of the end-to-end loop.
3. `skills/<bucket>/README.md` — one-line description, name linked to its `SKILL.md`.
4. `docs/skills/index.md` — row in the table under the matching **role-in-the-loop** section (Plan / Break down / Build / Verify / Ship / Overnight / Cross-cutting / Off-loop and meta — *not* the bucket folder; the page groups by role and says so). If it's a loop skill, also add a node to the "Which skill do I want?" mermaid decision tree.
5. `mkdocs.yml` — nav line under the matching **role** group (same role headings as `docs/skills/index.md`, not the bucket).

Per-skill pages under `docs/skills/<name>.md` are auto-generated from `SKILL.md` by `scripts/mkdocs_hooks/skill_pages.py` — don't edit by hand. `mkdocs build --strict` (= `make docs`) runs on every push to `main` that touches `docs/**`, `skills/**/SKILL.md`, `scripts/mkdocs_hooks/**`, or `mkdocs.yml`, so a stale nav entry will fail the GitHub Pages deploy.

### Release sync — version fields + the release workflow

Update, in lockstep:

1. `.claude-plugin/plugin.json` — `version` field.
2. `.claude-plugin/marketplace.json` — `version` field. Must match `plugin.json`, otherwise the marketplace UI advertises the old version while the installed plugin reports the new one.
3. `docs/changelog.md` — new entry at the top describing the user-facing change.

The changelog is the only narrative record of what each release shipped, so:

- Add an **Upgrading from X.Y** sub-block whenever the release has migration steps (lingering hook state from a removed skill, manual workflows that became automatic, breaking renames, etc.) — `README.md`'s "Updating" section and the FAQ's "How do I update?" answer both point readers here, so the implicit promise is that breaking-ish releases will have one.
- If the entry was drafted mid-development (common here, since behaviour is often spec'd before it's built), reconcile it against the actual `git diff` of `skills/**` before release — drafted entries drift from final behaviour (a renamed mechanism, a reversed default, a state added late), and the changelog is the one place that drift becomes a published lie. Flag any change that alters *interactive* behaviour even when the release headline is a new opt-in path.

A push to `main` that bumps `plugin.json`'s `version` field triggers `.github/workflows/release.yml`, which validates the rules above (changelog section present for the new version, `marketplace.json` in sync) and creates a `v<version>` GitHub Release with the extracted changelog section as its body. Failures here block the release — fix the rule violation and re-push. The workflow only fires on actual version diffs; touching `plugin.json` for other reasons (adding a skill entry) is a no-op.

If the release changes a skill's behavior, also check whether the prose describing it has gone stale. Pages that most often need updating: `README.md` (workflow walk-through + per-skill one-liners), `docs/workflow.md` (mirrors the README), `docs/quickstart.md`, and `docs/faq.md`.

### The remote-agents loop — four files (runtime contract)

Unlike the two contracts above, this one governs *runtime behaviour*, not just repo bookkeeping.

Scheduled `/afk-worker` routines fire in fresh remote claude.ai sessions with **no plugins installed**, and plugin availability is **not** configurable per claude.ai environment. Skills are provisioned by a repo-level `SessionStart` hook (`.claude/hooks/zsl-remote-skills.sh`, written by `/setup-zsl-superpowers` Section F) — NOT by "installing the plugin in the environment." Don't reintroduce environment-plugin-install language in the remote-agents docs.

The loop is a contract across four files that must stay in lockstep: `afk-fanout`, `afk-worker`, `morning-review` (in `skills/remote-agents/`) plus `skills/engineering/setup-zsl-superpowers/remote-env.md`. They share the `afk-runs` ledger schema and the claim lifecycle (`scheduled → in-progress → done|tracking`); change one, check the others. Anything that must cross from an isolated worker clone to your local session travels on the `afk-runs` branch — `.scratch/` state does not sync across clones.
