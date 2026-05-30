# Language

Shared vocabulary for every suggestion this skill makes. Most terms come from the bundled rule sets in [SKILL.md](SKILL.md) — when we use a book's term, we use it the way the book uses it. A few terms are ours, added where the books don't have a precise name for what we mean.

## From the bundled rules

**Module** *(both books)*
Anything with an interface and an implementation. Scale-agnostic — applies equally to a function, class, package, or tier-spanning slice. APoSD: a *deep* module has a small interface hiding a large body of behaviour; a *shallow* module has an interface nearly as wide as its implementation.
_Avoid_: unit, component, service.

**Interface** *(both books)*
Everything a caller must know to use the module correctly. Includes the type signature, but also invariants, ordering constraints, error modes, required configuration, and performance characteristics. Clean Architecture calls inward-owned interfaces **ports** (see below).
_Avoid_: API, signature (too narrow — those refer only to the type-level surface).

**Implementation** *(APoSD)*
What's inside a module — its body of code. Distinct from **adapter**: a thing can be a small adapter with a large implementation (a Postgres repository) or a large adapter with a small implementation (an in-memory fake).

**Boundary** *(Clean Architecture)*
A line across which source dependencies cross in one direction only. Enforces the dependency rule: dependencies point inward toward higher-level policy. A boundary is a particular kind of **seam** — one that also enforces a dependency direction.

**Layer** *(Clean Architecture)*
A horizontal stack of modules at the same level of policy. The inward direction is *upward* in policy (more general, more stable). Not interchangeable with **module** — a layer is the stack; a module is a unit within it.

**Port** *(Clean Architecture)*
An interface owned by an inner layer, implemented by an outer-layer adapter. Use "port" when the dependency-direction property is the point; otherwise just **interface**.

**Adapter** *(Clean Architecture)*
A concrete thing that satisfies an interface at a seam or boundary. Describes *role* (what slot it fills), not substance (what's inside). **Humble** adapters do *only* translation between external formats and the use-case call — no business decisions.

**Cognitive load / Change amplification / Hidden dependencies / Temporal coupling** *(APoSD)*
The dimensions a deep module reduces. Use these names when describing *why* a deepening helps:

- **Cognitive load** — total facts a reader must hold at once.
- **Change amplification** — one conceptual change requiring many code changes.
- **Hidden dependencies** — knowledge required to use the module that isn't visible at the interface.
- **Temporal coupling** — operations that must be called in a specific order; almost always a sign of a shallow module exposing its phases.

## Our additions

Where the bundled books don't have a precise term, we've added these.

**Seam** *(from Michael Feathers, Working Effectively with Legacy Code — also bundled in /tdd's rules)*
A place where behaviour can be altered without editing in that place. The *location* at which a module's interface lives. Choosing where to put the seam is its own design decision, distinct from what goes behind it.

A **boundary** in Clean Architecture's sense is a particular kind of seam — one that also enforces a dependency direction. Prefer **seam** when the topic is testability and substitution; **boundary** when the topic is policy/detail separation.

**Depth-as-leverage**
We measure depth as *behaviour per unit of interface a caller has to learn*. APoSD also frames depth as a ratio of implementation lines to interface lines; we don't use the ratio because it rewards padding the implementation. Both framings agree on what makes a module shallow.

**Leverage**
What callers get from depth. More capability per unit of interface they have to learn. One implementation pays back across N call sites and M tests. Not a book term — added because the concept is useful enough to name.

**Locality**
What maintainers get from depth. Change, bugs, knowledge, and verification concentrate at one place rather than spreading across callers. Fix once, fixed everywhere. Not a book term — same reason.

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can be internally composed of small, mockable, swappable parts — they just aren't part of the interface. A module can have **internal seams** (private to its implementation, used by its own tests) as well as the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, the module wasn't hiding anything (it was a pass-through). If complexity reappears across N callers, the module was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. If you want to test *past* the interface, the module is probably the wrong shape.
- **One adapter = hypothetical seam. Two adapters = real one.** Don't introduce a seam unless something actually varies across it.
- **Information hiding** (APoSD) and **the dependency rule** (Clean Architecture) are the two pressures the skill applies. The bundled rule sets in [SKILL.md](SKILL.md) are the canonical source for both.

## Relationships

- A **module** has exactly one **interface** (the surface it presents to callers and tests).
- **Depth** is a property of a **module**, measured against its **interface**.
- A **seam** is where a **module**'s **interface** lives.
- A **boundary** is a **seam** that also enforces a dependency direction (Clean Architecture's term).
- An **adapter** sits at a **seam** and satisfies the **interface**.
- A **port** is an **interface** owned by an inner **layer**.
- **Depth** produces **leverage** for callers and **locality** for maintainers.
