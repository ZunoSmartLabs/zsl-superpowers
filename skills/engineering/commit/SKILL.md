---
name: commit
description: Plan and create git commits autonomously for changes made in this session (no per-commit approval prompt). Cross-session dirty files — files modified outside this conversation's tool calls — get confirmed before inclusion. Explicit file lists only, never `git add -A`. No Claude attribution lines. Use when the user wants to commit, says "/commit", or asks to land changes — and composable by any skill that needs to land changes (e.g. commit-push-pr, tdd-parallel).
---

# Commit Changes

Fully autonomous for changes made in this session. Whoever summoned this skill — the user typing `/commit`, or another skill composing it as its commit step — *that* is the approval. Don't pause to ask "Shall I proceed?"

The only legitimate reason to stop and ask is **cross-session ambiguity**: dirty files in the tree that this conversation didn't produce.

```mermaid
flowchart TB
    git["git status<br/>(every dirty + untracked file)"] --> q{"did this conversation<br/>touch the file?"}
    q -->|"yes — Edit/Write/Bash<br/>in this session"| session["**Session bucket**<br/>auto-included"]:::good
    q -->|"no — already dirty<br/>or external write"| other["**Other-origin bucket**<br/>confirm before including"]:::warn
    q -->|"unsure"| other
    session --> stage["explicit `git add &lt;path&gt;`<br/>(never `-A`)"]
    other --> stage
    stage --> rails{"safety rails"}
    rails -->|".env* · *.pem ·<br/>credentials · >10MB"| skip["skipped<br/>(reported in summary)"]:::bad
    rails -->|"clean"| route{"touches code?<br/>(SKILL.md · scripts ·<br/>plugin.json · mkdocs.yml)"}
    route -->|"yes — any code file<br/>(mixed counts)"| branch["create feature branch<br/>(feature/ fix/ chore/…)"]:::warn
    route -->|"no — only docs/**<br/>or .scratch/**"| onmain["stay on `main`"]:::good
    branch --> commit["`git commit`<br/>no Claude attribution"]:::good
    onmain --> commit

    classDef good fill:#dcfce7,stroke:#16a34a;
    classDef warn fill:#fef3c7,stroke:#d97706;
    classDef bad fill:#fee2e2,stroke:#dc2626;
```

## Process

1. **Classify the dirty tree.**
   - Run `git status` to list every dirty and untracked file.
   - For each, decide which bucket it falls into:
     - **Session changes** — files this conversation modified via `Edit`, `Write`, `NotebookEdit`, or files you created/modified through `Bash` commands you ran. You have the full conversation history; you know what you touched.
     - **Other-origin changes** — files that were already dirty when the session started, or modified by something outside your tool calls (the user editing in another window, a build process, a pre-commit hook, a sibling agent).
   - When in doubt, classify as other-origin — better to confirm than to over-include.

2. **Confirm the other-origin bucket (only if non-empty).**
   - Show the list, one line per file: `<path> — <one-line note on what kind of change, if known>`.
   - Ask once: *"These files are dirty but I didn't touch them this session. Include in the commit, leave them out, or stage them as a separate commit?"*
   - Default to "leave them out" if the user is uncertain — they can always re-run `/commit` after staging by hand.
   - If the bucket is empty, skip this step entirely.

3. **Plan the commit(s).**
   - Group session changes into **one logical commit by default**. Always include all the session's code changes — don't ask which subset to land. Split into multiple commits only when the diff genuinely covers two unrelated concerns (e.g. a feature change plus a doc typo that crept in).
   - Draft a clear, imperative commit message focused on *why*, not what. Multi-line if there's substance worth recording; one line for a small change. Match the repo's existing commit-message style (check `git log --oneline -n 20` if unsure).

4. **Route to the right branch** *(PR-ship-style repos only — `docs/agents/ship-style.md`; trunk-style repos commit everything to `main`).*
   - **Docs- or scratch-only commit → `main`.** If every file in the commit is documentation (`docs/**`, narrative markdown like `README.md` / `CLAUDE.md` / `docs/changelog.md`) or lives under `.scratch/`, commit it directly on `main`. These are low-risk, board/tracker, and prose changes — a branch-and-PR round-trip buys nothing.
   - **Any code → a feature branch.** If the commit touches even one code file, the **whole** commit goes on a branch — never split a mixed docs+code commit. Code means source and scripts (`*.py`, `*.sh`, `*.ts`, …), the skill definitions themselves (`**/SKILL.md` and their bundled assets), and the sync/build manifests (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `mkdocs.yml`, `Makefile`). The distinction is *what the file is*, not its extension — a `SKILL.md` is code here, a `docs/**` markdown page is not.
   - When a branch is required and you're on `main`, **create it yourself** — don't stop to ask — with the prefix convention (`feature/` `fix/` `chore/` `refactor/` `env/`, per /zsl:git-branch), then switch to it and commit. If you're already on a non-default branch, just commit there.

5. **Execute.**
   - `git add <file1> <file2> …` — explicit paths only. **Never `git add -A`, `git add .`, or any wildcard form** that could sweep in untracked files you didn't intend.
   - `git commit -m "<message>"` — use a heredoc for multi-line messages.
   - `git log --oneline -n <count>` to verify.

6. **Report.** One short line per commit: sha + subject — and the branch it landed on when that wasn't `main`. Done.

## Safety rails (override autonomy)

These checks fire automatically and **do not** count as "confirmation prompts" — they protect the commit, they don't ask permission:

- **Refuse to stage** `.env*`, `*credentials*`, `*secret*`, `*.pem`, `*.key`, files matching any pattern in `.gitignore` that somehow got dirty, and large binaries (>10 MB). Surface them in the final report as "skipped for safety" with a one-line reason each.
- **Pre-commit hook failure** — fix the underlying issue and create a **new** commit. Never use `--no-verify`; never `git commit --amend` after a failed hook (the previous commit may not have been created at all, so amend would modify the wrong target).
- **Code never lands on `main` (PR-ship-style repos)** — a commit that touches code is rerouted to a feature branch by Step 4, not refused: the skill creates the branch itself and commits there. Only documentation (`docs/**`, narrative `*.md`) and `.scratch/` changes commit straight to `main`. A mixed docs+code commit counts as code and goes to the branch whole.

## Important

- **No co-author lines, no Claude attribution.** Commits should read as if the user wrote them. No `Co-Authored-By:`, no "🤖 Generated with…", no trailer of any kind beyond what the repo's own commit convention requires.
- **No `git add -A`.** Ever. Explicit file lists are how we prevent unrelated dirt from sneaking into a commit.
- **Autonomous means autonomous.** Don't draft a plan and ask "Shall I proceed?" — just execute. The user already said yes when they typed `/commit`.

## Why this shape

- **Autonomous for session changes** because `/commit` is invoked after work the user already knows about. Re-confirming each commit was friction without value.
- **Confirm for other-origin changes** because the conversation history can't account for them — they're a genuine signal of ambiguity, the one case where stopping is the right call.
- **Never `-A`** because the cost of a bad surprise (committing `.env` or a stash file) is far higher than the cost of typing a few paths.
- **Docs to `main`, code to a branch** because the two carry different risk. Prose and tracker edits are cheap to land and cheap to revert, so a PR round-trip is pure friction; code changes behaviour and deserves review, so they always get a branch (and a mixed commit is code). The skill makes that call and creates the branch itself — the opinion is enforced, not negotiated each time.
