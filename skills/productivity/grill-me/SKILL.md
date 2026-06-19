---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

<what-to-do>

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

Run the interview using the shared design-tree protocol in [`grilling`](../grilling/SKILL.md): print the tree before the first question (status markers `[ ]`/`[→]`/`[✓]`), traverse one branch at a time, and reprint the full tree whenever its shape or status changes.

</what-to-do>
