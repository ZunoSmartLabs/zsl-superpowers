---
name: diagnose
description: Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce → minimise → hypothesise → instrument → fix → regression-test. Use when user says "diagnose this" / "debug this", reports a bug, says something is broken/throwing/failing, or describes a performance regression.
---

# Diagnose

A discipline for hard bugs. Skip phases only when explicitly justified.

When exploring the codebase, use the project's domain glossary to get a clear mental model of the relevant modules, and check ADRs in the area you're touching.

## Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a fast, deterministic, agent-runnable pass/fail signal for the bug, you will find the cause — bisection, hypothesis-testing, and instrumentation all just consume that signal. If you don't have one, no amount of staring at code will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**

### Ways to construct one — try them in roughly this order

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with a fixture input, diffing stdout against a known-good snapshot.
4. **Headless browser script** (Playwright / Puppeteer) — drives the UI, asserts on DOM/console/network.
5. **Replay a captured trace.** Save a real network request / payload / event log to disk; replay it through the code path in isolation.
6. **Throwaway harness.** Spin up a minimal subset of the system (one service, mocked deps) that exercises the bug code path with a single function call.
7. **Property / fuzz loop.** If the bug is "sometimes wrong output", run 1000 random inputs and look for the failure mode.
8. **Bisection harness.** If the bug appeared between two known states (commit, dataset, version), automate "boot at state X, check, repeat" so you can `git bisect run` it.
9. **Differential loop.** Run the same input through old-version vs new-version (or two configs) and diff outputs.
10. **HITL bash script.** Last resort. If a human must click, drive _them_ with `scripts/hitl-loop.template.sh` so the loop is still structured. Captured output feeds back to you.

Build the right feedback loop, and the bug is 90% fixed.

### Iterate on the loop itself

Treat the loop as a product. Once you have _a_ loop, ask:

- Can I make it faster? (Cache setup, skip unrelated init, narrow the test scope.)
- Can I make the signal sharper? (Assert on the specific symptom, not "didn't crash".)
- Can I make it more deterministic? (Pin time, seed RNG, isolate filesystem, freeze network.)

A 30-second flaky loop is barely better than no loop. A 2-second deterministic loop is a debugging superpower.

### Non-deterministic bugs

The goal is not a clean repro but a **higher reproduction rate**. Loop the trigger 100×, parallelise, add stress, narrow timing windows, inject sleeps. A 50%-flake bug is debuggable; 1% is not — keep raising the rate until it's debuggable.

### When you genuinely cannot build a loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) access to whatever environment reproduces it, (b) a captured artifact (HAR file, log dump, core dump, screen recording with timestamps), or (c) permission to add temporary production instrumentation. Do **not** proceed to hypothesise without a loop.

Do not proceed to Phase 2 until you have a loop you believe in.

## Phase 2 — Reproduce

Run the loop. Watch the bug appear.

Confirm:

- [ ] The loop produces the failure mode the **user** described — not a different failure that happens to be nearby. Wrong bug = wrong fix.
- [ ] The failure is reproducible across multiple runs (or, for non-deterministic bugs, reproducible at a high enough rate to debug against).
- [ ] You have captured the exact symptom (error message, wrong output, slow timing) so later phases can verify the fix actually addresses it.

Do not proceed until you reproduce the bug.

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses** before testing any of them. Single-hypothesis generation anchors on the first plausible idea.

Each hypothesis must be **falsifiable**: state the prediction it makes.

> Format: "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

If you cannot state the prediction, the hypothesis is a vibe — discard or sharpen it.

**Show the ranked list to the user before testing.** They often have domain knowledge that re-ranks instantly ("we just deployed a change to #3"), or know hypotheses they've already ruled out. Cheap checkpoint, big time saver. Don't block on it — proceed with your ranking if the user is AFK.

## Phase 4 — Instrument

Each probe must map to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:

1. **Debugger / REPL inspection** if the env supports it. One breakpoint beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at the end becomes a single grep. Untagged logs survive; tagged logs die.

**Perf branch.** For performance regressions, logs are usually wrong. Instead: establish a baseline measurement (timing harness, `performance.now()`, profiler, query plan), then bisect. Measure first, fix second.

## Phase 5 — Fix + regression test

Write the regression test **before the fix** — but only if there is a **correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it occurs at the call site. If the only available seam is too shallow (single-caller test when the bug needs multiple callers, unit test that can't replicate the chain that triggered the bug), a regression test there gives false confidence.

**If no correct seam exists, that itself is the finding.** Note it. The codebase architecture is preventing the bug from being locked down. Flag this for the next phase.

If a correct seam exists:

1. Turn the minimised repro into a failing test at that seam.
2. Watch it fail.
3. Apply the fix.
4. Watch it pass.
5. Re-run the Phase 1 feedback loop against the original (un-minimised) scenario.

## Phase 6 — Cleanup + post-mortem

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes (or absence of seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix)
- [ ] Throwaway prototypes deleted (or moved to a clearly-marked debug location)
- [ ] The hypothesis that turned out correct is stated in the commit / PR message — so the next debugger learns

**Then ask: what would have prevented this bug?** If the answer involves architectural change (no good test seam, tangled callers, hidden coupling) hand off to the `/improve-codebase-architecture` skill with the specifics. Make the recommendation **after** the fix is in, not before — you have more information now than when you started.

<!-- BEGIN bundled-book-rules -->

## Bundled book rules

Do not hand-edit content between the `BEGIN`/`END` markers — `scripts/sync_book_rules.py` overwrites it from `vendor/agent-rules-books/`.

### Rules from "Release It!" by Michael T. Nygard

<!-- BEGIN release-it.mini.md v0.5 -->

# OBEY Release It! by Michael T. Nygard

## When to use

Use for services, APIs, jobs, queues, deployment paths, control tooling, and critical flows that must survive production failures, overload, latency, bad data, hostile traffic, and operational mistakes.

## Primary bias to correct

A passing happy path is not production readiness. Design the failure semantics, demand limits, isolation, recovery path, and diagnosis surface before production defines them for you.

## Decision rules

- Assume every dependency, queue, cache, timeout, caller retry, and degraded state can fail in slow, partial, or prolonged ways; code must assume production mess instead of merely tolerating it by accident.
- Prefer designs that fail visibly, limit blast radius, shed load, preserve core service, and make diagnosis possible over designs that maximize coupling or ideal-path elegance.
- Treat deployment, operations, security, observability, rollback, build and runtime state, dependency state, and configuration validation as part of the system, not after-release chores.
- Put explicit, intentional time limits on outbound calls and waits. Do not rely on library defaults or allow infinite waits where finite response matters.
- Retry only when the operation is safe for the caller and provider; bound count and total time, use backoff or jitter, and do not retry validation errors or permanent failures.
- Isolate dependency and workload failures with circuit breakers, fast failure, bulkheads, separate resource pools, and slow-work isolation so one outage cannot consume all threads, connections, or workers.
- Design overload behavior explicitly with back pressure, finite queues, demand limits, capacity reserved for critical traffic, and load shedding of lower-value work before core functions collapse.
- Use stability patterns by failure mode: steady state for routine cleanup and bounded growth, fail fast when continuing hides unrecoverable trouble or holds scarce resources, let-it-crash only with supervision and isolation, handshaking for readiness, decoupling middleware with monitoring, and governors for expensive behavior.
- Make runtime state, external responses, automation progress, migrations, operational assumptions, and boundary data visible and validated before trusted; keep rollback or roll-forward paths for partial operational changes.
- Budget scarce resources explicitly, release them deterministically, avoid holding locks or expensive connections across slow remote calls, and stream or paginate large payloads instead of defaulting to huge in-memory batches.
- Treat external input and external responses as untrusted: validate syntax, shape, business plausibility, status, content type, and semantics; prevent malformed data from poisoning caches, queues, or downstream systems.
- Build observability into boundaries and failure points with structured context, correlation identifiers, latency, throughput, error, saturation, queue, retry, breaker, dependency, version, configuration, health, and runtime signals while avoiding secrets and retry-storm log spam.
- Make startup, health checks, migrations, one-time jobs, administrative controls, process code, and delivery tooling fail safely, auditable, authorized, observable, stoppable, and recoverable.
- Make interconnects, routing, API contracts, caches, scheduled work, and background work production-aware: avoid concentrated demand, hidden single points of failure, uncontrolled fan-out, fragile chattiness, cache dogpiles, stale data surprises, and synchronized job retries.
- Include security and hostile traffic in production readiness, and use production tests, launch checks, capacity tests, game days, chaos, or disaster simulations only with limited blast radius, observability, stop conditions, and feedback into design.

## Trigger rules

- When adding an outbound call, dependency operation, resource checkout, queue consume, or thread wait, define timeout, retry eligibility, retry bounds, fallback or degraded mode, validation, and caller-survival behavior.
- When adding a queue, buffer, resource pool, cache, log stream, background job, scheduled job, or collection-returning API, define capacity, full behavior, cleanup, miss/stampede/staleness behavior, pacing, pagination or streaming, and saturation monitoring.
- When a change touches deployment, configuration, startup, migrations, one-time jobs, scripts, or operational automation, make it idempotent or restartable where practical and give it durable state, auditability, verification, and rollback or roll-forward.
- When adding health checks, load balancing, service discovery, routing, or inter-service handshakes, ensure traffic reaches only ready components and health signals reflect real ability to serve.
- When designing API or integration contracts, make material failure modes explicit, distinguish retryable from non-retryable outcomes, prefer coarse-grained resilient interactions, and document timeout, retry, version, and compatibility expectations.
- When reviewing an incident, performance failure, or capacity issue, identify the failure chain, missing defenses, detection gaps, demand, saturation, latency distribution, queue age, dependency behavior, traffic concentration, and design changes.
- When adding administrative controls, control planes, delivery tooling, hostile-traffic handling, or chaos/disaster work, require authorization, auditability, safe defaults, clear stop mechanisms, bounded blast radius, and recovery paths.

## Final checklist

- Explicit timeouts and no infinite waits?
- Retries safe, bounded, backed off or jittered, and not duplicated across layers?
- Queues, buffers, pools, caches, logs, payloads, jobs, and result sets bounded?
- Failure isolated with breakers, bulkheads, fast failure, degradation, or load shedding?
- External input and dependency responses validated before they affect state, caches, queues, or downstream systems?
- Diagnostics cover logs, metrics, health, correlation, runtime, version, configuration, dependencies, saturation, queue depth, retries, and breaker state?
- Startup, deployment, migration, automation, and operational controls restartable, observable, authorized, auditable, and recoverable where practical?
- Interconnects, APIs, caches, scheduled work, security, and chaos tests have explicit production failure behavior?

<!-- END release-it.mini.md -->

<!-- END bundled-book-rules -->
