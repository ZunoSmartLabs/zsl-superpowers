---
name: to-issues
description: Break a plan, spec, or PRD into independently-grabbable issues on the project issue tracker using tracer-bullet vertical slices. Use when user wants to convert a plan into issues, create implementation tickets, or break down work into issues.
---

# To Issues

Break a plan into independently-grabbable issues using vertical slices (tracer bullets).

The issue tracker and triage label vocabulary should have been provided to you — run `/setup-zsl-superpowers` if not.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes an issue reference (issue number, URL, or path) as an argument, fetch it from the issue tracker and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Issue titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

### 3. Draft vertical slices

Break the plan into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

#### Title format

Each slice gets a title in the form `[<TYPE>] <wave>[<letter>] — <description>`:

- **Type prefix**: `[AFK]` or `[HITL]`.
- **Wave number**: dependency depth, starting at 1. Slices sharing a wave number are runnable in parallel (same fan-out batch that `/tdd-parallel` would pick up).
- **Letter suffix**: when a wave has more than one slice, assign `a`, `b`, `c`... in the order slices were drafted. Single-slice waves stay unlettered.
- **Em dash separator**: ` — ` between the wave token and the description.
- **Description**: short and action-oriented.

Examples:

- `[HITL] 1 — Decide auth provider`
- `[AFK] 2a — Add OAuth callback endpoint`
- `[AFK] 2b — Render login button`
- `[AFK] 3 — Wire callback to session store`
- `[AFK] 4 — Show user profile after login`

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: as drafted in step 3 (with the `[TYPE] wave[letter] — description` format)
- **Type**: HITL / AFK
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories this addresses (if the source material has them)

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the correct slices marked as HITL and AFK?

Iterate until the user approves the breakdown.

### 5. Publish the issues to the issue tracker

For each approved slice, publish a new issue to the issue tracker. Use the issue body template below. Apply both the `needs-triage` triage label (so each issue enters the normal triage flow) and the `backlog` label (so each issue shows up on the project board).

Publish issues in dependency order (blockers first) so you can reference real issue identifiers in the "Blocked by" field.

<issue-template>
## Parent

A reference to the parent issue on the issue tracker (if the source was an existing issue, otherwise omit this section).

## What to build

A concise description of this vertical slice. Describe the end-to-end behavior, not layer-by-layer implementation.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Blocked by

- A reference to the blocking ticket (if any)

Or "None - can start immediately" if no blockers.

</issue-template>

### 6. Link each new issue as a sub-issue of the parent

If a parent issue exists and the tracker supports sub-issues, link each child to the parent so the parent auto-closes when all children close.

- **GitHub**: use the `addSubIssue` GraphQL mutation. Fetch parent and child node IDs first, then link (replace `OWNER`, `REPO`, `PARENT`, `CHILD`):
  ```bash
  PARENT_ID=$(gh api graphql -f query='query{repository(owner:"OWNER",name:"REPO"){issue(number:PARENT){id}}}' -q .data.repository.issue.id)
  CHILD_ID=$(gh api graphql -f query='query{repository(owner:"OWNER",name:"REPO"){issue(number:CHILD){id}}}' -q .data.repository.issue.id)
  gh api graphql -f query='mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){subIssue{number}}}' -f p="$PARENT_ID" -f c="$CHILD_ID"
  ```
- **Linear**: set `parentId` on each child when creating it.
- **GitLab / local files / unsupported trackers**: skip; the `## Parent` text reference is the only link.

Do NOT close the parent or modify its body. The only allowed parent changes are adding sub-issue links and updating the state label as described in step 7.

### 7. Move the parent to `tracking`

If the source was an existing parent issue (i.e. the new issues were linked as sub-issues in step 6), update the parent's state label to `tracking` (use the configured label string from `docs/agents/triage-labels.md`). Remove any prior state label (`needs-triage`, `ready-for-agent`, etc.) — the parent is no longer a unit of work, it's a container.

GitHub will auto-close the parent when the last child closes. Do not close the parent yourself.

If `docs/agents/project-board.md` exists, also update the parent's project item Status to the option mapped to `tracking` (typically `In progress`). Use the same lookup-then-update procedure documented in `triage/SKILL.md` step 6: fetch the project item via `gh api graphql` filtered by the configured project node ID, then `updateProjectV2ItemFieldValue` with the mapped Status option ID. If the parent isn't on the configured project, log and continue. Best-effort — the label change is the source of truth.

Children created in step 5 are auto-added to the project (the user's existing "Auto-add to project" workflow handles that) and start in the project's default Status (`Backlog`); `/triage` will advance them to `Ready` later.

Skip this step if there's no parent issue (e.g. the source was a freeform plan in conversation).
