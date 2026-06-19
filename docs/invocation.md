# Skill invocation model

Every skill in the plugin is one of two kinds. The distinction is small but
load-bearing: it decides whether a skill can fire on its own, and how lightly it
has to be wired across the repo's parallel surfaces.

## User-invoked vs model-invoked

| Kind | Fires when | Frontmatter |
|---|---|---|
| **User-invoked** | Only when the user types it (`/zsl:<name>`). Never auto-fires. These are the *orchestrators* — they drive a whole workflow and would be disruptive if they triggered on their own. | `disable-model-invocation: true` |
| **Model-invoked** | When the user types it **or** when Claude Code matches the task against its trigger phrases. The default for a skill that holds reusable knowledge or a self-contained step. | *(no flag)* |

A model-invoked skill is the normal case; the flag is the exception you add to a
pure orchestrator so it stays quiet until summoned.

## The composition rule

> **A user-invoked skill may invoke model-invoked skills, but never another
> user-invoked skill.**

User-invoked skills sit at the top of the call graph — one per session, started
by a human. Model-invoked skills are the shared primitives they compose. Letting
one orchestrator call another would create ambiguous, re-entrant control flow
(which one "owns" the session?) and duplicate the human's single point of entry.

So when an orchestrator needs shared behaviour, it reaches for a model-invoked
skill, not a sibling orchestrator. For example `decision-mapping` (user-invoked)
composes the model-invoked primitives `grilling` and `domain-modeling`
directly — it must **not** call `grill-with-docs`, which is itself user-invoked.

## Why this exists

Two payoffs:

- **Predictable orchestrators.** Flagging `commit`, `commit-push-pr`,
  `afk-fanout`, `tdd-parallel` and the other pure orchestrators with
  `disable-model-invocation: true` guarantees they only run when typed — no
  surprise auto-fire mid-task.
- **Deduplicated knowledge.** Shared reference material (the deep-module
  vocabulary, the ADR/CONTEXT formats, the grilling loop) lives in *one*
  model-invoked skill (`codebase-design`, `domain-modeling`, `grilling`) that
  other skills compose instead of copy. The guidance stops drifting across
  surfaces.

## Lighter sync for model-invoked-only skills

Because users don't pick model-invoked-only skills off a list, they get a
lighter treatment in the [skill-sync contract](architecture.md#keeping-the-catalogue-in-sync):
they are registered in `plugin.json` and documented under a **Shared /
model-invoked** subsection of the [Skills overview](skills/index.md), but they
are **omitted** from the "Which skill do I want?" decision tree and the
user-command lists. See `CLAUDE.md` for the full sync lane.

The decision is recorded in
[ADR 0001](https://github.com/ZunoSmartLabs/zsl-superpowers/blob/main/docs/adr/0001-user-invoked-model-invoked-taxonomy.md).
