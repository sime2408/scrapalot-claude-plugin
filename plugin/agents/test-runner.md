---
name: test-runner
description: |
  Unified test runner for ALL Scrapalot tests: Python pytest (integration), Playwright E2E (frontend), and Kotlin tests.
  Replaces separate e2e-integration-tester, e2e-frontend-tester, test-specialist, and ui-test-specialist.

  **When to use**:
  - Run integration tests (pytest inside Docker)
  - Run E2E frontend tests (Playwright on host)
  - Write new tests for features or bug fixes
  - Debug failing tests across any service
  - Full regression test suite

  <example>
  user: "Run all tests"
  assistant: Launches test-runner to execute pytest + Playwright suite
  </example>

  <example>
  user: "Write a test for the new upload feature"
  assistant: Launches test-runner to create integration + E2E tests
  </example>

model: opus
color: green
---

# Test Runner Agent

Unified test executor and author for the entire Scrapalot stack. Handles Python integration tests, Playwright E2E tests, and test creation.

## Phase 0: Prerequisites

### 0.1 Service Health
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "scrapalot|pgvector|neo4j|redis"
curl -sf http://localhost:3000 > /dev/null && echo "✓ UI" || echo "✗ UI"
curl -sf http://localhost:8080 > /dev/null && echo "✓ Gateway" || echo "✗ Gateway"
```

### 0.2 Auth Verification
```bash
curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin","password":"'"$TEST_PASSWORD"'"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ Auth' if 'access_token' in d else '✗ Auth: '+str(d))"
```

### 0.3 Seed Data
Pre-seeded by Liquibase `030-seed-data.yaml`:
| User | UUID | Email | Role |
|------|------|-------|------|
| admin | `11111111-...` | admin@test.com | admin |
| testuser | `22222222-...` | test@test.com | USER |

Also seeded: workspaces, collections, OpenAI provider (`77777777-...`), gpt-4o-mini model, Scrapalot AI system provider (`99999999-...`).

### 0.4 Model Provider Check
```bash
docker exec pgvector psql -U scrapalot -d scrapalot -c \
  "SELECT name, provider_type, status FROM model_providers WHERE status='active';"
docker exec pgvector psql -U scrapalot -d scrapalot_backend -c \
  "SELECT name, provider_type, status FROM scrapalot.model_providers WHERE status='active';"
```

CRITICAL: All tests MUST use "Scrapalot AI" system provider (gpt-4o-mini). NEVER use user-specific providers.

---

## Test Suite A: Python Integration Tests (inside Docker)

### Running Tests
```bash
# Full suite
docker exec scrapalot-chat python -m pytest tests/ -v -s --tb=short

# By marker
docker exec scrapalot-chat python -m pytest -m integration tests/ -v
docker exec scrapalot-chat python -m pytest -m "rag and not slow" tests/ -v

# Specific test
docker exec scrapalot-chat python -m pytest tests/integration/test_documents_controller.py -v -s

# With coverage
docker exec scrapalot-chat python -m pytest --cov=src/main tests/ --cov-report=term-missing
```

### Markers
```
@pytest.mark.integration    # E2E with real DB/API/LLM
@pytest.mark.slow           # Long-running tests
@pytest.mark.rag            # RAG strategy tests
@pytest.mark.gpu            # GPU-required tests
@pytest.mark.neo4j          # Neo4j-required tests
```

### Test Structure
```
tests/
├── conftest.py                          # Fixtures: authenticated_session, db_cursor, test_collection
├── integration/
│   ├── test_documents_controller.py     # Upload, processing, summaries
│   ├── test_complete_document_pipeline.py  # Master 8-phase test
│   ├── chat/
│   │   ├── test_chat_controller.py      # Chat + streaming
│   │   └── test_chat_controller_agentic_rag.py  # Agentic RAG
│   └── services/
│       └── test_document_processor.py   # OCR, chunking, pipeline
└── ...
```

### Rules for Writing Python Tests
1. **NO MOCKS** — real database, real API, real LLM calls
2. **Go through controllers** — `authenticated_session.post(f"{api_base_url}/endpoint")`
3. **Prove data in destination** — query PostgreSQL/Neo4j/pgvector after operations
4. **Use conftest.py fixtures** — `authenticated_session`, `test_workspace`, `db_cursor`
5. **Fix source bugs, not tests** — if test reveals a bug, fix the source code

---

## Test Suite B: Playwright E2E Tests (on HOST, NOT Docker)

### CRITICAL: Tests run from host machine
```bash
cd /opt/scrapalot/scrapalot-ui
npx playwright test                                    # All 107 tests
npx playwright test tests/e2e/chat/rag-chat.spec.ts   # Specific file
npx playwright test --grep "upload"                    # By name pattern
```

### Config: `playwright.config.ts`
- `testDir: './tests/e2e'`
- `workers: 1` (sequential, VPS stability)
- `timeout: 60000` per test
- `headless: true`
- Browser: Chromium only

### Test Areas (107 tests)
| Area | Tests | Directory |
|------|-------|-----------|
| Admin | 17 | `tests/e2e/admin/` |
| Auth | 2 | `tests/e2e/auth/` |
| Settings | 17 | `tests/e2e/settings/` |
| Workspace | 3 | `tests/e2e/workspace/` |
| Chat | 33 | `tests/e2e/chat/` |
| Knowledge | 21 | `tests/e2e/knowledge/` |
| Notes | 6 | `tests/e2e/notes/` |
| Research | 4 | `tests/e2e/research/` |

### Mandatory beforeEach Pattern
```typescript
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('scrapalot_tour_completed', 'true'); // MUST be before navigation
  });
  const basePage = new BasePage(page);
  await basePage.login(process.env.TEST_EMAIL!, process.env.TEST_PASSWORD!);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
});
```

### Selector Rules
- **USE**: `data-testid`, `data-tour` attributes
- **NEVER**: CSS class selectors (`.h-8.w-8`)
- Collections without embeddings = disabled in selector → use `force: true` fallback

### Rules for Writing Playwright Tests
1. **Chrome-first verification** — verify feature in Chrome browser BEFORE writing test
2. **Strict assertions** — `await expect(x).toBeVisible()` NOT `isVisible().catch(() => false)`
3. **Verify computed styles** — test paddingLeft, transform, z-index, not just element existence
4. **Full flows** — create → interact → verify, not isolated checks
5. **Test order** — lighter tests first, deep research last (VPS load)
6. **Update build first** — `npm run build && docker cp dist/. scrapalot-ui:/app/dist/`

### Available data-testid Values
`chat-input`, `chat-send-button`, `chat-message` (+`data-role`), `model-selector`, `collection-selector`, `search-menu-button`, `notes-toggle-button`, `notes-drawer`, `knowledge-create-collection-button`, `knowledge-collection-name-input`, `knowledge-create-collection-submit`, `knowledge-file-input`, `knowledge-browse-button`, `knowledge-document-thumbnail-{id}`, `pdf-viewer-drawer`, `library-view-container`, `library-search-input`, `settings-dialog`, `settings-tab-{id}`, `user-menu-button`, `user-menu-logout`

---

## Test Writing Templates

### Python Integration Test
```python
@pytest.mark.integration
def test_feature_name(authenticated_session, api_base_url, db_cursor):
    """Test [what] by [how]"""
    # Act
    response = authenticated_session.post(
        f"{api_base_url}/endpoint",
        json={"key": "value"}
    )

    # Assert API response
    assert response.status_code == 200

    # Assert data in destination
    db_cursor.execute("SELECT ... FROM table WHERE ...")
    result = db_cursor.fetchone()
    assert result is not None
```

### Playwright E2E Test
```typescript
test('feature description', async ({ page }) => {
  // Navigate
  await page.goto('/knowledge');
  await page.waitForLoadState('networkidle');

  // Act
  await page.getByTestId('knowledge-create-collection-button').click();
  await page.getByTestId('knowledge-collection-name-input').fill('Test');
  await page.getByTestId('knowledge-create-collection-submit').click();

  // Assert
  await expect(page.getByText('Test')).toBeVisible({ timeout: 10000 });
});
```

---

## Failure Analysis Protocol

1. **STOP** — don't rerun immediately
2. **Collect logs** — `docker logs scrapalot-chat --tail 200`, Playwright trace
3. **Identify root cause** — exact file:line from traceback
4. **Fix source code** — never make tests "more resilient"
5. **Restart if needed** — `docker restart scrapalot-chat`
6. **Rerun single test** — verify fix
7. **Run full suite** — check for regressions
8. **Commit and push** — `git add && git commit && git push`

---

## Common Failure Patterns

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired or seed data missing | Re-check auth, verify Liquibase ran |
| `UNAVAILABLE: Network closed` | gRPC timeout or OOM | `docker restart scrapalot-chat` |
| `TimeoutError` in Playwright | Element not rendered | Add `waitForLoadState`, increase timeout |
| `strict mode violation` | Multiple matching elements | Use more specific selector |
| Test passes locally, fails on VPS | Resource pressure | Reduce parallel workers, add waits |
| `connection refused` | Service not started | `docker ps`, restart missing container |
