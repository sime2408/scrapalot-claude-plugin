---
name: code-improver
description: |
  Run the Scrapalot code improvement agent on scrapalot-chat (Python/FastAPI).
  Phases: 1=Code Style, 2=Architecture (analysis-only), 3=Docker Verify, 4=Audit.
  (No lint phase — the pre-commit hook runs ruff check + format on every commit.)
  Usage: /scrapalot:code-improver [1|2|3|4|style|architecture|docker|audit]
---

# Scrapalot Code Improver

Dispatches the `scrapalot:code-improver` subagent to systematically improve the scrapalot-chat Python codebase. Runs ONE phase per invocation.

## Phases

| # | Name | What it does |
|---|------|-------------|
| 1 | Code Style | Idioms & modern 3.12+ types, error-handling style, function/class hygiene, dedup, code-level perf & security — with actual fixes |
| 2 | Architecture | WHOLE-SYSTEM analysis: parallel read-only agents trace flows E2E across all repos, evaluate distributed patterns (Saga, CQRS, Circuit Breaker, ...) AND propose restructuring — new/merged microservices, responsibility moves — within the 8 vCPU / 16 GB host budget. Report only, NO code changes |
| 3 | Docker Verify | Restart container, health check, import check, gRPC, workers, error scan |
| 4 | Audit | Ruff status + summary of all improvements, no commit |

There is deliberately no lint phase: the pre-commit hook runs the pinned host
ruff (check + format) on every commit, so the repo is lint-clean by construction.

## Instructions

**Step 1 — Resolve the phase from args.**

| Arg | Phase |
|-----|-------|
| `1`, `style`, `code style`, `phase 1`, `phase1` | Phase 1: Code Style |
| `2`, `architecture`, `arch`, `patterns`, `phase 2`, `phase2` | Phase 2: Architecture |
| `3`, `docker`, `verify`, `phase 3`, `phase3` | Phase 3: Docker Verification |
| `4`, `audit`, `report`, `phase 4`, `phase4` | Phase 4: Audit Report |
| *(no arg or unrecognized)* | Ask user which phase to run |

**Step 2 — If no phase resolved**, list the phases table above and ask: "Which phase would you like to run?"

**Step 3 — Dispatch the subagent.**

Use the Agent tool with:
- `subagent_type: "scrapalot:chat-code-improver"`   (the Python agent; Kotlin is `scrapalot:backend-code-improver`)
- `description: "scrapalot-chat Phase N — [phase name]"`
- `prompt:` the phase instruction below

### Phase prompts

**Phase 1 (Code Style):**
```
Run Phase 1 (Code Style) on scrapalot-chat at /opt/scrapalot/scrapalot-chat.
Follow the PHASE 1 instructions in your agent definition exactly.
Process directories in order: config/ → constants/ → utils/ → models/ → dto/ → repository/
→ connectors/ → background/ → mcp/ → service/chat/ → service/rag/ → service/agents/
→ service/graph/ → service/deep_research/ → service/document/ → service/retriever/
→ service/streaming/ → service/ (remaining) → grpc/ → workers/
Apply fixes: modern 3.12+ types, StrEnum, guard clauses, bare excepts, missing `from e`,
mutable defaults, god classes, duplicate code, sequential awaits, N+1 queries,
SQL text() wrapper, code-level security hygiene.
Then: COMPILE-CHECK → commit → push → report and stop.
```

**Phase 2 (Architecture — analysis only, WHOLE SYSTEM):**
```
Run Phase 2 (Architecture) across the ENTIRE system — all four repos
(scrapalot-ui, scrapalot-gw, scrapalot-backend, scrapalot-chat) plus runtime
topology (workers, Postgres, Neo4j, Redis, nginx, CI runners).
Follow the PHASE 2 instructions in your agent definition exactly:
dispatch parallel READ-ONLY subagents — one per request-flow family
(chat/RAG streaming, document lifecycle, deep research, settings & sync,
auth/billing/quota, notes & collaboration) PLUS two cross-cutting agents
(service boundaries & responsibility separation; runtime topology & resource
envelope). Each flow agent traces its flow end-to-end
(UI → GW → Kotlin → gRPC → Python → datastores) and evaluates the full
pattern catalog with file:line evidence — present / gap / not-applicable.
Synthesize ONE report: current-state responsibility map, restructuring
proposals (new/merged microservices, responsibility moves, redrawn
boundaries — each with resource budget proving it fits 8 vCPU / 16 GB,
Strangler-Fig migration path, blast radius + rollback), and a ranked
top 3-5 shortlist. NO code changes, NO commit — report and stop.
```

**Phase 3 (Docker Verification):**
```
Run Phase 3 (Docker Verification) on scrapalot-chat.
Run: bash ${CLAUDE_PLUGIN_ROOT}/scripts/chat-verify-docker.sh
If issues are found, fix them, then commit and push.
Report results and stop.
```

**Phase 4 (Audit Report):**
```
Run Phase 4 (Audit Report) on scrapalot-chat.
Run `.venv-precommit/bin/ruff check src/ --statistics` (host ruff) for current lint status.
Present the full report: ruff status, code style improvements by category,
architecture findings summary, Docker verification results, files changed
with 1-line descriptions.
Suggest running regression tests. Do NOT commit — report only, then stop.
```
