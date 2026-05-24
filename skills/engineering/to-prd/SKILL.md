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

3. **Draft user stories as automatable specs.** Each story must be expressible as a public-interface assertion — an API result, a state transition, a rendered value, an emitted event. For each story, write:
   - The `As an <actor>, I want <feature>, so that <benefit>` line.
   - An `acceptance: automatable` sub-bullet asserting it can be pinned by a test.
   - An `observable: <one-line description>` sub-bullet stating *what public-interface behaviour* a test would assert (e.g. "POST /login with valid creds returns 200 + sets `session` cookie; with invalid creds returns 401"). This line feeds `/verify-coverage`'s Tier B test generation later, so be concrete: name the endpoint/state/event, not the implementation.

   **Refuse to draft a non-automatable story.** Visual/UX stories ("feels welcoming", "looks polished"), pure human-judgement stories ("legal signs off", "design reviews"), and real-external-system stories ("DNS propagates globally") cannot be pinned by an assertion. If the user wants one, push back: either reframe it as an automatable observable (e.g. "feels welcoming" → "first-render Lighthouse score ≥ 90"), split it into a separate PRD that goes through a manual path (not `/tdd-parallel`), or drop it. Do not write `acceptance: manual-attestation` — that lane has been removed from this pipeline. A PRD that mixes automatable and non-automatable stories will be refused by `/tdd-parallel`'s pre-flight.

4. Write the PRD using the template below, then publish it to the project issue tracker. Apply both the `ready-for-agent` triage label (no additional triage needed — you just wrote it) and the `backlog` label (so it shows up on the project board).

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story carries two tags
that `/tdd-parallel` and `/verify-coverage` consume:

```
1. As an <actor>, I want a <feature>, so that <benefit>.
   - acceptance: automatable
   - observable: <what public-interface behaviour a test would assert>
```

<user-story-example>
1. As a mobile bank customer, I want to see balances on my accounts, so that I can make better informed decisions about my spending.
   - acceptance: automatable
   - observable: GET /accounts returns 200 with a JSON list whose every element has a numeric `balance` field; the home-screen account card renders that value formatted as currency.
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature. **Every** story must have both sub-bullets; a story without them blocks `/tdd-parallel`. The `observable:` line is the contract Tier B will generate a test against — be specific.

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
