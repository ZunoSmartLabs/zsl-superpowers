# Triage Labels

The skills speak in terms of six canonical triage roles. This file maps those
roles to the actual label strings used in this repo.

In this repo's **hybrid tracker** (`docs/agents/issue-tracker.md`), each role
string is used in two places that must stay identical:

- the `Status:` line of the `.scratch/` markdown file (the source of truth), and
- the GitHub label on that issue's mirror (so the project board can group by it).

| Canonical role    | Label in our tracker | Meaning                                                       |
| ----------------- | -------------------- | ------------------------------------------------------------ |
| `needs-triage`    | `needs-triage`       | Maintainer needs to evaluate this issue                      |
| `needs-info`      | `needs-info`         | Waiting on reporter for more information                     |
| `ready-for-agent` | `ready-for-agent`    | Fully specified, ready for an AFK agent                      |
| `ready-for-human` | `ready-for-human`    | Requires human implementation                                |
| `tracking`        | `tracking`           | Container/parent issue (e.g. PRD) — work lives in sub-issues |
| `wontfix`         | `wontfix`            | Will not be actioned                                         |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the
corresponding label string from this table — as the `Status:` value in the file
**and** as the GitHub label on the mirror issue.

All six labels exist in `ZunoSmartLabs/zsl-superpowers`. Edit the right-hand
column (and the GitHub labels) together if you change the vocabulary.
