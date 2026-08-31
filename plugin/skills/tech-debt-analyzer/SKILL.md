---
name: tech-debt-analyzer
description: Use this skill when analyzing technical debt in the Scrapalot-Chat Python/FastAPI codebase. Identifies code smells, RAG strategy inefficiencies, database design issues, missing tests, async/await anti-patterns, dependency problems, and creates comprehensive technical debt documentation.
---

# Technical Debt Analyzer (Scrapalot-Chat)

## Overview

Systematically identify, analyze, document, and track technical debt in Scrapalot-Chat's Python/FastAPI RAG application. Specialized analysis for RAG systems, async patterns, multi-database architecture, and comprehensive debt categorization.

## Python-Specific Debt Categories

### 1. RAG System Debt

**Indicators:**
- RAG strategies without reranking
- Missing caching for repeated queries
- No fallback strategies when primary fails
- Hardcoded prompts instead of config-driven
- Inefficient document retrieval (N+1 queries)
- Missing error handling in async generators
- No monitoring/metrics for strategy performance

**Example:**
```python
# DEBT: No reranking, hardcoded prompt
async def execute(self, query, collection_ids):
    docs = await self.retriever.process(query)
    # Missing: rerank_documents(query, docs, self.retriever)

    prompt = f"Answer: {query}"  # Hardcoded, should be in config
    return prompt
```

### 2. Async/Await Anti-Patterns

**Indicators:**
- Sequential await when parallel is possible
- Blocking I/O in async functions
- Missing async context managers
- Unhandled asyncio.CancelledError
- No timeout on external API calls

**Example:**
```python
# DEBT: Sequential when parallel is better
async def process_documents(doc_ids):
    results = []
    for doc_id in doc_ids:
        result = await process_document(doc_id)  # Sequential!
        results.append(result)

# SHOULD BE:
async def process_documents(doc_ids):
    tasks = [process_document(id) for id in doc_ids]
    results = await asyncio.gather(*tasks)  # Parallel!
```

### 3. Database Architecture Debt

**Indicators:**
- Missing RLS policies on user-scoped tables
- No indexes on frequently queried columns
- Hardcoded schema names (breaks SQLite compatibility)
- Direct SQL without `text()` wrapper
- Missing dialect-aware migrations
- Inefficient pgvector index configuration
- No connection pooling limits

**Example:**
```python
# DEBT: Breaks cross-database compatibility
query = f"SELECT * FROM scrapalot.users WHERE id = '{user_id}'"

# SHOULD BE:
from src.main.utils import db_utils
table_name = db_utils.get_table_name('users')
query = text(f"SELECT * FROM {table_name} WHERE id = :user_id")
result = db.execute(query, {"user_id": user_id})
```

### 4. Type Hint Debt

**Indicators:**
- Functions missing return type hints
- Use of `Any` type without justification
- Missing Optional for nullable parameters
- No type hints for complex data structures
- Untyped dictionary returns (should use dataclasses/Pydantic)

**Example:**
```python
# DEBT: No type hints
def process_request(request, db, user_id):
    result = do_something(request)
    return result

# SHOULD BE:
from typing import Dict, Optional
from src.main.dto.chat_request import ChatRequest

def process_request(
    request: ChatRequest,
    db: Session,
    user_id: str
) -> Dict[str, Any]:
    result = do_something(request)
    return result
```

### 5. Error Handling Debt

**Indicators:**
- Bare `except:` clauses
- Swallowed exceptions (pass in except)
- No exception chaining (`from e`)
- Missing `exc_info=True` in error logs
- Generic HTTPException without detail

**Example:**
```python
# DEBT: Poor error handling
try:
    result = process()
except:  # Too broad!
    pass  # Swallowed!

# SHOULD BE:
try:
    result = process()
except ValueError as e:
    logger.error("Validation error: %s", str(e), exc_info=True)
    raise HTTPException(status_code=400, detail=str(e)) from e
```

### 6. Testing Debt

**Indicators:**
- RAG strategies without unit tests
- Controllers without integration tests
- No tests for database migrations
- Missing tests for error conditions
- Tests that depend on execution order
- Low coverage (<80%) for critical paths

**Analysis:**
```bash
# Check coverage
python -m pytest --cov=src/main --cov-report=term-missing

# Find untested files
find src/main -name "*.py" ! -name "__init__.py" | while read f; do
    test_file="tests/${f#src/main/}"
    test_file="${test_file%.py}_test.py"
    [ ! -f "$test_file" ] && echo "Missing: $test_file for $f"
done
```

### 7. Configuration Debt

**Indicators:**
- Hardcoded configuration values
- Secrets in code or version control
- No environment variable fallbacks
- Configuration scattered across files
- Missing validation for required settings

**Example:**
```python
# DEBT: Hardcoded configuration
API_KEY = "sk-abc123..."  # Never hardcode!
TIMEOUT = 30  # Should be configurable

# SHOULD BE:
from src.main.utils.config_loader import resolved_config
api_key = resolved_config["secrets"]["openai_api_key"]
timeout = resolved_config.get("api", {}).get("timeout", 30)
```

### 8. Dependency Debt

**Indicators:**
- Outdated packages (check `pip list --outdated`)
- Security vulnerabilities (check `pip-audit`)
- Unused dependencies in requirements.txt
- Missing version pins (allows breaking changes)
- Conflicting dependency versions

**Analysis:**
```bash
# Check for outdated packages
pip list --outdated

# Security audit
pip-audit

# Find unused imports
pylint src/main --disable=all --enable=unused-import
```

## Analysis Workflow

### Step 1: Automated Code Analysis

Use `pylint` and `flake8` for automated detection:

```bash
# Comprehensive analysis
pylint src/main --rcfile=.pylintrc --output-format=text > debt_analysis.txt

# Check specific issues
flake8 src/main --max-complexity=10 --max-line-length=100

# Type checking
mypy src/main --strict
```

### Step 2: RAG-Specific Analysis

Check RAG strategy implementation quality:

```python
# Checklist for each strategy:
# - [ ] Inherits from RAGStrategy
# - [ ] Uses reranking
# - [ ] Handles empty results
# - [ ] Async generator pattern
# - [ ] Emits status updates
# - [ ] Prompts from config
# - [ ] Has unit tests (>80% coverage)
# - [ ] Documented in README_RAG_ARCHITECTURE.md
```

### Step 3: Database Schema Review

```sql
-- Check missing indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'scrapalot'
ORDER BY tablename;

-- Check missing RLS policies
SELECT tablename, policyname
FROM pg_policies
WHERE schemaname = 'scrapalot';

-- Check vector index configuration
SELECT indexname, indexdef
FROM pg_indexes
WHERE indexdef LIKE '%vector%';
```

### Step 4: Async Code Review

Look for these anti-patterns:

```python
# Anti-pattern 1: Blocking in async
async def bad_async():
    time.sleep(1)  # BAD! Use asyncio.sleep()

# Anti-pattern 2: Sequential awaits
async def bad_sequential():
    a = await fetch_a()  # Sequential
    b = await fetch_b()  # Should use gather()

# Anti-pattern 3: No timeout
async def bad_no_timeout():
    await external_api_call()  # Might hang forever
```

### Step 5: Document Findings

Use the debt register template:

```markdown
## DEBT-001: RAG strategies missing reranking

**Category:** RAG System / Performance
**Severity:** High
**Location:** src/main/service/rag/

**Description:**
5 out of 13 RAG strategies don't use reranking, resulting in lower
quality document retrieval.

**Impact:**
- Business: Users get less relevant answers (30-40% quality drop)
- Technical: Inconsistent strategy quality
- Risk: User dissatisfaction, poor metrics

**Affected Files:**
- src/main/service/rag/rag_multi_query.py
- src/main/service/rag/rag_step_back.py
- src/main/service/rag/rag_decomposition.py

**Proposed Solution:**
Add `rerank_documents()` call after retrieval in each strategy:

    documents = await rerank_documents(
        query=query,
        documents=documents,
        retriever=self.retriever
    )

**Effort Estimate:** 2 hours (straightforward fix)
**Priority:** High (affects user experience)
**Target Resolution:** Sprint 24
```

## Severity Assessment

### Critical (Fix Immediately)

- Security vulnerabilities (SQL injection, XSS)
- Data loss risks (missing RLS, unsafe migrations)
- Production crashes (unhandled exceptions)
- Secrets in version control

### High (Fix This Sprint)

- Missing tests for critical paths (RAG strategies, auth)
- Performance issues (N+1 queries, missing indexes)
- Async anti-patterns causing slowness
- Missing error handling in key flows

### Medium (Fix This Quarter)

- Type hint gaps
- Missing documentation
- Inconsistent code style
- Outdated dependencies (non-security)
- Moderate code smells

### Low (Address When Convenient)

- Minor refactoring opportunities
- Nice-to-have optimizations
- Non-critical documentation gaps
- Low-impact code duplication

## Prevention Strategies

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        args: [--rcfile=.pylintrc, --fail-under=8.0]

      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
        args: [--strict]

      - id: tests
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        args: [tests/, --cov=src/main, --cov-fail-under=80]
```

### Code Review Checklist

Before approving PRs:

- [ ] All functions have type hints
- [ ] Async code uses gather() for parallel operations
- [ ] Database queries use dialect-aware helpers
- [ ] Errors logged with `exc_info=True`
- [ ] Tests added/updated (80%+ coverage)
- [ ] No hardcoded config or secrets
- [ ] RAG strategies use reranking
- [ ] RLS policies added for user-scoped tables

## Metrics to Track

### Code Quality Metrics

```bash
# Test coverage
pytest --cov=src/main --cov-report=term

# Type coverage
mypy --strict src/main | grep "Found"

# Complexity
radon cc src/main -a -nb  # Average complexity

# Maintainability index
radon mi src/main
```

### RAG System Metrics

- Strategy execution time (p50, p95, p99)
- Document retrieval accuracy
- Reranking effectiveness
- Cache hit rate
- Query latency

### Database Metrics

- Query execution time
- Connection pool usage
- RLS policy hit rate
- Vector index usage

## Reference

- `docs/README_RAG_ARCHITECTURE.md` - RAG best practices
- `docs/README_DATABASE_DESIGN.md` - Database design patterns
- `CLAUDE.md` - Project conventions
- `.pylintrc` - Linting configuration
