---
description: "ONE book, end to end — parse layer AND graph layer in a single pass, because parse defects are what usually break the graph. Never marches to a second book. Never skips silently."
allowed-tools: Agent, Bash, Read, Edit, Grep, Glob, Write, AskUserQuestion
---

# One book. Both layers. Loop until a critic says it matches.

**Read `.claude/postprocess/GAUNTLET.md` first and follow it.** This command runs
as a gauntlet loop: the bar is the book itself, a separate critic with fresh
context judges blind, and the exit is that critic saying yes — never a round
count.

## DIRECTION — restate this verbatim at the start of every phase

> **We are taking ONE book across BOTH layers until a separate critic agrees
> the stored structure is the book's structure and the stored entities are its
> entities. We are not processing a corpus. We are not fixing unrelated things
> we notice on the way. When the critic says yes — or the loop runs out of ideas
> — we STOP and report.**

This block exists because the failure mode of this task is drift, not error.
Previous runs wandered from the book into CI, into queue config, into ingestion
performance — all real problems, none of them the direction. If you notice
something unrelated and genuinely broken, **write it to
`.claude/postprocess/side_findings.txt` and keep going**. Do not chase it. Do not
open a second front. The user has stated this is the single biggest problem in
working with the agent.

If the user's reply is short ("da", "može", "next") it means *continue this
book*, never *start a new topic*.

## TALK PLAINLY — no pipeline jargon to the user

Everything you say to the user is plain Croatian aimed at someone who does NOT
read our code, logs, or database. Describe what is actually wrong in everyday
words: *"the scan is mostly an old bookseller's advert list, not the actual
book"* — never *"72% catalog chunks filed under chapter_number=1"*. BANNED in
anything the user reads (chat + AskUserQuestion options): chunk, tier, entity,
MENTIONS / CO_OCCURS / SHARED_ENTITY / node, character offsets, `file:line`,
table or column names, severity codes. Those belong in the report file and the
ledger row, NEVER in chat. A choice the user cannot make without first decoding
jargon is a broken choice — this has been raised repeatedly and outranks being
concise. (`feedback_plain_language_first`, `no_shorthand_codes`.)

## Why this exists (read before changing anything)

The `scrapalot:postprocess-parse` and `scrapalot:postprocess-graph` **agents**
(`.claude/agents/`, invoked through the Agent tool — `/scrapalot:postprocess-parse`
is the thin per-book slash wrapper around the first one; the graph agent has no
wrapper) split the audit in two. That split is wrong for diagnosis, because
**the graph is built from parse output**: bad chapter detection, stale chunks,
duplicated blocks or wrong `documents.content` all surface later as missing
entities, thin MENTIONS density or a broken hierarchy. Diagnosing the graph
while forbidden to look at parse means reading the symptom with the cause out of
frame.

The two sibling commands remain valid for their own narrow jobs. This one is for
**discovery**: one book, both layers, one report, root cause allowed to cross the
boundary.

## The standing goal — read it before Phase 0

`${CLAUDE_PROJECT_DIR}/.claude/postprocess/GOAL.md` holds the mandate this
command serves: every book stored the way the book actually is, ready for a
graph. Read it every run — it is the file the owner edits to change what "done"
means, and it carries the five conditions a book must meet, the guardrails that
outrank the goal, and the standing open questions so you stop re-deriving them.

Under `/loop`, that file is the loop's objective. **One book per tick, always** —
the loop's job is to keep starting this command, not to make it audit more books
per run. A defect found in one book is measured corpus-wide and fixed at source;
it never becomes a sweep.

## Phase 0 — resolve exactly ONE book, and SHOW the choice

Accept `$ARGUMENTS` as a document id, a title fragment, or a collection name.

- If it identifies exactly one book → use it, print id + title + collection.
- If it is ambiguous → list at most 8 candidates and ask which one. Do not guess.
  Ask under the ten-minute rule below; the announced default is the first
  candidate alphabetically.
- If empty → **pick the alphabetically-first tier-2 book not yet audited**
  (order: `collection_name`, then `title`), announce which one, and PROCEED. Do
  not propose-and-ask, do not offer a menu — the owner asked for straight
  alphabetical order. The anti-drift guarantee is that this command audits ONE
  book and STOPS; it is not the per-book stop that alphabetical selection would
  violate. Skip a book only if it is already in `progress.txt` as audited.

Print the resolved book. Everything downstream refers to this one book.

## Phase 0.5 — open the gate ledger, BEFORE the first fix

**Read `.claude/gates/CONTRACT.md` and follow it.** The gauntlet decides who
judges; the ledger decides what a judgement may rest on. A run without a ledger
reports itself done, which is the failure both files exist to kill.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py open \
    --run book-<short-doc-id> --command /scrapalot:book \
    --scope "<title> — parse + graph, until a critic says the stored structure is the book's"
```

Starter gates for this command. Adapt the wording and the `CHECK:` lines to the
book you actually resolved; do not ship them with the placeholders in place.

```markdown
- [ ] G1: the book's own printed structure is extracted and written down (the bar)
  EVIDENCE: pending
- [ ] G2: the content is coherent knowledge, not watermark / catalogue / OCR sludge
  EVIDENCE: pending
- [ ] G3: a critic with fresh context, given both chapter lists unlabelled, says they are the same book
  EVIDENCE: pending
- [ ] G4: every chunk is reachable Book → Chapter → Section → Chunk (traversal filtered on the Book)
  EVIDENCE: pending
- [ ] G5: the stored entity names were read one by one and are things, not sentences, mottos or OCR noise
  EVIDENCE: pending
- [ ] G6: every source fix in this run carries a corpus regression scan in BOTH directions
  EVIDENCE: pending
- [ ] G7: the ledger row for this book is in progress.txt
  CHECK: grep -c "<document_id>" ${CLAUDE_PROJECT_DIR}/.claude/postprocess/progress.txt
  EXPECT: /[1-9]/
  EVIDENCE: pending
```

G1–G6 are manual because no command can settle them — which means `EVIDENCE:`
must carry the proof itself: the extracted heading list, the quote that decided
"sludge", the critic's verdict sentence, the traversal counts, the scan's
improve/degrade numbers. A gate whose evidence still reads `pending` is unmet
however the box looks.

If the collection resolves to tier 0/1, the graph half does not run: that is
`ABANDON: G4 tier 0 — no full graph is built for this collection` plus the same
for G5, stated in the report. Abandoning is honest. Deleting the gate is not.

## Phase 1 — preconditions, reported not enforced

Check and **report** each. A failed precondition is a FINDING about this book,
not a reason to move to a different book.

| Check | Where | If it fails |
|---|---|---|
| effective `graph_tier` | `resolve_graph_tier()`, `collection_workspace_cache.py:135` | **STOP the graph half and say so.** Tier 0/1 builds no full graph. Name the collection and its tier, offer to set it. |
| `documents.content` non-empty | pgvector | parse-layer finding |
| chunks exist in `langchain_pg_embedding` | pgvector | parse-layer finding |
| `graph_sync_status` row | pgvector | records whether the graph was ever attempted |
| Neo4j reachable, heap value | `NEO4J_server_memory_heap_max__size` | record it; production is **768M** |

**Measured 2026-07-20, so you know what "normal" looks like here:** 3 of 176
collections have explicit tier 2; 63 are NULL with no parent and therefore
resolve to tier 0 (no graph); 107 are NULL inheriting up a chain that almost
certainly ends NULL. 297 of 5724 documents have entities. If the book you were
handed is tier 0, that is not an accident to skip past — it is very likely THE
finding, and the user needs to decide whether that collection should build a
graph at all.

## Phase 2 — parse layer (structural), on THIS book

Delegate to `scrapalot:postprocess-parse` (agent) scoped to this document_id.
That agent is 68 KB of hard-won forensics — do NOT reimplement or thin it out.
Its Phase 2 runs seven sub-audits: content fidelity, chapter detection,
source-code path forensics, metadata-stub detection, `document_hierarchy`
integrity, status/chunk consistency, Cat-I eligibility.

Bring back a per-defect list AND, for each defect, whether it could damage the
graph downstream. Record that judgement explicitly even when the answer is "no" —
Phase 3's gate reads it.

## Phase 2.5 — reasoning audit: does the content actually MEAN anything?

The structural audit proves the chunks MATCH `documents.content`. It does NOT
prove the content is worth anything. A book passes every structural check while
its text is watermark noise, OCR sludge, duplicated boilerplate, or simply the
wrong book. No previous tool covered this — it is the whole reason a MODEL runs
this audit instead of a script (`feedback_reasoning_audit_of_content`).

READ the real thing, not the numbers:
- a representative sample of chunks — start, middle, AND end, never just the first
- the head and a mid-section of `documents.content`
- the detected chapter titles as a plain list

Then JUDGE, in sentences, with a quote as evidence:
- Is this coherent knowledge, or noise / boilerplate / repetition?
- Do the chapter titles reflect what the text is actually about?
- Would the entities the graph is about to extract be real, given what you read?
- Is this even the book the metadata claims (title vs content)?

Emit a one-word verdict — **content-sound** or **content-suspect** — plus the
quote that decided it. THIS verdict, not the structural pass, gates the graph.

## Phase 2.6 — bad scan? find a cleaner copy BEFORE you patch (OCR rule — ALWAYS)

When Phase 2.5 returns **content-suspect** because of *scan / OCR quality* —
garbled or unreadable letters (a decorative or old font the extractor could not
read), watermark-only text, an appended bookseller's catalog / advertising pages /
library due-date card, duplicated boilerplate, or plainly the wrong scan — the
first move is **NOT** to truncate or hand-edit the bad copy. Most of this corpus
is old, public-domain material, so a cleaner copy of the same work almost always
exists online (archive.org, Google Books, HathiTrust, Wikisource, Project
Gutenberg, sacred-texts, specialist libraries).

So **dispatch a web search for a cleaner version of the SAME work** (match on
title + author + edition/year). Delegate to an agent that has web tools; have it
report the candidate sources, each one's format (full plain text / clean PDF /
scanned-only) and how clean it looks — but **do NOT download or re-ingest yet**.
Then present the found options to the user in plain language and let them decide
whether to replace this book's text with a cleaner copy. Ask under the
ten-minute rule below — but if the stored text is the only copy of this book
left, that is one of the cases where you stop and wait instead.

This rule **ALWAYS applies** to OCR / dirty-scan cases. Truncation or manual
content edits are the fallback only when no cleaner copy can be found. Re-ingesting
a cleaner copy is destructive (it replaces the stored text and re-runs processing)
— it is an approval-gated fix, never auto-applied. Record in the report which
cleaner source was chosen (or that none was found) so the next run has the trail.

## Phase 3 — graph layer, on THE SAME book — GATED ON PARSE

Build or audit the graph ONLY when BOTH hold:
1. Phase 1 resolved effective tier 2, AND
2. Phase 2.5 returned **content-sound** AND Phase 2 flagged no defect marked
   "would damage the graph".

If either fails: **STOP. Do not touch the graph.** Building a graph on bad parse
is exactly how the corpus got 1.2M null-weight edges and watermark entities.
Report the parse problem as the finding, recommend the parse fix, and leave the
graph until the book is re-parsed clean. **This gate is the entire reason the two
layers live in one command** — a graph audit that cannot see the parse cause is
reading a symptom with the cause out of frame.

When the gate passes, delegate to `scrapalot:postprocess-graph` (agent) for this
document_id: hierarchy reachability, MENTIONS count and density, chunk-level
REFERENCES, CO_OCCURS weights, SHARED_ENTITY, NEXT chains, communities, orphans.
**Do not let it pick its own book.** It is scoped to the book from Phase 0.

## Phase 3.5 — entity-name SANITY (mandatory) — garbage means a SOURCE-CODE bug

Density is not quality. A book can have the "right" MENTIONS count and still be
full of nonsense entity names. **Always** read the actual entity names, do not
just count them:

```cypher
MATCH (b:Book {document_id: $did})-[:MENTIONS]->(e:Entity)
RETURN e.name AS name, e.source AS source, e.entity_type AS type
ORDER BY e.name
```

Judge each name by reasoning, not a metric. Flag as garbage anything that is:
- a **sentence, clause, quotation, or verse line** ("Follow me, but look not to the right…") — quotations are NOT entities (QUOTE was removed as an extraction type on 2026-07-22),
- a **foreign-language phrase / motto** ("ut bos locutus est", "populo barbaro"),
- **OCR noise** — spaced single letters ("R T N T"), symbol runs ("ALGAR + ALGASTNA + + +"), garbled/misspelled words ("Librkry Madison Av", "modo Bacchl").

**When you find garbage, it is a defect in the EXTRACTION SOURCE CODE, never a
data blemish to patch away.** Fixing the graph rows leaves the bug live for the
next 5000 books. Trace it to source and propose the code fix:
- LLM path — the extraction prompt (`configs/prompts.yaml` → `entity_extraction.extraction_prompt`, the "What to NEVER Extract" list) and the name gate `is_valid_llm_entity_name` (`src/main/utils/documents/utils.py`).
- spaCy path — `create_spacy_entity` / `SpacyExtractor._is_valid_entity` (`src/main/service/graph/entity_extraction/spacy_extractor.py`).
- The Redis `entity_cache:*` (`entity_pipeline.py`) serves cached extractions for 2h — a re-extraction after a prompt/gate change is a NO-OP until that cache is cleared. Say so; clear it before re-extracting.

Report the garbage as a finding with its source cause and the smallest code fix.
A source-code change is approval-gated (see Fixes below) — propose, do not auto-apply.

## Phase 4 — fuse, and look for the causal link

For every graph defect, ask the question the split tooling could not:

> Is this caused by something Phase 2 already found in the parse layer?

Examples of the shape: thin MENTIONS because chunks are duplicated boilerplate;
missing Chapter nodes because chapter detection produced one giant section;
entities extracted from a watermark because `documents.content` is watermark
text. Write the chain out — parse defect → graph symptom — or state plainly that
the graph defect stands on its own.

## Phase 4.5 — the loop (this is what makes it a gauntlet)

Diagnosing is half the job. Now fix and re-judge until a critic agrees.

**Two bars, one per layer:**

- *parse* — the book's own printed structure: its table of contents and the
  chapter headings in its body, extracted from `documents.content` before any
  fixing starts. Write that list down; it does not change between rounds.
- *graph* — the entity names actually in the text. A `:Entity` that is a
  sentence, a verse line, a foreign motto, or OCR sludge is not an entity, and
  no density number redeems it (Phase 3.5).

**Each round:** builder fixes → a **separate critic agent, fresh context**,
judges. Give the critic the two structures — the book's and the stored one —
**unlabelled where the comparison allows**, plus, for a source fix, the **raw**
regression scan rather than the builder's summary of it. Its question is binary:
*do these describe the same book — yes or no, and if no, the single biggest
difference.* "Mostly" is a no. Never a score.

If no: the critic's one sentence goes back to the builder. Repeat.

**The exit is the critic saying yes, or the owner stopping.** Never a round
count. If two different fixes hit the same gap, stop and report it as needing an
idea we do not have, naming what was tried — that is a result. `2cdd2f36`'s
missing chapters 7 and 10 are the standing example.

**What the loop may do alone:** source fixes on a branch, scans, tests, PRs,
re-running the critic, and **merging its own PR** under the five conditions in
"Merging" below. **What it must ask for:** any reprocess, any content edit, any
Neo4j write — asked under the ten-minute rule below, which says how to ask and
when a question may answer itself. A gauntlet that reprocesses a book
forty times to win its own comparison has burned the book.

## Phase 5 — report and STOP

**No report until the gate ledger is full.** Run it, then close it:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py close gates/active/book-<short-doc-id>.md
```

`close` refuses while a gate is open, and the Stop hook will not let the turn end
either. If you are composing this report with boxes still unchecked, that is the
finishing reflex firing — open the ledger and pick the next unmet gate. Every
`ABANDON:` line goes into the report in plain Croatian, as a thing this run did
not settle.

- One report: `.claude/postprocess/reports/<did[:8]>__book.md`
- One ledger row appended to `.claude/postprocess/progress.txt`
- The gate summary (`N/M met`, re-measured, never recalled) in the report file
- In chat: the short summary only — findings, causal chains, and the single
  recommended next action.

Then stop. Do not offer to run the next book unprompted. Do not start fixing
systemic issues discovered along the way. The user decides what happens next.

## Merging — yours to do, under five conditions

Set by the owner on 2026-08-31, replacing the older "never merge, the owner
merges": *"i sam mergeaš pr-ove kad ih auto review pregleda, max 5 rundi, kad se
poprave critical i major bugovi."*

Merge the PR yourself when **all five** hold:

1. **The auto-review bot has actually reviewed it.** Not "CI passed" — the review
   job has run and left its findings. A PR nobody reviewed is not ready because
   it merges on one pair of eyes, and the whole point of the review is that they
   are not yours. The bot cannot see CI status and will ask you to confirm it;
   confirm it explicitly.
2. **Every critical and major finding is fixed.** Minor remarks, nits and
   suggestions may stay open — say in the PR which ones you left and why.
3. **CI is green** on the commit you are merging, including any commit the bot
   pushed into your branch. Merging red CI is not a judgement call.
4. **It took at most 5 review→fix rounds.** A fifth round that still has a
   critical or major finding open is the signal to **stop and hand it over** —
   five rounds without convergence means the disagreement is about something the
   loop is not settling, and merging anyway would be the loop overruling a
   reviewer by exhaustion.
5. **No other book is made worse.** The owner's words, 2026-08-31: *"svaka
   promjena ne smije donjeti regresiju na ostale knjige."* This is not "the
   average improved" and not "net positive" — it is **zero books degraded**, and
   you only know it by scanning the corpus in both directions and reading the
   degraded cases one by one. A change that fixes the book in front of you and
   costs one other book is refused, not traded off. The corpus already paid for
   this rule twice in one day: a filter whose first version deleted a printed
   copyright footer from 525 pages, and the review's own widening of it, which
   started eating a colophon, an index entry and the phrase "running headlong
   into vice". Both were caught only because the scan was re-run and the removals
   were read, not summarised.

Say in the report which round it merged on. The bot pushes commits into your
branch — keep them and correct on top, never force-overwrite; re-run the corpus
scan after its changes, because a widened pattern can silently start eating real
text (that happened on #326, where the review's correct fix opened a second hole
the scan caught).

## Fixes — what may be applied without asking

Auto-apply only pure-additive, single-book, reversible changes:
- Neo4j property backfill where the property is NULL (never overwrite)
- Missing `Chapter-[:NEXT]->Chapter` links via `node_factory._link_chapters_sequentially`

Everything else asks first, one question at a time, in plain language describing
the CONSEQUENCE rather than the category name:
- **replacing this book's text with a cleaner copy found online** (Phase 2.6 OCR
  rule — the PREFERRED remedy when the content is content-suspect from a bad
  scan; destructive: replaces `documents.content` and re-runs processing)
- reprocessing this document (destructive: wipes chunks + Neo4j subtree, re-runs
  extraction, shares the `documents` Celery queue)
- truncating / hand-editing `documents.content` (fallback only when no cleaner
  copy exists — never the first move for an OCR/dirty scan)
- any workspace-wide housekeeping dispatch
- any source-code change

**Never** run `MATCH … DETACH DELETE` outside an orchestrated reprocess. **Never**
run a mass operation across books. One book is the entire scope.

## Asking — the ten-minute rule

A question that blocks forever is how this command stalls overnight. So every
question it asks carries its own answer if none arrives.

**The default IS your recommendation.** Not the safest option, not the smallest
one — the thing you would do if the decision were yours. Say which it is and why
in one sentence, then take it when the clock runs out. The owner asked for this
in those words on 2026-08-27: *"ako ti ne odgovorim 10 min, ideš po svojoj
preporuci."* A default you would not recommend is not a default, it is a stall
wearing a timer.

**TEST YOUR CLAIM BEFORE THE CLOCK CAN DECIDE IT.** Added 2026-08-31 on the
owner's instruction: *"ti odlučuješ šta je najbolje ali tek nakon što testiraš
svoju tvrdnju."* Every recommendation rests on a factual claim — *this fix helps
more books than it hurts*, *this book's structure is wrong*, *this is the only
copy left*. **You may not start the clock until that claim has been MEASURED**,
and the measurement goes in the question you post, so the owner is deciding
against evidence rather than against your confidence.

What counts as having tested it:

- a **corpus scan in both directions** for anything that changes stored text or
  structure — how many documents improve, how many degrade, and the single worst
  case, with the degraded ones read one by one, not summarised;
- the **new test run against the pre-fix code** for a source fix, so you know it
  guards something (a test that passes against the broken build guards nothing);
- for "no better copy exists", the **search actually run** and its result named,
  not an assumption about what is on archive.org;
- for "this is a defect", the **number of documents it affects**, split by the
  dimension that could make it a false positive — file type, language, whether
  the book really does print that heading.

If the claim cannot be measured in the time you have, that is not a licence to
start the clock anyway. **Say what you could not measure and wait.** An untested
default carried out by a timer is the failure this whole file exists to prevent,
and a timer makes it worse than a wrong answer given in person: nobody was there
to catch it.

Three things measured on 2026-08-31 that would each have shipped as a confident,
untested recommendation:

| the claim | what measuring it did |
|---|---|
| "this filter removes the model's commentary" | its first version deleted a printed copyright footer from **525** pages across 3 books |
| "over-fragmented chapters mark a defect" | its top entries were devotionals with 365 genuine one-chunk sections — the metric was discarded |
| "every chunk on page 0 is a defect" | **2,459 of 3,973** were markdown, which has no pages; 62% of the number was not a defect |

State in the report, and in the gate ledger's `EVIDENCE:` line, WHICH measurement
backed a self-chosen default. "I judged it best" is not evidence; a number is.

**Inside a `/loop` shift the loop's own wakeup IS the clock.** Do not add a
separate `sleep` — ask, then arm `ScheduleWakeup` for 600 s with the loop's
prompt. The next tick either finds an answer or carries out the recommendation.
Never let a question cost the shift more than one tick.

**How to ask.** Do NOT use `AskUserQuestion` for these — it blocks the turn and
there is no way to time it out. Instead:

1. Write the question in chat as an ordinary message, in plain Croatian, with
   the options.
2. **Say which option you will take if nobody answers, before you start the
   clock, and show the measurement behind it.** The owner must never be
   surprised by what happened while they were away, and must never have to take
   your word for why.
3. Start the clock in the same turn and end the turn:
   ```
   Bash(command="sleep 600", run_in_background=true, description="ten-minute answer window")
   ```
4. The owner replying first wins — follow their answer and let the timer die.
5. The timer firing first means proceed with the option you announced. Say so in
   the next message: *"nije bilo odgovora 10 minuta, idem s <opcijom>"*, and put
   the same sentence in the report and in the gate ledger's `EVIDENCE:` line, so
   the record shows a self-chosen answer and not an approved one. Name the
   measurement in the same breath — *"idem s X; mjerenje koje to nosi je Y"* —
   because a self-chosen answer is the one nobody checked.

**When NOT to start the clock — stop and wait instead.** Use `AskUserQuestion`
and block, with no timer, when:

- **no option is clearly better** — the alternatives are genuinely tied on the
  evidence you have, so a self-chosen answer would be a coin flip dressed as a
  decision;
- **every option destroys something that cannot be rebuilt** — the original file
  is gone, the stored text is the only copy, the reprocess cannot be undone from
  anything on disk;
- **the question is about what the owner wants**, not about what is true —
  priorities, scope, whether a book is worth the effort. There is no best answer
  to find, only theirs.

Saying "nemam dobru opciju, čekam te" is a legitimate outcome and is worth more
than a confident wrong pick.

**The clock does not upgrade a `Never`.** Everything above marked **Never** stays
never, no matter how long the silence. The timeout picks among the options you
were allowed to offer, it does not widen them.

## Environment facts that were wrong in the sibling commands until 2026-07-20

Keep these correct; each one silently broke a check.

- **Flower does not exist** (removed). Celery state:
  `docker exec scrapalot-workers supervisorctl status`; worker logs live in
  `/app/data/logs/celery_worker_*.log`, NOT on container stdout.
- Celery task sources are in `scrapalot-chat/src/main/workers/tasks/`, not
  `src/main/celery_app/tasks/`.
- Neo4j heap is **768M**. A gate demanding ≥1024M blocks every housekeeping
  dispatch forever, including the co-occurrence weight recompute.
- Graph housekeeping runs on **`scrapalot-workers-graph`** (`graph_extraction`
  queue), a different container from `scrapalot-workers`.
- Deep research now has its own `research` queue (2026-07-20), so a long research
  run no longer blocks the `documents` queue a reprocess needs.
- `GRAPH_HOUSEKEEPING_PAUSED=true` is set deliberately in the CI `.env` template
  (`deploy-backend.yml`). 14 graph beat jobs are paused on purpose. If a fix
  depends on one of them, say so — do not assume it will run.

## Known state as of 2026-07-20 — verify before trusting

- 1.237.320 CO_OCCURS_WITH edges, **100% with NULL weight**. The job that fixes
  this (`recompute_cooccurrence_weights`) is one of the paused ones.
- 308.498 entities, 0 duplicate canonical keys, 2.353 orphans (0.8%), all with
  complete properties. The graph is **incomplete, not corrupt** — do not propose
  wiping it as a first move.
- 297 books have entities; 1.278 Book nodes have none; 4.310 documents sit at
  `graph_sync_status = 'pending'` since 2026-06-11.
