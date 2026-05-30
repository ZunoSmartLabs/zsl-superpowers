# Vendored: agent-rules-books

Snapshot of selected rule sets from [ciembor/agent-rules-books](https://github.com/ciembor/agent-rules-books) by Maciej Ciemborowicz, licensed MIT. See `LICENSE` for the full upstream license.

## Pinned version

`v0.5` (see `VERSION`).

## What we use

Eight zsl-superpowers skills bundle decision-pressure rules from these books, inline-appended into their `SKILL.md` between `BEGIN <file>` / `END <file>` markers:

| Skill | Book file(s) |
|---|---|
| `engineering/tdd` | `refactoring/refactoring.nano.md`, `working-effectively-with-legacy-code/working-effectively-with-legacy-code.nano.md` |
| `engineering/improve-codebase-architecture` | `a-philosophy-of-software-design/a-philosophy-of-software-design.mini.md`, `clean-architecture/clean-architecture.mini.md` |
| `engineering/diagnose` | `release-it/release-it.mini.md` |
| `engineering/grill-with-docs` | `domain-driven-design-distilled/domain-driven-design-distilled.mini.md`, `implementing-domain-driven-design/implementing-domain-driven-design.mini.md` |
| `engineering/to-prd` | `domain-driven-design-distilled/domain-driven-design-distilled.mini.md` |
| `engineering/code-review` | `clean-code/clean-code.mini.md`, `refactoring/refactoring.mini.md` |
| `engineering/verify-coverage` | `working-effectively-with-legacy-code/working-effectively-with-legacy-code.mini.md` |
| `engineering/prototype` | `the-pragmatic-programmer/the-pragmatic-programmer.mini.md` |

Skill `SKILL.md` files are the canonical embed location. Do not hand-edit content inside the `BEGIN`/`END` fences — `scripts/sync-book-rules.py` overwrites it from the files in this directory.

## Updating

We hand-pick upstream releases. Workflow:

```
make check-upstream-books   # diff vendor/ against upstream's latest tag
# review diffs; if you want them:
# 1. update VERSION
# 2. copy new files into the appropriate subdirectories
# 3. make sync-books   # rewrites the BEGIN/END fences in each SKILL.md
# 4. regression-test the affected skills
# 5. commit + ship a plugin version bump
```

## Provenance

These rule sets are MIT-licensed engineering instructions distilled from classic software-engineering books. They are not the book text itself. See [upstream README](https://github.com/ciembor/agent-rules-books#readme) for the original author's notes on scope, methodology, and the validation experiment.
