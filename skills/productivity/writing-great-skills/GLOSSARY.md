# Skill-authoring glossary

The shared vocabulary for talking about skills. Use these terms exactly so a
skill's design can be discussed without ambiguity.

**Skill**
A unit of packaged expertise: a `SKILL.md` plus any bundled resources, loaded
into the agent's context when its trigger matches. Scale-agnostic — a skill can
be a one-screen reference or a multi-file workflow.

**Frontmatter**
The YAML block at the top of `SKILL.md`. Carries `name`, `description`, and
optional flags (`disable-model-invocation`). It is metadata the harness reads —
not body content.

**Description**
The single `description:` field. **The only thing the agent sees when deciding
whether to load the skill** — it is surfaced in the system prompt alongside every
other skill's description. Hard-capped at 1024 characters (see the deterministic
gate in `SKILL.md`).

**Trigger**
The "Use when …" clause of the description. The phrases, keywords, file types,
and contexts that should cause the skill to fire. A description without a sharp
trigger is a skill that never activates — or activates for the wrong prompts.

**Progressive disclosure**
The core design principle: `SKILL.md` stays small and loads first; heavier detail
lives in sibling files (`REFERENCE.md`, `GLOSSARY.md`, `EXAMPLES.md`) linked one
level deep and read only when needed. Keeps context cost low until depth is
actually required.

**Body**
Everything after the frontmatter. The instructions, process, and examples the
agent follows once the skill is loaded. Body length is runtime context cost —
keep it tight; push long-form material to linked files.

**Bundled resource**
A file shipped inside the skill directory — a reference doc, a template, or a
script. Travels with the skill through every distribution path.

**Deterministic gate**
A *secretly-deterministic* step (one with exactly one correct answer — a length
cap, a clean-tree check, a fixed serialization) delegated to a small bundled
script behind a callout, with a prose **Fallback** for when the script can't be
resolved. The description-length check is the canonical example.

**User-invoked / model-invoked**
The two invocation kinds. **User-invoked** skills (`disable-model-invocation:
true`) only run when typed — the orchestrators. **Model-invoked** skills can also
auto-fire when the task matches their trigger. See the project's invocation
model.

**Shallow vs deep description**
A *shallow* description restates the name ("Helps with documents."). A *deep*
description gives the agent enough to distinguish this skill from its neighbours:
what it does, then precisely when to reach for it.
