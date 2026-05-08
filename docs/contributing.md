# Contributing

Pull requests welcome. The repo is small and the conventions are explicit — this
page is the short version.

## Repo layout

Skills live under `skills/<bucket>/<name>/SKILL.md`:

- `engineering/` — daily code work
- `productivity/` — daily non-code workflow tools
- `misc/` — kept around but rarely used

Every skill in `engineering/`, `productivity/`, or `misc/` must be:

1. Listed in the top-level [`README.md`](https://github.com/ZunoSmartLabs/zsl-superpowers/blob/main/README.md) (with a name-link to its `SKILL.md`).
2. Listed in [`.claude-plugin/plugin.json`](https://github.com/ZunoSmartLabs/zsl-superpowers/blob/main/.claude-plugin/plugin.json) under `skills`.
3. Listed in its bucket's `README.md` with a one-line description.

The docs site picks up new skills automatically — the
[`scripts/mkdocs_hooks/skill_pages.py`](https://github.com/ZunoSmartLabs/zsl-superpowers/blob/main/scripts/mkdocs_hooks/skill_pages.py)
hook scans every `SKILL.md` at build time. **You do still need to add the new
skill to the `nav:` block in `mkdocs.yml`** — mkdocs runs in `--strict` mode and
won't auto-include unlisted pages in the navigation.

## Adding a new skill

The plugin includes a skill for this:

```
/zsl:write-a-skill
```

It walks you through name, bucket, frontmatter, trigger phrases, and bundled
resources. Use it — it knows the conventions better than this page can write
them down.

Manually, the shape is:

```
skills/<bucket>/<name>/
├── SKILL.md           # required — frontmatter + body
├── REFERENCE.md       # optional — long-form reference loaded on demand
└── <other-resources>  # scripts, templates, examples
```

`SKILL.md` frontmatter must include:

- `name:` — kebab-case, must match the directory name.
- `description:` — one paragraph. **Lead with the capability, then the trigger
  phrases** (e.g. "Use when user says X / does Y / asks for Z"). This text is
  what Claude Code matches against to decide whether to auto-invoke the skill.

Optional:

- `disable-model-invocation: true` — only user can invoke (skill won't
  auto-trigger). Use this for high-blast-radius or interactive skills like
  `tdd-parallel` and `setup-zsl-superpowers`.

The body is plain markdown. Keep it scannable: short sentences, headed
sections, examples that paste cleanly.

## Versioning

Bumping the plugin version requires updating **both**:

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

They must stay in sync. Otherwise the marketplace UI advertises the old version
while the installed plugin reports the new one.

## Style

- Match the surrounding tone: opinionated where it asserts a position
  (e.g. "Build the right feedback loop, and the bug is 90% fixed."), dry where
  it documents mechanism.
- No emojis in skill bodies. The README and docs site use them sparingly for UI
  affordances; skill bodies don't.
- Stick to the project's vocabulary: *vertical slice*, *AFK / HITL*, *wave*,
  *integration PR*, *agent brief*, *out-of-scope knowledge base*. Don't invent
  parallel terms.

## Testing changes locally

Clone the repo and register the path as a local marketplace:

```bash
git clone git@github.com:ZunoSmartLabs/zsl-superpowers.git ~/code/zsl-superpowers
```

In Claude Code:

```
/plugin marketplace add ~/code/zsl-superpowers
/plugin install zsl@zsl-superpowers
```

Edit, then refresh:

```
/plugin marketplace update zsl-superpowers
```

Restart Claude Code to pick up changes.

## Building the docs site

```bash
pip install 'mkdocs-material[imaging]'
mkdocs serve
```

`mkdocs serve` rebuilds on save. Per-skill pages are generated at build time by
the hook, so editing any `SKILL.md` triggers a rebuild of the corresponding
`/skills/<name>/` page.

The CI build runs `mkdocs build --strict` — broken links, missing nav entries,
or hook errors fail the build. Run the same locally before opening a PR:

```bash
mkdocs build --strict
```

## Filing issues

Use the GitHub issue tracker:
[github.com/ZunoSmartLabs/zsl-superpowers/issues](https://github.com/ZunoSmartLabs/zsl-superpowers/issues).

Bugs: include the skill name, what you ran, what happened, what you expected.

Feature requests: describe the failure mode you're hitting first, the proposed
skill second. Skills exist to fix specific failure modes — if we can't see the
failure mode, we can't evaluate the skill.
