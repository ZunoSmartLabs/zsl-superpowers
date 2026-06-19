---
name: domain-modeling
description: The home for domain-doc reasoning — the CONTEXT.md Ubiquitous Language format, the ADR format, and the Domain-Driven Design book-rules. Use when capturing or sharpening a project's domain language, deciding whether a decision deserves an ADR, classifying subdomains, naming bounded-context relationships, or writing/structuring CONTEXT.md or docs/adr/. Composed by grill-with-docs and improve-codebase-architecture.
---

# Domain Modeling

The single home for how this repo captures domain reasoning in docs: the
`CONTEXT.md` Ubiquitous Language, the ADR format, and the Domain-Driven Design
rules that inform both. Other skills — `grill-with-docs`, `improve-codebase-architecture`
— compose this skill instead of carrying their own copies, so the formats and the
reasoning stay in one place.

This is **model-invoked**: it activates when domain language, subdomain
classification, bounded-context relationships, or ADR/CONTEXT writing is in play.
It doesn't run a session of its own — it supplies the formats and the rules the
user-invoked skills apply.

## The two domain documents

### `CONTEXT.md` — the Ubiquitous Language

`CONTEXT.md` is the Bounded Context's canonical glossary: the terms that carry
specific meaning inside this part of the system, written so devs and domain
experts speak one language. It follows the Bounded Context / Ubiquitous Language
discipline from *Domain-Driven Design Distilled* (bundled below).

The full structure, the writing rules (be opinionated, flag conflicts, keep
definitions tight, only domain-specific terms), the single- vs multi-context
layout (`CONTEXT-MAP.md`), and the nine context-relationship types
(Partnership, Shared Kernel, Customer/Supplier, Conformist, Anticorruption
Layer, Open Host Service, Published Language, Separate Ways, contained Big Ball
of Mud) live in [CONTEXT-FORMAT.md](CONTEXT-FORMAT.md).

### ADRs — recording load-bearing decisions

ADRs live in `docs/adr/` with sequential numbering (`0001-slug.md`). An ADR can
be a single paragraph — its value is recording *that* a decision was made and
*why*. Offer one only when the decision is **hard to reverse**, **surprising
without context**, and **the result of a real trade-off**.

The template, the optional sections, the numbering rule, and the full "what
qualifies" list (architectural shape, subdomain classification, integration
patterns, aggregate boundaries, lock-in tech choices, scope decisions,
deliberate deviations, hidden constraints, non-obvious rejected alternatives)
live in [ADR-FORMAT.md](ADR-FORMAT.md).

## Why these live together

Subdomain classification and bounded-context relationships are recorded *in*
ADRs but reasoned about *with* the DDD rules and named *with* the
Ubiquitous Language — so the CONTEXT format, the ADR format, and the DDD
book-rules belong in one skill. Re-keying `scripts/sync_book_rules.py` to embed
the two DDD rule sets here (below) means the rules follow the reasoning into
every consumer.

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
