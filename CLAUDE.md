Skills are organized into bucket folders under `skills/`:

- `engineering/` — daily code work
- `misc/` — kept around but rarely used
- `productivity/` — daily non-code workflow tools

Every skill in `engineering/`, `productivity/`, or `misc/` must have a reference in the top-level `README.md` and an entry in `.claude-plugin/plugin.json`.

Each skill entry in the top-level `README.md` must link the skill name to its `SKILL.md`.

Each bucket folder has a `README.md` that lists every skill in the bucket with a one-line description, with the skill name linked to its `SKILL.md`.

Bumping the plugin version requires updating both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` — they must stay in sync, otherwise the marketplace UI advertises the old version while the installed plugin reports the new one.
