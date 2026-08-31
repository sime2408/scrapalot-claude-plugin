---
description: Full-stack code quality audit — model providers, database schema, Redis sync, dead code across all services
allowed-tools: Bash, Read, Grep, Glob
---

## Context

Scrapalot uses two PostgreSQL databases (`scrapalot` for Python, `scrapalot_backend` for Kotlin), Redis Streams SAGA for cross-service sync, and multiple LLM providers. This command audits all of them in one pass.

## Your Task

Run a comprehensive code quality and infrastructure audit.

### Part 1: Model Provider Audit

1. **List providers in BOTH databases:**
   ```bash
   docker exec pgvector psql -U scrapalot -d scrapalot -c "
     SELECT id, name, provider_type,
       CASE WHEN api_key IS NOT NULL AND api_key != '' THEN 'YES' ELSE 'NO' END as has_key,
       status, user_id IS NULL as is_system
     FROM public.model_providers ORDER BY name;"

   docker exec pgvector psql -U scrapalot -d scrapalot_backend -c "
     SELECT id, name, provider_type,
       CASE WHEN api_key IS NOT NULL AND api_key != '' THEN 'YES' ELSE 'NO' END as has_key,
       status, user_id IS NULL as is_system
     FROM scrapalot.model_providers ORDER BY name;"
   ```

2. **Check sync drift** — same provider IDs should exist in both DBs.

3. **List models per provider:**
   ```bash
   docker exec pgvector psql -U scrapalot -d scrapalot -c "
     SELECT p.name as provider, m.model_name, m.model_type
     FROM model_provider_models m
     JOIN model_providers p ON p.id = m.provider_id
     ORDER BY p.name, m.model_name;"
   ```

4. **Verify system AI provider** — exactly ONE with `user_id IS NULL`, active, has models.

### Part 2: Database Schema Audit

1. **List tables in both databases:**
   ```bash
   docker exec pgvector psql -U scrapalot -d scrapalot -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
   docker exec pgvector psql -U scrapalot -d scrapalot_backend -c "SELECT tablename FROM pg_tables WHERE schemaname='scrapalot' ORDER BY tablename;"
   ```

2. **Check Redis Streams status:**
   ```bash
   REDIS_PASS=$(docker exec scrapalot-chat python -c "from src.main.config.config import get_config; print(get_config().get('redis',{}).get('password',''))" 2>/dev/null)
   for stream in collections workspaces connectors user_settings model_providers token_usage; do
     echo "=== scrapalot:stream:$stream ==="
     docker exec redis redis-cli -a "$REDIS_PASS" XINFO GROUPS "scrapalot:stream:$stream" 2>/dev/null || echo "  (not found)"
   done
   docker exec redis redis-cli -a "$REDIS_PASS" XLEN scrapalot:dlq:cwm_sync 2>/dev/null
   ```

3. **Redis snapshot health:**
   ```bash
   docker exec redis redis-cli -n 1 -a "$REDIS_PASS" EXISTS scrapalot:sync:collection_workspace_snapshot
   docker exec redis redis-cli -n 0 -a "$REDIS_PASS" EXISTS scrapalot:sync:model_providers_snapshot
   ```

### Part 3: Dead Code Scan

1. **Python — unused imports and functions:**
   ```bash
   docker exec scrapalot-chat python -c "
   import ast, os, sys
   dead = []
   for root, dirs, files in os.walk('/app/src/main'):
       for f in files:
           if f.endswith('.py'):
               path = os.path.join(root, f)
               try:
                   tree = ast.parse(open(path).read())
                   # Check for TODO/FIXME/HACK
                   content = open(path).read()
                   for i, line in enumerate(content.split('\n'), 1):
                       for tag in ['TODO', 'FIXME', 'HACK', 'XXX']:
                           if tag in line and '#' in line:
                               dead.append(f'{path}:{i}: {line.strip()[:80]}')
               except: pass
   for d in dead[:30]:
       print(d)" 2>/dev/null
   ```

2. **Kotlin — check for unused endpoints:**
   ```bash
   # List all controller endpoints
   grep -rn "@\(Get\|Post\|Put\|Delete\|Patch\)Mapping" /opt/scrapalot/scrapalot-backend/src/ | head -30
   ```

### Part 4: Resource Health

```bash
# Disk usage by Docker
docker system df

# Large volumes
docker volume ls -q | xargs -I{} docker volume inspect {} --format '{{.Name}}: {{.Mountpoint}}' | head -10

# Container restart counts
docker ps --format "{{.Names}}: {{.Status}}" | grep -i restart
```

### Output Format

Present findings as:

```
CODE QUALITY AUDIT

Providers:
  Python DB: N providers (N active, N system)
  Kotlin DB: N providers
  Sync drift: [none | list of mismatched IDs]

Database:
  Python tables: N | Kotlin tables: N
  Duplicate tables: [list]
  Redis Streams: [healthy | N pending messages]
  DLQ: N entries

Dead Code:
  TODOs: N | FIXMEs: N | HACKs: N
  [List top findings]

Resources:
  Disk: X/80GB used
  Docker images: X total size
  Largest volumes: [list]
```

### Guardrails

- **Read-only** — never modify data or code
- Never log full API keys — only YES/NO
- Cross-reference with CLAUDE.md Data Ownership table
- Test provider connectivity from INSIDE container
