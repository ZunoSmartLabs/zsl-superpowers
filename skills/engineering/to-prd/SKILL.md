---
name: to-prd
description: Turn the current conversation context into a PRD and publish it to the project issue tracker. Use when user wants to create a PRD from the current context.
---

This skill takes the current conversation context and codebase understanding and produces a PRD. Do NOT interview the user — just synthesize what you already know.

The issue tracker and triage label vocabulary should have been provided to you — run `/setup-zsl-superpowers` if not.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the PRD, and respect any ADRs in the area you're touching.

2. Sketch out the major modules you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep modules that can be tested in isolation.

A deep module (as opposed to a shallow module) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes.

Check with the user that these modules match their expectations. Check with the user which modules they want tests written for.

3. **Write each story at value altitude; push the testable detail into acceptance criteria.** A user story is a slice of *user value* — who, what capability, why — and the story line must stay there: no endpoints, no status codes, no state names, no implementation. Every concrete, testable assertion moves *down* into the story's acceptance criteria, where technical detail belongs. For each story, write:
   - The `As an <actor>, I want <capability>, so that <benefit>` line — value only, no technical detail.
   - An `acceptance: automatable` sub-bullet asserting the story can be pinned by tests.
   - One or more `AC<n>: <assertion>` sub-bullets — the **acceptance criteria**. Each states *what public-interface behaviour* a test would assert — an API result, a state transition, a rendered value, an emitted event (e.g. "POST /login with valid creds returns 200 + sets `session` cookie; with invalid creds returns 401"). The acceptance criteria are the contract `/verify-coverage`'s Tier B generates tests against, so be concrete: name the endpoint/state/event, not the implementation. When one capability needs several distinct assertions, give it several ACs — do **not** fracture it into multiple stories just to give each one a single observable (that is exactly what made earlier PRDs read like a flat list of acceptance criteria).

   **Refuse to draft a story with no automatable acceptance criterion.** Visual/UX stories ("feels welcoming", "looks polished"), pure human-judgement stories ("legal signs off", "design reviews"), and real-external-system stories ("DNS propagates globally") cannot be pinned by an assertion. If the user wants one, push back: either reframe it with an automatable acceptance criterion (e.g. "feels welcoming" → AC "first-render Lighthouse score ≥ 90"), split it into a separate PRD that goes through a manual path (not `/tdd-parallel`), or drop it. Do not write `acceptance: manual-attestation` — that lane has been removed from this pipeline. A PRD that mixes automatable and non-automatable stories will be refused by `/tdd-parallel`'s pre-flight.

4. Write the PRD using the template below, then publish it to the project issue tracker. Apply both the `ready-for-agent` triage label (no additional triage needed — you just wrote it) and the `backlog` label (so it shows up on the project board).

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each story is written at **value altitude** — who/what/why, no technical detail — and carries an `acceptance: automatable` tag plus one or more **acceptance criteria** (`AC<n>:`), the concrete testable assertions that `/tdd-parallel` and `/verify-coverage` consume:

```
1. As an <actor>, I want <capability>, so that <benefit>.
   - acceptance: automatable
   - AC1: <a public-interface behaviour a test would assert>
   - AC2: <another, if the capability needs more than one assertion>
```

<user-story-example>
1. As a mobile bank customer, I want to see the balances on my accounts, so that I can make better informed decisions about my spending.
   - acceptance: automatable
   - AC1: GET /accounts returns 200 with a JSON list whose every element has a numeric `balance` field.
   - AC2: the home-screen account card renders that balance formatted as currency.
   - AC3: an account with no transactions still renders, showing a 0.00 balance.
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature. Keep the *story line* free of endpoints, status codes, and state names — those live in the acceptance criteria beneath it. **Every** story must carry the `acceptance: automatable` tag and at least one `AC<n>:` acceptance criterion; a story missing either blocks `/tdd-parallel`. The acceptance criteria are the contract Tier B generates tests against — be specific.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.

</prd-template>

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

<!-- END bundled-book-rules -->
