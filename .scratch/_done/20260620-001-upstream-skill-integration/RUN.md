# RUN — drive PRD-001 (upstream-skill-integration → v2.0.0) to completion, autonomously

This is a docs/skills-repo PRD, not application code, so there's no red-green on code.
Apply the SAME discipline anyway: every slice has a written, checkable contract; you
prove the contract FAILS before doing the work, make it pass with the minimal change,
keep the repo green, and verify by RUNNING a command — never by asserting.

## Read first, in full

1. `.scratch/001-upstream-skill-integration/PRD.md` — spec (Solution, Implementation
   Decisions, Testing Decisions, Out of Scope).
2. `.scratch/001-upstream-skill-integration/issues/*.md` — 11 slices. Each has What to
   build / Acceptance criteria / `User stories covered` (verbatim `observable:` lines) /
   Blocked by. **The `observable:` lines ARE your tests.**
3. `CLAUDE.md` — the "Invariants that break silently" (five-place skill sync,
   deterministic-gate scripts, release sync). Honor them on every slice.
4. `docs/agents/{issue-tracker,triage-labels,project-board,ship-style}.md` — hybrid
   tracker: `.scratch/` md is truth, mirrored to GitHub (#11–#21, parent #10); PR ship style.

## Branch (once)

`git checkout main && git pull && git checkout -b feature/v2.0.0-upstream-skill-integration`
The PRD ships as ONE 2.0.0 release, so slices accumulate on this branch and land in a
single PR at the end.

## The loop — repeat until no open slice remains

Re-derive the worklist each pass (so this survives a context compaction): an OPEN slice
is an issue file still under `issues/` (not `issues/_done/`). Pick the lowest-numbered
open slice whose every "Blocked by" issue is already in `issues/_done/`. If none qualify,
stop and report (blocked/cycle).

For the chosen slice:

1. RED — run each `observable:` check as a real shell command and confirm it currently
   FAILS (or shows the pre-change state). Paste the output. If all already pass, the slice
   is done — go to step 6.
2. GREEN — implement per "What to build" + the PRD's Implementation Decisions. Seed any
   extracted skill from the UNION of the existing inline files so no local phrasing
   regresses. Minimal change that satisfies every acceptance criterion.
3. SYNC — apply every CLAUDE.md contract the slice touches: five-place sync for adds/
   removes (model-invoked skills get ONLY plugin.json + the "Shared / model-invoked" doc
   subsection — no decision-tree node, no user-command list); deterministic-gate rules for
   any moved/added script; release-sync rules for the release slice.
4. REFACTOR / delete — extractions are net-deletion: remove the old inline copies and every
   dangling link. Leave the tree smaller wherever the slice says "delete".
5. GATE + VERIFY (the non-vacuous part):
   a. `make lint test docs` — all three exit 0 (docs --strict is the exact Pages deploy
      gate). If any fail, fix and re-run; never proceed red.
   b. Re-run every `observable:` check for this slice; confirm each now PASSES. Paste the
      output. A claim with no command output behind it does not count.
   c. This is also a regression gate: the full run must stay green for earlier slices' work.
6. SHIP (record + archive):
   - Append a "## Verification" note to the issue file listing the observable commands you
     ran and their PASS output (the receipt).
   - Move `issues/<NN>-*.md` → `issues/_done/<NN>-*.md`, final state intact.
   - Commit with an EXPLICIT file list (never `git add -A`), conventional message, NO
     Claude/AI attribution line. One commit per slice.
7. LOOP.

## Halt-with-RCA (don't thrash)

If a slice won't go green after 2 honest attempts: stop it, append "## Triage Notes" RCA
(the exact failing check + why) to its issue file, set its `Status:` → `needs-info` (and the
GitHub mirror label), then continue with any other now-unblocked independent slice. If
nothing remains that doesn't depend on the halted one, stop and report. Never `--no-verify`,
never force-push, never fake a green gate.

## Finish

(Release slice #21 is always last; it bumps plugin.json + marketplace.json to 2.0.0 and
writes the changelog — that's what makes the merge cut the v2.0.0 release.)

When every slice is in `issues/_done/`:

1. Final audit: `make lint test docs` green; re-verify story 22/25/26 (full inventory,
   five-place sync of every add/remove, decision-tree state) and story 2 (all EIGHT
   orchestrators carry `disable-model-invocation: true`).
2. Push; open ONE PR into main titled for the 2.0.0 release, body summarizing the six adds /
   three removals-renames + the "Upgrading from 1.4" note, with
   `Closes #11 #12 #13 #14 #15 #16 #17 #18 #19 #20 #21` so merge closes every child and
   auto-closes parent #10.
3. ⚠️ Merging cuts a PUBLIC v2.0.0 release — so do NOT merge. Leave the PR open and
   all-green, and report the URL for the human to merge. (To change this to auto-merge,
   replace this step with: "if all three gates are green, `gh pr merge --merge
   --delete-branch`, then confirm release.yml + the docs deploy both succeeded.")

Report at the end: slices landed, PR URL, release/deploy status, and any halted slices.
