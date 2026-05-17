# The loop

The plugin's skills compose into one end-to-end engineering loop. Most
days you only touch a few of them; the loop tells you which skill picks
up where the previous one left off, and which ones sit on the side as
cross-cutting helpers.

The [workflow page](../workflow.md) is the canonical walkthrough with
slash-command examples. This page is the **conceptual map** — the
phases, what each phase produces, and what flows between them.

## The five phases

```mermaid
flowchart LR
    setup(["one-time<br/>setup-zsl-superpowers"]):::oneoff
    plan["**Plan**<br/>grill-me<br/>grill-with-docs<br/>to-prd"]
    breakdown["**Break down**<br/>to-issues<br/>triage"]
    build["**Build**<br/>tdd-parallel<br/>human-itl<br/>tdd<br/>verify-coverage<br/>diagnose"]
    ship["**Ship**<br/>code-review<br/>commit<br/>git-branch"]
    track["**Track & close**<br/>state machine<br/>project board / .scratch"]

    setup -.->|once per repo| plan
    plan --> breakdown --> build --> ship --> track --> plan

    cross["**Cross-cutting**<br/>triage (inbound)<br/>diagnose<br/>improve-codebase-architecture<br/>zoom-out"]:::cross
    cross -.-> build

    classDef oneoff stroke-dasharray: 4 4
    classDef cross fill:#fef3c7,stroke:#d97706,color:#1a1a1a
```

| Phase | Produces | Consumed by |
|---|---|---|
| **Plan** | A PRD issue on the tracker (or a `.scratch/<feature>/PRD.md`) describing what you're building and why | Break down |
| **Break down** | A set of vertical-slice sub-issues with `[AFK\|HITL] <wave><letter>` titles and `Blocked by` graphs, each triaged to a state | Build |
| **Build** | Slice branches with red-green-refactor commits, each closing one sub-issue | Ship |
| **Ship** | A merged PR (or pushed commit) per slice, *or* one consolidated integration PR for an AFK fanout (gated on a `/zsl:verify-coverage` receipt for the integrated tip) | Track |
| **Track & close** | Closed issues. The PRD parent auto-closes when its last child closes. | Next loop |

## Phase 1: Plan

```mermaid
flowchart LR
    chat(["conversation<br/>with Claude"]) --> grill{{"/zsl:grill-me<br/>or<br/>/zsl:grill-with-docs"}}
    grill -->|"shared language updated<br/>in CONTEXT.md + ADRs"| docs[("CONTEXT.md<br/>docs/adr/")]
    grill --> prd{{"/zsl:to-prd"}}
    prd -->|"synthesises chat → PRD"| tracker[("issue tracker<br/>or .scratch/")]

    classDef skill fill:#e0e7ff,stroke:#3f51b5;
    classDef artifact fill:#dcfce7,stroke:#16a34a;
    class grill,prd skill
    class docs,tracker artifact
```

[`/zsl:grill-me`](../skills/grill-me.md) and
[`/zsl:grill-with-docs`](../skills/grill-with-docs.md) interview you
relentlessly about a plan or design until every branch of the decision
tree is resolved. The `with-docs` variant also updates your `CONTEXT.md`
(the shared language) and ADRs (the decisions) inline — that's the lever
that cuts agent verbosity over time.

Once the conversation feels concrete, [`/zsl:to-prd`](../skills/to-prd.md)
synthesises it into a PRD on the tracker. No interview — just packaging
what you've already discussed.

!!! tip "The grilling step is the highest-leverage one"
    The most common failure mode in agent-coded software is
    misalignment — you think the agent knows what you want, then you
    see what it built. Spending five minutes here costs orders of
    magnitude less than re-doing work later.

## Phase 2: Break down

```mermaid
flowchart LR
    prd[("PRD on tracker")] --> to_issues{{"/zsl:to-issues"}}
    to_issues -->|"vertical-slice children<br/>with [AFK|HITL] &lt;wave&gt;&lt;letter&gt; titles"| children[("N sub-issues<br/>labeled needs-triage")]
    to_issues -.->|"relabels parent"| prd_tracking[("PRD → tracking")]
    children --> triage{{"/zsl:triage<br/>(one per child)"}}
    triage -->|"per child"| states[("ready-for-agent<br/>ready-for-human<br/>needs-info")]

    classDef skill fill:#e0e7ff,stroke:#3f51b5;
    classDef artifact fill:#dcfce7,stroke:#16a34a;
    class to_issues,triage skill
    class prd,children,prd_tracking,states artifact
```

[`/zsl:to-issues`](../skills/to-issues.md) breaks the PRD into
vertical-slice sub-issues. The `[AFK|HITL] <wave><letter>` title format
is the **dependency contract** that the rest of the loop consumes:

- `[AFK]` = the agent can run it unattended
- `[HITL]` = needs a manual action an agent can't perform (cleared by `/zsl:human-itl`, not a disguised decision)
- `<wave>` = serialisation level (wave 1 before wave 2)
- `<letter>` = parallelism within a wave (same wave = disjoint)

Then [`/zsl:triage`](../skills/triage.md) walks each child through the
state machine. See [the state machine page](state-machine.md) for the
full transition map.

## Phase 3: Build

This is where the two TDD skills diverge — see
[the branching page](branching.md) for the full topology.

```mermaid
flowchart TB
    sub["one ready-for-agent<br/>sub-issue"] --> choice{{"single slice or<br/>parallel fanout?"}}
    choice -->|"single"| tdd["/zsl:tdd &lt;num&gt;<br/>red→green→refactor<br/>one branch"]
    choice -->|"multiple unblocked AFK"| parallel["/zsl:tdd-parallel &lt;PRD&gt;<br/>worktree per slice<br/>wave-by-wave merges"]
    bug["bug or perf regression"] --> diagnose["/zsl:diagnose<br/>repro → minimise →<br/>hypothesise → fix"]

    classDef skill fill:#e0e7ff,stroke:#3f51b5;
    class tdd,parallel,diagnose skill
```

[`/zsl:tdd`](../skills/tdd.md) handles a single sub-issue with the
red-green-refactor loop on whatever branch you're on.
[`/zsl:tdd-parallel`](../skills/tdd-parallel.md) fans out the unblocked
`[AFK]` slices into worktrees and consolidates everything into one
integration PR. Before that PR opens, step 4a enforces a **coverage
gate**: [`/zsl:verify-coverage`](../skills/verify-coverage.md) must have
run against the integrated tip, proving every PRD user story is covered
by a passing test (or routed to the HITL lane). It's an *execution* gate,
not an *outcome* gate — open gaps still pass and ride a later fanout;
only skipping the check is blocked.

[`/zsl:diagnose`](../skills/diagnose.md) sits beside both — the
disciplined bug/perf-regression loop you use when something specific is
broken rather than when you're building new behavior.

### How a slice routes by type

The `[AFK|HITL]` prefix from Phase 2 isn't decoration — it decides
*which* skill picks the slice up. A slice is one of three things, and
only two of them are work:

```mermaid
flowchart TB
    s["a slice from /zsl:to-issues"] --> q{"what does it need?"}
    q -->|"agent can do it"| afk["[AFK]"]
    q -->|"a manual action<br/>a human must perform"| man["[HITL]"]
    q -->|"a decision / review<br/>(no manual action, no code)"| dec["mislabelled —<br/>a decision in disguise"]

    afk --> tddp["/zsl:tdd-parallel<br/>fan out in worktrees"]
    man --> hitl["/zsl:human-itl<br/>walk the human through it,<br/>record it, mark done"]
    hitl --> unblock["dependent [AFK] slices unblock<br/>→ re-run /zsl:tdd-parallel"]
    dec --> leak["process leak"]
    leak --> grill["/zsl:grill-with-docs + ADR<br/>resolve upstream,<br/>then relabel the slice [AFK]"]

    classDef good fill:#dcfce7,stroke:#16a34a;
    classDef ok fill:#fef3c7,stroke:#d97706;
    classDef bad fill:#fee2e2,stroke:#dc2626;
    class afk,tddp,unblock,grill good
    class man,hitl ok
    class dec,leak bad
```

[`/zsl:human-itl`](../skills/human-itl.md) is the serial, human-present
counterpart to the fanout: `/zsl:tdd-parallel` filters `[HITL]` slices
out (an unattended sub-agent can't click a console or rotate a
credential), and `/zsl:human-itl` walks you through those manual actions,
records each as an audit-trail comment, and marks them done so the
`[AFK]` slices that were `Blocked by` them unblock — then it stops with a
hint to re-run the fanout. It never writes code (that's `/zsl:tdd`) and
hard-refuses a slice that's really a decision in disguise, sending you
back to `/zsl:grill-with-docs` + an ADR.

## Phase 4: Ship

```mermaid
flowchart LR
    branch["slice branch with<br/>red→green→refactor commits"] --> commit{{"/zsl:commit"}}
    commit -->|"explicit file list<br/>no -A<br/>no Claude attribution"| committed["clean commit"]
    committed --> review{{"/zsl:code-review"}}
    review -->|"approval gate before fixes"| pr_or_push["ship style"]
    pr_or_push -->|"PR-style"| pr[("PR opened<br/>Closes #&lt;sub-task&gt;")]
    pr_or_push -->|"direct-push"| push[("commits pushed<br/>Closes in commit body")]
    pr_or_push -->|"local-markdown"| mv[("Status: shipped<br/>git mv to done/")]

    classDef skill fill:#e0e7ff,stroke:#3f51b5;
    class commit,review skill
```

[`/zsl:commit`](../skills/commit.md) is non-negotiable for the
commit-crafting step: explicit file lists (never `git add -A`), no
Claude attribution, sub-task and parent issue references in the body.

[`/zsl:code-review`](../skills/code-review.md) runs an issues-only
pre-PR review with an approval gate before applying any fixes — so the
review itself doesn't silently mutate your branch.

Ship behaviour depends on `docs/agents/ship-style.md` (written by
[`/zsl:setup-zsl-superpowers`](../setup.md)). See
[the branching page](branching.md#standalone-zsltdd) for the matrix.

## Phase 5: Track & close

```mermaid
flowchart LR
    pr[("PR merged or<br/>commit pushed")] --> closer["tracker auto-close"]
    closer -->|"GitHub"| labels[("label set on issue<br/>+ project board Status")]
    closer -->|"Local markdown"| mv[("Status: shipped<br/>+ git mv to issues/done/")]
    labels --> parent["last child closed?"]
    mv --> parent
    parent -->|"yes (GitHub)"| auto_close["parent auto-closes"]
    parent -->|"yes (local)"| prompt["/zsl:tdd prompts<br/>'archive feature?'"]
    parent -->|"no"| wait["wait for next child"]

    classDef auto fill:#dcfce7,stroke:#16a34a;
    class closer,auto_close,prompt auto
```

State storage and closure depend on the tracker you picked in
`/zsl:setup-zsl-superpowers`:

- **GitHub project dashboard** — state lives as labels mirrored to the
  project board's `Status` field. PR merge → GitHub closes the child.
  Last child closes → GitHub auto-closes the `tracking` parent.
- **Local markdown** — state is the `Status:` line in each `.md`. Closure
  is folder-based, atomic with the slice commit. Feature-level archive
  is prompted, never automatic.

See [the state machine page](state-machine.md) for the full transition
policy.

## The cross-cutting band

Some skills don't belong to a single phase — they run *across* the
loop:

| Skill | When to reach for it |
|---|---|
| [`/zsl:triage`](../skills/triage.md) | Inbound bug reports / feature requests from outside the loop, or re-evaluating stale issues |
| [`/zsl:diagnose`](../skills/diagnose.md) | Hard bugs and performance regressions, regardless of which phase you're in |
| [`/zsl:improve-codebase-architecture`](../skills/improve-codebase-architecture.md) | Every few days, to fight entropy. Surfaces deepening opportunities informed by `CONTEXT.md` + ADRs |
| [`/zsl:zoom-out`](../skills/zoom-out.md) | Whenever you're lost in a section of code and need higher-level framing |
| [`/zsl:prototype`](../skills/prototype.md) | Off-loop: throwaway exploration of a state machine or UI direction before you commit to a PRD |

## See also

- [Workflow](../workflow.md) — the same loop with slash-command examples and the canonical phase descriptions
- [The triage state machine](state-machine.md) — how issues move between states
- [Git branching in the build phase](branching.md) — what the Build phase actually does to your git tree
