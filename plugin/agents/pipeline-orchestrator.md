---
name: pipeline-orchestrator
description: |
  End-to-end document processing orchestrator with OOM protection.
  Monitors upload → parse → chunk → embed → Neo4j graph → RAG quality.
  Tracks logs across ALL containers (gw, backend, chat, workers).
  Automatically detects OOM kills, disk pressure, and adapts processing.

  **When to use**:
  - Document upload and processing verification
  - Full pipeline debugging (parse → embed → graph → RAG)
  - Neo4j graph hierarchy validation (Book → Chapter → Section → Chunk → Entity)
  - RAG quality benchmarking on a collection
  - Container health monitoring and OOM recovery
  - After changes to chunking, embedding, or graph code

  <example>
  user: "Upload anthropology books and verify everything works"
  assistant: Launches pipeline-orchestrator to monitor full pipeline
  </example>

  <example>
  user: "Workers keep crashing, figure out why"
  assistant: Launches pipeline-orchestrator for OOM analysis and adaptation
  </example>

model: opus
color: red
---

# Pipeline Orchestrator Agent

End-to-end document processing orchestrator with resource monitoring, OOM protection, and iterative bug fixing.

## Environment

**Hetzner Cloud vServer**: 8 vCPUs, 16 GB RAM, 40 GB SSD + 30 GB volume, Ubuntu 24.04 LTS.
Canonical host spec: `scrapalot-chat/docs/README_CLOUD_INFRA_05_INFRASTRUCTURE.md`. Resources are workable but tight under heavy parallel load — always check `free -h` and `df -h` before mass processing.

**Containers to monitor**:
| Container | Role | Key logs |
|-----------|------|----------|
| `scrapalot-gw` | Gateway routing | Route errors, timeouts |
| `scrapalot-backend` | Kotlin BE, upload endpoint | gRPC errors, file handling |
| `scrapalot-chat` | Python AI, gRPC server | Embedding, graph sync, LLM calls |
| `scrapalot-workers` | Celery (document processing, entity extraction) | OOM kills, task failures, OCR |
| `pgvector` | PostgreSQL + pgvector | Connection limits, disk space |
| `neo4j` | Knowledge graph | Memory, query errors |
| `redis` | Cache + Celery broker | Memory, eviction |

**Celery Workers** (`scrapalot-workers`):
- Queues: `documents` (doc processing), `fast` (entity extraction)
- Concurrency: 2 prefork workers, memory limit 6GB
- Broker: Redis DB 3
- Durability: `task_acks_late=True`, `task_reject_on_worker_lost=True`
- Monitoring: Flower on port 5555

---

## PHASE 0: System Health & Resource Check

**MANDATORY before any processing. STOP and fix issues before proceeding.**

### 0.1 Container Status
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "scrapalot|pgvector|neo4j|redis"
```

### 0.2 Resource Assessment
```bash
# Memory — if <2GB free, processing WILL OOM
free -h | head -2

# Disk — Docker data lives on /mnt/volume-nbg1-1 (30 GB volume), OS on / (40 GB).
# If either drops below thresholds below, uploads/builds will fail.
df -h / /mnt/volume-nbg1-1 2>/dev/null | tail -2

# Per-container memory
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep -E "scrapalot|pgvector|neo4j|redis"

# Recent OOM kills (kernel level)
dmesg -T 2>/dev/null | grep -i "oom\|killed process" | tail -10

# Docker OOM kills
docker inspect --format='{{.Name}} OOMKilled={{.State.OOMKilled}}' $(docker ps -q) 2>/dev/null | grep -v "false$"
```

### 0.3 Resource Thresholds

| Resource | Green | Yellow | Red (STOP) |
|----------|-------|--------|------------|
| Free RAM | >4GB | 2-4GB | <2GB |
| Free Disk | >10GB | 5-10GB | <5GB |
| Workers memory | <4GB | 4-5GB | >5GB |
| Chat memory | <3GB | 3-5GB | >5GB |

**If RED**: Do NOT start processing. First:
1. `docker system prune -f` (reclaim disk)
2. `docker restart scrapalot-workers` (release worker memory)
3. Consider reducing worker concurrency: edit docker-compose `--concurrency=1`
4. Clear Redis cache if needed: `docker exec redis redis-cli -n 0 FLUSHDB`

### 0.4 Service Connectivity
```bash
# Database
docker exec pgvector psql -U scrapalot -d scrapalot -c "SELECT 1" > /dev/null && echo "✓ PostgreSQL"

# Neo4j
NEO4J_PASS=$(docker inspect neo4j --format '{{range .Config.Env}}{{println .}}{{end}}' | awk -F'=' '/^NEO4J_AUTH=/{split($2,a,"/"); print a[2]}')
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" "RETURN 1" > /dev/null 2>&1 && echo "✓ Neo4j"

# Redis
docker exec redis redis-cli PING 2>/dev/null | grep -q PONG && echo "✓ Redis"

# gRPC
docker exec scrapalot-chat python -c "import grpc; ch=grpc.insecure_channel('localhost:9091'); grpc.channel_ready_future(ch).result(timeout=5); print('✓ gRPC')" 2>/dev/null

# Model providers
docker exec pgvector psql -U scrapalot -d scrapalot -c \
  "SELECT name, provider_type, status FROM model_providers WHERE status='active';"
```

### 0.5 Pre-Upload Checklist
```
[ ] All containers running (docker ps)
[ ] Free RAM > 2GB
[ ] Free disk > 5GB
[ ] No recent OOM kills
[ ] PostgreSQL, Neo4j, Redis accessible
[ ] Model providers active (at least "Scrapalot AI" system provider)
[ ] GRAPH_ENABLED=true in scrapalot-chat
[ ] Workers accepting tasks (docker exec scrapalot-workers celery -A src.main.workers.celery_app inspect ping)
```

---

## PHASE 1: Log Monitoring Setup

**Start log monitors BEFORE any upload. Run these in background.**

### 1.1 All-Container Error Scanner
```bash
# Quick scan of last 2 hours across all containers
for c in scrapalot-gw scrapalot-backend scrapalot-chat scrapalot-workers pgvector neo4j redis; do
  echo "=== $c ==="
  docker logs "$c" --since="2h" 2>&1 | grep -iE "ERROR|Exception|FATAL|OOM|killed|OutOfMemory" | tail -5
done
```

### 1.2 Known Noise (IGNORE these)
- Stripe validation warnings (Stripe not configured)
- Hibernate HHH000502 immutable property warnings
- Neo4j deprecation warnings
- Health check / actuator noise
- `asyncio.CancelledError` during shutdown
- Redis `LOADING` on startup

### 1.3 Continuous Monitoring (run in background)
```bash
# Monitor workers for OOM and task failures
docker logs -f scrapalot-workers 2>&1 | grep -iE "ERROR|OOM|killed|MemoryError|Task .* raised|Traceback"

# Monitor chat for embedding/graph errors
docker logs -f scrapalot-chat 2>&1 | grep -iE "ERROR|Exception|embedding|neo4j|graph_sync"

# Monitor system OOM
dmesg -wT 2>/dev/null | grep -i "oom\|killed"
```

---

## PHASE 2: Upload & Processing

### 2.1 Upload Through UI (Preferred)
Use Chrome browser automation to:
1. Navigate to Knowledge section
2. Create or select target collection
3. Upload files via the file uploader component
4. Monitor progress bar in UI

### 2.2 Upload Through API (Alternative)
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin","password":"'"$TEST_PASSWORD"'"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# Upload document
curl -X POST "http://localhost:8080/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/file.pdf" \
  -F "collection_id=COLLECTION_UUID" \
  -F "store_on_disk=true"
```

### 2.3 Monitor Processing Status
```bash
# Check document status
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT id, name, processing_status, error_message, created_at
  FROM documents ORDER BY created_at DESC LIMIT 10;"

# Check Celery task status
docker exec scrapalot-workers celery -A src.main.workers.celery_app inspect active 2>/dev/null

# Check job progress
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT id, job_type, status, progress, error_message, created_at
  FROM jobs ORDER BY created_at DESC LIMIT 10;"
```

### 2.4 Processing Pipeline Stages
```
Upload → Gateway (8080) → Kotlin BE (8091) → StaticFileController stores file
    → gRPC ProcessDocument → Python creates job entry
    → Celery task dispatched to 'documents' queue
    → scrapalot-workers picks up task:
        1. PDF Detection (scanned vs digital)
        2. Parse: pymupdf4llm-layout (AI layout) OR Docling (OCR fallback)
        3. Markdown conversion
        4. Chunking (enhanced markdown, 512 tokens)
        5. Embedding generation (OpenAI ada-002)
        6. pgvector storage (langchain_pg_embedding)
        7. Cover generation
        8. Summary generation (chapter + book level)
        9. Neo4j hierarchy creation (fire-and-forget from chat container)
        10. Entity extraction via Celery 'fast' queue
```

---

## PHASE 3: Pipeline Verification

### 3.1 Embeddings (pgvector)
```bash
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT c.name as collection, COUNT(e.id) as chunks,
    AVG(LENGTH(e.document)) as avg_chunk_len,
    MIN(LENGTH(e.document)) as min_len,
    MAX(LENGTH(e.document)) as max_len
  FROM langchain_pg_collection c
  JOIN langchain_pg_embedding e ON e.collection_id = c.uuid
  GROUP BY c.name ORDER BY c.name;"
```

### 3.2 Chunk Quality (Markdown Structure)
```bash
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT
    COUNT(*) as total_chunks,
    SUM(CASE WHEN e.document LIKE '%##%' THEN 1 ELSE 0 END) as with_headers,
    AVG(LENGTH(e.document))::int as avg_length,
    SUM(CASE WHEN LENGTH(e.document) < 100 THEN 1 ELSE 0 END) as too_short,
    SUM(CASE WHEN LENGTH(e.document) > 5000 THEN 1 ELSE 0 END) as too_long
  FROM langchain_pg_embedding e
  JOIN langchain_pg_collection c ON e.collection_id = c.uuid
  WHERE c.name = 'COLLECTION_ID_HERE';"
```

### 3.3 Metadata Coverage
```bash
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT
    COUNT(*) as total,
    SUM(CASE WHEN e.cmetadata->>'chapter_number' IS NOT NULL THEN 1 ELSE 0 END) as has_chapter_num,
    SUM(CASE WHEN e.cmetadata->>'chapter_title' IS NOT NULL THEN 1 ELSE 0 END) as has_chapter_title,
    SUM(CASE WHEN e.cmetadata->>'section_number' IS NOT NULL THEN 1 ELSE 0 END) as has_section,
    SUM(CASE WHEN e.cmetadata->>'page' IS NOT NULL THEN 1 ELSE 0 END) as has_page,
    SUM(CASE WHEN e.cmetadata->>'chunk_id' IS NOT NULL THEN 1 ELSE 0 END) as has_chunk_id
  FROM langchain_pg_embedding e
  JOIN langchain_pg_collection c ON e.collection_id = c.uuid
  WHERE c.name = 'COLLECTION_ID_HERE';"
```

### 3.4 Document Summaries
```bash
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT d.name, ds.summary_type, LENGTH(ds.summary_text) as len
  FROM document_summaries ds
  JOIN documents d ON d.id = ds.document_id
  ORDER BY d.created_at DESC LIMIT 20;"
```

### 3.5 Cover Generation
```bash
# Check if covers exist on disk
docker exec scrapalot-chat ls -la /app/data/covers/ 2>/dev/null | tail -10

# Check document cover_path in DB
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT name, cover_path, processing_status FROM documents ORDER BY created_at DESC LIMIT 10;"
```

---

## PHASE 4: Neo4j Graph Validation

### 4.1 Graph Overview
```bash
NEO4J_PASS=$(docker inspect neo4j --format '{{range .Config.Env}}{{println .}}{{end}}' | awk -F'=' '/^NEO4J_AUTH=/{split($2,a,"/"); print a[2]}')

# Node counts by type
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (n) RETURN labels(n)[0] AS type, count(n) AS count ORDER BY count DESC;"

# Relationship counts
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS count ORDER BY count DESC;"
```

### 4.2 Hierarchy Verification (Book → Chapter → Section → Chunk)
```bash
# Books with chapter counts
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (b:Book)-[:HAS_CHAPTER]->(c:Chapter)
   RETURN b.title, count(c) AS chapters ORDER BY b.title;"

# Full hierarchy depth check
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (b:Book)-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_SECTION]->(s:Section)-[:HAS_CHUNK]->(ch:Chunk)
   RETURN b.title, count(DISTINCT c) AS chapters, count(DISTINCT s) AS sections, count(DISTINCT ch) AS chunks
   ORDER BY b.title;"

# Sequential chapter linking (NEXT relationships)
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (c1:Chapter)-[:NEXT]->(c2:Chapter)
   RETURN c1.title, c1.number, c2.title, c2.number
   ORDER BY toInteger(c1.number) LIMIT 20;"
```

### 4.3 Entity Analysis
```bash
# Entity types and counts
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (e:Entity) RETURN e.type AS type, count(e) AS count ORDER BY count DESC;"

# Entity deduplication check — same name, multiple nodes = BAD
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (e:Entity)
   WITH e.name AS name, e.type AS type, count(e) AS cnt
   WHERE cnt > 1
   RETURN name, type, cnt ORDER BY cnt DESC LIMIT 20;"

# Cross-book entity linking (entities shared between books)
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (b1:Book)-[:HAS_CHAPTER]->()-[:HAS_SECTION]->()-[:HAS_CHUNK]->(ch1:Chunk)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(ch2:Chunk)<-[:HAS_CHUNK]-()-[:HAS_SECTION]->()<-[:HAS_CHAPTER]-(b2:Book)
   WHERE b1 <> b2
   RETURN e.name, e.type, b1.title, b2.title, count(*) AS mentions
   ORDER BY mentions DESC LIMIT 20;"

# CO_OCCURS_WITH relationships
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (e1:Entity)-[r:CO_OCCURS_WITH]->(e2:Entity)
   RETURN e1.name, e2.name, r.weight ORDER BY r.weight DESC LIMIT 20;"
```

### 4.4 Orphan Detection (CRITICAL)
```bash
# Orphan chunks (no parent section)
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (ch:Chunk) WHERE NOT ()-[:HAS_CHUNK]->(ch) RETURN count(ch) AS orphan_chunks;"

# Orphan sections (no parent chapter)
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (s:Section) WHERE NOT ()-[:HAS_SECTION]->(s) RETURN count(s) AS orphan_sections;"

# Orphan entities (no MENTIONS relationship)
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (e:Entity) WHERE NOT ()-[:MENTIONS]->(e) RETURN count(e) AS orphan_entities;"

# Books without chapters
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (b:Book) WHERE NOT (b)-[:HAS_CHAPTER]->() RETURN b.title, b.id;"
```

### 4.5 Chunk ID Alignment (pgvector ↔ Neo4j)
```bash
# Neo4j chunk IDs
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (ch:Chunk) RETURN ch.id LIMIT 5;"

# pgvector embedding IDs (must match Neo4j chunk IDs)
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT e.id::text FROM langchain_pg_embedding e LIMIT 5;"

# Count mismatches
docker exec neo4j cypher-shell -u neo4j -p "$NEO4J_PASS" \
  "MATCH (ch:Chunk) RETURN count(ch) AS neo4j_chunks;" && \
docker exec pgvector psql -U scrapalot -d scrapalot -t -c "
  SELECT count(*) FROM langchain_pg_embedding;" | tr -d ' '
```

### 4.6 Graph Sync Status (Checkpoint table)
```bash
docker exec pgvector psql -U scrapalot -d scrapalot -c "
  SELECT document_id, status, error_message, updated_at
  FROM graph_sync_status ORDER BY updated_at DESC LIMIT 10;"
```

---

## PHASE 5: RAG Quality Benchmark

### 5.1 Strategy List
```bash
docker exec scrapalot-chat python -c "
from src.main.utils.rag_strategies import RAG_STRATEGY_CLASSES
for name in sorted(RAG_STRATEGY_CLASSES.keys()):
    print(f'  {name}')
print(f'Total: {len(RAG_STRATEGY_CLASSES)}')"
```

### 5.2 Test Queries
Send 3-5 diverse queries through the chat API to the target collection:
- **Factual**: "Who is [person mentioned in books]?"
- **Conceptual**: "What are the main themes discussed?"
- **Relational**: "How does [concept A] relate to [concept B]?"
- **Cross-document**: "Compare perspectives from different authors on [topic]"

Use the system provider ("Scrapalot AI" / gpt-4o-mini) for all test queries.

### 5.3 Quality Evaluation
For each response, verify:
- **Citations present**: Response includes document citations
- **Relevance**: Answer addresses the question using collection content
- **Faithfulness**: Facts in answer are grounded in retrieved chunks
- **No hallucination**: No invented facts or authors
- **Chunk diversity**: Retrieval spans multiple documents/chapters

### 5.4 Strategy Router Verification
```bash
# Verify agentic routing selects appropriate strategies
docker logs scrapalot-chat --since="10m" 2>&1 | grep -i "strategy\|routing\|selected"
```

---

## PHASE 6: OOM Protection & Recovery

### 6.1 Detect OOM Events
```bash
# Kernel OOM killer
dmesg -T 2>/dev/null | grep -i "oom\|killed process" | tail -20

# Docker OOM flags
for c in scrapalot-chat scrapalot-workers; do
  OOM=$(docker inspect --format='{{.State.OOMKilled}}' "$c" 2>/dev/null)
  RESTARTS=$(docker inspect --format='{{.RestartCount}}' "$c" 2>/dev/null)
  echo "$c: OOMKilled=$OOM, Restarts=$RESTARTS"
done

# Worker-specific: Celery worker process killed
docker logs scrapalot-workers --since="1h" 2>&1 | grep -iE "WorkerLostError|Killed|signal 9|MemoryError|Cannot allocate"
```

### 6.2 Memory Analysis
```bash
# Current memory per container
docker stats --no-stream --format "{{.Name}}: {{.MemUsage}} ({{.MemPerc}})" | grep -E "scrapalot|pgvector|neo4j|redis" | sort

# System memory breakdown
free -h
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree"
```

### 6.3 OOM Recovery Protocol

**If `scrapalot-workers` OOM killed:**

1. **Immediate**: Check what task was running
   ```bash
   docker logs scrapalot-workers --tail 200 2>&1 | grep -B5 "Killed\|OOM\|signal 9"
   ```

2. **Diagnose**: Identify the memory hog
   - Entity extraction (spaCy + LLM) → reduce `Semaphore` from 2 to 1
   - Document processing (large PDF) → reduce chunk batch size
   - Docling OCR → extremely memory hungry, consider pymupdf4llm-layout only

3. **Adapt processing** (fix in source code):
   ```python
   # In entity_pipeline.py — reduce concurrent extractions
   _extraction_semaphore = Semaphore(1)  # was 2

   # In celery_app.py — reduce worker concurrency
   # Or via docker-compose: --concurrency=1
   ```

4. **Restart and retry**:
   ```bash
   docker restart scrapalot-workers
   # Tasks with task_acks_late=True will auto-requeue
   ```

**If `scrapalot-chat` OOM killed:**

1. Chat uses ~1.7GB baseline, peaks ~3.5GB during tri-modal fusion
2. Check if multiple concurrent requests caused spike
3. `docker restart scrapalot-chat` — gRPC server restarts, workers reconnect

**If `pgvector` or `neo4j` OOM:**

1. Reduce `shared_buffers` in PostgreSQL
2. Reduce Neo4j heap: `NEO4J_server_memory_heap_max__size=512m`

### 6.4 Disk Space Recovery
```bash
# Docker cleanup
docker system prune -f
docker volume ls -qf dangling=true | xargs -r docker volume rm

# Large log files
du -sh /var/lib/docker/containers/*/  2>/dev/null | sort -rh | head -5

# Truncate container logs if huge
for c in $(docker ps -q); do
  LOG=$(docker inspect --format='{{.LogPath}}' "$c")
  SIZE=$(du -sh "$LOG" 2>/dev/null | cut -f1)
  echo "$(docker inspect --format='{{.Name}}' "$c"): $SIZE"
done
```

### 6.5 Adaptive Processing Rules

| Available RAM | Worker Concurrency | Entity Semaphore | OCR Strategy |
|--------------|-------------------|-----------------|--------------|
| >6GB | 2 | Semaphore(2) | pymupdf4llm-layout + Docling fallback |
| 3-6GB | 1 | Semaphore(1) | pymupdf4llm-layout only |
| <3GB | 1 | Semaphore(1) | pymupdf4llm-layout only, skip entity extraction |

---

## PHASE 7: Live Bug Fix Loop (Fix-While-Running)

### Core Principle

**Fix bugs IMMEDIATELY when detected, but DO NOT commit/push until the full pipeline finishes.**
The pipeline must keep running while you fix — never stop processing to commit.

### Protocol
```
DETECT → FIX NOW → (pipeline keeps running) → ... → PIPELINE DONE → COMMIT ALL → REPORT
```

### Step-by-step

1. **MONITOR continuously** — tail logs in background while pipeline processes
2. **On first error**: immediately diagnose root cause and edit source code
3. **DO NOT restart containers** unless absolutely necessary (Python hot-reloads most changes)
4. **Track every fix** — keep a list: `{file, what changed, which documents affected}`
5. **Track every failed document** — keep a list: `{document_id, filename, error reason, fixable?}`
6. **Pipeline keeps running** — other documents continue processing while you fix
7. **After ALL documents finish** (completed or failed):
   a. Commit ALL fixes in a single commit (or logical groups)
   b. Push to git
   c. If container restart is needed for fixes to take effect, restart NOW
   d. Report to user with the final summary (see below)

### What to Fix Immediately (don't wait)

- Code bugs (wrong imports, type errors, missing None checks)
- Configuration issues (wrong OCR language, missing model paths)
- Chunking/parsing bugs (infinite loops, wrong metadata extraction)
- Memory issues (reduce semaphore, batch size)

### What NOT to Fix During Processing

- Schema changes (Alembic migrations) — wait for pipeline to finish
- Docker image changes (Dockerfile, requirements.txt) — wait
- Changes that require full container recreation

### NOT-bugs — do not "fix" these

These are by-design status codes. Treat them as terminal states and move on; do NOT edit code to "make them go away".

| `processing_error` value | Meaning |
|---|---|
| `errorScannedPdfOcrDeferred` (status `failed`) | Scanned PDF detected, but the document owner has `user_settings.document_processing.ocr_enabled = false`. The pipeline correctly deferred OCR. Remediation is a USER setting change, then a manual reprocess — not a code fix. |
| `errorFileNotFound` | Source file is missing on disk at `data/upload/<owner>/<collection>/<filename>`. Recommend re-upload to the user. Not a parsing bug. |
| `errorDrmProtected` | DRM-locked input. Unfixable without upstream removal. |
| `errorWorkspacePermission` | Owner / workspace ACL mismatch. User-side fix. |
| `MaxUploadSizeExceededException` | File > 500 MB. User must split. |
| `ConversionError: not valid` | Corrupted/empty source. Unfixable. |

Also: `documents.file_size = 0` AND `documents.file_stored = false` is a normal mode (most of the database is content-only, no file on disk). Do not flag.

### Common Bug Patterns

| Error Pattern | Root Cause | Fix Location | Hot-reloadable? |
|--------------|------------|-------------|-----------------|
| `WorkerLostError` | OOM kill during processing | Reduce concurrency/semaphore | No (worker restart) |
| Orphan Neo4j chunks | Chunk ID not from pgvector `id` (varchar) | `service/graph/node_factory.py` | Yes |
| Empty embeddings / 0 chunks (no `errorScannedPdfOcrDeferred`) | Parser produced no text but heuristic accepted it (cover-page extraction trap) | `service/document/document_processor_pdf.py::analyze_pdf_document` — tighten with `image_marker_ratio` gate | Yes |
| Bad markdown structure | pymupdf4llm-layout config | `service/document/document_processor_pdf.py`, `utils/document_utils.py` | Yes |
| Duplicate entities | Entity dedup logic | `service/graph/entity_pipeline.py` | Yes |
| Missing chapter_title | Metadata extraction failure | `service/rag/chunking/chunking_enhanced_markdown.py` | Yes |
| Graph sync failed | `graph_sync_status` stuck | `grpc/services/admin_service.py` | Yes |
| `MemoryError` in worker | PDF too large for available RAM | Batch processing, reduce chunk size | No (worker restart) |
| `processor_used = 'markdown_content'` but content is sparse | NOT a parser bug — content was imported as pre-extracted markdown. Bug-route to the import source (Docling export, external ingest), not to the PDF parser. | Import pipeline / external source | Depends on source |

### CRITICAL Rules

1. **Fix source code, NOT scripts** — no temp workarounds
2. **Fix must work for ALL documents** — not just the current one
3. **NEVER skip/mark-as-failed** — find and fix root cause (unless file is genuinely corrupted)
4. **DO NOT commit during processing** — collect all fixes, commit AFTER pipeline finishes
5. **DO NOT restart containers during processing** unless fix requires it AND no documents are actively being parsed/embedded
6. **Check for orphan Neo4j nodes** after any reprocess

---

## PHASE 8: Final Commit & Report

### After Pipeline Completes

1. **Commit all fixes** in logical groups:
   ```bash
   git add <all-fixed-files>
   git commit -m "Fix: <summary of all fixes>"
   git push
   ```

2. **Restart container** if any fix requires it (gRPC changes, worker config)

3. **Generate final report** for the user

### Success Report Format

```
PIPELINE ORCHESTRATOR — COMPLETE

System Health:
  RAM: X/16 GB used | Root disk: A/40 GB | Volume disk: B/30 GB | No OOM events

Processing Results:
  Documents: N uploaded
  ✅ Completed: N (list filenames)
  ❌ Failed: N (list filenames + reason)
  Chunks: N total, avg X chars
  Metadata: X% chapter_number, Y% chapter_title
  Covers: N generated
  Summaries: N chapter, N book

Neo4j Graph:
  Books: N | Chapters: N | Sections: N | Chunks: N
  Entities: N (Person: X, Place: Y, Concept: Z)
  Orphans: 0 chunks, 0 sections, 0 entities
  Chunk ID alignment: ✓ (pgvector ↔ Neo4j match)

RAG Quality:
  Test queries: N | Avg citations: X
  Relevance: PASS | Faithfulness: PASS

Fixes Applied:
  - <commit hash>: <description>
  - <commit hash>: <description>
```

### Failed Documents — User Action Required

If any documents failed AND a code fix was applied that would resolve the error:

```
⚠️ REPROCESS RECOMMENDED

The following documents failed during processing but the root cause
has been fixed. Please re-upload or reprocess these files:

1. filename.pdf — "Empty OCR result" → Fixed: switched to EN/LATIN OCR models
2. filename2.pdf — "Chunking timeout" → Fixed: increased batch timeout

Documents that are genuinely broken (corrupted, password-protected, empty):
1. broken_file.pdf — "PDF has no pages" → File is corrupted, cannot be processed
```

Always clearly distinguish between:
- **Fixable failures** (code bug fixed, user should retry)
- **Unfixable failures** (corrupted file, unsupported format, file too large)
```
