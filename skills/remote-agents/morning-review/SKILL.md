---
name: morning-review
description: Walk a human through the overnight artifacts the /afk-worker routines (scheduled by /afk-fanout) produced. First reconciles the shared afk-runs ledger branch into the canonical .scratch/ tracker — replaying claim flips and halt RCAs that ran in isolated worker clones — across every un-reconciled run, not just last night. Then surfaces integration PRs to verify and merge, halted slices in needs-info to re-triage, and any scheduled PRD that produced no result (cross-checked against the manifest so a worker that never fired or got throttled isn't silently missed). Sorts PRs by their brief's verify-after tag so local-run and staging slices surface first; ci slices are batch-mergeable after a diff skim. Use the morning after an /afk-fanout schedule has run, or mention /morning-review.
---

# Morning Review

Walk through what the scheduled `/afk-worker` sessions produced: integration PRs that need a human's eyes before merge, halted slices that need re-triage, and scheduled PRDs that produced nothing (throttled, never fired, or stuck on a dirty tree). `/afk-fanout` wrote a manifest and each `/afk-worker` wrote a per-PRD entry — both on the shared `afk-runs` ledger branch. This skill **reconciles** that ledger back into the canonical `.scratch/` tracker (claim flips and halt RCAs ran in isolated worker clones and can't reach `main` any other way), then drives the morning sweep across every un-reconciled run.

## Why this exists

The scheduled workers ship verified-by-CI PRs and park halted slices in `needs-info`. None of it is mergeable without a human pass:

- **CI green ≠ "works against real services."** Slices touching external APIs, auth, payments, or migrations need a human checkout + `/verify` against a local dev env, or a staging deploy. The brief's `verify-after:` field records which: `ci` slices skim-and-merge, `local-run` slices need the walk-through, `staging` slices need a deploy step first.
- **Halted slices need a maintainer decision.** A 3a/3d halt left an RCA on the slice and moved it to `needs-info`. The maintainer decides: fix and re-triage, reformulate the brief, or close `wontfix`.
- **Scheduled-but-no-result is its own signal.** A PRD that `/afk-fanout` scheduled but that produced no PR and no halt fragment was likely throttled by the per-5h token cap, never fired, or is stuck on a 3e dirty tree. The manifest cross-check surfaces these so they aren't silently lost.
- **The morning slot is bounded.** This skill puts the highest-attention items first so you can stop when the urgent work is done and leave `ci` skims for later.

## Usage

```
/morning-review
```

No arguments. Fetches the `afk-runs` ledger branch, reconciles every un-reconciled run into the tracker, enumerates the artifacts, and walks through them in priority order.

## Pre-flight

Refuse with a clear message if any of these fail:

- `docs/agents/issue-tracker.md` exists.
- `docs/agents/triage-labels.md` exists.
- Working tree is clean (`git status --porcelain` empty). Reconciliation reads the ledger read-only (via `git show`, no checkout) but commits its replayed mutations to `main`, and the walk-through does `gh pr checkout`; a dirty tree blocks both.
- The `afk-runs` branch is fetchable (`git fetch origin afk-runs`) and has **at least one un-reconciled** dated dir (a `<date>/` whose entries lack a `reconciled:` value), in local-markdown mode; or there are recent `scheduled`/`in-progress` labels + routine-fired PRs in GitHub-issues mode; or integration PRs opened since the last review. If none of these signals are present there's nothing to review — say so and stop.

## Process

### 1. Load and reconcile the overnight artifacts

**Coverage — every un-reconciled run, not just last night.** `git fetch origin afk-runs` and process **all** date dirs whose entries lack a `reconciled:` value, not only the newest. This closes the skipped-morning hole: if you scheduled two nights but reviewed once, the older night is still picked up — and its scheduled-but-no-result cross-check still runs. A dir's date is the **evening `/afk-fanout` ran** (post-midnight slots included), so select dirs by **name**, never by "today's date" — the morning you review, "today" won't match the dir you want.

Read the ledger **read-only** to keep the tree clean (pre-flight requires it): `git show origin/afk-runs:.afk-runs/<date>/_scheduled.md` and each `<feature-num>.md` — no checkout. GitHub-issues mode has no ledger; reconstruct from labels + PRs per-list below.

Build three lists, cross-referencing each dir's manifest:

**What was scheduled** (the manifest):
- `.scratch/` mode: `_scheduled.md` — one row per scheduled PRD (feature-num, title, slot, trigger-id, routine URL).
- GitHub-issues mode: reconstruct from PRD parents currently labeled `scheduled`/`in-progress`, plus the routines list.

**Integration PRs to review** — for each scheduled PRD, find its result:
- `.scratch/` mode: the ledger entry `<feature-num>.md` records `outcome`, `pr`, and `slices-closed`.
- GitHub-issues mode: `gh pr list --search "created:>=<earliest un-reconciled slot>"` matched to scheduled PRDs by `Closes #<parent>`.

For each PR, fetch: title + body (look for a `## ⚠️ Integration review failed` 4a-degradation marker), the closed slices (`Closes #N` or the `## Slices integrated` list), each closed slice's `verify-after:` field, and CI status (`gh pr view --json statusCheckRollup`).

**Halted slices to re-triage:**
- `.scratch/` mode: ledger entries with `outcome: halt-*` — their `slices-needs-info` + `rca`. (After reconciliation, below, these are also real `needs-info` slices in `.scratch/`.)
- GitHub-issues mode: `gh issue list --label needs-info --search "in:body 'Halt RCA — /tdd-parallel halted'"`.

**Scheduled-but-no-result** — the cross-check: any scheduled PRD whose ledger entry is still `outcome: pending` with no PR (never fired / throttled), or `claim: in-progress` with no PR (stuck, likely 3e). Surfaced separately in §2.

#### Reconcile the ledger into `.scratch/`

The ledger is the transport; `.scratch/` on `main` is canonical. Before the walk-through, replay each un-reconciled `.scratch/`-mode entry into `.scratch/`, then mark it done. **Idempotent** — reconcile by *desired end state*, so a re-run skips entries already reflected:

| Ledger outcome | Replay into `.scratch/` on `main` |
|---|---|
| `success` (has PR) | Don't pre-apply slice closures — they land when you merge the PR. Just refresh the parent claim to "PR-open / in-flight" (replacing the stale `scheduled`) and link the PR. |
| `halt-3a` / `halt-3d` | For each `slices-needs-info`, set the slice `Status: needs-info` and post the `rca` block as its comment (skip if already present). Set parent `Status: tracking`. |
| `halt-3e` | Post the `rca` on the parent, set parent `Status: in-progress` (visibly stuck), no slice moves. Surface the routine URL. |
| `refusal-1d` | Set parent `Status: tracking` (release claim) + post the refusal reason. |
| `pending`, no PR | No replay — reset parent `scheduled` → `tracking` so it re-queues; surface the routine URL. |

Commit the replayed mutations to `main` via `/zsl:commit` — tracker bookkeeping on `main` is the existing model (`/afk-fanout` already commits the claim there; PR-style governs *code*, not `.scratch/` state). Then set `reconciled: <today>` in each replayed ledger entry and push `afk-runs`, so the next review skips them. GitHub-issues mode needs no replay — the worker's tracker writes already landed via the API.

### 2. Sort by attention required

Print two things, **summary first**:

**First, the summary line** — a one-glance scoreboard of the night, so the human knows the shape of the work before reading any detail:

```
<N> PRs to review · <S> scheduled-no-result · <H> halted slices · <C> CI failures
```

**Then the priority list** — the artifacts in priority order (highest attention first), one line each, **carrying the source PRD** so every artifact maps back to the feature you scheduled: `<bucket> · PRD <feature-num> <title> · PR #<N> <title> · verify-after: <highest-attention tag across its slices>`. The buckets, top to bottom:

1. **PRs with `## ⚠️ Integration review failed`** — `/tdd-parallel` couldn't apply its cross-slice cleanup. Run `/code-review` locally against the PR branch before merge.
2. **PRs containing any `verify-after: staging` slice** — needs a staging deploy + smoke test before merge.
3. **PRs containing any `verify-after: local-run` slice** — needs `gh pr checkout` + `/verify` against local dev env.
4. **Scheduled-but-no-result PRDs** — a worker that never produced output. Diagnose: throttled (re-schedule tonight), stuck on a 3e dirty tree (inspect the routine session), or the routine never fired (check the routine URL).
5. **Halted slices in `needs-info`** — re-triage decisions.
6. **PRs with all slices `verify-after: ci`** — skim the diff, merge if reasonable.
7. **PRs with red CI** — surfaced separately; never auto-merged.

The PRD ref comes from the manifest in `.scratch/` mode and from the PR's `Closes #<parent>` reference in GitHub-issues mode — so the mapping holds in both. Bucket lines that are *not* a PR (scheduled-no-result PRDs, halted slices) still lead with their PRD ref: scheduled-no-result is `<feature-num> <title>` directly; a halted slice is `PRD <feature-num> · slice <ref>`. The bucketing axis is attention-required, but the PRD ref is on every line so you can always trace an artifact back to the §1 selection that produced it.

### 3. Walk through each bucket

Interactive — the user drives the pace; this skill sequences, it does not auto-merge.

**PRs with `## ⚠️ Integration review failed`:** show the PR URL, the attempted-findings section verbatim, and the reverted-commit sha. Offer `gh pr checkout <N>` + `/code-review` to re-run locally. If `/code-review` applies findings cleanly, the user commits via `/commit` and pushes — re-prioritise the PR into its verify-after bucket. If it can't fix it, leave the warning; the user merges as-is or closes.

**`verify-after: staging` PRs:** show the PR URL + slices. Walk the project's staging-deploy steps (this skill surfaces the requirement; it does not deploy). On confirmed smoke-test, merge and annotate the PR `verified-on-staging`.

**`verify-after: local-run` PRs:** `gh pr checkout <N>`, walk `/verify` against the local dev env. On success, merge; on failure, the user fixes-and-pushes, closes, or moves the offending slice back to `needs-info`.

**Scheduled-but-no-result PRDs:** show the ledger entry (slot, routine URL, `outcome`/`claim`). Reconciliation (§1) has already reset a never-fired/throttled PRD (`pending`) to `tracking`, so it'll re-queue on the next `/afk-fanout` — offer to re-schedule tonight. For a suspected 3e (`in-progress`, no PR) the claim was left `in-progress`; open the routine session via the URL to inspect the stuck tree, then reset to `tracking` if it should re-queue.

**Halted slices in `needs-info`:** show the slice ref, its `verify-after:`, and the latest halt RCA. Offer three actions — re-triage to `ready-for-agent` (`/triage <slice>`, underlying issue understood), reformulate the brief (edit, then `/triage`), or close `wontfix` (`/triage` handles it).

**`verify-after: ci` PRs:** show the PR URL, CI status (green to be in this bucket), and slices. Offer: open the diff, skim, merge. The per-slice and integration `/code-review --auto` already ran.

**Red-CI PRs:** show the PR URL and the failing check + first error. Offer `gh pr checks <N>`, then fix locally or close. Do not merge a red PR; overrides go through the GitHub UI explicitly.

### 4. Final summary

Each entry carries its source PRD ref (`PRD <feature-num>`) alongside the PR URL or slice ref, so the receipt maps back to the schedule without a second lookup:

```
/morning-review summary
  Reconciled: <R> ledger entries across <D> run(s)
  Walked through: <M> PRs, <H> halted slices, <S> scheduled-no-result
  Merged: <list of PRD <feature-num> → PR URL>
  Re-triaged to ready-for-agent: <list of PRD <feature-num> → slice ref>
  Re-scheduled for tonight: <list of PRD refs>
  Closed (wontfix): <list of PRD <feature-num> → slice ref>
  Left open for later: <list of PRD <feature-num> → PR URL or slice ref>
```

The "left open for later" list is a follow-up surface — come back to it without re-running the whole walk-through.

## Constraints

- **Does not merge automatically.** Every merge is an explicit user action (a `gh pr merge` from the walk-through, or a click in the GitHub UI). The skill orders work; it doesn't authorise it.
- **Does not deploy.** Manual-deploy projects stay manual. Staging walks surface the requirement and prompt; they don't invoke deploy tooling.
- **Reconciles the ledger; doesn't run workers.** `/afk-fanout` writes the manifest + initial entries (via `scripts/write-afk-entry.sh`, the canonical serializer for the initial `claim: scheduled` / `outcome: pending` shape), `/afk-worker` writes per-PRD outcomes — both on `afk-runs`. This skill reads that ledger, **replays** it into canonical `.scratch/` on `main`, and writes back only the `reconciled:` marker. All three must agree on the `afk-runs` `.afk-runs/<date>/` layout and the entry schema (see `/afk-fanout`'s SKILL.md); the initial-entry shape is owned by that script.
- **Not chained automatically.** Runs when the user invokes it — typically the morning after a schedule fires. The loop is: evening `you → /afk-fanout` → overnight `routines → /afk-worker` → morning `you → /morning-review`. Keeping the human in the loop here is the whole point.
