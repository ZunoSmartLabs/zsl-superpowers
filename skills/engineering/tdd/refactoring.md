# Refactor Candidates

After the TDD cycle (step 4 in [SKILL.md](SKILL.md)), scan the touched code for the smells below. The bundled *Refactoring* rules at the bottom of `SKILL.md` are the canonical source; this file is a quick scannable checklist for the triggers most likely to show up after a green test.

## Triggers

- **Duplication** → extract function, class, or value object. When the same edit appears for the *third* time, centralize ownership instead of copying again.
- **Long methods** → break into private helpers; keep tests on the public interface.
- **Shallow modules** → combine, or deepen — small interface, more logic behind it.
- **Conditionals or type codes growing** → decompose intent (rename, extract, split phases) *before* reaching for polymorphism, state machines, strategy, or lookup tables.
- **Feature envy** → move logic to where the data lives.
- **Primitive obsession** → introduce a value object.
- **Boolean flag parameters / output parameters / parameter reassignment** → split the function or model the concept.
- **Hidden side effects** → make the mutation explicit, or separate command from query.
- **Existing code the new code reveals as problematic** → fix the smell that blocks the current change, not every smell nearby.

## Discipline

- **Preserve observable behavior.** Refactoring is structure, not behavior. If a test goes red during refactor, you've changed behavior — back out, get green, and try a smaller move.
- **Small named moves only.** Rename, extract, inline, move, split phases, encapsulate mutation, decompose conditional, remove duplication. Reach for a named move before inventing one.
- **Separate cleanup from behavior.** If a single patch mixes "I added the feature" with "I refactored the surrounding area," split it. Two commits, or two PRs.
- **Stop when the change is easy.** Further cleanup beyond that is speculative; speculative refactor breaks the next person's intuition without earning its keep.
- **Never rewrite when a smaller move would do.** When the temptation to rewrite shows up, choose the next small behavior-preserving transformation instead.
