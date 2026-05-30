Skills are organized into bucket folders under `skills/`:

- `engineering/` — daily code work
- `misc/` — kept around but rarely used
- `productivity/` — daily non-code workflow tools
- `remote-agents/` — the overnight loop: schedule unattended remote runs, run them, review the results

## Adding or removing a skill

A skill in `engineering/`, `productivity/`, `misc/`, or `remote-agents/` must be cited in five places, all kept in sync. Adding or removing one means updating all five:

1. `.claude-plugin/plugin.json` — entry in the `skills` array.
2. Top-level `README.md` — one-line description in the matching bucket of the **Reference** section, skill name linked to its `SKILL.md`. Plus a workflow-section reference if it's part of the end-to-end loop.
3. `skills/<bucket>/README.md` — one-line description, name linked to its `SKILL.md`.
4. `docs/skills/index.md` — bullet under the matching bucket.
5. `mkdocs.yml` — nav line under the matching bucket.

Per-skill pages under `docs/skills/<name>.md` are auto-generated from `SKILL.md` by `scripts/mkdocs_hooks/skill_pages.py` — don't edit by hand. `mkdocs build --strict` runs on every push to `main` that touches `docs/**`, `skills/**/SKILL.md`, `scripts/mkdocs_hooks/**`, or `mkdocs.yml`, so a stale nav entry will fail the GitHub Pages deploy.

## Releasing a new version

Update, in lockstep:

1. `.claude-plugin/plugin.json` — `version` field.
2. `.claude-plugin/marketplace.json` — `version` field. Must match `plugin.json`, otherwise the marketplace UI advertises the old version while the installed plugin reports the new one.
3. `docs/changelog.md` — new entry at the top describing the user-facing change. The changelog is the only narrative record of what each release shipped. Add an **Upgrading from X.Y** sub-block whenever the release has migration steps (lingering hook state from a removed skill, manual workflows that became automatic, breaking renames, etc.) — `README.md`'s "Updating" section and the FAQ's "How do I update?" answer both point readers here, so the implicit promise is that breaking-ish releases will have one.

A push to `main` that bumps `plugin.json`'s `version` field triggers `.github/workflows/release.yml`, which validates the rules above (changelog section present for the new version, `marketplace.json` in sync) and creates a `v<version>` GitHub Release with the extracted changelog section as its body. Failures here block the release — fix the rule violation and re-push. The workflow only fires on actual version diffs; touching `plugin.json` for other reasons (adding a skill entry) is a no-op.

If the release changes a skill's behavior, also check whether the prose describing it has gone stale. Pages that most often need updating: `README.md` (workflow walk-through + per-skill one-liners), `docs/workflow.md` (mirrors the README), `docs/quickstart.md`, and `docs/faq.md`.
