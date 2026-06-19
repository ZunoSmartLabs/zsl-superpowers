---
name: decision-mapping
description: Turn a loose, multi-session idea into a sequenced map of the decisions and tickets it implies, so it matures before becoming a PRD. Use at the front of the loop when an idea is still fuzzy, spans several sessions, or you want to see the decision dependencies and a rough build order before committing to a PRD.
disable-model-invocation: true
---

# Decision Mapping

The front-of-loop skill for an idea that isn't a PRD yet. You have a loose,
possibly multi-session idea; before committing to a PRD you want to see the shape
of it — the decisions it forces, how they depend on each other, and a rough
sequence of the work it implies. Decision mapping produces that **map**: a living
document of decisions (open, leaning, settled) and the ticket-sized slices that
fall out of them, in dependency order.

This is **user-invoked only** (`disable-model-invocation: true`) — it's a
deliberate planning act, not something to auto-fire.

## What it composes

Decision mapping is thin glue over the shared model-invoked primitives — it
doesn't reimplement them:

- **[`grilling`](../../productivity/grilling/SKILL.md)** — drives the interview that
  surfaces each decision. Walk the decision tree one branch at a time, recording
  what's open, what you're leaning toward, and what's settled.
- **[`domain-modeling`](../domain-modeling/SKILL.md)** — when the idea introduces
  domain terms or bounded-context questions, reach for the `CONTEXT.md` and ADR
  formats and the DDD reasoning here. (Don't author `CONTEXT.md` from a half-formed
  idea — note the term and let it firm up.)
- **`/prototype`** — when a decision hinges on something you can only learn by
  building (a data-model shape, a state machine, a UI feel), spin a throwaway
  prototype to settle it, then fold the answer back into the map.

When the map is mature — decisions settled enough, slices sequenced — hand off to
**`/to-prd`** to synthesise it into a PRD on the tracker. Decision mapping matures
the idea; `to-prd` packages it; `/to-issues` then slices the PRD.

> **Taxonomy note.** Decision mapping composes the *model-invoked* primitives
> (`grilling`, `domain-modeling`) directly and never invokes another *user-invoked*
> skill — that's the repo's invocation rule. The grilling *engine* (`grilling`) is
> shared and composable; the user-invoked doc-writing grilling orchestrator is not,
> so decision mapping reaches for `grilling` itself.

## Where the map lives

Write the map to **`.scratch/decision-maps/<slug>.md`**, matching this repo's
state convention (the same `.scratch/` tree the issue tracker uses). A map is a
working artefact that survives across sessions: you can leave it half-resolved,
come back, and pick up where the decision tree left off. One file per idea; name it
after the idea's slug.

A map typically holds:

- **The idea** in a sentence or two — what you're trying to do and why.
- **Decisions** — each with a status (`open` / `leaning: <option>` / `settled:
  <option> — <one-line why>`) and its dependencies on other decisions.
- **Slices** — the ticket-sized pieces the settled decisions imply, in dependency
  order (the rough wave plan `/to-issues` will later formalise).
- **Open questions** — what still needs a prototype, a spike, or a conversation.

## Explicit non-goals

- **Not AFK-wired.** Decision mapping is a **local, interactive** skill. It is *not*
  part of the `/afk-fanout` → `/afk-worker` overnight loop, and wiring its maps into
  that remote pipeline is an explicit non-goal — maturing a fuzzy idea needs a human
  in the loop, not an unattended remote session. (If a future investigation changes
  that, it's a separate piece of work.)
- **Not a PRD.** The map is pre-PRD scaffolding. It stays in `.scratch/decision-maps/`
  and is never itself published to the tracker — `/to-prd` produces the tracked PRD.
- **Not a CONTEXT.md author.** It reaches for `domain-modeling` to *reason* about
  domain terms, but it doesn't commit `CONTEXT.md` entries from a half-formed idea.
