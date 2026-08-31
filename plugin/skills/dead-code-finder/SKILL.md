---
name: dead-code-finder
description: Identify unused code in scrapalot-chat (Python/FastAPI). Runs parallel agents per directory area, produces a candidate list with confidence levels. Output is for human review — NOT auto-deletion.
---

# Scrapalot Dead Code Finder

Find dead code in `scrapalot-chat/src/main/` using parallel Explore agents. Results are **candidates for review**, not a definitive deletion list — see the false positive guide below before removing anything.

## Why grep-based analysis is not 100% reliable

Grep finds callers by text search. It will **miss** these real-world call patterns:

| Pattern | Example | Risk |
|---|---|---|
| Dynamic attribute access | `getattr(service, method_name)()` | Missed caller |
| Celery task by name | `.signature('tasks.reindex_connector_documents')` | Missed caller |
| Redis Streams dispatch | Event handler matched by event type string | Missed caller |
| RAG strategy by name | Strategy class name in `strategies.py` string registry | Missed caller |
| Config-driven routing | Function name in `config.yaml` or `prompts.yaml` | Missed caller |
| `tests/` not searched | Function called only from integration tests | False positive |
| `__init__.py` re-export | Function imported and re-exported for external use | False positive |
| Pydantic validators | `@validator`, `@root_validator` — called by Pydantic | False positive |
| SQLAlchemy events | `@event.listens_for` — called by SA | False positive |

**Always verify** before deleting: does the function name appear in any `.yaml`, `.json`, string literal, or `getattr` call?

## Scrapalot-specific: NEVER flag as dead code

These patterns are called by framework, not by Python code:

- **gRPC handlers** — methods on `*Servicer` classes matching proto definitions (e.g., `Chat`, `ProcessDocument`, `GetSettings`)
- **Pydantic AI tools** — methods decorated with `@agent.tool` or `@agent.system_prompt`
- **Celery tasks** — functions decorated with `@celery_app.task`
- **Abstract methods** — `@abstractmethod` on ABC subclasses
- **Dunder methods** — `__init__`, `__str__`, `__repr__`, `__enter__`, `__exit__`, etc.
- **Pydantic validators** — `@validator`, `@field_validator`, `@model_validator`
- **SQLAlchemy event listeners** — `@event.listens_for`
- **Background task registration** — Celery auto-discovers tasks by importing modules
- **RAG strategy classes** — registered by class name in `src/main/utils/rag/strategies.py`
- **Proto-generated code** — anything in `grpc/protos/` or `bridge/proto/`

## Confidence scoring

When reporting candidates, assign one of three confidence levels:

| Level | Criteria | Action |
|---|---|---|
| **HIGH** | Not callable by framework, not in any string/config, grep finds 0 callers in `src/` AND `tests/` | Safe to propose deletion |
| **MEDIUM** | No Python callers found, but could be string-dispatched or config-driven | Ask user before deleting |
| **LOW** | Grep finds 0 callers but pattern matches a framework hook or dynamic dispatch risk | Do NOT propose deletion |

## Execution: parallel agents

When the user asks to find dead code, spawn **10 Explore agents in parallel** — one per area. Each agent must:
1. Read all Python files in its area (Glob + Read)
2. List every top-level function, class, and non-dunder class method
3. For each candidate, run Grep across the FULL codebase: `src/main/`, `tests/`, `alembic/`, `scripts/`
4. Also grep for the name as a string literal (catches dynamic dispatch)
5. Skip framework-called patterns (see above)
6. Assign confidence level (HIGH / MEDIUM / LOW)
7. Report only HIGH and MEDIUM candidates

### Area split for 10 agents

| Agent | Directory |
|---|---|
| 1 | `src/main/grpc/services/` |
| 2 | `src/main/service/chat/` |
| 3 | `src/main/service/rag/` (incl. strategies, orchestrators, chunking, citations) |
| 4 | `src/main/service/document/` + `service/document_processing/` |
| 5 | `src/main/service/deep_research/` (incl. agents/, coordination/) |
| 6 | `src/main/service/agents/` (incl. rag_agents/) |
| 7 | `src/main/service/` — remaining: `llm/`, `podcast/`, `paper/`, `speech/`, `graph/`, `desktop_service.py`, etc. |
| 8 | `src/main/background/` + `src/main/workers/` |
| 9 | `src/main/utils/` + `src/main/models/` |
| 10 | `src/main/scripts/` + `alembic/` + commented-out code blocks |

### Agent prompt template

Each agent receives a prompt with this structure:

```
Find dead code candidates in [DIRECTORY].

For each Python file:
1. List every top-level function, class, and class method (skip dunders)
2. For each, run Grep across src/main/, tests/, alembic/, scripts/ for callers
3. Also grep for the name as a quoted string literal (dynamic dispatch)
4. Skip: gRPC Servicer methods, @agent.tool, @celery_app.task, @abstractmethod,
         @validator/@field_validator, @event.listens_for, RAG strategy class names
         registered in strategies.py

Assign confidence:
- HIGH: 0 callers in Python code AND 0 string references
- MEDIUM: 0 Python callers, but name appears as string or in config
- LOW: framework hook risk — omit from report

Report only HIGH and MEDIUM items.
Format: | file:line | name | confidence | reason |
```

## Output format

After collecting all 10 agent results, compile into these sections:

### A) Entire classes/files (highest priority)
Classes where the class itself is never instantiated or imported.

### B) Unused functions by area
Table per area: `file:line | function | confidence | note`

### C) Write-only attributes
Class attributes that are set but never read.

### D) Planned-but-unintegrated code
Fully implemented subsystems not wired into the main execution flow (e.g., a coordinator with 10 methods, none called from orchestrator).

### E) Commented-out code blocks
Files with 5+ consecutive commented Python lines (def, class, return, import).

## Verification before deletion

Before reporting any item as dead code, verify:

```bash
# 1. Check Python callers
grep -rn "function_name" scrapalot-chat/src/ scrapalot-chat/tests/

# 2. Check string references (dynamic dispatch)
grep -rn '"function_name"' scrapalot-chat/src/ scrapalot-chat/configs/

# 3. Check YAML config (RAG strategies, prompts, model names)
grep -rn "function_name" scrapalot-chat/configs/

# 4. Check if it's a Celery task called by task name
grep -rn "function_name" scrapalot-chat/ --include="*.py" --include="*.yaml"
```

## What to do with results

- **Do NOT delete automatically** — present the list to the user for review
- Let the user decide which items to delete
- When deleting: just delete, no deprecation comments, no "removed" stubs
- After deletion: run `docker exec scrapalot-chat python -m pytest tests/` to verify

## Common false positives encountered in this codebase

Based on previous analysis runs:

- **RAG strategies** registered by class name in `strategies.py` — grep finds 0 direct calls but they're instantiated via string lookup
- **Background task progress functions** — may be called from future scheduler code
- **Graph service annotation functions** — scaffolding for planned features, user decides
- **`research_coordinator_agent.py` methods** — planned multi-agent orchestration, not yet wired in
- **`firecrawl_coordinator.py`** — confirmed dead (no string references, no config usage)
