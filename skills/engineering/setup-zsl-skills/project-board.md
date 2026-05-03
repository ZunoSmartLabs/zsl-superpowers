# Project board

This repo's triage labels and `/tdd` lifecycle sync to a GitHub Projects v2 board's `Status` column. Skills consult this file to look up the project, its `Status` field, and the option to set for each lifecycle event. If this file is missing, the skills silently skip the project sync.

## Project

- **Name**: <project name, e.g. "Tina TheAI Turing">
- **URL**: <https://github.com/users/OWNER/projects/NUMBER>
- **Owner type**: `user` or `org` (matters for `gh project` commands)
- **Owner login**: <OWNER>
- **Number**: <NUMBER>
- **Node ID**: `PVT_…` *(used in GraphQL mutations)*

## Status field

- **Field name**: `Status` *(or whatever the user named their lifecycle column)*
- **Field ID**: `PVTSSF_…`
- **Options** *(option name → option ID)*:
  - `Backlog` → `…`
  - `Ready` → `…`
  - `In progress` → `…`
  - `In review` → `…`
  - `Done` → `…`

## Mapping

Skills write Status at these lifecycle moments:

| Skill action                                       | Status option |
|----------------------------------------------------|---------------|
| `/triage` → `needs-triage`                         | Backlog       |
| `/triage` → `needs-info`                           | Backlog       |
| `/triage` → `ready-for-agent`                      | Ready         |
| `/triage` → `ready-for-human`                      | Ready         |
| `/triage` → `tracking` *(or `/to-issues` step 7)*  | In progress   |
| `/tdd` step 1 (work begins on the issue)           | In progress   |
| `/tdd` ship in PR-style (PR opened, awaiting merge) | In review     |
| `/triage` → `wontfix`                              | Done          |

Issue closure (PR merged, direct-push commit, manual close) lands at `Done` automatically via the project's built-in **Auto-close issue** workflow — skills don't write `Done` themselves.

## How skills use this file

When a skill changes an issue's lifecycle, it:

1. Reads this file for the project node ID, Status field ID, and option IDs.
2. Queries the issue's project items via GraphQL:
   ```bash
   gh api graphql -f query='query { repository(owner:"<owner>", name:"<repo>") { issue(number:N) { projectItems(first:20) { nodes { id project { id } } } } } }'
   ```
3. Filters to the item whose `project.id` matches the node ID above. If no match, logs *"issue not in configured project; skipping Status update"* and continues.
4. Updates the field via:
   ```bash
   gh api graphql -f query='mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}' \
     -f p=<project-node-id> -f i=<item-id> -f f=<status-field-id> -f o=<option-id>
   ```

If the update fails, skills log the failure but do **not** abort their main work — label transitions and lifecycle events are the source of truth; the board sync is best-effort.
