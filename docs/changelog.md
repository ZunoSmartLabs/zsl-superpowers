# Changelog

For the full commit history, see
[github.com/ZunoSmartLabs/zsl-superpowers/commits/main](https://github.com/ZunoSmartLabs/zsl-superpowers/commits/main).
This page summarises the user-facing changes per plugin version.

## 0.6.0

- New skill: [`/zsl:human-itl`](skills/human-itl.md). The serial,
  human-present counterpart to [`/zsl:tdd-parallel`](skills/tdd-parallel.md):
  it walks you through the `[HITL]` slices the fanout skips — the manual
  actions a coding agent physically can't perform (third-party console
  clicks, credential rotation, external sign-off, a hand-run migration) —
  records each as an audit-trail comment, marks them done so the dependent
  `[AFK]` slices unblock, then stops with the hint to re-run
  `/zsl:tdd-parallel`. It never writes code (that's `/zsl:tdd`) and never
  chains the fanout for you.
- **Narrowed the `[HITL]` definition.** [`/zsl:to-issues`](skills/to-issues.md)
  previously called a slice HITL if it needed "human interaction, such as
  an architectural decision or a design review." That conflated two things.
  A `[HITL]` slice is now strictly a *manual action an agent can't perform*.
  Architectural decisions and design reviews are **not** HITL slices —
  they're resolved upstream in [`/zsl:grill-with-docs`](skills/grill-with-docs.md)
  + an ADR *before* issues are cut, so slices fall out maximally AFK. A
  `[HITL]` slice that's really a decision in disguise is a process leak,
  and `/zsl:human-itl` hard-refuses it with a pointer back to grilling.
- `/zsl:tdd-parallel`'s "Skipped — HITL" guidance no longer tells you to
  run `/zsl:tdd <num>` (you don't red-green-refactor a manual action). It
  now points at `/zsl:human-itl <parent>`, after which you re-run the
  fanout.
- `/zsl:tdd-parallel` now **resumes correctly after a `/zsl:human-itl`
  round-trip.** Previously its "is this blocker satisfied?" check only
  recognised slice branches *it* merged during the current run, so an
  `[AFK]` slice `Blocked by` a `[HITL]` slice would zero-progress halt
  *again* on re-run even though `/zsl:human-itl` had finished the blocker
  (it was closed/done, never a merged branch) — and the RCA would
  mislabel the finished blocker as `unresolvable`. The unblocked rule now
  also counts a blocker that is closed/done within the parent's sub-tree
  (sub-tree-scoped, so an unrelated closed issue can't spuriously satisfy
  a dependency). This also fixes the quieter cousin: a blocker shipped by
  a prior independent `/zsl:tdd` is now recognised too.

**Upgrading from 0.5:** standard refresh — `/plugin marketplace update zsl-superpowers`
then restart Claude Code. One thing worth knowing:

- The `[HITL]` definition is narrower. Any existing open issue titled
  `[HITL] … — Decide …` / `… — Pick …` / `… — Review …` is now considered
  mislabeled: it's a decision, not a manual action. Resolve those with
  `/zsl:grill-with-docs` (capture the outcome as an ADR), then relabel the
  slice and its dependents `[AFK]` so `/zsl:tdd-parallel` will pick them
  up. Genuine manual-action `[HITL]` slices need no change — just clear
  them with `/zsl:human-itl` instead of `/zsl:tdd` from now on.

## 0.5.0

- [`/zsl:tdd`](skills/tdd.md) now closes local-markdown sub-tasks itself on
  ship: it flips the `Status:` line to `shipped` and runs
  `git mv .scratch/<feature>/issues/<NN>-<slug>.md` into the feature's
  `issues/done/` folder, both in the same commit as the slice's code so the
  close is atomic with the work that earned it. GitHub/GitLab path unchanged
  (still relies on `Closes #<n>` for tracker-side closure).
- When that close empties the feature's open `issues/`, `/zsl:tdd` prompts
  to archive the feature with `git mv .scratch/<feature> .scratch/done/<feature>`.
  Never automatic — gives you a chance to spin up a follow-up issue first.
- `/zsl:tdd` invoked with **no argument** now works on local-markdown
  trackers: it scans `.scratch/`, resolves each open issue's `## Blocked by`
  against the `issues/done/` archive, and presents the unblocked issues as a
  numbered picker (with "pending future waves" and "features archived but not
  closed" buckets shown for context). Auto-discovery for GitHub/GitLab is
  out of scope — use [`/zsl:triage`](skills/triage.md) for that.
- Removed: `git-guardrails-claude-code`. Claude Code's harness already
  hard-blocks pushes to default branches and asks before other destructive
  ops, so the hook's closed pattern list was redundant where it overlapped
  and risked false confidence where it didn't (`rm -rf`, `dropdb`, etc.
  were never covered). The `block-dangerous-git.sh` script is preserved
  in git history if anyone wants to revive it standalone.
- Releases are now automated. A push to `main` that bumps the plugin
  version triggers `.github/workflows/release.yml`, which validates the
  changelog entry exists and the two version JSONs agree, then creates a
  `v<version>` GitHub Release with the changelog section as its body.
  CI enforcement for the rules captured in `CLAUDE.md`. This entry is the
  workflow's first execution — `v0.5.0` will appear on GitHub Releases
  the moment the bumping commit lands on `main`.

**Upgrading from 0.4.x:** standard refresh — `/plugin marketplace update zsl-superpowers`
then restart Claude Code. Two things worth knowing:

- If you ran `/zsl:git-guardrails-claude-code` previously, its PreToolUse hook
  lives in *your* `.claude/settings.json` (and the `block-dangerous-git.sh`
  script under `.claude/hooks/`), not in the plugin. The update won't remove
  them. Leave them if you want the extra protection, or delete the `hooks`
  block from your settings and the script file by hand.
- On local-markdown trackers, `/zsl:tdd` now closes sub-tasks itself —
  flipping `Status:` to `shipped` and `git mv`-ing the issue file into
  `issues/done/` as part of the slice commit. If you'd been doing this
  manually after each slice, you can stop. The contract for the local-markdown
  tracker (where issues live, archive folder layout) is unchanged; only the
  tool that maintains it has more automation.

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
