# Per-repo setup

Run `/zsl:setup-zsl-superpowers` in any repo where you want to use these skills. It will:

- Ask which **issue tracker** you use (GitHub, GitLab, or local markdown files).
- Ask which **labels** you apply when triaging issues (`/zsl:triage` uses these).
- Ask where to save the **per-repo docs** the skills consume.
- Ask which **ship style** the repo follows (PR or direct push).

The output lands in `AGENTS.md` (or `CLAUDE.md`), `docs/agents/`, and (for PR-style repos) the project board mapping at `docs/agents/project-board.md`.

## Why this exists

The engineering skills in this plugin make assumptions about your repo's setup — *which issue tracker, what label vocabulary, where domain docs live, how you ship*. Rather than hard-code one opinion, `setup-zsl-superpowers` writes a small per-repo config that the other skills read.

`/zsl:to-issues`, `/zsl:to-prd`, `/zsl:triage`, `/zsl:diagnose`, `/zsl:tdd`, `/zsl:improve-codebase-architecture`, and `/zsl:zoom-out` all consume this config. If they appear to be missing context (don't know which tracker to use, can't find the right labels), it's because setup hasn't run.

## Two backends

**GitHub project dashboard** — state lives as labels on each issue and is mirrored to the project board's `Status` field via the mapping in `docs/agents/project-board.md`. `/zsl:triage` updates both. Closure is automatic via GitHub's PR-merge → issue-close behaviour.

**Local markdown files** — state lives as a `Status:` line near the top of each `.md` file under `.scratch/<feature-slug>/`. Closure is folder-based: move issue files to `.scratch/<feature-slug>/issues/done/` when complete, and the whole feature folder to `.scratch/done/<feature-slug>/` when shipped. Nothing is deleted; the archive records why each issue closed.

## When to re-run

Re-run `setup-zsl-superpowers` if:

- You change issue trackers (e.g. moved from local markdown to GitHub).
- You change your label vocabulary.
- The skills start asking questions that the config should already answer.
