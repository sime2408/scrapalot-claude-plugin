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

## Cheap hours only — every phase of this command spends money

DeepSeek bills peak hours at exactly double. Peak is **Monday to Friday,
01:00-04:00 and 06:00-10:00 UTC** — 03:00-06:00 and 08:00-12:00 in CEST, and
02:00-05:00 / 07:00-11:00 once CET returns on 2026-10-25. Weekends are cheap all
day, midnight to midnight.

The windows are not restated as a constant here. `DEEPSEEK_PEAK_WINDOWS_UTC` in
`scrapalot-chat/src/main/service/llm/model_pricing.py` is the source of truth,
and `scripts/book-graph/cheap-now.sh` reads it from the running container, so a
price change moves this rule with it.

What a peak hour costs, measured rather than assumed: the 2026-09-03 extraction
batch spent 2.8M input and 9.0M output tokens over ~13 documents — about
**USD 0.45 of graph work per book off-peak, USD 0.90 in peak** at the V4.1 Flash
rate. Half of that is paid for nothing. (Never write a bare `$0` in this file:
argument substitution eats it, and `$0.45` reaches you as the document id with
`.45` stuck on the end — the one number that justifies this rule, destroyed
exactly when the command is used for real.)

**Do not try to confirm that figure from the logs** — the usage lines carry no
document_id, `/app/data/logs` is one shared volume written by every container,
and a housekeeping backfill of other books runs concurrently, so a window
measured during one book held 354 calls and USD 1.2918 for an unknown number of
books. Read it from the database instead, where it IS attributed per document:

```sql
SELECT phase, chunks_processed, llm_calls, tokens_in, tokens_out, cost_cents,
       round(duration_ms/1000.0,1) AS sec
FROM entity_extraction_metrics WHERE document_id = '<id>' ORDER BY started_at;
```

(`sum(llm_calls)` over that table double-counts — there is a `total` phase row
alongside the per-phase rows.) One 107-chunk book measured USD 0.3878, close to
the per-book figure above. The same table is what the admin Data Inspector's
extraction-cost pane reads, so a number quoted in chat and a number on that
screen are the same number.

The phase rows are also a cheap first look at a thin graph layer: on that same
book `cooccurrence` ran 0.7 s and `shared_entity` 0.2 s. They cannot explain
missing co-occurrence weights, though: a book's own `cooccurrence` phase sets only
`r.shared_chunks`, and `document_weighted_score` is written by the housekeeping
recompute alone.

**The rule: never START a build inside a peak window.**

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/cheap-now.sh   # exit 0 = cheap now
```

Inside a peak window: name the window, say when it ends, and stop — unless the
owner says otherwise in this session or `SCRAPALOT_ALLOW_PEAK=1` is set. A build
already running when a window opens is NOT killed: the guarantee is that no new
one is started, which is what the Celery beat schedule already promises for the
housekeeping tasks.

## Disk before every pass — Neo4j and pgvector share one volume

The graph layer is the part of this pipeline that grows the disk: entity
extraction writes nodes and relationships into Neo4j and chunk metadata back
into pgvector, and both stores sit on the same Hetzner volume
(`/mnt/volume-nbg1-1`, 79 GB). Measured on 2026-09-12: that volume is **77% full
with 18 GB free**, of which Neo4j's own store is 4.7 GB. Nothing in this loop
reclaims space — every book only adds.

**The rule: measure before every pass and while a pass runs. At 88% the loop
stops itself, writes `.claude/book-graph/STOPPED-disk-full`, and notifies the
owner — mid-book if that is where the line is crossed.**

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/disk-check.sh   # 0 = room, 2 = stop, 1 = unmeasurable
```

88 and not 90, because a pass keeps writing between two checks and Neo4j meeting
a full volume does not fail cleanly: it stops accepting writes, and the store can
come back needing recovery — which costs more than every book this sweep would
have finished that night. `DISK_STOP_PCT` moves the limit for a deliberate,
stated exception; nothing moves it by default.

Two filesystems are measured, because two can wedge this work. The volume
Neo4j's `/data` is on is asked **inside the container**: the docker volume
directory is 0700, so from the host `df` on it answers "Permission denied" and
the check would fall back to docker's root — the same volume today, but the
database's own view is the one that cannot drift. The second is the filesystem
carrying the checkout, the worktrees a fix is built in, and the ledgers. Exit 1
— nothing could be measured — skips the pass instead of guessing.

A full or unmeasurable disk is never a reason to "just finish this one book". A
book finished onto a wedged database has to be built again anyway.

## Phase 0 — the precondition that is not negotiable

This command runs **only** on a book whose parse layer is recorded clean in
`.claude/postprocess/progress.txt` (`parse_done_clean`, or an equivalent row
stating the chapter layer matches the book).

**Read that row for what it promises: the CHAPTER LAYER is right, not that the
text is clean.** A book carrying that row was found storing `ArgonautenSage` and
`JohannesBuch` — line breaks whose hyphen the parser swallowed — alongside
`Sulfiir`, `Dr. Karl KOnig` and `Gäblr ibn Hayyän`, straightforward OCR mangling.
All of it is in `documents.content` already; the extractor propagated it
faithfully. The graph is simply where that damage becomes legible, because a
corrupted word that reads as noise in a paragraph becomes a named thing in an
entity list. Report it, never blame the extractor for it, and never delete: the
fix is upstream and is the owner's call.

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
| `graph_sync_status` | pgvector — its own **table**, not a column on `documents`; key `document_id`, columns `status`, `chunks_created`, `entities_extracted`, `error_message` | records whether a graph was ever attempted, and whether a previous run left it half-built. `status` decides; `error_message` is a lead, never a verdict — nothing clears it when a new run starts, so a row can read `status='entity_running'` beside a days-old failure string. Compare it against `started_at` before believing it |
| Neo4j reachable, heap | `NEO4J_server_memory_heap_max__size` | production is **768M**; a gate demanding ≥1024M blocks every housekeeping dispatch forever |
| graph worker alive | `celery inspect active_queues` (or `ping`), and read the **hostname** | NOT `inspect active`: an alive but idle worker answers `- empty -`, which is the same trap this file warns about two sections down. `active_queues` proves subscription. Measured on 2026-09-17: each worker node consumes its own queue only, and `graph_extraction` is answered by `celery@…` inside `scrapalot-workers-graph` alone (`documents@`, `fast@` and `research@` inside `scrapalot-workers` list theirs). `celery inspect` broadcasts to every worker on the broker, so its output does not say which container answered unless you read `hostname` |
| chapter membership is the book's | `bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/chapter-windows.sh <document_id>` | STOP, as for an unclean parse. `CHAPTER_WINDOWS_LINEAR` means every chapter but the last holds exactly chunks // chapters — the chapter-lock recovery handing out chapters by `chunk_index` and ignoring where each one starts. Measured: a book recorded `parse_done_clean` was 19 × 8 + 24 over 176 chunks, with 55 of 129 body chunks under a neighbouring chapter and its last chapter node holding none of its own text; its build went ahead and G3's reachability check went green over it. The parse row's audit had seen only the first window |
| chapter titles are the book's headings | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/chapter-titles.py <document_id>` | STOP, as for an unclean parse. `CHAPTER_TITLES_SENTENCES` means the stored titles are whole lines that open a sentence the next line finishes — a chapter layer read out of hard-wrapped prose, which chapter sizes cannot show. Measured: a book whose chapters a reprocess rewrote eleven days after its `parse_done_clean` row stored “A notable fact is” (its line 1594, followed by “that the Philosophers’ Stone wisdom had involved”), “We can shine a” and “The” as chapters; its sizes were irregular, so `chapter-windows.sh` passed it, and the parse audit had never seen those titles. Over the first 300 candidates, 5 have a title most of whose printed lines are followed by a lower-case line, and the check flags 2: that book, and one whose titles are sidebar boxes run into the text (“DON’T FORGET adult behavior can have pos…”), at exactly the quarter the threshold asks for. The other three are two long titles wrapped onto a second line and a heading followed by leftover markup, which it reports and passes. `judged=0` — no stored title printed as a line of its own, 54 of those 300 — proves nothing |
| the clean row was written about the chunks stored now | `bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/parse-fresh.sh <document_id>` | STOP, as for an unclean parse. `PARSE_ROW_STALE` means text chunks were written more than an hour after the latest `parse_done_clean` row: a reprocess re-cut the book and ran chapter detection again, so the row vouches for a layer its audit never read. Measured: 386 of the 2,803 candidates are stale, 120 of the first 300, every one rewritten by its own reprocess. One row counts 1,374 chunks and 217 chapter titles where a reprocess seven days later stored 1,080 chunks under 4 titles; two rows from a batch pass count 7 and 6 titles where the stored chunks now carry 9 and 7. Of the stale rows that record counts, 352 no longer match them and 28 still do, so a stale verdict does not prove the chapters changed, only that nobody read them. One accepted book was built on such a layer. `PARSE_ROW_UNJUDGED` (no chunk carries `enriched_at`: 3 candidates, all dataset imports) passes and proves nothing |

## Phase 0.5 — open the gate ledger, BEFORE any build or fix

**Read `${CLAUDE_PLUGIN_ROOT}/gates/CONTRACT.md` and follow it.** The precondition above is the
first gate, and it is the one most worth writing down: a graph built on a wrong
chapter layer is permanent, and this is the run that must not talk itself past
that.

`gate-check.py` resolves its ledger directory from `CLAUDE_PROJECT_DIR`, and
falls back to `$CWD/.claude/gates` when that is unset — so run from a subproject
directory it silently audits THAT subproject's stale ledgers and reports their
failures as if they were yours. **Put `CLAUDE_PROJECT_DIR=/opt/scrapalot` in front
of every invocation**, here and in Phase 5. **Name this run's ledger in `run`,
`wait` and `resume`:** without a path they act on every active ledger, other
sessions' included — a bare `wait` wrote its WAITING line into another session's
devops ledger.

**Write this book's CHECK scripts fresh; never copy them from another book's
work directory.** A copied script carries the other book's hardcoded paths and,
worse, its own output format — an EXPECT written for the script you *think* you
copied does not match the one you actually did. That fails the box rather than
ticking it, so it is safe, but it costs a diagnosis in the middle of a run.

```bash
CLAUDE_PROJECT_DIR=/opt/scrapalot python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py open \
    --run graph-<short-doc-id> --command /scrapalot:book-graph \
    --scope "<title> — graph layer only, until a critic says the stored entities are the book's"
```

Starter gates. Adapt to the book you resolved.

```markdown
- [ ] G0: every book this command closed before is still what its critic accepted
  CHECK: bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/closed-intact.sh check
  EXPECT: /^CLOSED_INTACT_OK closed=\d+ reopened=\d+$/m
  EVIDENCE: pending
- [ ] G1: parse is recorded clean for this book and the collection resolves to tier 2
  CHECK: awk -F'|' '$4=="<document_id>" && $6 ~ /^parse_done_clean/ {n++} END{print "parse_clean_rows="n+0}' ${CLAUDE_PROJECT_DIR}/.claude/postprocess/progress.txt
  EXPECT: /parse_clean_rows=[1-9]/
  EVIDENCE: pending
- [ ] G1b: the chapter layer is not linear windows of chunk_index — the equal-window shape the chapter-lock recovery left
  CHECK: bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/chapter-windows.sh <document_id>
  EXPECT: /^CHAPTER_WINDOWS_OK$/m
  EVIDENCE: pending
- [ ] G1c: no stored chapter title that the text prints as a line of its own opens a sentence the next line finishes (the OK line says how many titles were judged; 0 judged proves nothing)
  CHECK: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/chapter-titles.py <document_id>
  EXPECT: /^CHAPTER_TITLES_OK judged=\d+ of \d+$/m
  EVIDENCE: pending
- [ ] G1d: the parse row was written about the chunks stored now — no chunk was written more than an hour after it (UNJUDGED passes and proves nothing)
  CHECK: bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/parse-fresh.sh <document_id>
  EXPECT: /^PARSE_ROW_(FRESH|UNJUDGED)/m
  EVIDENCE: pending
- [ ] G1e: the stored chunks hold the book's words — the chunker's old running-header rule cut no word out of a sentence here (the check only measures; G1e-read judges)
  CHECK: bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/chunk-text-loss.sh <document_id>
  EXPECT: /^CHUNK_TEXT_LOSS_(NONE|FOUND)$/m
  TIMEOUT: 300
  EVIDENCE: pending
- [ ] G1e-read: every lost word G1e lists was READ: NONE passes; FOUND is a block when the lost words change what the book's sentences say or would feed the graph a name the book does not print, and is recorded and built on only when they are a handful of index cross-references or a stray word
  EVIDENCE: pending
- [ ] G2: the book's real entity material is read out of documents.content and written down (the bar)
  EVIDENCE: pending
- [ ] G2b: the build outlived every deploy — no worker became ready between the recorded dispatch and completion, and an extraction received once after the dispatch succeeded storing the recorded entities
  CHECK: bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/build-survived.sh <document_id> <dispatched_at>
  EXPECT: /^BUILD_SURVIVED$/m
  EVIDENCE: pending
- [ ] G3: every chunk is reachable Book → Chapter → Section → Chunk, traversal filtered on the Book
  EVIDENCE: pending
- [ ] G4: the stored entity names were read one by one, by a reader who is not the builder, and are things — not sentences, mottos or OCR noise; every name that fails (not a thing, a damaged spelling, a layout artifact, a generic word naming nothing) is named with its class and its owner (extractor, parse, structure), and keeps this gate open until it is fixed at source, the graph rebuilt and its names read again clean by such a reader, or it is recorded as `ABANDON: G4` with the list; stem-variant runs and near-duplicates are counted here and judged at G7a-read, and their members that are not things still fail here
  EVIDENCE: pending
- [ ] G4b: which names the book prints was MEASURED whole word over documents.content with its whitespace collapsed — not by substring, which passes `Eagle` on a book that prints `eagles`, and not against the un-collapsed text, which fails every multi-word name the book hard-wraps
  CHECK: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/name-presence.py <document_id>
  EXPECT: /^PRESENCE names=[1-9]\d* whole_word=\d+ variant_form=\d+ not_found=\d+[\s\S]*PRESENCE_OK$/m
  TIMEOUT: 300
  EVIDENCE: pending
- [ ] G4b-read: every name outside WHOLE_WORD was READ against spelling variants, morphology and the chunk text behind its edges, and called the book's own, a normalisation of what the book prints, or the extractor's invention — a printed plural and an invented label land in the same bucket, so the count alone judges nothing
  EVIDENCE: pending
- [ ] G5: a critic with fresh context, given both entity lists unlabelled, says they are the same book's
  EVIDENCE: pending
- [ ] G6: entity_cache:* was cleared before any re-extraction, or no re-extraction was run
  EVIDENCE: pending
- [ ] G7: every source fix in this run carries a corpus regression scan in BOTH directions
  EVIDENCE: pending
- [ ] G7a: the connectivity layers were measured — aliases, cross-book links, communities, co-occurrence weights, chapter order
  CHECK: bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/graph-layers.sh <document_id>
  EXPECT: /LAYER=canonical [1-9]\d*, \d+[\s\S]*LAYER=alias_person_short_forms \d+, \d+, \d+, \d+[\s\S]*LAYER=real_overlap \d+, \d+[\s\S]*LAYER=communities \d+, \d+[\s\S]*LAYER=cooccurrence \d+, \d+[\s\S]*LAYER=chapter_chain \d+, \d+[\s\S]*LAYERS_OK/
  EVIDENCE: pending
- [ ] G7a-read: those numbers were READ — the book's own figure is quoted beside the corpus baseline `graph-layers.sh` prints for it (canonical names, entities in a community), and anything that is this book's defect rather than the standing corpus gap is named
  EVIDENCE: pending
- [ ] G7b: every cross-book link was READ, and any link riding on a bare surname, an ambiguous common noun, or a name this book never prints is named — `LAYER=shared_link_names` counts that last kind for you, and each one is a FALSE link, not a thin one: the extractor labelled a passage with a word from elsewhere and the label then met another book's real entity
  EVIDENCE: pending
- [ ] G7c: chunk->entity labels were tested against the chunk text, and the number is read as the pointer it is, never reported as a defect rate
  CHECK: bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/edge-honesty.sh <document_id>
  EXPECT: /EDGE_HONESTY chunk_texts=\d+ edges=[1-9]\d* unresolvable_chunk_ids=\d+[\s\S]*EDGE_HONESTY_TOTAL edges=[1-9]\d* name_absent=\d+/
  EVIDENCE: pending
- [ ] G7d: parse damage that reached the graph as an entity NAME was measured — fused words and one-off spellings
  CHECK: bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/name-damage.sh <document_id>
  EXPECT: /NAME_DAMAGE names=[1-9]\d* fused=\d+ oneoff=\d+[\s\S]*NAME_DAMAGE_OK/
  EVIDENCE: pending
- [ ] G7d-read: every flagged name was READ and called parse damage or a correct form — about 59% of `fused` corpus-wide are names a book legitimately writes
  EVIDENCE: pending
- [ ] G8: the ledger row for this book is in progress.txt AND next-book.py can read it
  CHECK: awk -F'|' '$4=="<document_id>" && $6 ~ /^graph_done_clean/ {n++} END{print "canonical_rows="n+0}' ${CLAUDE_PROJECT_DIR}/.claude/postprocess/progress.txt
  EXPECT: /canonical_rows=[1-9]/
  EVIDENCE: pending
```

G1, G1b, G1c, G1d or a G1e-read block is the end of the run, not a hurdle to argue with: report
it, point at `/scrapalot:postprocess-parse`, and close the ledger with the rest
abandoned and the reason stated.

**G1e is about the chunk TEXT, not the chapters.** Until the chunker's
running-header rule was fixed it deleted every line under 40 characters that
repeats three or more times, and a book that puts a short string on a line of its
own inside a sentence — an EPUB converter does this with every italic run — lost
the sentence's own words. cc32d8f5's stored chunk says "Dreams in which suicide is
highlighted are encouraging the actual taking of an individual's physical life"
where the book prints "are not encouraging", and its italic heading line `Themes`
became the entity `strong emotional dreams`. The fix changes new chunking only;
every chunk stored before it keeps the cut. A graph built on such a book extracts
from text the book does not print, and has to be rebuilt the day the book is
re-chunked, so the build is waste twice over. `chunk-text-loss.sh` runs the live
filter over `documents.content` with and without the sentence rescue, then looks
each rescued word up in the stored chunks: `sentence_words_lost` is the number
of words really absent from them. It counts only words that open in lower case
and carry no digit, because the rescue also re-admits some margins — a title
running head where a page broke mid-sentence (4fb26145 printed "The Experience
of Eternity" 54 times that way) and index rows — whose absence is the old rule
being right; those are listed separately and never block. Measured over the
picker's next 25 books: 19 lost nothing, 8ba92b05 lost 44 words and f6cbf45f 33
(`and`, `or`, `must`, `justice`), and three lost 1 to 9, mostly index
cross-references. Re-chunking is the owner's decision, so the sweep cannot repair
a blocked book, only decline to build on it and leave the row that puts it on
his list.

When the stop is a verdict on the stored chapters — `CHAPTER_WINDOWS_LINEAR`,
`CHAPTER_TITLES_SENTENCES` or `PARSE_ROW_STALE` — also append a progress row
whose STATUS begins `graph_blocked_chapter_layer`
(`graph_blocked_chapter_layer;<reason>`, the narrative in NOTE). `next-book.py`
skips a book whose latest row between `parse_done_clean` and that block is the
block, a reopened book included, and a later parse pass that records the book
clean returns it to the queue. A G1e-read block writes the same kind of row with
the reason `chunk_text_lost` (`graph_blocked_chapter_layer;chunk_text_lost`), so
the picker skips it by the same rule until the book is re-chunked and parsed
clean again. No picker offers a blocked book on its own, so
that pass has to be aimed at the book. `next-book.py` already skips a book it can
see is LINEAR or STALE, so the row matters most after `CHAPTER_TITLES_SENTENCES`,
which only the per-book check reads: without it the sweep is handed the same book
again. Write no block row for anything else. Not when G1 fails: `next-book.py`
never offers a book without a clean parse row, and the parse pickers would count
the row as an audit. Not on a `*_FAIL` line or a check that timed out: that is a
failure to look, not a verdict, and a block row would park a clean book for good.
Stop the run and look again later.

G6 exists because the 24 h Redis cache makes a re-extraction after a prompt or
gate change a silent no-op — the evidence is the clear command you actually ran.

## Phase 1 — extract the bar

Before looking at Neo4j, read the book. Pull the real entity material out of
`documents.content` — the people, places, works, concepts it actually discusses,
sampled from start, middle and end. Write that down. Everything after this is
judged against it, not against a density metric.

Write down the **discriminators** too: terms the field would expect that this
book does NOT use, with their zero hit count. They cost nothing and they are what
turns "these look like alchemy words" into a test — a 1980 monograph writing
Melanosis / Leukosis / Xanthosis and never nigredo / albedo / rubedo is provable
in one grep, and the Latin trio appearing in its graph would be contamination.
**A discriminator tests something only if another book's node carries it**: on
one book 29 of 47 zero-hit field terms existed nowhere in the graph, so they could
not have attached and proved nothing. Write each zero beside that term's node
count in the whole graph.

A bar's closed list of the people, institutions and places a book names is a list
to read against, never a filter. One bar declared everything beyond its six names
foreign, and the book itself prints `California`, `Egypt` and `Mother Goose`.

**Count presence as whole words** — `grep -oiwE`, `\b…\b`, or
`regexp_count(content, '\mterm\M', 1, 'i')` in Postgres. `grep -oiE orme` returned
45 on a book that writes `ORMEs` exactly once, so 44 of the 45 were inside other
words — and the 45 went into the table that refuted a critic, then into a progress
row, before anyone counted again. **A zero is the other way round:** a
discriminator's zero must hold as a substring too, because a whole-word zero can
miss a form the book does write. **The stored text marks italics with underscores,
and `_` is a word character**, so `\b…\b`, `grep -w` and Postgres `\m…\M` all miss
a name that opens or closes an italic span: measured, `Magnum Opus` counts 0 that way and 3 with `_`
treated as a boundary (`(?<![^\W_])…(?![^\W_])`).

Then, **before dispatching any build**, measure how many of those names the graph
ALREADY holds from other books. Once entities are written the two are
indistinguishable, and "did this extraction produce the book's entities" quietly
becomes "does the corpus happen to contain these words". Measured on one book:
12 of 53 were already there; the other 41 had to come from that run or not at
all.

## Phase 2 — build or audit

Run `scripts/book-graph/disk-check.sh` before you dispatch anything. A build is
the single biggest writer in this pipeline, and starting one at 88% is how the
volume fills with nobody watching.

**A deploy from ANY session can kill a build, and nothing reports it.** A deploy of
scrapalot-chat `main` restarts the workers when the push touches code they import,
and its image-build path recreates them; workspace gotcha #12 covers only your own
push. Measured: a build dispatched at 18:53:06Z stopped at batch 8 of 15 when
another session's deploy restarted the workers (at 19:21, and again at 19:26) — no error, no failed
task, `graph_sync_status` still reading `entity_running`, and about USD 0.31 of
finished batches with no `extract` row, because the phase timer writes when a phase
ENDS. It happened again the next night: a rebuild dispatched at 02:50:46Z died when
a deploy restarted the workers at 03:11:38Z. So dispatch only while no
`deploy-backend.yml` run is in progress on `main` (a PR's checks restart nothing)
**and no open scrapalot-chat PR is about to merge**: sessions here merge within
minutes of a green automated review. Measured: a build dispatched at 10:00:18Z,
with no deploy in flight, died at 10:16:17Z because a PR whose automated review
finished at 10:03:02Z merged at 10:03:32Z and its deploy recreated the workers. Read
`gh pr list --repo sime2408/scrapalot-chat --json number,headRefName,updatedAt` and
`gh run list --repo sime2408/scrapalot-chat --branch <headRefName>` for PRs with
checks running or finished in the last half hour, and hold the dispatch until that
PR has merged and its deploy has finished, or until its session confirms it will
not merge during the build. Write the dispatch time down, and prove survival at the end with `scripts/book-graph/build-survived.sh <document_id>
<dispatched_at>`: the sync row completed after the dispatch, no worker logged `ready.`
between the dispatch and `completed_at`, and an `extract_entities` task received once after
the dispatch succeeded storing exactly the recorded entities. Not StartedAt, which is a container's last start only:
a restart 43 minutes after one build finished turned a StartedAt check red over that
finished build, and one timestamp cannot say whether an earlier restart fell inside
the build. A killed build is half-built — the branch below — and its
spend goes into the progress row by hand, because no table attributes it to the book.

**A killed extraction comes back 3h20m later, onto whatever the book has become.**
The broker keeps the unacked message and redelivers it after `visibility_timeout`
(12000 s). Measured: `extract_entities[30a7ec5c…]` was received at 18:53:11, killed by the 19:21 restart, and received AGAIN at 22:13:28 with the same id — over a book
that had been rebuilt and accepted in between — and that run wiped its graph (the
purge rule it met was fixed since; the redelivery was not). After any kill, find
the killed task's id in the Celery log and `revoke` it on every worker. A revoke
lives in worker memory only and a restart drops it, so look at the log again once
the 3h20m mark has passed.

**The weekly backup stops Neo4j on Sunday morning.** `scrapalot-backup.sh` runs at
04:00 UTC every Sunday and dumps Neo4j last, with a stop and a start. Over the 12
Sunday runs in its log (2026-06-07 to 2026-09-13) the stop came between 04:12 and
04:43 and Neo4j was healthy again by 04:44 in the 11 runs that log it; two runs off the schedule (2026-06-12
at 11:04, 2026-07-11 at 04:31) stopped it too. On 2026-09-13 a query inside the stop
failed with "container ... is not running". Do not start a build that would span
Sunday 04:00-05:00 UTC. The backup can also fail to bring Neo4j back — on
2026-09-06 its `docker start neo4j` failed and the database was healthy only 56 s
later — so read `/mnt/volume-nbg1-1/backups/backup.log` for the stop, any start error
and the `neo4j state: healthy` line before calling an outage expected.

If no graph exists, dispatch `scrapalot.build_graph_from_existing_chunks` — the
ordering-safe entry point (hierarchy sync on `fast`, then entity extraction on
`graph_extraction`). Ordering is mandatory:
`entity_pipeline._create_chunk_entity_relationships` **MATCHes** Chunk nodes
rather than MERGEing them, so entities before hierarchy silently drops every
chunk-level edge, of all five types.

If a graph exists, delegate to the **`scrapalot:postprocess-graph` agent** (Agent
tool), scoped to this document_id. Do not let it pick its own book.

**There is a third state, and it is the common one after an interrupted run:
half-built.** Hierarchy complete and entity count ZERO, because the chained build
died between its two steps — a Neo4j circuit breaker, a restart, a killed worker.
The tell is `graph_sync_status.status` in (`pending`, `hierarchy_done`) with
`chunks_created` > 0 and `entities_extracted` = 0 — or `entity_running` with zero
entities and no extract task for the document in `celery inspect active`: a build
killed mid-extraction leaves `entity_running` behind, and the reconciler leaves
that state alone for 180 minutes (`IN_FLIGHT_GRACE_MIN`). Treat it as "no graph" and
dispatch the ordering-safe build: it MERGEs the hierarchy, so re-running is safe.
Handing it to the audit agent instead audits an entity layer that does not
exist.

Either way, verify the chain end to end yourself:
`Book → Chapter → Section → Chunk`, every chunk reachable. **Filter traversals
on the Book, not on `document_id`** — `Section` nodes do not carry it, and a
scan that filters on it reports a broken hierarchy that is perfectly intact.

**Use these names. Guessing them costs queries and, worse, returns a plausible
wrong answer instead of an error:**

| Thing | It is | It is NOT |
|---|---|---|
| Section → Chunk edge | `[:CONTAINS]` | `HAS_CHUNK` |
| Book → Chapter, Chapter → Section | `[:HAS_CHAPTER]`, `[:HAS_SECTION]` | — |
| chapter number | `ch.number` | `ch.chapter_number` |
| chunk text | not on the node at all — pgvector only | `c.text` |
| Chunk → Entity edges | five types: `MENTIONS`, `DEFINES`, `REFERENCES`, `DESCRIBES`, `DISCUSSES` — measured on one book 1,050 / 415 / 186 / 25 / 20 of 1,696 | `[:REFERENCES]` alone, which reached 75 of that book's 635 names |
| co-occurrence weight | `r.document_weighted_score` (with `r.weight_updated_at`) | `r.weight`, which nothing writes |

A wrong relationship name returns **zero rows**, which reads exactly like "no
orphans". A wrong property returns **NULL for every row**, which reads exactly
like "the field is never populated" — that one nearly went into a report as a
finding on 2026-09-12 before it was checked.

**`cypher-shell --format plain` prints nothing at all — not even a header — when
an aggregation with a grouping key matches zero rows.** So empty output is
indistinguishable from "zero problems found".

**Never let a gate infer success from an empty cypher result** — that rule covers
every query shape, not just counts: a list-shaped check for orphan chunks prints
nothing when the book is clean AND when the query is wrong.

**The literal marker is not a weak defence — it is the CAUSE.** A bare
aggregation with no grouping key is already safe: `MATCH (x:NoSuchLabel) RETURN
count(x)` prints a row reading `0`. Add a marker and it prints nothing at all:

```
MATCH (x:NoSuchLabel) RETURN count(x);            -- prints  count(x) / 0
MATCH (x:NoSuchLabel) RETURN 'M' AS k, count(x);  -- prints  NOTHING
```

Both verified against this database. The literal becomes a grouping key, zero
rows means zero groups, and the query that was going to answer honestly now
answers with silence — so the advice to "add a marker" manufactures the very
failure it was meant to prevent. **If a plain count answers your question, do not
decorate it.** When you genuinely need a marker or extra fields on the row,
anchor on a node you know exists and make the counted pattern OPTIONAL:

```cypher
MATCH (b:Book {document_id: $did}) WITH b
OPTIONAL MATCH (b)-[:MENTIONS]->(e:Entity)
RETURN 'ents' AS k, count(e) AS n        -- prints  "ents", 0
```

Prove it on your own check before trusting it: swap the relationship for one that
cannot exist, `[:NO_SUCH_REL]`, and confirm the check prints a zero rather than
nothing.

**`cypher-shell --format plain` is not CSV.** Names and stored contexts contain
commas and escaped quotes, and a CSV reader over 1,984 edge rows (`RETURN c.id,
e.name, r.context`) broke on them. Concatenate the fields in Cypher with a separator
no name contains (`c.id + '|~|' + e.name`) and split on that.

## Phase 3 — entity names, by reading them

Density is not quality. Read the actual names, and never as the builder: a fresh
agent holding only the names and the book text reads them, for the first read
and for every re-read after a fix. On three books the builder's own first read
ticked G4 over names that an independent re-read then failed (9, 12 and 60
not-things).

Read them in six classes and name every exception with its owner. One book's 966
names had 127 (13%) flagged by one reader, before the generic-word test below existed: **not things** (the motto `as above, so below`, stage
notation, item lines of a list the book quotes — extractor); **damaged spellings**
(8 printed so by the book, e.g. `Diodes` for Diocles — parse; 2 normalised by the
extractor); **layout artifacts** (speaker labels such as `ALEXANDER`, citation
captions such as `Hymn XCI`, part labels such as `First Part` — structure);
**stem-variant runs** (Calcination / Calcined / Calcining — dedup, though a bare verb
form such as `Putrefy` is also not a thing); **near-duplicates** (Paracelsus in 5
forms, and the book's own equations such as Cauda Pavonis = Peacock's Tail — the
dedup gap); **generic words** stored as entities (`Hope`, `Lord` —
extractor).

**Not things, damaged spellings, layout artifacts and generic words that name nothing
fail G4** — any fail is a fail; the list is what an `ABANDON: G4` carries, never a
reason to tick it. A spelling the extractor merely normalised (an added accent) is
not damage. A word is generic when the book only uses it in passing — in lists,
idioms or ordinary phrasing — and never makes it the subject of a passage, a
practice, a definition or a heading: the text decides, never a sense that the word
"is a concept". A single aphorism, quotation or "X is ..." sentence is not a
definition (`Desire is an illusion caused by separation`); a definition is a
passage the book spends on the word, and G4's evidence quotes that passage for
every abstract name kept out of the class. Read that way, one book's 785 names
held 74 generic words, while `Fear`, `Forgiveness` and `Magic`, which that book
makes the subject of passages, were not. Stem-variant runs and near-duplicates are the dedup gap no book can
close today, since every name is its own canonical name: count them here, judge
them under G7a-read, and fail G4 only for their members that are not things. A name
in a failing class fails as that class even when it also sits in a dedup group:
`Ph&nix` beside `Phoenix` is a damaged spelling, and `Lord` beside `Lord Jesus` a
generic word.

**If the book is not in English, read them twice.** A German book stored the
philosophers' stone as `Steines der Weisen` — the genitive, lifted from a
sentence — while `Stein der Weisen`, its own chapter subtitle with 43 hits, was
never stored at all; the grail came out as `heiligen Grales`. 10% of that book's
names began with an inflected lowercase adjective taken straight from running
text. The citation form is what links across books and across languages, so when
it is missing the entity is effectively unreachable: that book could not reach
the English `Philosopher's Stone` node that already existed.

Expect translation too, and do not mistake it for contamination. The same book
carried thirteen English names — `Rosicrucians` for Rosenkreuzer (45 hits),
`three principles` for its Sal/Mercur/Sulfur triad, `Quintessence` for
Quintessenz — every one a faithful rendering of something the book contains.
**Read the chunk text behind the edge before calling any of it foreign — never
the edge's stored `context`.** That property is the opening 200 characters of the
extraction unit the entity was first found in (`entity.source_text[:200]`), copied
onto every chunk edge the entity gets. Measured over one book's 1,984 chunk edges:
it occurs in the edge's own chunk for 54.4% of them, contains the entity's name for
24.4%, and a single context sits on 76 different chunks. On that book the stored
context "condemned" `Sündflut` as contamination; four of the five chunks behind its
edges speak of the Flood and Noah, so it was the book's own Flood under another
book's German node. Fetch the chunk from pgvector by the edge's chunk id and read
that.

```cypher
MATCH (b:Book {document_id: $did})-[:MENTIONS]->(e:Entity)
RETURN e.name AS name, e.source AS source, e.entity_type AS type ORDER BY e.name
```

Garbage is never a row to patch away, but **whose bug it is starts with one
test: does the string appear in `documents.content`?**

* **It does not** — the extractor INVENTED it. A sentence or verse line ("Follow
  me, but look not to the right…"), a foreign motto ("ut bos locutus est"), a
  composed description the book never writes. That is a **source-code bug**:
  trace it to the LLM prompt (`entity_extraction.extraction_prompt` and
  `is_valid_entity_name`, the name gate both extraction paths share) or the spaCy
  path (`create_spacy_entity` in `entity_extractor.py`) and fix it there.
* **It does, and the string is damaged** — the extractor COPIED it faithfully and
  the damage is upstream in the parse. `Sulfiir`, `Dr. Karl KOnig`, `ArgonautenSage`
  are all in the stored text already. Fixing the extractor cannot help, and
  `parse_done_clean` does not contradict it: that row promises the chapter layer,
  not clean text. Report it to the owner; do not delete; do not blame the prompt.
* **It does, and the string is well-formed but not a thing** — still the
  extractor's, or the structure's for labels and captions; the six classes above
  name them.

The presence test below separates invented strings from present ones;
`name-damage.sh` in Phase 3.5 separates damaged copies from well-formed names,
mechanically, for the cases it can. It cannot do that for OCR mangling with no
seam and no near neighbour —
`Gäblr ibn Hayyän`, `Mvlaprakrti`, `al-Färäbl` — nor for `King Solotmn`: the
name occurs once, but it has two words, and its damaged token `Solotmn` occurs
twice, so neither the single-token rule nor a per-token variant can call it a
one-off (that variant also flagged 28 real words over five books). Both are still
found only by reading the list, and were. So were a fusion with no internal
capital (`Godconsciousness`, printed once, and `God consciousness` never) and a
two-word name whose damaged token is printed as often as the intact form
(`vibeshifting mist`, 1 against 1 for `vibe-shifting`).

**Then run the cheapest check in this file, because reading names one by one does
not catch this one:** `name-presence.py <document_id>`, every stored name tested
against `documents.content`, case-insensitive **and quote-normalised**. Count
nothing from it. **This check FLAGS; it never concludes.**

Use the script rather than writing the test again for this book. Both halves of
it were got wrong by hand, in opposite directions, on one book: the first pass
was `name in text`, a plain substring, so `Eagle` counted as printed because the
book prints `eagles`; and it ran against the text with its line breaks, so every
multi-word name the book hard-wraps failed it — `Regaining the West Bank of
Jerusalem` was reported missing from the book whose chapter it names. The
corrected reading was 637 printed / 22 another form / 49 absent where the
hand-rolled one said 621 / 37 / 50, and the reading of the flagged names had
already been sent out on the wrong list. The script collapses the whitespace
once, matches whole words with the name's own spaces matching any whitespace
run, and sorts into three buckets instead of two, so a printed plural stops
looking like an absence. A flagged name is a name to
read, and before any verdict you check it against:

* **spelling variants** — a book wrote `Uroboros` three times, the extractor
  stored the standard `Ouroboros`, and the check called it contamination from
  another book. It was correct entity resolution, and acting on that finding
  would have deleted a true fact from the graph;
* **plurals and morphology** — `Synchronicities` for synchronicity,
  `Apprenticeships` for apprenticeship, `Hermeticism` for hermetic;
* **hyphenation and spacing, in either text** — `Bhagavad-Gita` for "Bhagavad
  Gita", and the other way round: the SOURCE can carry a stray space inside a
  word. A book printing `swimming-g irdles` made the correctly stored
  `swimming-girdles` read as absent, a finding was built on that absence — "the
  extractor completed a famous list from its own knowledge" — and it had to be
  withdrawn. Before calling a name absent, test it again allowing whitespace
  between any two of its characters, bounded as a whole word at both ends —
  stripping every space from the whole text instead lets a short name match
  across a word boundary. A name that passes only this way is still read;
* **quote characters** — one book used 45 curly apostrophes and no straight ones,
  the next 30 straight and no curly, so `philosopher's stone` read as absent from
  a book that writes it twice;
* **labels borrowed from another book's node** — the extractor resolves the book's
  own idea onto a node another book already created, in that book's wording or
  language. On one book 8 of 13 flagged names were exactly that, and 3 more were
  spacing or accent normalisations that landed on nodes another document had
  created: the German
  `Sündflut` for its "the Flood", `Goldmacherei` for its "Gold-making",
  `illusion of separation` for its "Separation is an illusion." Only the chunk text
  behind the edge settles it.

On the book where the first four were found, **zero** of twenty flagged names were
contamination. What survived the reading was different and real: labels invented
over true headings, and descriptive phrases the book never writes.

**Never build a pass/fail contamination gate on a fixed word list.** Absence of a
string is not absence of a thing, and a gate that equates them returns a
plausible wrong answer rather than an error — the same failure this file warns
about for Cypher, in a new place. Read the exceptions individually rather than
counting them — most are benign normalisations (a hyphen the book does not
use, a first name the book omits), but the corruptions hide in the same list, and
they are the ones that matter. On a 457-name book this returned 4 exceptions in
under a second: two normalisations and two corruptions of titles the book writes
18 and 29 times respectively. Run it before the critic sees the list, so the
critic spends its one question on whether the graph is the book's rather than on
spelling.

The Redis `entity_cache:*` serves cached extractions for 24 h (the default
`cache_ttl_hours`; a live key had 72,755 s left) and keys them on the unit's text
alone, not the prompt or the model, so a re-extraction
after a prompt or gate change is a **no-op until that cache is cleared**. Clear
it before re-extracting, and say that you did.

## Phase 3.5 — the layers a name list cannot show you

Reading 457 entity names one by one says nothing about how they are JOINED, and
a book can pass every check above while its connective tissue is wrong. Run both
scripts and read the output; neither needs a model or a round.

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/graph-layers.sh  <document_id>
bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/edge-honesty.sh  <document_id>
bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/name-damage.sh   <document_id>
```

**Always print the corpus baseline beside the book's own number**, which both
scripts do. Otherwise you cannot tell "this book is broken" from "nothing in the
corpus has this yet", and you will report a standing gap as a fresh defect.

What to do with each:

* **Aliases.** `canonical_name` is only a lowercase/despace of `name`, so it
  resolves nothing: if entities and distinct canonical names are the SAME
  number, there is no deduplication at all. The script counts short person names
  stored beside a longer one and puts each short form in exactly ONE class,
  because they are different evidence. A surname matching one full name (`Hart`
  beside `Clive Hart`) is a likely missing alias; a given name matching one is
  weaker; a short form matching several names cannot be merged on its own — it
  can be several people (`John` matched five different men in one book: Dee,
  Aubrey, Trithemius, Mehung, Helvetius) or several names of one person (`Steiner`
  beside `Rudolf Steiner` and `Dr. Steiner`). Those are printed by name; read
  every one. A short form stored under ANOTHER type escapes all three classes
  (`Lauren` typed place beside `Lauren Aletta`), so the script lists those too.
  Over five books it listed 11: 5 mistyped people (`Lauren`, `Newton`, `Bacon`,
  `Berkeley`, `Johannes`) and 6 words inside a longer name: places in a title or byname
  (`England`, `Tyana`), gods or planets (`Jupiter`, `Venus`), `Egypt` in
  `Alexandrian Egypt` and `Divine` in `Divine Mother`. Read the person- and place-typed names as well: on one
  book 6 of 15 were mistyped (crystals typed person, a bird typed place).
* **Cross-book links — read them, never count them.** `shared_entity_edges`
  against `real_overlap` shows how incomplete the linking is, but the damage is
  in WHAT each link rides on, which is why the script prints `top_entities` per
  edge. A link built on bare surnames is a false claim about two books: one
  measured case joined a Joyce monograph to a family-violence casebook on `Hart`
  and `Finn` — in that book, Clive Hart the scholar and Finn MacCool. **Alias
  duplication and wrong cross-book linking are ONE defect**; naming them
  separately hides the cause. The stored `shared_entity_count` and
  `top_entities` count only shared entities past the corpus IDF cutoff, or with
  no idf yet, and on one book they sat below the real overlap on 11 of 17 links (7
  stored against 25 shared) and matched it on the other 6. Read the shared names behind a link, not only
  what the edge stores.
  **A shared name the book never prints is a FALSE link, not a thin one**, and
  `LAYER=shared_link_names` now counts them so nobody has to find them by hand
  again. The extractor labels a passage with the standard name of what it judges
  the passage to be about, in words the book does not use, and that label then
  meets another book's real entity: on cc32d8f5 a passage on air, breath and
  fire was labelled `Water of life` and joined an alchemy text; theme 16, on
  earthquakes as a shift in self-image, was labelled `catastrophic thinking` and
  joined two CBT workbooks; and an English account of withdrawing from society
  was labelled `Initiationspfad`, in German, joining a German alchemy book. Nine
  of the 99 names carrying that book's 22 links were absent from it. Read the
  chunk behind each absent name — the edge is real, the shared thing is not.
* **Communities and co-occurrence weights.** Report the book's coverage beside
  the corpus total. Zero weights corpus-wide means no successful weight recompute
  is reflected in the store — a dispatch question for the owner, not a book
  defect.
* **Label honesty.** An edge pointing at a chunk that never writes the entity's
  name is wrong whatever the label means. It is a floor in one direction and an
  upper bound in the other, so it is a pointer and never a score: it cannot see
  an edge whose name is present but whose label is wrong, and it wrongly flags
  every edge whose stored name is a normalised spelling of what the text writes.
  `EDGE_HONESTY_SPLIT` sorts the flags. `variant` is such a normalised spelling.
  `neighbour` means the name is printed within two chunks of the edge's own: still
  a wrong edge, but mostly with one cause. Production extracts from merged units and
  gives every entity found in a unit an edge to every source chunk of that unit.
  Over five books `neighbour` ran from 0.8% to 38.6% of all edges and from 16% to
  78% of the flags; rebuilding the units put the name, or a variant of it, inside
  the edge's own unit for 1,522 of those 1,575 edges and outside it for 53, which
  that cause does not explain. Read `elsewhere` and `nowhere` first, then a sample
  of `neighbour`. The reverse
  also happens: a name printed once, in a chunk that carries no edge to it. Read
  the offenders; do not report the percentage as a defect rate.

**A runnable CHECK here can only prove the measurement RAN.** Both scripts fail
closed — a mistyped id, a missing Book node, an unreachable Neo4j or an EMPTY
entity layer aborts with `LAYERS_FAIL` / `EDGE_HONESTY_FAIL` rather than printing
blanks and a cheerful marker — and both EXPECTs are bound to nonzero digits, so a
blind run cannot tick the box. The empty case was a green tick until it was
measured: on a book mid-rebuild with 0 entities, both scripts printed zeros that
matched their EXPECTs. But no regex can prove anyone READ the numbers, which is the whole point of
these layers; that is what the manual gate beside G7a is for, and why G7b has no
CHECK at all. A machine proves the measurement; only a written claim proves
someone looked.

**Parse damage in entity names** (`name-damage.sh`) is the third: fused words
where a line break lost its hyphen, and names occurring exactly once while a
hyphenated variant occurs more often. A blind critic found this class on a German
book after every other gate had passed, which is why it is now a check. It
excludes Gaelic and Scottish surnames — `McHugh`, `MacCool`, `MacDougall` carry
an internal capital by right, and flagging them would repeat the verbatim check's
mistake of calling a correct form an error.

Everything here is **measured and reported, never fixed in place**: aliases need
re-extraction and weights/communities need a workspace-wide dispatch, and both
are the owner's call.

## Phase 4 — the loop

Builder fixes → **separate critic agent, fresh context** → judge.

The critic gets the entity material read out of the book and the entity names
stored in the graph, **unlabelled**, and one binary question: *are these the same
book's entities — yes or no; if no, the single biggest difference.* For a source
fix it also gets the **raw** corpus scan, not a summary. "Mostly" is a no. Never
a score.

**Method, written into the critic's prompt: judge compatibility, never
expectation.** The question stays exactly the one above; the method for answering
it is to ask whether these names could come from the text that produced the
material, never whether a book of that kind *would* contain them. Left to itself a
critic reasons from genre. One said NO because "a ufology apparatus cannot belong
to a urine manual": UFO/UFOs (18), Shambhala (17), New Atlantis (9), ORMUS (6),
Agartha (5) and Vril (3) are all in that book's text, counted as whole words. Of
three names it flagged in the same answer, `illusion of separation` is the book's
own "Separation is an illusion." stored under a label another book's node already
had; `vibratory planes` and `cognitive illusions` have no whole-word hit, and nobody
read the chunks behind them before that build was wiped. Judge the terms one by
one, against the chunk text — a batch verdict is wrong in both directions.

So a NO whose reason is a claim about the book is checked against
`documents.content`, term by term and as whole words, by an agent that is not the
builder. **It is refuted only when every term it names turns out to be the book's
own** — present as a whole word, or read as a variant of what the book writes. Then that
round measured the critic rather than the graph, and a fresh critic gets the same
two lists and this instruction — never the rebuttal. One absent term and the NO
stands. Save every critic prompt beside the ledger, so "never the rebuttal" can be
checked later. A second refuted NO in a row is not re-rolled: stop and report both.

**A count of what changed is not a measurement of whether it improved.** "129
entities retyped" answers neither direction — a retype can be a correction or a
regression, and the scan cannot tell you which. Turning the diff into the
both-directions number G7 asks for takes a second blind pass:

- hand the judge **one row per change**, with the fields that actually differ and
  nothing else. On 2026-09-12 the descriptions were byte-identical in both arms,
  so each row was `{name, description, type_A, type_B}` — the type was the only
  variable;
- **randomise which arm is A per row**, and keep the key in a file the judge never
  sees. "Always pick A" must be worth nothing;
- never tell the judge a change is under test, which side is the fix, or what the
  fix was meant to achieve. Ask only which label is correct for the thing;
- allow **BOTH** and **NEITHER** verdicts. Without them a judge is forced to
  manufacture a winner on rows where the vocabulary has no right answer, and the
  regression count comes back fiction. Both appeared in the real run.

Then join the verdicts back through the key. **Improved / degraded / tie, plus the
single worst case read in full** — that is the number, and it is the builder's job
to produce it and nobody's job to estimate it.

If the NO stands, the critic's one sentence goes back to the builder. **Exit is the critic
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
CLAUDE_PROJECT_DIR=/opt/scrapalot python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py run gates/active/graph-<short-doc-id>.md
CLAUDE_PROJECT_DIR=/opt/scrapalot python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py close gates/active/graph-<short-doc-id>.md
```

Every `ABANDON:` line is named in the report. The gate summary is re-measured at
report time, never recalled.

Then record what the critic accepted, so every later pass can prove it is still
there. A closed ledger is not a stable fact: a book closed 16/16 with 965 entities
held 0 seventy minutes later, and no check existed that would have looked again.

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/book-graph/closed-intact.sh record <document_id>
```

It refuses a graph with any empty layer, and a closed book whose numbers moved
since it was recorded: that book is `reopen`ed, not re-recorded.

**Correcting a closed ledger.** A manual gate found wrong after `close` is
corrected in its own ledger, never in a new one. Move the file back to
`gates/active/`, untick the box, add the correction to its EVIDENCE and the
`ABANDON:` line if the gate is not met, then `close` again WITHOUT `run`. `close`
reads the boxes and executes nothing, while an old ledger's CHECK EXPECTs may no
longer match the output of scripts changed since, so a re-run would fail them
for their format, not their outcome. Say in the evidence that the CHECKs were not
re-run, and append a `graph_correction` progress row that names every correction.
Closing without `run` may only untick a box, abandon a gate or correct evidence,
never tick a box: a tick needs the full `run`. On 2026-09-13 three ledgers had G4
corrected this way after an independent re-read refuted it, and two ledgers had
evidence details corrected, one of them twice.

Ledger row in `.claude/postprocess/progress.txt`, appended, never edited in
place. Its STATUS column — the sixth, `ISO_TS|COLLECTION_UUID|COLLECTION_NAME|
DOCUMENT_UUID|FILENAME|STATUS|BUG_COUNT|NOTE` — **must begin with the token
`graph_done_clean`**, and everything this pass wants to call the outcome goes
after a `;`. That token is not decoration: `next-book.py` reads it to decide the
book is finished, and a row that opens with prose instead is invisible to it —
the sweep then offers the same finished book again and cannot advance. Write the
narrative in NOTE, where it belongs. Off-topic findings to
`side_findings.txt`; in chat, plain Croatian with no pipeline jargon — no
"chunk", "tier", "entity", `file:line` or table names in what the owner reads.

Then stop. Do not start the next book unprompted.

## Phase 6 — sharpen this command, once per book

This audit is only as sharp as what this file tells you to look at, and every
book teaches it something. **Before the next book starts, edit this command so
the next pass sees what this one had to find the hard way.**

Three sources, and nothing else counts as one:

1. **A check that went green while the thing it checked was wrong.** A ledger
   CHECK that passes on a broken outcome is a defect in the check, not bad luck.
2. **Anything the critic found that no check here asked about.** The critic is
   the bar; whatever it caught first is a hole in the phases — turn it into a
   query that would have failed before the critic ever saw the book.
3. **Anything you had to work out by hand that this file should have said**: a
   query that measures the wrong thing, a path that has moved, an order that
   only works one way round.

Each becomes one concrete edit — a corrected query, a new check with the number
that makes it fail, or a deleted line that misled — committed to the plugin repo
with the evidence in the message: the query that lied, what it returned, what
was true.

The plugin has no CI and no deploy: the checkout at `/opt/scrapalot/.claude` IS
the live plugin, and it is shared, so the edit takes the same route as any other
change in this workspace — a worktree, never the shared tree:

```bash
REPO=/opt/scrapalot/.claude
git -C "$REPO" fetch -q origin master
git -C "$REPO" worktree add "$REPO/worktrees/sharpen-<book>" -b chore/sharpen-<book> origin/master
# ...edit plugin/commands/book-graph.md in the worktree, commit with the evidence...
git -C "$REPO/worktrees/sharpen-<book>" push -q origin HEAD:master
git -C "$REPO" pull -q --ff-only origin master        # this is what makes it live
git -C "$REPO" worktree remove "$REPO/worktrees/sharpen-<book>" --force
git -C "$REPO" branch -D chore/sharpen-<book>
```

The next pass reads the sharpened file; the one in flight does not, since a
session reads its command once at start.

**What keeps this from becoming drift:**

- **Measured, never guessed.** No edit without a number or a quoted line from
  this pass. "Could be clearer" is not a finding.
- **General, never about this book.** A rule naming one book or one collection
  is wrong by construction: write the class of defect, not the instance.
- **It may sharpen how you SEE. It may never loosen what you MUST do.** The
  invariants below are outside this phase.
- **Delete as you add.** A command that only grows stops being read; if a new
  rule makes an old line redundant, remove the old line in the same commit.
- **One independent reader.** A fresh sub-agent — never the one that proposed
  the edit — reads the diff against the invariants and answers one question:
  *does this weaken a gate, the bar, or an owner gate?* A yes means it does not
  land. One round: git is the undo.
- **Interrupted mid-book?** The lesson goes to `.claude/book-graph/STATE.md` and
  is applied at the start of the next pass, never dropped.

### Invariants — Phase 6 never edits these

The DIRECTION. The bar (the book's own text, a blind critic, "mostly" is a no).
Builder is not critic. The parse precondition. The cheap-hours, disk and balance
gates and their thresholds. Every owner-gated action. The stop table. The
two-consecutive-APPROVE rule for code. The five-minute limit on a question to
the owner (4b below). Changing any of those is the owner's call, asked in plain
Croatian — never a self-edit.

## Unattended mode — the `books-5` session

**Nothing schedules this command any more.** The cron was removed on 2026-09-12:
the owner wants to watch the work and steer it, not find it done. The work lives
in the `books-5` tmux session — one long-lived Claude in `system.slice`, where a
memory squeeze on `user.slice` cannot reach it; `books-5` attaches to it, Ctrl-B
D leaves it running, and it does nothing until the owner says so.

`scripts/book-graph/run-loop.sh` still exists and still gates a run — cheap
hour, disk, balance, candidate — but it is now a manual entry point;
`scripts/book-graph/install-cron.sh` is what would put a schedule back.

Armed by the owner saying to keep going, or by `SCRAPALOT_BOOK_GRAPH_LOOP=1`.
Then five things change and nothing else; every rule above still binds.

**1. The goal is read, not remembered.** `.claude/book-graph/GOAL.md` holds the
standing instruction. Read it at the start of every iteration and restate it in
one line. `.claude/book-graph/STATE.md` is the memory between runs: which book,
which phase, what was tried, what stopped it.

**2. One book, then the next, with no gap.** Phase 5 says "stop; do not start the
next book unprompted". Once armed the prompt IS standing — until the owner says
otherwise, and in `books-5` they can say it mid-sentence: when a book's critic
says yes and its ledger is closed and its progress row is written, run
**Phase 6** — it is part of the iteration, not an extra — then run
`scripts/book-graph/closed-intact.sh check`, then pick the next candidate with
`scripts/book-graph/next-book.py` and start it, as long as the hour is still
cheap, the disk still has room and the balance still holds. Anything but
`CLOSED_INTACT_OK` and the next book waits: `reopen` the changed book with the
reason, and trace the change to its cause before anything is rebuilt — a graph
that changed after its acceptance is a bug to find, not a book to redo.
`next-book.py` offers a reopened book before any new one, unless a Phase 0 block
row came after it, and `record` refuses a closed book whose numbers moved, so the
only way back to closed is a critic's yes. It also skips, without a ledger or a
row, every candidate on which `chapter-windows.sh` would say LINEAR or
`parse-fresh.sh` STALE, since one query reads both (a FAIL or UNJUDGED is never
skipped), and says how many it skipped before the book it picks and why on stderr,
naming any reopened book among them (`--skipped` lists them all). Phase 0 still runs every check on the book it hands out.
Measured at the change: 436 of 2,802 candidates skipped, 62 on equal runs and 374
on a stale parse row, where opening and closing a ledger for each had been the
sweep's whole work for three books in a row.

**3. Sub-agents do the work.** The orchestrator holds the thread; the passes run
as agents so a long book cannot silt up one context:
`scrapalot:postprocess-graph` for the audit and build, a fresh critic per round
(never the builder), `scrapalot:devops-verifier` for code review. Fan out over
independent checks — entity sample, hierarchy reachability, cross-book links —
rather than walking them one by one in the main thread.

**4. Code changes ship themselves, under a review that is not the author's.**
The loop decides on its own whether a defect is worth fixing at source. When it
is:

- an isolated **git worktree** and a feature branch — never the shared checkout,
  never a commit on `main`;
- `scrapalot:devops-verifier` reviews the **pushed branch**, and the loop keeps
  iterating until **two CONSECUTIVE rounds come back APPROVE**. An immediate first
  approval is not enough: one reviewer reading one diff once is exactly how the
  running-head fix shipped a regression that the second measurement caught;
- **only then open the PR**, its body carrying the measurement that justifies the
  fix, both directions, as every other corpus fix in this repo does. An open PR
  does not wait for its review: on 2026-09-13 one was merged at 01:59:22Z while a
  verifier was rejecting its rule — which shipped — and the next at 02:32:13Z
  after a single approval, both within minutes of their auto review. An approval
  binds to the sha it read, and the auto-fix bot pushes into PR branches: compare
  `git ls-remote` with that sha before opening the PR and again before merging —
  a head that moved, whoever moved it, restarts the two-APPROVE count;
- the repository's own `PR Auto Review` check must be green as well; it runs when
  the PR opens;
- only then merge (squash), and only when the queues are empty and no job is
  `processing` — a merge restarts the containers and kills what is in flight;
- **still owner-gated, and the loop must ask rather than act:** any reprocess,
  any Neo4j write beyond the orchestrated build, `delete_document_hierarchy`,
  and any workspace-wide housekeeping dispatch. Merging its own code is
  delegated; changing stored data is not.

**4b. A question to the owner blocks for five minutes at most.** Set by the owner
on 2026-09-13, in these words: *"nikad ne čekaš moj odg duže od 5 min, inače ideš
po svojoj preporuci i dalje u /loop"*. This is an owner-directed change to how
the owner-gated actions below are reached, recorded here so no later Phase 6
mistakes it for a self-edit.

- Moving to the next book is **never** a question, and neither is anything this
  command already lets the loop decide. The clock exists only for a decision that
  genuinely needs the owner: a reprocess, a Neo4j write beyond the orchestrated
  build, a workspace-wide dispatch, a change of policy.
- **Announce first, then start the clock.** The question goes into the chat as a
  plain Croatian message with the options, and it names the option the loop will
  take if nobody answers. That option is the loop's own RECOMMENDATION — what it
  would do if the decision were its own — not the smallest or safest one.
- **Five minutes, then act.** Inside `/loop` the clock is the loop's own wakeup:
  ask, then arm `ScheduleWakeup` at 300 s with the loop prompt. The next tick
  either finds an answer or carries out the recommendation. Outside `/loop`,
  `Bash(sleep 300, run_in_background=true)` in the same turn. An owner's answer
  that arrives first always wins.
- **When it fires, say so and keep going.** "nije bilo odgovora 5 minuta, idem s
  <opcijom>" — in the chat, in the report and in the gate's `EVIDENCE:` line, so
  the record shows a self-chosen action, never an approval. Then continue the
  sweep in `/loop`.
- **The clock does NOT start** — stop and wait for the owner instead — when every
  option destroys something that cannot be rebuilt, when no option is clearly
  better, or when the question is about what the owner WANTS rather than what is
  true. These exceptions are the owner's own, carried over unchanged from the
  ten-minute rule this one tightens.
- **Silence never widens the menu.** Everything under **Never** stays never,
  however long the quiet lasts; the clock chooses among options the loop was
  allowed to offer, it does not add new ones.

**5. It stops itself.** Every stop writes STATE.md, logs one line, and says why:

| Stop | What the loop does |
|---|---|
| **No balance** — a 402 `Insufficient Balance` from any call | stop immediately, `touch .claude/book-graph/STOPPED-no-balance`, notify the owner (`scripts/book-graph/notify-owner.sh`), exit. Never retry: every further call is a guaranteed failure, and the log fills with them. |
| **Disk nearly full** — `disk-check.sh` exits 2: the Neo4j volume or the checkout's filesystem is at 88% or above | stop **immediately, mid-pass if that is where it happens**: notify the owner first, then interrupt the session with INT so it can park its ledger, `.claude/book-graph/STOPPED-disk-full`, exit. `run-loop.sh` re-checks every 3 minutes while a pass runs, because cron cannot see a volume that fills between two starts. Free space and delete the marker to resume. |
| **A peak window opens** | finish the step in hand, close or park the ledger, exit. The next cheap hour starts a fresh run. |
| **No candidate books left** | say so and exit — the sweep is done. |
| **Two different fixes hit the same gap** | the existing rule: name what was tried and stop. |
| **The owner interrupts** | the normal case now, not the exception: stop where it is, say what was in flight, and leave STATE.md good enough for a cold resume. |

The loop never notifies on success — and with the owner attached to `books-5`,
a notification is the fallback, not the channel. It writes the issue anyway when
it stops on money or disk, because a session nobody is watching at 03:00 is
still possible.
