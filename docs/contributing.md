# Contributing

Pull requests welcome. The repo is small and the conventions are explicit — this
page is the short version. For the bigger picture — the three-layer model and
the five places a skill must be cited — see
[Plugin architecture](architecture.md).

## Repo layout

Skills live under `skills/<bucket>/<name>/SKILL.md`, in one of four buckets
(`engineering/`, `productivity/`, `misc/`, `remote-agents/`). Each skill must be
cited in **five** places kept in lockstep — `.claude-plugin/plugin.json`, the
top-level `README.md`, its bucket `README.md`, `docs/skills/index.md`, and the
`mkdocs.yml` nav.
[Plugin architecture → Keeping the catalogue in sync](architecture.md#keeping-the-catalogue-in-sync)
is the single source of truth for the bucket layout and the full citation list.

The per-skill docs page is the one thing you *don't* hand-write — the
[`scripts/mkdocs_hooks/skill_pages.py`](https://github.com/ZunoSmartLabs/zsl-superpowers/blob/main/scripts/mkdocs_hooks/skill_pages.py)
hook generates it from each `SKILL.md` at build time. But the `mkdocs.yml` `nav:`
entry is still manual, and `mkdocs build --strict` fails on an unlisted page.

## Adding a new skill

The plugin includes a skill for this:

```
/zsl:writing-great-skills
```

It's the principles + vocabulary reference for authoring a skill — name, bucket,
frontmatter, sharp descriptions/triggers, progressive disclosure, and when to
bundle a deterministic-gate script. Use it — it knows the conventions better than
this page can write them down.

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

## Editing bundled book rules

Eight engineering skills bundle decision-pressure rules from
[ciembor/agent-rules-books](https://github.com/ciembor/agent-rules-books)
(MIT, pinned via `vendor/agent-rules-books/VERSION`). The rules are
embedded between `<!-- BEGIN bundled-book-rules -->` / `<!-- END
bundled-book-rules -->` markers near the bottom of each affected
`SKILL.md`.

**Do not hand-edit content between the `BEGIN`/`END` fences** —
`scripts/sync_book_rules.py` overwrites it from
`vendor/agent-rules-books/` on every sync.

To edit a bundled rule set:

1. Edit the file in `vendor/agent-rules-books/<book>/<file>.md`.
2. Run `make sync-books` — this rewrites the fences in every affected `SKILL.md`.
3. Commit both the vendor edit and the regenerated `SKILL.md` content.

To check for upstream changes (we hand-pick; we don't auto-track):

```bash
make check-upstream-books
```

This diffs the vendored snapshot against `ciembor/agent-rules-books`'s
latest tag. When a diff looks worth adopting, update
`vendor/agent-rules-books/VERSION`, copy the new files in, run
`make sync-books`, regression-test the affected skills, and ship a
plugin version bump.

To add or change a book→skill mapping, edit the `MAPPING` dict near
the top of `scripts/sync_book_rules.py`, then run `make sync-books`.
The script's `BEGIN`/`END`-fence machinery handles inserting a new
region (or removing one) cleanly.

The current skill→book mapping table lives in
[`vendor/agent-rules-books/README.md`](https://github.com/ZunoSmartLabs/zsl-superpowers/blob/main/vendor/agent-rules-books/README.md).
Per-skill supporting files (e.g. `DEEPENING.md` in
`improve-codebase-architecture/`, `CONTEXT-FORMAT.md` in
`grill-with-docs/`, `tests.md`/`mocking.md`/`refactoring.md` in `tdd/`)
sit *outside* the fences and **are** hand-editable — they exist to
align skill-specific vocabulary and process with the bundled rules.

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
