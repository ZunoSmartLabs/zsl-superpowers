# Changelog

For the full commit history, see
[github.com/ZunoSmartLabs/zsl-superpowers/commits/main](https://github.com/ZunoSmartLabs/zsl-superpowers/commits/main).
This page summarises the user-facing changes per plugin version.

## 0.4.1

- Polished skill descriptions and the README intro for the marketplace listing.
- Documented the plugin/marketplace version-sync requirement in `CLAUDE.md`.

## 0.4.0

- New skill: [`timesheet`](skills/timesheet.md). Reads recent Claude Code
  session histories from `~/.claude/projects/` and synthesises copy/paste-ready
  timesheet bullets, grouped by project.
- The skill ships as LLM synthesis (not deterministic templating) so the output
  reads like notes you'd actually paste into standup.

## 0.3.x

- New skill: [`prototype`](skills/prototype.md). Builds a throwaway prototype
  to flush out a design before committing — routes between a runnable terminal
  app for state/business-logic questions and several radically different UI
  variations for design questions.
- Auto-resolve merge conflicts in [`/zsl:tdd-parallel`](skills/tdd-parallel.md):
  the orchestrator now attempts a clean, lint+test-passing merge before halting,
  and only halts on genuine semantic conflicts.
- Made the project-board update mandatory in `/zsl:tdd-parallel` (was previously
  best-effort) — the integration PR opens with the parent and every merged
  sub-issue moved to "In review."
- Reworked `/zsl:tdd-parallel` to a single integration PR per fanout (was
  previously one PR per slice). See
  [the deep-dive](tdd-parallel.md) for why.
- Renamed the plugin to `zsl-superpowers` (was `zsl-skills`).
- PRDs published by [`/zsl:to-prd`](skills/to-prd.md) now land with
  `ready-for-agent` instead of `needs-triage` — saves a triage round-trip on
  PRDs you authored yourself.
- Documented the `done/` archive convention for the local-markdown issue tracker:
  closed issues move to `.scratch/<feature>/issues/done/`, closed features move
  to `.scratch/done/<feature>/`. Nothing is deleted.

## 0.2.x and earlier

- Converted from a standalone repo to a Claude Code plugin (`zsl`) installable
  from a local clone, then from the GitHub-shorthand marketplace path.
- Added `marketplace.json` so the repo can register itself as a marketplace.
- New `tracking` state for container/parent issues — the parent doesn't carry a
  state on its own children's behalf.
- Synced triage labels and the `tdd` lifecycle to GitHub Projects v2 `Status`
  field, behind the optional `docs/agents/project-board.md` mapping.
- Added the `[AFK]` / `[HITL]` slice prefix and the wave-letter format
  (`<wave><letter>`) to slice titles so dependency graphs read at a glance.
- Auto-clean residue and sync `main` in `/zsl:tdd-parallel` pre-flight.
- New skill: [`zoom-out`](skills/zoom-out.md) for higher-level context on
  unfamiliar code.
