# CONTEXT.md Format

`CONTEXT.md` is the Bounded Context's **Ubiquitous Language** — the canonical glossary of terms that carry specific meaning inside this part of the system. The format follows the Bounded Context / Ubiquitous Language discipline from *Domain-Driven Design Distilled* (bundled into this skill's rules in [SKILL.md](SKILL.md)).

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Order**:
{A concise description of the term}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account

## Relationships

- An **Order** produces one or more **Invoices**
- An **Invoice** belongs to exactly one **Customer**

## Example dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed."

## Flagged ambiguities

- "account" was used to mean both **Customer** and **User** — resolved: these are distinct concepts.
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others as aliases to avoid.
- **Flag conflicts explicitly.** If a term is used ambiguously, call it out in "Flagged ambiguities" with a clear resolution.
- **Keep definitions tight.** One sentence max. Define what it IS, not what it does.
- **Show relationships.** Use bold term names and express cardinality where obvious.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.
- **Write an example dialogue.** A conversation between a dev and a domain expert that demonstrates how the terms interact naturally and clarifies boundaries between related concepts.

## Single vs multi-context repos

**Single context (most repos):** One `CONTEXT.md` at the repo root.

**Multiple contexts:** A `CONTEXT-MAP.md` at the repo root lists the contexts, where they live, and how they relate to each other:

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md) — generates invoices and processes payments
- [Fulfillment](./src/fulfillment/CONTEXT.md) — manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment** *(Published Language)*: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
- **Fulfillment → Billing** *(Published Language)*: Fulfillment emits `ShipmentDispatched` events; Billing consumes them to generate invoices
- **Ordering ↔ Billing** *(Shared Kernel)*: Shared types for `CustomerId` and `Money`
```

The skill infers which structure applies:

- If `CONTEXT-MAP.md` exists, read it to find contexts
- If only a root `CONTEXT.md` exists, single context
- If neither exists, create a root `CONTEXT.md` lazily when the first term is resolved

When multiple contexts exist, infer which one the current topic relates to. If unclear, ask.

## Context relationship types

When `CONTEXT-MAP.md` describes how contexts relate, tag each relationship with its type — each carries different ownership and translation duties. Types come from *Domain-Driven Design Distilled* (bundled in [SKILL.md](SKILL.md)):

- **Partnership** — two contexts succeed or fail together; teams coordinate closely on schedules and changes.
- **Shared Kernel** — a small, jointly-owned overlap of code (often value objects or events). Costly to maintain; only justified when the overlap is small and stable.
- **Customer / Supplier** — upstream context (Supplier) provides; downstream (Customer) consumes. Downstream has negotiating leverage.
- **Conformist** — downstream accepts whatever shape upstream gives, with no translation. Cheap, but every upstream change ripples.
- **Anticorruption Layer (ACL)** — downstream translates the upstream's model into its own language. Insulates the local model from foreign concepts; expensive but protective.
- **Open Host Service (OHS)** — upstream exposes a stable, documented protocol designed for many consumers (vs. one-off integration).
- **Published Language** — upstream publishes a shared schema or event format (often paired with OHS).
- **Separate Ways** — contexts deliberately don't integrate; users bridge them by hand or data is duplicated.
- **Big Ball of Mud (contained)** — the legacy mess is its own context; nothing else inherits from it. Containment is the goal.

Naming the type makes implementation expectations obvious: an *Anticorruption Layer* implies real translation code at the boundary; *Conformist* implies you'll feel every upstream change; *Shared Kernel* implies joint governance.
