---
description: "Sequential code improvement: one phase at a time, one repo at a time. After each phase: compile → commit → push → STOP and wait for user. Phases: Code Style → Architecture (analysis-only) → Docker Verify → Audit. (No lint phase — pre-commit hooks cover linting.)"
argument-hint: "[chat|backend] [style|arch|docker|audit] [style sub-check]"
allowed-tools: Agent, Bash, Read, Grep, Glob, Edit, Write, TaskCreate, TaskUpdate, TaskList
---

# Scrapalot Code Improvement — Full Stack (Phase by Phase)

Runs code improvement **one phase, one repo at a time**. After each phase the agent compiles, commits, pushes, and STOPS to report. User decides when to continue.

## Arguments

Invoked with: `$ARGUMENTS` — order-independent tokens (all optional):

- **repo** — `chat` (Python) or `backend` (Kotlin). Required for `style` / `docker` / `audit`.
  **Omitted for `architecture`** — that phase is WHOLE-SYSTEM: it looks at every repo
  plus the runtime topology at once, so a repo token is ignored. `arch` is the one
  phase that runs alone: `/scrapalot:improve-all arch`.
- **phase** — one of:

| Phase | What it does | Repo | Shorthand |
|---|---|---|---|
| `style` | Code-level style, idioms, error handling, dedup, perf & security hygiene — real fixes, commits | required | `1` |
| `architecture` | Whole-system E2E analysis + restructuring proposals — analysis-only, no commit | **none** | `2` · `arch` |
| `docker` | Docker verification: restart + health + imports + gRPC + workers + error scan | required | `3` |
| `audit` | Final report of the run (ruff status, summary) — no commit | required | `4` |

- **style sub-check** (optional, only with `style`) — narrow Phase 1 to ONE aspect instead of running all of it:

| Sub-check | Focus | Alias |
|---|---|---|
| `idioms` | Modern-language idioms, comprehensions, guard clauses, naming (Phase 1 §A) | |
| `errors` | Exception handling: bare `except`, `from e`, lazy `%s` logging (§B) | |
| `hygiene` | Function/class hygiene: god classes, mutable defaults, duplicate blocks (§C) | |
| `perf` | Code-level perf: `asyncio.gather`, N+1 queries, `join()` (§D) | |
| `security` | Security hygiene: `text()` SQL, input validation, unsafe eval/pickle, path traversal (§E) | |
| `dedup` | Extract duplicate code into shared utilities (Phase 1-B) | `reuse` |

A sub-check implies `style`, so `chat security` == `chat style security`. Multiple are allowed (`chat security perf`).

Examples:
- `/scrapalot:improve-all arch` — whole-system architecture analysis, no repo (the only phase that goes alone).
- `/scrapalot:improve-all chat style` — full Code Style pass on scrapalot-chat.
- `/scrapalot:improve-all chat security` — Phase 1 on chat, only the security-hygiene sub-check.
- `/scrapalot:improve-all backend dedup` — Phase 1 on backend, only deduplication / reuse.
- `/scrapalot:improve-all docker backend` — order-free → Docker verify on backend.
- `/scrapalot:improve-all chat` — phase omitted → next logical phase for chat.
- `/scrapalot:improve-all` — no args → ask, or default to the next logical phase.
- `/scrapalot:improve-all help` — print this table and stop.

## Your Task

**First, resolve `$ARGUMENTS`:**

1. If it contains `help` or `?` → print the Arguments table above and STOP (nothing else).
2. Split into whitespace-separated tokens and classify each (case-insensitive):
   - `chat` / `backend` → **repo**
   - `style` / `architecture` (`arch`) / `docker` / `audit`, or shorthand `1`–`4` → **phase**
   - `idioms` / `errors` / `hygiene` / `perf` / `security` / `dedup` (`reuse`) → **style sub-check** (implies phase `style`)
   - anything else → unknown token: show the Arguments table, name the invalid token, and STOP.
3. `architecture` is whole-system — it takes NO repo; ignore any repo token supplied with it.
4. `style` / `docker` / `audit` with no repo token → ask which repo (or pick the next logical one).
5. A style sub-check with a non-`style` phase (e.g. `docker security`) is a conflict → tell the user, ask which they meant.
6. Once resolved → launch the agent **directly** (map name → agent phase: `style`=1, `architecture`=2, `docker`=3, `audit`=4).
   If one or more style sub-checks were given, tell the agent to run ONLY those Phase 1 sub-sections
   (`idioms`=§A, `errors`=§B, `hygiene`=§C, `perf`=§D, `security`=§E, `dedup`=Phase 1-B) and skip the rest.
   No extra confirmation.

If NO arguments were given, fall back to the interactive path: ask the user which repo and phase to run, OR default to the next logical phase.

### Repo + Phase Selection

Repos and phases are the tokens documented under **## Arguments** above
(`chat` / `backend`; phases `style` / `architecture` / `docker` / `audit`).
The notes below add per-phase detail.

There is no lint phase: scrapalot-chat runs ruff check + format in its
pre-commit hook, so every commit is lint-clean already. For a one-off manual
lint pass use host ruff (`.venv-precommit/bin/ruff`) directly, outside this
workflow.

Phase 2 (Architecture) is special: it is WHOLE-SYSTEM, not per-repo — repo
selection does not apply to it. It dispatches PARALLEL read-only subagents:
one per request-flow family tracing the flow end-to-end
(UI → GW → Kotlin → gRPC → Python → datastores), plus cross-cutting agents
for service boundaries/responsibility separation and runtime topology/resource
envelope. It evaluates the distributed-pattern catalog (Saga, Event Sourcing,
API Gateway, Circuit Breaker, Bulkhead, Retry, CQRS, Database per Service,
Data Sharding, Polyglot Persistence, Sidecar, Smart Endpoints/Dumb Pipes,
Async Messaging, Consumer-Driven Contracts, Strangler Fig, Shadow Deployment,
Stateless Services, Outbox, Idempotent Consumer, DLQ, Backpressure,
Cache-Aside, ...) with file:line evidence AND proposes restructuring — new or
merged microservices, responsibility moves, redrawn service boundaries — where
every proposal must include a resource budget proving it fits the 8 vCPU /
16 GB Hetzner host, a Strangler-Fig migration path, and blast radius +
rollback. Proposals that don't fit the host are rejected, not deferred.
NO code changes, NO commit. Implementation of any recommendation goes through
a PRD and explicit user approval. Read-only parallelism is exempt from the
one-agent-at-a-time rule (no builds, no OOM risk).

### Launch Agent

`[phase-specific instructions]` below carries the phase detail AND any narrowing:
when a `style` sub-check was resolved, spell out "run ONLY Phase 1 §A/§B/§C/§D/§E
or Phase 1-B for <sub-check>, skip the other sub-sections" so the agent scopes its pass.

For **scrapalot-chat**:
```
subagent_type: "scrapalot:code-improver"  (from scrapalot-chat/.claude/agents/)
Prompt: "Run Phase [N] on scrapalot-chat. [phase-specific instructions].
After: compile-check → commit → push → STOP and report."
```

For **scrapalot-backend**:
```
subagent_type: "scrapalot:code-improver"  (from scrapalot-backend/.claude/agents/)
Prompt: "Run Phase [N] on scrapalot-backend. [phase-specific instructions].
After: compile-check → commit → push → STOP and report."
```

### After Agent Completes

1. Present the agent's report to the user
2. Suggest next phase/repo
3. Wait for user confirmation before launching next

### Workflow Example

```
User: /scrapalot:improve-all
→ Agent runs Phase 1 (Code Style) on chat → compile → commit → push → report
→ "Phase 1 done on chat. 24 files improved. Run Phase 1 on backend?"
→ User: "da"
→ Agent runs Phase 1 (Code Style) on backend → compile → commit → push → report
→ "Phase 1 done on backend. Run Phase 2 (Architecture) — parallel E2E flow analysis?"
→ User: "da"
→ Parallel read-only agents trace flows → synthesized ranked report, no commit
→ ... and so on
```

## Important Notes

- **ONE agent at a time** for phases that compile or run builds — prevents OOM
  on 16GB Hetzner. Phase 2's read-only analysis agents may run in parallel.
- **STOP after each phase** — user controls pace
- Regression tests only run when user explicitly asks
- Each phase is independently valuable — no need to run all 4
