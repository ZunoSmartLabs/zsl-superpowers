---
name: tdd-parallel
description: Fan out unblocked sub-tasks of a parent issue into parallel /tdd sessions, each in its own git worktree, displayed side-by-side in a tmux session attached in a new iTerm window. Use when a parent issue has multiple ready-for-agent sub-tasks with no open blockers and the user wants to work on more than one at once. macOS + iTerm only.
disable-model-invocation: true
---

# Parallel TDD

Fan out unblocked sub-tasks of a parent issue into parallel `/tdd` sessions, each in its own git worktree, displayed side-by-side in a tmux session that auto-attaches in a new iTerm window.

## Usage

```
/tdd-parallel <parent-issue> [--max N]
```

- `<parent-issue>` — the parent issue whose unblocked sub-tasks should be fanned out.
- `--max N` — override the default cap of 2 worktrees.

## Process

### 1. Pre-flight checks

Refuse with a clear error message if any of these fail. Do **not** auto-fix or retry — surface the error and stop.

- `docs/agents/ship-style.md` exists. Each pane's `/tdd` reads it: in PR-style repos each pane opens its own PR; in direct-push repos each pane pushes its branch and you merge them by hand afterwards. If missing, tell the user to run `/setup-zsl-skills` first.
- `docs/agents/issue-tracker.md` exists. Read the tracker conventions from it.
- `docs/agents/triage-labels.md` exists. Read the `ready-for-agent` label string from it.
- `command -v tmux` succeeds.
- `command -v osascript` succeeds.
- `tmux has-session -t tdd-parallel-<parent>` returns non-zero. If a session already exists, tell the user to `tmux kill-session -t tdd-parallel-<parent>` and re-run — do not auto-kill (in-flight work would be lost).

Append `.worktrees/` to the repo root `.gitignore` if not already present.

### 2. Discover unblocked sub-tasks

Using the conventions from `docs/agents/issue-tracker.md`:

- Fetch the parent issue's sub-issues (GitHub: GraphQL `subIssues`; GitLab: linked issues; local files: directory listing).
- Keep only sub-issues that are:
  - Open
  - Carry the configured `ready-for-agent` label
  - Have every issue referenced in their `## Blocked by` section closed

Sort ascending by issue number (lowest = oldest).

### 3. Pick the top N

Default cap is 2; override with `--max N`. Print three buckets:

- **Selected** (numbered, will be worked on in parallel): issue number + title + branch name + worktree path.
- **Skipped — over cap**: issue number + title.
- **Skipped — still blocked**: issue number + title + the open `Blocked by` issues still preventing it.

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
```

### 6. Spawn iTerm pre-attached

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

### 7. Done

Print a summary:

- Parent issue.
- Selected sub-tasks (numbers, branches, worktree paths).
- Skipped sub-tasks (with reasons).
- tmux session name.

Note: the orchestrator Claude session can be closed safely — the tmux server runs independently and the parallel `/tdd` work continues.

## Cleanup

Not automated. After each PR merges:

- `git worktree remove .worktrees/<issue-num>-<slug>`
- `git branch -d tdd/<issue-num>-<slug>` (force with `-D` only if upstream branch was force-pushed)
- `tmux kill-session -t tdd-parallel-<parent>` once the last pane is done
