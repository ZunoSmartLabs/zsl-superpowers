---
name: grill-with-docs
description: Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates documentation (CONTEXT.md, ADRs) inline as decisions crystallise. Use when user wants to stress-test a plan against their project's language and documented decisions.
disable-model-invocation: true
---

<what-to-do>

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

## Design tree

Before the first question, print the design tree you intend to traverse — the decisions and sub-decisions you've identified, with a status marker on each:

- `[ ]` unresolved
- `[→]` currently being grilled
- `[✓]` resolved

Example:

```
Design tree
├── [→] Auth strategy
│   ├── [ ] Session storage (cookie vs JWT)
│   └── [ ] Refresh-token rotation
├── [ ] Persistence layer
│   ├── [ ] Primary store
│   └── [ ] Migration path from current schema
└── [ ] Rollout
    ├── [ ] Feature-flag gate
    └── [ ] Backfill plan
```

Reprint the tree whenever it changes: a node is resolved, a new branch is discovered, the focus moves to a new node, or scope shifts. Don't reprint between every question — only when the shape or status actually changes. Always reprint the full tree, not a diff, so progress is visible at a glance.

</what-to-do>

<supporting-info>

## Domain awareness

During codebase exploration, also look for existing documentation:

### File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

Don't couple `CONTEXT.md` to implementation details. Only include terms that are meaningful to domain experts.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).

</supporting-info>

<!-- BEGIN bundled-book-rules -->

## Bundled book rules

Do not hand-edit content between the `BEGIN`/`END` markers — `scripts/sync_book_rules.py` overwrites it from `vendor/agent-rules-books/`.

### Rules from "Domain-Driven Design Distilled" by Vaughn Vernon

<!-- BEGIN domain-driven-design-distilled.mini.md v0.5 -->

# OBEY Domain-Driven Design Distilled by Vaughn Vernon

## When to use

Use when business software has enough domain complexity, language ambiguity, strategic differentiation, or integration risk that modeling changes implementation decisions, but the project still needs the smallest effective DDD practice rather than ceremony.

## Primary bias to correct

Use DDD selectively, but seriously. Start from business capability, subdomain importance, bounded context, and local language before tactical patterns, frameworks, persistence, APIs, or class shapes.

## Decision rules

- Before designing code, identify the business capability, classify the subdomain as Core, Supporting, or Generic, define the Bounded Context, use its Ubiquitous Language, and choose only tactical patterns that earn their cost.
- Put the most modeling effort into the Core Domain. Keep Supporting and Generic Subdomains simpler unless their own complexity proves otherwise.
- Do not apply full tactical DDD to simple CRUD, generic subsystems, or mainly technical problems; strengthen the model only when invariants, lifecycle, language complexity, or integration risk justify it.
- Give every meaningful model one explicit Bounded Context. The context owns its language, rules, semantics, code structure, tests, and integration contracts.
- Treat the same word in different contexts as potentially different concepts. Translate at context boundaries instead of sharing domain classes or leaking foreign language into the local model.
- Choose context relationships deliberately: Partnership, Shared Kernel, Customer/Supplier, Conformist, Anticorruption Layer, Open Host Service, Published Language, Separate Ways, or Big Ball of Mud containment all imply different ownership and translation duties.
- Select integration style from business coupling and failure semantics: RPC requires acceptable request/response coupling; REST resources must not expose Aggregate internals; messaging must tolerate lag, duplicates, and ordering limits.
- Keep integration contracts separate from internal models and test translations wherever meanings cross a boundary.
- Use local domain terms in code, tests, Commands, Domain Events, APIs, and conversations. One concept gets one term, one term does not carry multiple meanings inside a context, and code is renamed when understanding improves.
- Use Entities when identity and lifecycle matter; make identity explicit and protect meaningful state transitions rather than exposing unrestricted setters.
- Use immutable, self-validating Value Objects when primitives hide domain meaning.
- Use Aggregates only as invariant and transactional consistency boundaries. Keep them small, modify through the root, reference other Aggregates by identity, avoid large object graphs, and usually change one Aggregate per transaction.
- Use Domain Events for meaningful past-tense business facts that clarify collaboration or integration; do not publish noisy field-change events.
- Application Services coordinate use cases by loading Aggregates, invoking domain behavior, saving results, and triggering integration work. They must not become the real domain model.
- Keep frameworks, persistence mechanics, transport formats, REST representations, and infrastructure types out of the domain model. Translate external data at the boundary and persist Aggregates without letting storage define the model.
- Prefer code that teaches the model: make domain assumptions explicit in names, tests, and events; expose richer concepts instead of hiding meaning behind flags, status codes, booleans, enums, helpers, or utilities.
- Use Event Storming, scenarios, acceptance tests, modeling spikes, and domain-expert walkthroughs when workflow, terminology, policies, or acceptance criteria are unclear. Timebox modeling and track modeling debt instead of drifting into detached analysis.
- Estimate and plan DDD work from modeling uncertainty, integration risk, implementation cost, team skill, and access to domain experts, not only from feature count.

## Trigger rules

- When language is fuzzy, generic, overloaded, or imported from another context, pause coding and sharpen the local Ubiquitous Language.
- When the core concern drifts, terms stop matching code, or supporting complexity hides the core, reassess subdomains, boundaries, and modeling investment.
- When one model spreads across billing, identity, catalog, fulfillment, support, permissions, or other separate concerns, split or translate instead of reusing shared domain classes.
- When an upstream model, schema, UI, framework, API payload, transport object, or database shape starts defining the domain model, restore boundary translation.
- When using Shared Kernel, require small stable overlap, joint ownership, and tests; without governance, choose another relationship.
- When calling something an Anticorruption Layer, verify that real translation exists.
- When a request wants to load and mutate a large graph or several Aggregate roots, revisit the invariant boundary and ask whether eventual consistency is acceptable.
- When controllers, helpers, services, or transport-shaped application services contain business decisions, move behavior into the domain model or name the missing concept.
- When a Domain Event is command-like, vague, trivial, or emitted for every field change, redesign it as a specific business fact or remove it.
- When a concept is represented as a primitive, flag, status code, enum, or boolean but carries domain rules, promote it to a richer concept or Value Object.
- When delivery pressure tempts the team to skip design, use a short modeling spike, scenario, or acceptance test and record known modeling debt.

## Final checklist

- Correct subdomain and Core Domain investment?
- Explicit Bounded Context and relationship to neighboring contexts?
- Ubiquitous Language visible in code, tests, Commands, Events, APIs, and conversations?
- Translation tested where external or foreign meanings cross boundaries?
- Tactical patterns used only where they clarify meaning or protect invariants?
- Aggregates small, root-protected, identity-referenced, and not graph-shaped?
- Application Services coordinating rather than owning business logic?
- Infrastructure, persistence, REST, and transport details kept out of the domain model?
- Modeling discoveries, acceptance tests, expert input, and modeling debt captured before shipping?

<!-- END domain-driven-design-distilled.mini.md -->

### Rules from "Implementing Domain-Driven Design" by Vaughn Vernon

<!-- BEGIN implementing-domain-driven-design.mini.md v0.5 -->

# OBEY Implementing Domain-Driven Design by Vaughn Vernon

## When to use

Use when DDD implementation choices affect bounded contexts, language, aggregates, repositories, events, application services, package structure, or cross-context integration.

## Primary bias to correct

Practical DDD is not renamed CRUD. Model the operational domain inside an explicit Bounded Context, with local language, small invariant boundaries, identity references across Aggregates, and explicit translation across context and infrastructure boundaries.

## Decision rules

- Name the Bounded Context before interpreting terms, modules, services, repositories, events, APIs, persistence, or integrations; never force one global company model.
- Use the local Ubiquitous Language consistently: one concept gets one term inside the context, one term must not carry multiple meanings, and code, tests, events, commands, repositories, services, and packages must speak that language.
- Protect the Core Domain from generic abstractions and vendor terms; spend richer modeling where competitive or operational complexity lives, keep supporting subdomains simpler, and avoid DDD ceremony for trivial CRUD.
- Make every context interaction explicit: show the relationship, translation responsibility, and upstream/downstream influence before sharing data, terms, models, or integration code.
- Translate foreign, legacy, partner, external, and infrastructure models into the local language; keep foreign schemas, statuses, contract models, and aggregates out of local domain objects.
- Treat Aggregates as immediate consistency boundaries: keep them small, expose one root, route invariant-changing behavior through the root, hide mutable internals, and expose intention-revealing behavior instead of arbitrary setters.
- Reference other Aggregates by identity, avoid large connected object graphs, and default to one Aggregate per transaction; use events, policies, or process coordination when consistency can be eventual.
- Use Entities when identity and lifecycle matter, and make their methods protect meaningful state transitions rather than generic state changes.
- Use immutable Value Objects for meaningful descriptive concepts; validate at construction, compare by value, and replace raw primitives for meaningful identifiers, quantities, ranges, names, and whole values.
- Use Domain Services only for domain-significant operations that require multiple domain objects and fit no Entity or Value Object; keep technical transformation, serialization, transport, and persistence mapping outside the domain model.
- Provide Repositories for Aggregate Roots, not tables; define interfaces by domain or application needs, return domain objects or domain-oriented results, and keep business rules out of repository implementations.
- Publish Domain Events only for meaningful completed business facts; name them in the past tense, keep payloads local to the model, and do not use events for every property change or to hide poor Aggregate design.
- Use Event Sourcing only when the event sequence is the right persistence model; streams must match Aggregate identity and versioning, replay must be deterministic, and event meaning changes need versioning, upcasters, or translators.
- Keep Application Services as use-case coordinators: load Aggregates, invoke domain behavior, persist results, publish resulting events, own transaction or integration coordination, and keep core decisions in the domain model.
- Organize modules by Bounded Context first and by domain or use-case ownership within the context; avoid giant `shared` or `common` packages for domain concepts.
- Use DTOs, projections, use-case queries, rendition adapters, or mediators when client needs differ from Aggregate shape; expose application-facing representations rather than aggregate internals.
- Keep command behavior separate from query models when consistency, performance, or representation needs justify it, and keep scope identifiers explicit where context or ownership affects invariants or access.
- When generating code, walk the model in order: context, language terms, tactical type, conservative Aggregate boundary, identity references, local invariants, Aggregate-oriented repositories, use-case services, and boundary translations.
- Test domain behavior and boundaries directly: Aggregate invariants, valid and invalid state transitions, Value Object validation, Domain Events as outcomes, repositories as infrastructure, translation layers, and application-service orchestration.

## Trigger rules

- When a term is ambiguous, reused across contexts, or drifting into a technical placeholder, qualify, split, or rename it before coding further.
- When code wants to import another context's domain package, share enums across contexts, or couple through another context's database, add explicit translation instead.
- When legacy, vendor, partner, API, transport, persistence, or UI shape appears in local domain code, add an Anticorruption Layer or mapping boundary before modeling locally.
- When an Aggregate boundary changes or one transaction wants multiple Aggregates, list the immediate invariants that require it; otherwise coordinate by identity, Domain Events, policies, processes, or Application Services.
- When external code mutates Aggregate internals or reads internals to decide state changes, move the operation behind root behavior.
- When a Repository becomes generic CRUD, table-shaped, row-returning, or starts enforcing business rules, reshape it around Aggregate access and move rules back to the model.
- When an event reads like a command, exposes framework or persistence artifacts, or describes a minor property change, rename, narrow, or remove it.
- When Application Services or controllers accumulate branching business rules, move the decision into the Entity, Value Object, Aggregate, or Domain Service that owns the concept.
- When client rendering, query speed, or representation needs pressure the model shape, use projections, DTOs, use-case queries, or adapters instead of enlarging or exposing Aggregates.
- When a subdomain is simple CRUD, keep it simple; when invariants and lifecycle complexity appear, model them honestly instead of hiding them in services.

## Final checklist

- Is the Bounded Context explicit before interpreting names, modules, events, repositories, APIs, persistence, or integrations?
- Does the code use one local term per concept across tests, commands, events, repositories, services, and packages?
- Is Core Domain effort protected while supporting or CRUD areas stay simpler?
- Are context relationships, translation responsibilities, and upstream/downstream pressures visible?
- Are Aggregates small, root-protected, invariant-driven, identity-linked, and usually one per transaction?
- Are Entities behavior-bearing and Value Objects immutable, validated, and value-equal?
- Are Repositories Aggregate-root access points rather than generic DAOs or ORM leaks?
- Are Domain Events meaningful past-tense facts, and is Event Sourcing used only when event history is the right persistence model?
- Are Application Services coordinating use cases instead of owning domain decisions?
- Are client, foreign, persistence, and infrastructure representations kept outside the local domain model?

<!-- END implementing-domain-driven-design.mini.md -->

<!-- END bundled-book-rules -->
