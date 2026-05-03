---
name: tdd-parallel
description: Fan out unblocked sub-tasks of a parent issue into parallel /tdd sessions, each in its own git worktree, displayed side-by-side in a tmux session attached in a new iTerm window. A watcher pane polls for newly-unblocked siblings and auto-spawns them into freed slots. Use when a parent issue has multiple ready-for-agent sub-tasks and the user wants to work on them in parallel. macOS + iTerm only.
disable-model-invocation: true
---

# Parallel TDD

Fan out unblocked sub-tasks of a parent issue into parallel `/tdd` sessions, each in its own git worktree, displayed side-by-side in a tmux session that auto-attaches in a new iTerm window.

## Usage

```
/tdd-parallel <parent-issue> [--max N] [--no-watch]
```

- `<parent-issue>` — the parent issue whose unblocked sub-tasks should be fanned out.
- `--max N` — override the default cap of 2 concurrent in-flight panes (applies to the initial fanout *and* to anything the watcher promotes later).
- `--no-watch` — disable auto-promotion; do a one-shot fanout and exit (matches the pre-watcher behavior — re-invoke `/tdd-parallel` manually after children close to fan out newly-unblocked siblings).

## Process

### 1. Pre-flight

Pre-flight has four phases: validate the environment, auto-clean stale tmux sessions, auto-clean stale worktrees and branches, and sync local `main`. Phase 1a refuses on failure; phases 1b–1d only refuse when there's in-flight work or unsafe state — otherwise they clean up silently and continue.

#### 1a. Environment validation

Refuse with a clear error message if any of these fail. Do **not** auto-fix or retry — surface the error and stop.

- `docs/agents/ship-style.md` exists. Each pane's `/tdd` reads it: in PR-style repos each pane opens its own PR; in direct-push repos each pane pushes its branch and you merge them by hand afterwards. If missing, tell the user to run `/setup-zsl-skills` first.
- `docs/agents/issue-tracker.md` exists. Read the tracker conventions from it.
- `docs/agents/triage-labels.md` exists. Read the `ready-for-agent` label string from it.
- `command -v tmux` succeeds.
- `command -v osascript` succeeds.

Append `.worktrees/` to the repo root `.gitignore` if not already present.

#### 1b. Auto-clean stale tmux session

If `tmux has-session -t tdd-parallel-<parent>` succeeds, decide whether the session is leftover residue (kill it) or active work (refuse):

1. List each pane in the session. Parse the issue number from the pane's working directory: worktree paths follow `.worktrees/<issue-num>-<slug>/`, so the issue number is the leading numeric chunk before the first `-`.
2. For each parsed issue, query the issue tracker (per `docs/agents/issue-tracker.md`) for the issue's state.
3. If **every** pane's issue is CLOSED, the session is finished residue → `tmux kill-session -t tdd-parallel-<parent>` and continue.
4. If **any** pane's issue is still OPEN, refuse with a clear error message naming the open issues — they're still in flight. Tell the user how to attach (`tmux attach -t tdd-parallel-<parent>`) and re-run after they ship.
5. If a pane's working dir doesn't match the `.worktrees/<num>-<slug>/` pattern (e.g. the watcher pane itself, or a pane the user manually opened), or the issue tracker is unreachable for a given issue, treat the state as OPEN — never auto-kill on uncertainty.

#### 1c. Auto-clean stale worktrees and branches

Scan `.worktrees/*`. For each entry whose name matches `<issue-num>-<slug>`:

1. Parse the issue number from the directory name (leading numeric chunk before the first `-`).
2. Query the issue tracker for the issue's state.
3. **Skip** if the issue is OPEN — not ours to remove.
4. **Skip** if `git -C .worktrees/<dir> status --porcelain` is non-empty — uncommitted changes; the agent may have crashed mid-edit and the user should investigate.
5. Otherwise:
   - `git worktree remove .worktrees/<issue-num>-<slug>` (no `--force`)
   - `git branch -d tdd/<issue-num>-<slug>` (no `-D`)
6. If `git branch -d` refuses because the branch isn't fully merged, **skip and log** — never use `-D` automatically. Commits could be lost.

Print a one-block summary: `cleaned: [...issue numbers]`, `skipped — open: [...]`, `skipped — uncommitted: [...]`, `skipped — unmerged branch: [...]`. Do not refuse on any skip; just continue.

#### 1d. Sync local main

The orchestrator's checkout may be behind `origin/main` — direct-push slices land on `origin/main` from worktrees, so this checkout doesn't auto-update. New worktrees inherit from the orchestrator's `HEAD`, so slice N+1 needs slice N's commits visible here.

```bash
git fetch origin
git pull --ff-only origin main
```

If `git pull --ff-only` fails because of local divergence, refuse with a clear error message and stop. Do **not** auto-merge.

### 2. Discover unblocked sub-tasks

Using the conventions from `docs/agents/issue-tracker.md`:

- Fetch the parent issue's sub-issues (GitHub: GraphQL `subIssues`; GitLab: linked issues; local files: directory listing).
- Keep only sub-issues that are:
  - Open
  - Carry the configured `ready-for-agent` label
  - Have every issue referenced in their `## Blocked by` section closed
  - Have **no open sub-issues of their own** (otherwise the candidate is itself a container/PRD, not a leaf unit of work)

Sort ascending by issue number (lowest = oldest).

### 3. Pick the top N

Default cap is 2; override with `--max N`. Print three buckets:

- **Selected** (numbered, will be worked on in parallel): issue number + title + branch name + worktree path.
- **Skipped — over cap**: issue number + title.
- **Skipped — still blocked**: issue number + title + the open `Blocked by` issues still preventing it.
- **Skipped — is a container**: issue number + title + count of open sub-issues (these are tracking issues, not units of work).

Confirm with the user before proceeding.

### 4. Create worktrees

For each selected sub-task, derive:

- **Slug**: kebab-case of the issue title, max 40 chars.
- **Branch**: `tdd/<issue-num>-<slug>`
- **Worktree path**: `.worktrees/<issue-num>-<slug>/`

Create:

```bash
git worktree add .worktrees/<issue-num>-<slug> -b tdd/<issue-num>-<slug>
```

Handle residue from prior runs:

- Worktree dir already exists → reuse it; skip the `git worktree add`.
- Branch exists but no worktree → attach without `-b`: `git worktree add .worktrees/<...> tdd/<issue-num>-<slug>`.

### 5. Set up the tmux session

Single detached session, one horizontal-split pane per sub-task:

```bash
tmux new-session -d -s tdd-parallel-<parent> -n tdd -c .worktrees/<issue-1>-<slug-1>
tmux split-window -h -t tdd-parallel-<parent> -c .worktrees/<issue-2>-<slug-2>
# repeat for each additional pane when --max > 2:
tmux split-window -h -t tdd-parallel-<parent> -c .worktrees/<issue-N>-<slug-N>
tmux select-layout -t tdd-parallel-<parent> tiled

# launch /tdd in each pane (pane indices are 0-based)
tmux send-keys -t tdd-parallel-<parent>.0 'claude "/tdd <issue-1>"' C-m
tmux send-keys -t tdd-parallel-<parent>.1 'claude "/tdd <issue-2>"' C-m
# ... one per pane

# unless --no-watch: add an extra pane for the watcher loop (anchored at repo root, not a worktree)
tmux split-window -h -t tdd-parallel-<parent> -c <repo-root>
tmux select-layout -t tdd-parallel-<parent> tiled
tmux send-keys -t tdd-parallel-<parent>.<watcher-pane-idx> \
  'bash <watcher-script> <parent> <max>' C-m
```

### 6. Run the watcher loop (skip if --no-watch)

The watcher pane runs a bash loop that polls every 60 seconds. On each tick:

1. Re-run the discovery from step 2 (open + `ready-for-agent` + blockers closed + not a container).
2. Skip any issue this watcher has already spawned a pane for in this session — tracked in an in-memory bash array. Failed panes stay visible but are not re-attempted; to retry, kill the watcher and re-invoke `/tdd-parallel`.
3. Count free slots: `<max> - <panes still running claude>`. Detect via `tmux list-panes -F '#{pane_pid} #{pane_current_command}'`; the watcher's own pane doesn't count toward the cap.
4. For each free slot (until candidates run out): create the worktree per step 4, then `tmux split-window` + `tmux send-keys 'claude "/tdd <issue>"' C-m`.
5. Log every poll/spawn/pane-finish event as a one-line entry to the watcher pane.
6. Fire a macOS notification (`osascript -e 'display notification ...'`) on each spawn and on watcher exit.
7. Exit the loop when no `ready-for-agent` open sub-issues remain **and** no `/tdd` panes are in flight. Print a final line: *"All sub-tasks complete. Kill this session with: `tmux kill-session -t tdd-parallel-<parent>`"*. Notify and exit.

The watcher pane stays visible after exit — do not kill the session or the pane automatically.

If the parent issue itself is closed mid-watch, treat that as the exit condition.

### 7. Spawn iTerm pre-attached

```bash
osascript <<EOF
tell application "iTerm"
  create window with default profile
  tell current session of current window
    write text "tmux attach -t tdd-parallel-<parent>"
  end tell
end tell
EOF
```

If the `osascript` call fails (iTerm not installed), print the manual attach command:

```
Detached tmux session 'tdd-parallel-<parent>' created with N panes.
Attach with: tmux attach -t tdd-parallel-<parent>
```

### 8. Done

Print a summary:

- Parent issue.
- Selected sub-tasks (numbers, branches, worktree paths).
- Skipped sub-tasks (with reasons).
- tmux session name.
- Whether the watcher is running (or `--no-watch` was passed).

Note: the orchestrator Claude session can be closed safely — the tmux server runs independently and the parallel `/tdd` work continues. The watcher pane keeps polling for newly-unblocked siblings; with `--no-watch`, re-invoke `/tdd-parallel` manually after children close.

## Cleanup

Not automated. After each PR merges:

- `git worktree remove .worktrees/<issue-num>-<slug>`
- `git branch -d tdd/<issue-num>-<slug>` (force with `-D` only if upstream branch was force-pushed)
- `tmux kill-session -t tdd-parallel-<parent>` once the last pane is done

The watcher exits itself once all sub-tasks are complete and no panes are in flight — you only need to `tmux kill-session` when you're done inspecting.
