---
name: writing-great-skills
description: Principles and vocabulary for authoring great agent skills — progressive disclosure, sharp descriptions/triggers, when to bundle scripts, and the structure that keeps SKILL.md small. Use when writing, designing, reviewing, or improving a skill, or when asked how to make a skill fire reliably.
disable-model-invocation: true
---

# Writing Great Skills

A principles-and-vocabulary reference for authoring skills that are small,
discoverable, and fire reliably. This is the *reference* — not a wizard. Reach
for it when you're designing a new skill or sharpening an existing one. Shared
terms live in [GLOSSARY.md](GLOSSARY.md).

## The three principles

1. **Progressive disclosure.** `SKILL.md` loads first and costs context on every
   activation, so keep it small (aim under ~100 lines). Push long-form detail —
   references, examples, glossaries — into sibling files linked **one level
   deep**, read only when the task needs them.
2. **The description is the product.** It is the *only* thing the agent sees when
   deciding whether to load the skill. A vague description is a skill that never
   fires (or fires for the wrong prompts). Make it deep, not shallow (see
   [GLOSSARY.md](GLOSSARY.md)).
3. **Bundle the deterministic, narrate the judgmental.** A step with exactly one
   correct answer (a length cap, a clean-tree check, a fixed serialization)
   belongs in a bundled script behind a gate — not in prose the model re-derives
   each run. Everything that needs judgment stays as instructions.

## Skill structure

```
skill-name/
├── SKILL.md           # Frontmatter + small body (required)
├── GLOSSARY.md        # Shared vocabulary (if the skill has its own terms)
├── REFERENCE.md       # Detailed docs (if needed)
├── EXAMPLES.md        # Usage examples (if needed)
└── scripts/           # Deterministic-gate utilities (if needed)
    └── check-something.py
```

Split a file out when `SKILL.md` exceeds ~100 lines, content spans distinct
domains, or advanced material is rarely needed.

## Writing the description

The description is surfaced in the system prompt next to every other skill's. The
agent picks based on it alone, so give it exactly two things:

1. **What the skill does** (first sentence, third person).
2. **When to reach for it** (second sentence: `Use when …` with concrete
   keywords, contexts, file types).

- **Good:** `Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.`
- **Bad:** `Helps with documents.` — gives the agent no way to distinguish this from any other document skill.

### Deterministic gate — count the 1024-char cap, don't eyeball it

The harness silently truncates a description over 1024 characters, dropping the
trailing `Use when …` trigger so the skill stops firing for exactly the cases the
cut-off text described. `len(description) <= 1024` has one correct answer, so
check it rather than guessing:

```bash
CK=$({ ls "$PWD"/skills/*/writing-great-skills/scripts/check-description-length.py 2>/dev/null
       ls "$HOME/.claude/skills/writing-great-skills/scripts/check-description-length.py" 2>/dev/null
       ls -d "$HOME"/.claude/plugins/cache/zsl-superpowers/zsl/*/skills/*/writing-great-skills/scripts/check-description-length.py 2>/dev/null | sort -Vr; } | head -1)
if [ -n "$CK" ]; then printf '%s' "$DESCRIPTION" | python3 "$CK"; else echo "zsl-gate: check-description-length.py unresolved — count chars by hand (Fallback)"; fi
```

A `FAIL:` line means trim before shipping.

**Fallback** (if `$CK` is empty): count the characters yourself and confirm
`<= 1024` — never approve a description by visual length alone. The trailing
`Use when …` clause is the first thing lost to truncation, so a description that
*looks* like two reasonable sentences can still be silently over the cap.

## When to add scripts

Add a bundled script when the operation is deterministic (validation,
formatting, a fixed serialization), the same code would otherwise be regenerated
every run, or errors need explicit handling. Scripts save tokens and improve
reliability versus generated code. Every gate script ships with tests, including
at least one input the prose way gets wrong.

## Review checklist

- [ ] Description names what it does **and** when to fire (`Use when …`).
- [ ] Description within 1024 chars (run the gate above — counted, not eyeballed).
- [ ] `SKILL.md` body stays small; depth lives in linked files one level deep.
- [ ] No time-sensitive info baked into the body.
- [ ] Terminology consistent with [GLOSSARY.md](GLOSSARY.md).
- [ ] Concrete examples included.
- [ ] Deterministic steps are bundled scripts with a Fallback; judgmental steps stay prose.
