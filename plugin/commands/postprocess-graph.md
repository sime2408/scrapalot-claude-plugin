---
description: Graph-only audit of ONE book whose parse is already clean. Loops until a separate critic agrees the graph is the book's graph — never a round count.
allowed-tools: Agent, Bash, Read, Edit, Write, Grep, Glob, AskUserQuestion
---

# One book. Graph layer only. Loop until a critic says it is the book's graph.

**Read `.claude/postprocess/GAUNTLET.md` first and follow it.** The bar is the
book's own text; a separate critic with fresh context judges blind; the exit is
that critic saying yes.

## DIRECTION — restate this at the start of every run

> **We are auditing the GRAPH of ONE book whose parse layer is already clean,
> and looping until a separate critic agrees the stored entities and hierarchy
> are the book's. We do not re-audit the parse layer beyond the precondition.
> We do not touch a second book.**

## Phase 0 — the precondition that is not negotiable

This command runs **only** on a book whose parse layer is recorded clean in
`.claude/postprocess/progress.txt` (`parse_done_clean`, or an equivalent row
stating the chapter layer matches the book).

If it is not: **stop and say so.** Run `/scrapalot:postprocess-parse` on it
first. Building a graph on a wrong chapter layer is not a slow path to a good
graph — it is a permanent bad one. `neo4j_service` merges `Chapter` with
`ON CREATE SET` and **no** `ON MATCH SET`, so a wrong title is not corrected by
re-running the build; it needs `delete_document_hierarchy` first. `32fdbafd`
carries a chapter permanently named "Introduction" for exactly this reason.

Then check and report:

| Check | Where | If it fails |
|---|---|---|
| effective `graph_tier` == 2 | `resolve_graph_tier()`, `collection_workspace_cache.py:135` | STOP. Tier 0/1 builds no full graph. Name the collection, its inherited tier, and offer to set it. **Inheritance is real** — `behavioral` is NULL and resolves to 2 through its parent `psychology`. |
| `graph_sync_status` | pgvector | records whether a graph was ever attempted, and whether a previous run left it half-built |
| Neo4j reachable, heap | `NEO4J_server_memory_heap_max__size` | production is **768M**; a gate demanding ≥1024M blocks every housekeeping dispatch forever |
| graph worker alive | `docker inspect scrapalot-workers-graph` | housekeeping runs on the `graph_extraction` queue, a **different container** from `scrapalot-workers` |

## Phase 0.5 — open the gate ledger, BEFORE any build or fix

**Read `.claude/gates/CONTRACT.md` and follow it.** The precondition above is the
first gate, and it is the one most worth writing down: a graph built on a wrong
chapter layer is permanent, and this is the run that must not talk itself past
that.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py open \
    --run graph-<short-doc-id> --command /scrapalot:postprocess-graph \
    --scope "<title> — graph layer only, until a critic says the stored entities are the book's"
```

Starter gates. Adapt to the book you resolved.

```markdown
- [ ] G1: parse is recorded clean for this book and the collection resolves to tier 2
  CHECK: grep -c "<document_id>.*parse_done_clean" ${CLAUDE_PROJECT_DIR}/.claude/postprocess/progress.txt
  EXPECT: /[1-9]/
  EVIDENCE: pending
- [ ] G2: the book's real entity material is read out of documents.content and written down (the bar)
  EVIDENCE: pending
- [ ] G3: every chunk is reachable Book → Chapter → Section → Chunk, traversal filtered on the Book
  EVIDENCE: pending
- [ ] G4: the stored entity names were read one by one — things, not sentences, mottos or OCR noise
  EVIDENCE: pending
- [ ] G5: a critic with fresh context, given both entity lists unlabelled, says they are the same book's
  EVIDENCE: pending
- [ ] G6: entity_cache:* was cleared before any re-extraction, or no re-extraction was run
  EVIDENCE: pending
- [ ] G7: every source fix in this run carries a corpus regression scan in BOTH directions
  EVIDENCE: pending
- [ ] G8: the ledger row for this book is in progress.txt
  CHECK: grep -c "<document_id>" ${CLAUDE_PROJECT_DIR}/.claude/postprocess/progress.txt
  EXPECT: /[1-9]/
  EVIDENCE: pending
```

G1 failing is the end of the run, not a hurdle to argue with: report it, point at
`/scrapalot:postprocess-parse`, and close the ledger with the rest abandoned and
the reason stated. G6 exists because the 2 h Redis cache makes a re-extraction
after a prompt or gate change a silent no-op — the evidence is the clear command
you actually ran.

## Phase 1 — extract the bar

Before looking at Neo4j, read the book. Pull the real entity material out of
`documents.content` — the people, places, works, concepts it actually discusses,
sampled from start, middle and end. Write that down. Everything after this is
judged against it, not against a density metric.

## Phase 2 — build or audit

If no graph exists, dispatch `scrapalot.build_graph_from_existing_chunks` — the
ordering-safe entry point (hierarchy sync on `fast`, then entity extraction on
`graph_extraction`). Ordering is mandatory:
`entity_pipeline._create_chunk_entity_relationships` **MATCHes** Chunk nodes
rather than MERGEing them, so entities before hierarchy silently drops every
chunk-level `REFERENCES` edge.

If a graph exists, delegate to the **`scrapalot:postprocess-graph` agent** (Agent
tool), scoped to this document_id. Do not let it pick its own book.

Either way, verify the chain end to end yourself:
`Book → Chapter → Section → Chunk`, every chunk reachable. **Filter traversals
on the Book, not on `document_id`** — `Section` nodes do not carry it, and a
scan that filters on it reports a broken hierarchy that is perfectly intact.

## Phase 3 — entity names, by reading them

Density is not quality. Read the actual names:

```cypher
MATCH (b:Book {document_id: $did})-[:MENTIONS]->(e:Entity)
RETURN e.name AS name, e.source AS source, e.entity_type AS type ORDER BY e.name
```

Garbage is a **source-code bug**, never a row to patch away: a sentence or verse
line ("Follow me, but look not to the right…"), a foreign motto ("ut bos locutus
est"), OCR sludge ("R T N T", "ALGAR + ALGASTNA + + +"). Trace it — the LLM
prompt (`entity_extraction.extraction_prompt` and `is_valid_llm_entity_name`) or
the spaCy gate (`SpacyExtractor._is_valid_entity`) — and fix it there.

The Redis `entity_cache:*` serves cached extractions for 2h, so a re-extraction
after a prompt or gate change is a **no-op until that cache is cleared**. Clear
it before re-extracting, and say that you did.

## Phase 4 — the loop

Builder fixes → **separate critic agent, fresh context** → judge.

The critic gets the entity material read out of the book and the entity names
stored in the graph, **unlabelled**, and one binary question: *are these the same
book's entities — yes or no; if no, the single biggest difference.* For a source
fix it also gets the **raw** corpus scan, not a summary. "Mostly" is a no. Never
a score.

If no, the critic's one sentence goes back to the builder. **Exit is the critic
saying yes, or the owner stopping** — never a round count. Two different fixes
hitting the same gap is a finding: name what was tried and stop.

**Autonomous:** source fixes on a branch, scans, tests, PRs, cache clears,
re-running the critic. **Approval-gated, every time:** any Neo4j write beyond the
orchestrated build, `delete_document_hierarchy`, any reprocess, any
workspace-wide housekeeping dispatch, any merge. **Never:** `DETACH DELETE`
outside an orchestrated reprocess, or mass operations across books.

## Phase 5 — report and STOP

**No report until the gate ledger is full.**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py close gates/active/graph-<short-doc-id>.md
```

Every `ABANDON:` line is named in the report. The gate summary is re-measured at
report time, never recalled.

Ledger row in `.claude/postprocess/progress.txt`; off-topic findings to
`side_findings.txt`; in chat, plain Croatian with no pipeline jargon — no
"chunk", "tier", "entity", `file:line` or table names in what the owner reads.

Then stop. Do not start the next book unprompted.
