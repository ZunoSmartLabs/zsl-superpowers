# Changelog

For the full commit history, see
[github.com/ZunoSmartLabs/zsl-superpowers/commits/main](https://github.com/ZunoSmartLabs/zsl-superpowers/commits/main).
This page summarises the user-facing changes per plugin version.

## 0.9.0

A focused release that ports three high-leverage additions from
upstream [`mattpocock/skills`](https://github.com/mattpocock/skills),
adds a sixth lens to `/code-review`, and aligns one skill with the
structured `<what-to-do>` / `<supporting-info>` SKILL.md pattern.
No breaking changes.

- **New skill: [`/zsl:handoff`](skills/handoff.md).** Compacts the
  current conversation into a handoff document so a fresh agent (or
  session) can continue cleanly without re-deriving context. Saves to
  the OS temp directory (`$TMPDIR` on macOS/Linux, `%TEMP%` on
  Windows) with a dated slug. Redacts API keys, tokens, JWTs, signed
  URLs, internal hostnames, and `.env`-derived values before writing.
  References existing artifacts (PRDs, ADRs, issue bodies, commits)
  by path/line/URL rather than duplicating them. Includes a
  *Suggested skills for next session* section that names specific
  `/zsl:<skill>` calls in order. Accepts an argument-hint so the
  doc can be tailored when the user knows what the next session will
  focus on. Filling the long-standing gap around session end / `/clear`
  / cross-agent handoff.
- **`/zsl:code-review` grows a sixth lens: Spec alignment.** The
  existing five lenses (clean-code, CLAUDE.md compliance, git
  history, prior PR comments, inline comments) all read the diff and
  the surrounding repo. None of them asked *"did this faithfully
  implement what the spec asked for?"* — the new Spec lens does. It
  looks up the originating PRD/issue (via commit-message references
  → user argument → matching path under `docs/`, `specs/`, or
  `.scratch/`) and reports missing requirements, scope creep, and
  wrong-implementation findings with the relevant spec line quoted.
  Returns "no spec available" and skips itself if nothing is found.
  Inspired by upstream's two-axis `/review` skill; merged as one more
  lens in our existing parallel scan rather than a separate skill.
- **`/zsl:improve-codebase-architecture` gains an HTML report
  output.** Architectural review's value is in the *seeing* —
  markdown bullets undersell deepening opportunities. The new
  [`HTML-REPORT.md`](skills/improve-codebase-architecture.md) scaffold
  renders candidates as a single self-contained HTML file in the OS
  temp dir, mixing Mermaid graphs (dependencies, call flow,
  sequences) with hand-built SVG diagrams (mass diagrams,
  cross-sections, call-graph collapse) for editorial weight Mermaid
  alone can't carry. Tailwind + Mermaid both come from CDNs; no build
  tooling. Strict glossary enforcement: prose must use the
  `LANGUAGE.md` terms (module, interface, depth, seam, adapter,
  leverage, locality) exactly — never "component", "API",
  "boundary". An optional new step 4 in the SKILL.md; conversational
  presentation in step 2 stays primary.
- **`/zsl:grill-me` adopts the
  `<what-to-do>` / `<supporting-info>` SKILL.md pattern** (matching
  `/zsl:grill-with-docs`, which already uses it). No behavioural
  change — same content, sectioned so the model can find "what to do
  right now" vs "design-tree format reference" without re-skimming.
  Not migrated: `/zsl:tdd`, `/zsl:tdd-parallel`, `/zsl:triage`,
  `/zsl:code-review`, and other skills with explicit numbered phases.
  The structured sections would clutter docs whose body IS the
  workflow; the pattern is for skills with a "here's the action;
  here's the reference" shape.

**Upgrading from 0.8:** standard refresh —
`/plugin marketplace update zsl-superpowers` then restart Claude
Code. Nothing breaking; nothing to migrate. `/zsl:handoff` is
available immediately; `/zsl:code-review` automatically picks up the
Spec lens; `/zsl:improve-codebase-architecture` runs unchanged but
will now offer an HTML report when it would land better than a
numbered list.

## 0.8.0

- **Code review becomes a first-class part of the loop.**
  [`/zsl:code-review`](skills/code-review.md) was rewritten as a
  more rigorous, less noisy review pass with three structural changes:
  - **Clean-code lens.** Opens with Uncle Bob framing — simple, correct,
    minimal; single responsibility; small functions with names that
    don't lie; no dead code; no premature abstraction. Eight concrete
    "always flag" standards (incl. behavior changes without test
    changes, modified `.env*` files, comments that explain *what* the
    code does instead of *why*).
  - **Parallel multi-lens scan.** Five concurrent sub-agents handle
    distinct concerns — CLAUDE.md compliance, shallow bug scan,
    git history/blame, prior PR comments on the same files, inline code
    comments — instead of one head doing everything sequentially.
    Findings are deduplicated, then **scored 0–100**; anything below 60
    is dropped before you ever see it, reducing the noise the approval
    gate has to filter. The git-blame and prior-PR-comment lenses in
    particular catch "this looks wrong but it's pre-existing" and "we
    already debated this exact thing on PR #142" — blind spots the
    previous single-pass review couldn't see.
  - **`--auto` flag for autonomous use.** Drops the approval gate,
    applies findings ≥80 as a single revertible commit
    (subject `review: <summary>`), reports 60–79 findings in the return
    summary for the orchestrator to surface, runs lint+tests post-fix
    and self-reverts on failure. Designed for AFK contexts — the
    interactive approval gate stays default and remains the
    differentiator versus the built-in `/review`.

  A **genericisation pass** also removed Sentry / coverage /
  SQL / Supabase-specific heuristics that didn't belong in a portable
  skill. The remaining "Before suggesting changes" section keeps three
  universal principles (match existing conventions, trust enforcement
  layers, don't push abstraction prematurely). Net effect: file is 47%
  shorter and applies to any project.

- **[`/zsl:tdd`](skills/tdd.md) now auto-triggers a review** between
  Refactor (step 4) and Ship (step 6, renumbered) as new step 5.
  Interactive mode runs `/code-review` with the approval gate (fixes
  commit via `/commit`, same discipline as ship); AFK mode (`--no-ship`)
  runs `/code-review --auto`, with deferred 60–79 findings riding out in
  the return summary under a **Deferred review findings** section.
  A new `reviewed` heartbeat phase fires after the review pass so the
  parent orchestrator sees progress. Catches what the author missed
  without leaving the loop. The Refactor checklist also gained a
  **Delete aggressively** discipline — every refactor pass should remove
  dead code, unused imports, debug statements, commented-out blocks, and
  comments that explain *what* instead of *why* (TDD that only adds is
  half-done).

- **[`/zsl:tdd-parallel`](skills/tdd-parallel.md) now runs an
  integration code review** before the coverage gate. New step 4a fires
  `/code-review --auto` against the merged PRD tip and rides any
  cross-slice fixes (duplicate helpers, drift between slices, redundant
  imports after merge) into the same integration PR. The per-slice
  review inside each `/tdd` invocation can't see across slices; this
  pass can. Old subsections 4a/4b shifted to 4b/4c, and a new
  **Integration review failure** halt path joins the other four —
  `/code-review --auto` reverts its own commit on lint/test failure and
  the orchestrator surfaces it in RCA with the reverted commit sha for
  inspection. The sub-agent prompt template also got a **Lean slices**
  reinforcement pointing at `/tdd`'s deletion discipline, so bloated
  slices don't compound into a bloated integration PR.

- **[`/zsl:grill-me`](skills/grill-me.md) and
  [`/zsl:grill-with-docs`](skills/grill-with-docs.md) now print a design
  tree** at the start of every session and reprint it whenever the
  shape or status changes (node resolved, new branch discovered, focus
  moved, scope shifted). Status markers `[ ] / [→] / [✓]` show where
  you are in the decision space — pacing and progress become visible at
  a glance instead of being implicit in the running dialogue.

- **[`/zsl:commit`](skills/commit.md) is now fully autonomous.** Invoking
  `/commit` no longer pauses for a "Shall I proceed?" approval prompt —
  the invocation itself is the approval, and all session changes land
  in one logical commit by default. The skill still classifies dirty
  files into **session changes** (modified via this conversation's tool
  calls) versus **other-origin** (files dirty before the session
  started, or modified outside the conversation) and confirms **only**
  the other-origin bucket before including or excluding it. Safety
  rails are unchanged: still never `git add -A`, still refuses to stage
  `.env*` / `*credentials*` / `*.pem` and other obvious secret patterns,
  still no Claude attribution lines, still creates a fresh commit
  (never `--amend`) after a pre-commit hook failure. This composes
  cleanly with `/zsl:tdd`'s default-on review (Section 1 above) — the
  user approves fixes once at the review gate; `/commit` then lands
  them without a second prompt.

- **Local-markdown tracker convention: features now carry a number prefix,
  archives carry a date prefix.** Active features live at
  `.scratch/<NNN>-<feature-slug>/` (was `.scratch/<feature-slug>/`),
  where `<NNN>` is a 3-digit feature number assigned at creation —
  auto-incremented from the highest existing number across active +
  archived. Archived features live at
  `.scratch/done/<YYYYMMDD>-<NNN>-<feature-slug>/` (was
  `.scratch/done/<feature-slug>/`), with the close date stamped before
  the feature number so `ls .scratch/done/` shows close order while the
  number stays embedded for lookup. **Net effect**: features can be
  addressed by number alone — `/zsl:triage 23`, `/zsl:to-issues 45`, or
  any other skill that accepts a feature reference resolves via glob
  (`.scratch/023-*/` for active, `.scratch/done/*-023-*/` for archived).
  No more typing the slug, no more guessing what the directory was
  called. [`/zsl:tdd`](skills/tdd.md)'s feature-level close `git mv` now
  stamps both the date and the embedded number; the number itself is
  permanent across the active→archive transition. Numbers and dates are
  unique enough on their own that lookups never have to disambiguate.

**Upgrading from 0.7:** standard refresh — `/plugin marketplace update zsl-superpowers`
then restart Claude Code. Two things worth knowing:

- **Local-markdown trackers only**: existing features either lack the
  number prefix (active and archive) or lack the date prefix (archive
  only), and won't pick up the new lookup semantics or chronological
  archive sort without a one-time rename. Re-run
  [`/zsl:setup-zsl-superpowers`](skills/setup-zsl-superpowers.md) — it
  now detects unprefixed and partially-prefixed features (new step 5)
  and offers a **single unified backfill** that assigns the missing
  numbers in date order (from `git log --diff-filter=A`) and stamps any
  missing archive dates, all in one commit. Confirmation is required
  before any `git mv` runs; the maintainer can edit dates, override
  numbers, or skip specific entries. Existing numbered features keep
  their numbers; new assignments start from `max(existing) + 1`.
  Alternatively, rename by hand — but the unified backfill is much
  easier to keep consistent. GitHub, GitLab, and "Other" trackers are
  unaffected.
- **`/zsl:tdd`'s interactive flow is slightly longer** because step 5
  (Review) is now default-on. The review pass is the differentiator
  versus running `/zsl:code-review` manually after — it stays in the
  slice's commit graph and gates Ship. If you want fast iteration on a
  trivial slice, the `--auto` path runs unattended; otherwise the
  approval gate stays in force and you decide which findings to fix.
- **`/zsl:commit` no longer asks "Shall I proceed?"** Previously the
  skill drafted a commit plan and waited for confirmation; now it
  commits directly after classifying the dirty tree. If you relied on
  the prompt to catch an unintended file, the **other-origin
  confirmation** (files dirty before this session) still fires and the
  **safety rails** (no `git add -A`, refuse to stage `.env*`,
  credentials, large binaries) still hold. If you want a dry run, run
  `git status` / `git diff` yourself before invoking `/commit`.

## 0.7.0

- New skill: [`/zsl:verify-coverage`](skills/verify-coverage.md). Closes
  the loop's missing half. Until now the only post-implementation
  completeness signal was structural — the tracker auto-closes a PRD when
  its last child closes — but "all slices shipped" is not "all user
  stories covered"; they diverge exactly when slicing drops or misframes
  a story. `/verify-coverage <PRD>` takes the PRD's `## User Stories` as
  an *acceptance oracle* (never as `/tdd` implementation context) and
  proves each story against the **implemented code via tests**, not
  prose or code-search judgement: **Tier A** maps a story to an existing
  passing behavioral test; **Tier B** generates a test for stories with
  none, proves it non-vacuous by mutation (it must go RED when the code
  path is perturbed), then runs it; a **HITL lane** routes visual / UX /
  external-system stories to human attestation. Genuine gaps are
  quarantined as skipped tests (referencing the gap issue) and auto-filed
  as `needs-triage` sub-issues of the PRD, so they re-enter the loop
  through `/zsl:triage` → `/zsl:tdd-parallel`. The coverage matrix is a
  review surface that ends in a user decision — never a silent auto-gate.
  Run it between a `/zsl:tdd-parallel` fanout and merging the integration
  PR so gaps close in the same cycle. `disable-model-invocation` —
  user-invoked only.
- [`/zsl:to-issues`](skills/to-issues.md) now **persists** the
  story→slice mapping. Previously the "User stories covered" mapping was
  only spoken in the step-4 quiz and then lost; each published issue now
  carries a `## User stories covered` section in its body. This is what
  `/zsl:verify-coverage`'s Tier A reads back as its oracle — without it,
  coverage would be re-derived from scratch every run.
- [`/zsl:tdd-parallel`](skills/tdd-parallel.md) now **enforces a coverage
  gate** (new step 4a) before opening the integration PR. After the
  fanout integrates, it refuses to push until a valid `/zsl:verify-coverage`
  receipt exists for the integrated tip — `mode: full` and
  `verified-sha` equal to the PRD branch HEAD. Missing, `--no-generate`
  partial, or stale → the run blocks (a checkpoint, not a restart):
  invoke `/zsl:verify-coverage <parent>` in the still-open session, then
  continue; reply `skip` for a new **coverage-gate-declined halt** that
  leaves the merged branch unpushed for you to PR by hand. It is an
  *execution* gate, not an *outcome* gate — open gaps still pass; only
  skipping the check is blocked. `/zsl:verify-coverage` writes the
  receipt as a PRD comment (GitHub/GitLab) or
  `.scratch/<feature>/verify-coverage-receipt.md` (local-markdown) on
  every completed run. (Supersedes the soft nudge that briefly shipped in
  this release's drafts — the gate is the shipped behavior.)

**Upgrading from 0.6:** standard refresh — `/plugin marketplace update zsl-superpowers`
then restart Claude Code. One thing worth knowing:

- Slice issues created by `/zsl:to-issues` *before* this release have no
  `## User stories covered` section. `/zsl:verify-coverage` still works
  against them — it falls back to inferring the story→slice map from each
  slice's `## What to build` plus its merged diff — but warns that the
  map is inferred and lower-confidence for those slices. New issues cut
  after upgrading carry the section and get the exact map. No action
  required; re-slicing old PRDs is optional and only sharpens Tier A.

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
