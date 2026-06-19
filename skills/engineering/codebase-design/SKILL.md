---
name: codebase-design
description: Shared vocabulary and refinements for reasoning about module depth, interfaces, seams, and adapters — the deep-module design language. Use when discussing module/interface design, whether a module is deep or shallow, where to place a seam, how to design an interface for testability, or when exploring alternative interfaces for a module. Composed by /improve-codebase-architecture and /tdd.
---

# Codebase Design

The shared design language for module depth, interfaces, seams, and adapters. One
home for the deep-module vocabulary so the terms mean the same thing in every
skill that reasons about architecture — `/improve-codebase-architecture`, `/tdd`,
and anything else that touches interface design composes this skill instead of
carrying its own copy.

Most terms come from two books — **A Philosophy of Software Design** (Ousterhout,
"APoSD") and **Clean Architecture** (Martin) — bundled as decision-pressure rules
into the skills that consume this vocabulary. When we use a book's term, we use it
the way the book uses it. A few terms are ours, added where the books don't have a
precise name for what we mean.

## Vocabulary

**Module** *(both books)*
Anything with an interface and an implementation. Scale-agnostic — applies equally
to a function, class, package, or tier-spanning slice. APoSD: a *deep* module has a
small interface hiding a large body of behaviour; a *shallow* module has an
interface nearly as wide as its implementation.
_Avoid_: unit, component, service.

**Interface** *(both books)*
Everything a caller must know to use the module correctly. Includes the type
signature, but also invariants, ordering constraints, error modes, required
configuration, and performance characteristics. Clean Architecture calls
inward-owned interfaces **ports** (see below).
_Avoid_: API, signature (too narrow — those refer only to the type-level surface).

**Implementation** *(APoSD)*
What's inside a module — its body of code. Distinct from **adapter**: a thing can
be a small adapter with a large implementation (a Postgres repository) or a large
adapter with a small implementation (an in-memory fake).

**Depth** *(APoSD)*
Leverage at the interface: a lot of behaviour behind a small interface. **Deep** =
high leverage. **Shallow** = interface nearly as complex as the implementation.

**Boundary** *(Clean Architecture)*
A line across which source dependencies cross in one direction only. Enforces the
dependency rule: dependencies point inward toward higher-level policy. A boundary
is a particular kind of **seam** — one that also enforces a dependency direction.

**Layer** *(Clean Architecture)*
A horizontal stack of modules at the same level of policy. The inward direction is
*upward* in policy (more general, more stable). Not interchangeable with
**module** — a layer is the stack; a module is a unit within it.

**Port** *(Clean Architecture)*
An interface owned by an inner layer, implemented by an outer-layer adapter. Use
"port" when the dependency-direction property is the point; otherwise just
**interface**.

**Adapter** *(Clean Architecture)*
A concrete thing that satisfies an interface at a seam or boundary. Describes *role*
(what slot it fills), not substance (what's inside). **Humble** adapters do *only*
translation between external formats and the use-case call — no business decisions.

**Cognitive load / Change amplification / Hidden dependencies / Temporal coupling** *(APoSD)*
The dimensions a deep module reduces. Use these names when describing *why* a
deepening helps:

- **Cognitive load** — total facts a reader must hold at once.
- **Change amplification** — one conceptual change requiring many code changes.
- **Hidden dependencies** — knowledge required to use the module that isn't visible
  at the interface.
- **Temporal coupling** — operations that must be called in a specific order; almost
  always a sign of a shallow module exposing its phases.

### Our additions

Where the bundled books don't have a precise term, we've added these.

**Seam** *(from Michael Feathers, Working Effectively with Legacy Code — also bundled in /tdd's rules)*
A place where behaviour can be altered without editing in that place. The *location*
at which a module's interface lives. Choosing where to put the seam is its own design
decision, distinct from what goes behind it.

A **boundary** in Clean Architecture's sense is a particular kind of seam — one that
also enforces a dependency direction. Prefer **seam** when the topic is testability
and substitution; **boundary** when the topic is policy/detail separation.

**Depth-as-leverage**
We measure depth as *behaviour per unit of interface a caller has to learn*. APoSD
also frames depth as a ratio of implementation lines to interface lines; we don't use
the ratio because it rewards padding the implementation. Both framings agree on what
makes a module shallow.

**Leverage**
What callers get from depth. More capability per unit of interface they have to learn.
One implementation pays back across N call sites and M tests. Not a book term — added
because the concept is useful enough to name.

**Locality**
What maintainers get from depth. Change, bugs, knowledge, and verification concentrate
at one place rather than spreading across callers. Fix once, fixed everywhere. Not a
book term — same reason.

## Deep vs shallow modules

**Deep module** = small interface + lots of implementation

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (avoid)

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing interfaces, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can
  be internally composed of small, mockable, swappable parts — they just aren't part
  of the interface. A module can have **internal seams** (private to its implementation,
  used by its own tests) as well as the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, the
  module wasn't hiding anything (it was a pass-through). If complexity reappears across
  N callers, the module was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. If you
  want to test *past* the interface, the module is probably the wrong shape.
- **One adapter = hypothetical seam. Two adapters = real one.** Don't introduce a seam
  unless something actually varies across it.
- **Information hiding** (APoSD) and **the dependency rule** (Clean Architecture) are
  the two pressures to apply. The bundled rule sets in the consuming skills
  (`/improve-codebase-architecture`, `/tdd`) are the canonical source for both.

## Relationships

- A **module** has exactly one **interface** (the surface it presents to callers and
  tests).
- **Depth** is a property of a **module**, measured against its **interface**.
- A **seam** is where a **module**'s **interface** lives.
- A **boundary** is a **seam** that also enforces a dependency direction (Clean
  Architecture's term).
- An **adapter** sits at a **seam** and satisfies the **interface**.
- A **port** is an **interface** owned by an inner **layer**.
- **Depth** produces **leverage** for callers and **locality** for maintainers.

## Designing interfaces for testability

Good interfaces make testing natural:

1. **Accept dependencies, don't create them**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Return results, don't produce side effects**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small surface area**
   - Fewer methods = fewer tests needed
   - Fewer params = simpler test setup

## Designing it twice — exploring alternative interfaces

When the user wants to explore alternative interfaces for a chosen module (e.g. a
deepening candidate from `/improve-codebase-architecture`), use this parallel
sub-agent pattern. Based on "Design It Twice" (Ousterhout) — your first idea is
unlikely to be the best.

Uses the vocabulary above — **module**, **interface**, **seam**, **adapter**,
**leverage**.

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for
the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see
  [DEEPENING.md](../improve-codebase-architecture/DEEPENING.md))
- A rough illustrative code sketch to ground the constraints — not a proposal, just a
  way to make the constraints concrete

Show this to the user, then immediately proceed to Step 2. The user reads and thinks
while the sub-agents work in parallel.

### 2. Spawn sub-agents

Spawn 3+ sub-agents in parallel using the Agent tool. Each must produce a **radically
different** interface for the module.

Prompt each sub-agent with a separate technical brief (file paths, coupling details,
dependency category from [DEEPENING.md](../improve-codebase-architecture/DEEPENING.md),
what sits behind the seam). The brief is independent of the user-facing problem-space
explanation in Step 1. Give each agent a different design constraint:

- Agent 1: "Minimize the interface — aim for 1–3 entry points max. Maximise leverage per entry point."
- Agent 2: "Maximise flexibility — support many use cases and extension."
- Agent 3: "Optimise for the most common caller — make the default case trivial."
- Agent 4 (if applicable): "Design around ports & adapters for cross-seam dependencies."

Include both this vocabulary and CONTEXT.md vocabulary in the brief so each sub-agent
names things consistently with the architecture language and the project's domain
language.

Each sub-agent outputs:

1. Interface (types, methods, params — plus invariants, ordering, error modes)
2. Usage example showing how callers use it
3. What the implementation hides behind the seam
4. Dependency strategy and adapters (see [DEEPENING.md](../improve-codebase-architecture/DEEPENING.md))
5. Trade-offs — where leverage is high, where it's thin

### 3. Present and compare

Present designs sequentially so the user can absorb each one, then compare them in
prose. Contrast by **depth** (leverage at the interface), **locality** (where change
concentrates), and **seam placement**.

After comparing, give your own recommendation: which design you think is strongest and
why. If elements from different designs would combine well, propose a hybrid. Be
opinionated — the user wants a strong read, not a menu.
