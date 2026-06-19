# Adopt a User-invoked / Model-invoked skill taxonomy, and dedup shared vocabulary into model-invoked skills

We split every skill into **user-invoked** (only runs when typed; the orchestrators) and
**model-invoked** (can also fire automatically when the task fits), enforce that a user-invoked
skill may call model-invoked ones but never another user-invoked one, and use that distinction to
extract duplicated guidance (deep-module vocabulary, ADR/CONTEXT formats, the grilling loop) into
shared **model-invoked** skills (`codebase-design`, `domain-modeling`, `grilling`) that other skills
compose rather than copy.

Status: accepted

## Considered Options

- **Keep the implicit model (rejected).** Skills were de-facto split already (`diagnose`/`triage`
  auto-fire; `commit`/`afk-fanout` only when typed), but the distinction was never named or
  enforced. Shared guidance lived inline and drifted — the deep-module vocabulary existed in four
  files across `improve-codebase-architecture` and `tdd`; the design-tree protocol was copy-pasted
  between `grill-me` and `grill-with-docs`. Inlining the new shared skills would have continued this.
- **Adopt the taxonomy heavyweight (rejected).** Rename every doc surface from the current framing
  wholesale. Higher churn for no extra leverage.
- **Adopt the taxonomy lightweight (chosen).** Add `disable-model-invocation` flags to the pure
  orchestrators, a short `docs/invocation.md` defining the split, and a sixth lane to the skill-sync
  contract; introduce the vocabulary only where it justifies the three extractions.

## Consequences

- The three extracted skills are model-invoked and **must not** be invoked by other user-invoked
  skills — e.g. `decision-mapping` (user-invoked) composes `grilling` + `domain-modeling`
  (model-invoked) directly, never `grill-with-docs` (user-invoked).
- Model-invoked-only skills get a lighter sync treatment: registered in `plugin.json` and documented
  under a "Shared / model-invoked" subsection, but omitted from the "Which skill do I want?" decision
  tree and the user-command lists, since users don't invoke them directly.
- The dedup is deletion-positive: extracting `codebase-design` removes four duplicated reference
  files; extracting `grilling` removes the duplicated design-tree blocks from two skills.
- `grill-me` and `grill-with-docs` become thin composers over the shared engine, which is the
  intended end state — most of their former body now lives in `grilling` + `domain-modeling`.
