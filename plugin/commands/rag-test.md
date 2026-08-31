---
description: "Drive ONE long chat session against a real book and grade every RAG answer (citations, search strategy, documents/web/llm routing, chat memory, source hallucination, graph, document_hierarchy). Two RAG-agent modes: auto (the agent routes itself) and manual (strategy pinned). Takes a free-text focus instruction. Halt on streamingError → fix root cause → push → resume in the same session until clean. tune = calibrate prompts.yaml against real user sessions."
argument-hint: "[auto|manual] [tune] [focus=<what to focus on>] [collection=<hint>] [questions=N]"
allowed-tools: Agent, Bash, Read, Edit, Grep, Glob, Write, AskUserQuestion
---

# /scrapalot:rag-test `[auto|manual]` `[tune]` `[focus=<what to focus on>]` `[collection=<hint>]` `[questions=N]` `[max_ticks=N]`

You are the **orchestrator** of the RAG quality test loop. ONE invocation drives
one batch of questions inside ONE persistent chat session against ONE real book,
grades each answer, and — when something breaks — STOPS, fixes the root cause,
and resumes the SAME session. Designed to be run repeatedly under `/loop` until
the whole session is clean.

Loop home: `${CLAUDE_PROJECT_DIR}/.claude/rag-test/` — `GOAL.md` (mandate + rubric),
`STATE.md` (progress + active session), `scripts/rag_chat_driver.py` (the
harness that logs in as admin, drives `chat/completions` over SSE, and emits a
verdict), `runs/` (raw packet logs), `corpus/` (the calibration question set +
scoreboard), `prompt_backups/` (one snapshot per prompt edit).

The driver is the ONLY way to touch the chat or the prompts — never hand-roll
curl/SSE, never hand-edit `configs/prompts.yaml`:
```
cd ${CLAUDE_PLUGIN_ROOT}/scripts/rag-test
python3 rag_chat_driver.py pick-book --workspace <wsid> [--collection <hint>]
python3 rag_chat_driver.py create-session --collection <cid> --name "rag-test"
python3 rag_chat_driver.py ask --session <sid> --question "<q>" [--mode auto|manual] \
        --workspace <wsid> --collection <cid> [--document <did>]
# --mode auto   → sent to the API as `agentic` (the RAG agent routes itself)
# --mode manual → no mode sent at all, so the strategy pinned in user_settings runs
#                 (identical to omitting --mode; `agentic` is still accepted as an alias of auto)
python3 rag_chat_driver.py analyze --session <sid>
python3 rag_chat_driver.py del-message --message <mid>
# prompt-calibration verbs (the `tune` activity):
python3 rag_chat_driver.py harvest-sessions [--user <u>] [--days N]
python3 rag_chat_driver.py prompt-get --key rag_agent.system_prompt
python3 rag_chat_driver.py prompt-set --key <k> --file <new.txt> --note "<why>"
python3 rag_chat_driver.py prompt-reload [--off]
python3 rag_chat_driver.py busy-check
```

## Arguments

Invoked with: `$ARGUMENTS` — order-independent, all optional. Two axes plus a
free-text focus:

| Placeholder | Values | Meaning |
|---|---|---|
| `[auto\|manual]` | `auto` (alias `agentic`) · `manual` | **Which RAG agent answers.** Omitted → both (see Modes below). |
| `[tune]` | `tune` · `test` | **What we do with the answers.** `tune` = calibrate `configs/prompts.yaml` (Step 3T). `test` = ask + grade only, never edit a prompt. Omitted → `tune` when no mode is named, `test` when one is. |
| `[focus=<...>]` | free text | **What to focus on this run** — steers question planning, technique selection, grading emphasis and defect ranking. See Focus below. |
| `[collection=<hint>]` | e.g. `collection=spirituality` | Narrows book pickup to a matching collection. |
| `[questions=N]` | int, default 20 | Sizes the `tune` corpus (half `auto` rows / half `manual` rows) and caps questions in `auto` mode. Ignored in `manual` mode — coverage is driven by the technique catalogue, not a count. |
| `[max_ticks=N]` | int, default 20 | Caps the `tune` loop across `/loop` ticks. |
| `[new-corpus]` | flag | Archive the frozen `tune` corpus to `corpus/archive/<UTC-ts>/` and build a fresh one (normally FORBIDDEN — only when the focus genuinely needs different questions). |
| `[help]` | flag | Print this table and STOP. |

Leading dashes are accepted everywhere (`--auto` == `auto`, `--tune` == `tune`),
so old muscle memory (`--agentic`, `--manual`, `--tune`) still works.

**Resolve `$ARGUMENTS` first, before anything else:**
1. `$ARGUMENTS` is exactly `help` or `?` → print the table above and STOP (do
   nothing else). A `?` inside a longer sentence is focus prose, not a help
   request — "why does it hedge?" is an instruction.
2. Strip leading `--` from every token, then classify case-insensitively:
   - `auto` / `agentic` / `manual` → **mode**
   - `tune` / `test` → **activity**
   - `new-corpus` → **corpus reset flag**
   - `collection=` / `questions=` / `max_ticks=` / `focus=` → **named value**
     (`focus:` and `focus="…"` are the same thing; strip surrounding quotes, and
     take everything after `focus=` — including spaces — as one instruction)
   - anything else that is plain prose → appended to the **focus** text
   - anything else shaped like a flag (`--xyz`) or `unknownkey=value` → STOP,
     name the token, print the table. A typo must never be silently swallowed as
     focus text.
3. Two modes named at once → STOP and ask which one (never run both silently).
4. Apply defaults: no mode + no activity → `tune` over BOTH modes (the historic
   default, what `/loop /scrapalot:rag-test` has always run). Mode named without
   activity → `test` in that mode. `tune` + a mode → calibrate using only that
   mode's corpus rows.
5. Echo the resolved run header before Step 0, so the run is self-describing:
   `mode=<auto|manual|both> activity=<tune|test> focus="<…|none>" collection=<…|auto> questions=<N> max_ticks=<N>`

Examples:
- `/scrapalot:rag-test` — default: prompt calibration over both RAG agents.
- `/scrapalot:rag-test auto` — ask + grade with the self-routing agent, no prompt edits.
- `/scrapalot:rag-test manual` — technique-coverage sweep over the pinned strategies.
- `/scrapalot:rag-test auto focus="citations — every claim must carry a source"` — one mode, one focus.
- `/scrapalot:rag-test manual focus=graph` — sweep only the graph/entity techniques.
- `/scrapalot:rag-test tune auto focus="answers in Croatian must stay Croatian"` — calibrate only the self-routing rows against that failure.
- `/scrapalot:rag-test collection=spirituality questions=12 max_ticks=10` — default calibration, narrower book pool and caps.
- `/scrapalot:rag-test check the book chat is not padding answers` — bare prose → focus.

## The two RAG-agent modes

The product answers a question through one of two engines, and they fail in
different ways, so the loop names them explicitly:

- **`auto`** (agentic routing — driver `--mode auto`, sent to the API as
  `agentic`). The RAG agent decides for itself which strategy to run and whether
  to answer from `documents`, `web` or `llm`. We grade **whether it chose right**.
  Caveat that makes the second mode necessary: here the named strategy is only a
  routing *intent* — the strategy's `execute()` is NOT invoked (see
  `dto/streaming.py`, `strategy_transparency` note) — so `auto` can never prove a
  technique actually works.
- **`manual`** (Engine A — `use_agentic_routing=false`, strategy pinned in
  `user_settings`; driver gets NO `--mode`). This is the only surface where a
  named strategy genuinely executes, so **RAG-technique COVERAGE lives here**: one
  distinct question per technique across the whole catalogue (Step 3M), each
  read back to confirm the intended technique ACTUALLY ran. Source routing is
  fixed to the book; still grade citations, memory, hallucination, graph and
  hierarchy per technique.

`tune` (the default activity) deliberately spans **both** modes — half the corpus
`auto` rows, half `manual` rows — because a prompt edit that helps one engine
very easily breaks the other. Naming a mode with `tune` narrows the corpus rows
worked on, but **never** narrows the regression check of Step T6.

## Focus — steering the run

`focus=<free text>` is the user telling you what this run is about ("citations",
"graph answers", "Croatian replies", "answers to short vague questions",
"the anthropology books"). It is an instruction, not a keyword filter — read it
the way a colleague would and judge what it implies
(never keyword-match it against strategy names or prompt text).

Where focus bites:
1. **Question planning** (Step 3A / corpus build in Step 3T-T2) — write the
   questions so they exercise the focus area against real passages. A focus on
   citations means questions whose answers must cite; a focus on memory means
   more follow-ups that restate nothing.
2. **Technique selection** (Step 3M, `manual`) — restrict the catalogue sweep to
   the techniques the focus implicates, via
   `manual_coverage_sweep.py --only <substring,substring>` (e.g. focus "graph"
   → `--only graph,entity`). Report the subset explicitly: `n/N techniques (focus: …)`.
   Never silently drop techniques — an unreported subset reads as full coverage.
3. **Grading emphasis** (Step 4) — grade the focus dimensions strictly and lead
   the report with them. **Still grade every other dimension** — a focused run
   must not hide a regression it happened to walk past.
4. **Defect ranking** (Step 3T-T3) — among defects at or below baseline, pick the
   focus-related one first. If nothing focus-related is failing, say so and fix
   the worst remaining defect anyway rather than idling.
5. **Book / collection pickup** — if the focus names a subject or a book, treat
   it as a `collection=` hint when no explicit hint was given.

Hard limits on focus (these outrank the focus itself):
- Focus **never** narrows the no-regression re-measurement (Step T6): the WHOLE
  frozen corpus is re-graded against `baseline.json` on every accepted edit,
  focused or not.
- Focus **never** regenerates or rewords a frozen corpus. A new focus on an
  existing run re-prioritises the same questions; if the focus genuinely needs a
  different question set, the user must pass `new-corpus` (archive + rebuild) —
  and the report must state that the baseline was reset.
- Focus **never** licenses a prompt edit that encodes the focus subject itself
  (Step T5 stays principle-level: no drug, horse, book, language or word from the
  failing case in a prompt).
- Record `focus` (and, when set, `focus_started_tick`) in STATE.md so `/loop`
  ticks inherit it. If a tick arrives with a different focus, keep the corpus,
  switch the ranking, and note both in the ledger.

### Which prompts.yaml (this trips people up)
`scrapalot-backend/src/main/resources/prompts.yaml` does **NOT** touch RAG. It
feeds Spring AI only — describe/suggest/summarize (`AiGenerationController`),
notes translate (`NotesAssistantController`), collection descriptions
(`CollectionController`), research templates (`ResearchController`). RAG chat
goes `ChatService.routeToGrpc()` → Python. **The RAG prompts are
`scrapalot-chat/configs/prompts.yaml`** (~4.7k lines, 44 sections). Tune that.
The Kotlin file has its own lane (Step 3K) because each edit needs a CI deploy.

### Why an earlier `manual` run kept showing RAGDecomposition
The first manual pass built 6 questions by *rubric dimension* (factoid, comparison,
…) and let the ROUTER pick the strategy. The router converges — several distinct
question shapes all routed to `RAGDecomposition`, so the run re-tested one technique
and never touched ~25 others. A dimension plan does NOT cover the engine. Step 3M
fixes this: iterate the technique CATALOGUE, pin/assert each technique, and ledger
coverage so no technique repeats until all are covered.

## Step 0 — orient & resume
- Read `rag-test/GOAL.md` (rubric + halting + fix policy) and `rag-test/STATE.md`.
- If `STATE.md` has an `active_session_id` AND `mode` matches the requested mode,
  **resume that session** — do NOT create a new one. Continue the question
  ledger where it left off (skip questions already marked `pass`). A different
  mode (`auto` ↔ `manual`) means a different engine and a different session —
  open a new one rather than mixing engines in one history.
- If STATE carries a `focus` and this invocation passed none, **inherit it** (a
  `/loop` tick must not silently lose the user's instruction). A new focus
  replaces it: record both, and never let the switch touch the frozen corpus.
- A pass that adds no new failures and leaves the session clean is a SUCCESS.
- **`tune` (default activity) resume contract:** read `corpus/questions.json`,
  `corpus/baseline.json`, `corpus/scoreboard.json` first.
  - `questions.json` missing → this is tick 1: generate + freeze the corpus (T2),
    then capture the baseline (T2b) before editing anything.
  - `questions.json` present and `frozen` → **reuse it verbatim**; verify
    `corpus_sha256` still matches and STOP if it moved. Never regenerate, never
    append, never reword. Same questions every tick is what makes iteration N
    comparable to iteration N+5 and any fix verifiable later. This holds even
    when the focus changed — the ONLY exception is an explicit `new-corpus`
    argument, which archives `corpus/` to `corpus/archive/<UTC-ts>/`, rebuilds
    (T2) and re-baselines (T2b) before any edit, and must be stated in the report.
  - `scoreboard.tick >= max_ticks` → the run is over; report and stop.

## Step 0.5 — open the gate ledger
**Read `.claude/gates/CONTRACT.md` and follow it.** This command's whole output
is a claim about quality, graded by the same system that produced it. The ledger
is where "every planned question passes" stops being a sentence in a report and
becomes something a command can settle.

One ledger per run (a `/loop` tick resumes the ledger it finds, exactly as it
resumes the session — do not open a second one):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py open \
    --run ragtest-<mode>-<activity> --command /scrapalot:rag-test \
    --scope "<mode>/<activity> on <book>, focus=<focus or none>, until the session is clean"
```

Then add `RESUMABLE: yes` to its header, immediately. This is the one command
here that is meant to be driven by `/loop`: a tick ends its turn with questions
still open, on purpose, and the next tick continues. The flag stops the Stop hook
from walling that in. It does not soften anything else — `close` still refuses
while a gate is open.

Starter gates — adapt the `CHECK:` lines to the ledger format you are actually
writing into `rag-test/STATE.md`:

```markdown
- [ ] G1: every planned question reached pass — no row left at fail
  CHECK: grep -c '| fail |' ${CLAUDE_PROJECT_DIR}/.claude/rag-test/STATE.md
  EXPECT: /^0$/
  EVIDENCE: pending
- [ ] G2: no streamingError is outstanding — every one caught was root-caused and its fix shipped
  EVIDENCE: pending
- [ ] G3: every pass is backed by the tester's verdict JSON, not by a recollection
  EVIDENCE: pending
- [ ] G4: what the focus left untested is named in the report
  EVIDENCE: pending
```

For the `tune` activity, add the two that outrank everything else in it:

```markdown
- [ ] T1: every corpus row is >= its baseline.json grade on every dimension (no regression on production)
  EVIDENCE: pending
- [ ] T2: the frozen corpus is unchanged — corpus_sha256 still matches
  EVIDENCE: pending
```

A `focus` never shrinks this ledger. It changes what gets attention first; G1
still covers every planned question, and the narrowing goes into G4 where the
report has to state it.

## Step 1 — health
`docker ps` shows `scrapalot-backend`, `scrapalot-chat`, `pgvector` up. The
driver's `login` must return an `access_token` (admin / TEST_PASSWORD). If the
gateway login fails, STOP and report — do not fabricate a token.

## Step 2 — pick the book & open the session (only if not resuming)
1. Admin workspace `books` = `0ebf2e09-7198-4b7a-a100-87b6dc969387` (override via
   STATE if changed). `pick-book` selects the first completed book with ≥8 chunks
   in that workspace (honor `collection=` hint, or the subject the focus names
   when no explicit hint was given).
2. `create-session` (with the book's `collection_id`, name `rag-test-<mode>`).
3. Record `active_session_id`, `mode`, `activity`, `focus`, `book` in STATE.md.

## Step 3A — question plan for `auto` mode (book-grounded, memory-probing)
Build `questions=N` questions ABOUT THE PICKED BOOK that each exercise a
different rubric dimension. They must be DISTINCT (never one question reused) and
ordered so later ones lean on earlier answers (memory test). A good plan:
1. **Factoid** — a specific fact only in this book ("What does the book say
   about X?"). Tests citations + documents routing + hierarchy.
2. **Comparison / multi-aspect** — forces a multi-query strategy
   (`RAGMultiQuery` / decomposition). Tests strategy choice.
3. **Entity / relationship** — "How does <entity A> relate to <entity B> in this
   book?". Tests graph usage (`graph_expansion` / `used_graph_element_ids`).
4. **Section-targeted** — "In the chapter on <topic>, what …?". Tests
   document_hierarchy retrieval.
5. **Memory follow-up** — refers to a previous answer with NO restated context
   ("Expand on the second method you mentioned"). Tests chat memory.
6. **Out-of-scope probe** — asks something NOT in the book. A good system says so
   or routes to `web`/`llm` honestly; a bad one hallucinates citations. Tests
   source hallucination + routing honesty.
Derive concrete entities/topics for (1)(3)(4) from the book: read a few chunks
first — `docker exec pgvector psql -U scrapalot -d scrapalot -c "SELECT left(document,400) FROM langchain_pg_embedding WHERE cmetadata->>'document_id'='<did>' LIMIT 3"`.

**With a focus**, keep all six dimensions but bend each question toward it (a
citations focus → every question demands a sourced claim; a memory focus → more
context-free follow-ups). Never drop a dimension because the focus did not name
it — that is how a regression slips through unseen. If the focus asks for a
question shape none of the six covers, add it as a seventh rather than replacing
one, and say so in the report.

## Step 3M — technique COVERAGE plan for `manual` mode (test all ~29, no repeats)
The mandate (per user): **every individual question must trigger a DIFFERENT
technique so all ~29 are tested.** Do NOT let the router converge — drive the
catalogue. Maintain a COVERAGE LEDGER in STATE.md: one row per technique with
`status` (pending → ran → graded | failed), the question used, the strategy that
ACTUALLY executed, and the quality verdict. A technique is "covered" ONLY when it
actually executed AND produced a gradeable answer. A repeat (technique X runs for a
question meant for Y) is a COVERAGE MISS, not a pass — re-craft sharper or pin.

**Canonical catalogue** (source of truth: `src/main/utils/rag/strategies.py`
`get_rag_strategy_class` + `src/main/service/rag/strategy_presets.py`; verify the
live list with `grep -oE 'RAG[A-Za-z]+' …strategies.py | sort -u` before a run —
do not trust this snapshot if the code changed). Each row = technique → the
question SHAPE that triggers it (from its `prompt_bias`):

| Technique | Question shape that triggers it |
|---|---|
| RAGSimilaritySearch | plain single-fact lookup ("What does the book say about X?") |
| RAGSparseSearch | literal keyword / acronym / exact term ("define the term BTU as used here") |
| RAGRegexGrep | verbatim quote / identifier ("quote the exact sentence about …") |
| RAGHyDE | lay-worded question about a technical topic (vocabulary mismatch) |
| RAGMultiQuery | multi-faceted single question ("benefits AND risks AND uses of X") |
| RAGDecomposition | explicit multi-part question ("what is X, how does it work, and why") |
| RAGStepBack | broad principle then specifics ("what general principle underlies X?") |
| RAGRewriteRetrieveRead | terse/vague query ("X stuff?") |
| RAGGraphSearch | entity relationship ("how is A related to B?") |
| RAGEntityExpanded | shared entity across docs ("what links A across the chapters?") |
| RAGParentDocument | needs surrounding context ("explain the full context around X") |
| RAGSectionExpansion | full verbatim passage ("give the complete passage on X") |
| RAGAgenticContextNavigator | hierarchy navigation ("in the part about X, …") |
| RAGSelfQuery | metadata-filter question ("in chapter 3 specifically, …") |
| RAGHybridSelfQuery | exact code/rare term + filter |
| RAGFusion | broad question needing many angles fused |
| RAGGenerativeFeedbackLoop | iterative follow-up that refines a prior answer |
| RAGQueryChain | causal/trace ("trace how X led to Y led to Z") |
| RAGHybridSummarySearch | overview ("what is this book about?" / summary) |
| RAGTwoPhaseContext | core fact + its surrounding context |
| RAGAgenticExpansion | exploratory ("everything the book covers on X") |
| RAGAdaptiveOrchestrator | mixed complex query |
| RAGKnowledgeIntensiveOrchestrator | complex multi-hop reasoning |
| RAGDocumentHierarchyOrchestrator | structure-based ("walk the book's structure on X") |
| RAGQueryRefinementOrchestrator | ambiguous query needing refinement |
| RAGBalanced / RAGContextEnhanced / RAGFeedbackLoop / RAGPrecision Orchestrator | crafting alone is unreliable → PIN (see below) |

**Mechanism — PIN each technique through the REAL gateway path (deterministic).**
Engine A runs whatever the admin's `settings_general` says, and `agentic_routing.py`
reads that row **straight from the Python `user_settings` table (no cache)**, so a
direct SQL pin takes effect on the very next request. Per technique:
- **Pin** (note: the column is `json`, cast through `jsonb`): for a STRATEGY set
  `use_agentic_routing=false`, `use_orchestrator=false`, `rag_strategy=<T>`; for an
  ORCHESTRATOR (name ends `Orchestrator`) set `use_orchestrator=true`,
  `rag_orchestrator=<T>`.
  ```sql
  UPDATE user_settings SET setting_value = (jsonb_set(jsonb_set(jsonb_set(
    setting_value::jsonb,'{use_agentic_routing}','false'),
    '{use_orchestrator}','<bool>'),'{<rag_strategy|rag_orchestrator>}','"<T>"'))::json
  WHERE user_id='<admin>' AND setting_key='settings_general';
  ```
- **Ask** one catalogue-shaped question through the driver with NO `--mode`
  (settings-driven), scoped to a rich collection (anthropology
  `5eeec701-…`). **Read back** `analyze` → `search_strategy.strategy_name` (or the
  `strategy_selected` packet) and confirm it == `<T>`. Mismatch = coverage miss.
- **Ledger** the row (intended, executed, answer_len, ok). **Restore the original
  `settings_general` at the end (back it up first; restore in a `finally`).**

This is already automated — **reuse, don't hand-roll**:
**`python ${CLAUDE_PLUGIN_ROOT}/scripts/rag-test/manual_coverage_sweep.py`** pins +
asks + reads-back every catalogue technique through the gateway, writes an
incremental ledger to `rag-test/runs/manual_coverage_ledger.json`, and restores
settings on exit. Run it (background), then parse the ledger into the coverage grid.
```
manual_coverage_sweep.py [--only graph,entity] [--collection <cid>] [--workspace <wsid>]
                         [--limit N] [--ledger <path>] [--list]
```
`--list` prints the catalogue and exits (useful to translate a focus into a
subset). `--only` takes comma-separated exact names or substrings — that is how a
`focus=` reaches this sweep. The ledger is `{"meta": {selected, catalogue, subset,
only, skipped, …}, "rows": [ … ]}`; a subset run also prints
`SUBSET RUN — n techniques NOT tested: …`. Carry that line into the report so a
focused sweep is never mistaken for full coverage.

**Do NOT use the in-process `verify_all_techniques.py` for coverage** — in a
standalone process its `llm_manager.get_llm(provider_type="system")` cannot resolve
the system DeepSeek provider (falls back to the config.yaml openai stub → every cell
fails: `401` if `OPENAI_API_KEY` is polluted, else `Failed to get LLM`). It only
works inside the running server. The gateway-pin sweep above sidesteps that.

**Coverage exit criterion:** the ledger shows EVERY catalogue technique with
`status=ran` (or a documented "technique disabled/no-graph-data" skip with reason)
AND no technique was silently substituted for another. Report the coverage grid
(✅ ran+graded / ⚠️ ran-empty / ❌ error / — skipped-with-reason) at the end.
With a focus-driven subset the criterion applies to the subset, and the report
must name the techniques left untested and why.

## Step 3T — prompt calibration for `tune` (DEFAULT activity)
The mandate: make the answer contract right for every question shape a user can
ask, anchored in real documents and real conversations — **without leaving
production worse than you found it**. An LLM grading an LLM and then rewriting
the prompt overfits to the grader; real users re-asking, and a frozen baseline,
are the anchors that cannot be gamed.

**T0 — gate.** `busy-check` must report `safe_to_tune`. `configs/prompts.yaml`
is production for every user; never edit it under someone's live conversation.
Not safe → report and stop this tick (a skipped tick is a success).

**T1 — enable live reload.** `prompt-reload` writes the sentinel
`configs/.prompts_autoreload`; the service then reloads prompts ~5s after any
change with no restart (`background/prompt_reloader.py`; log line
`♻️ Prompts reloaded live`). Without the sentinel prompts move only on restart.
Turn it back OFF (`prompt-reload --off`) at close-out — the gate exists so a git
branch switch cannot silently swap production prompts.

**T2 — BUILD THE CORPUS (first tick only, then FROZEN).**
If `corpus/questions.json` exists with `"frozen": true`, **skip this step and
reuse it verbatim**. Every iteration must ask the SAME questions, or the
scoreboard cannot be compared across ticks and no fix can be verified later.
Regenerating mid-run invalidates the whole run.

On the first tick, generate the set from material the system really has:
1. `list-books --workspace <ws> --per-collection 2 --limit 12` → real books
   spread across collections (do not take them all from one subject).
2. For each candidate, `sample-chunks --document <did> --n 5` → real passages.
   **Write every question from those passages**, so the expected answer is known
   and citations/hallucination are gradeable. Never invent a question about
   content you have not read.
3. Cover BOTH RAG agents — this is why the activity spans both modes:
   - **auto rows** (`mode: auto`, half the corpus): one per rubric
     dimension from Step 3A (factoid, comparison, entity/relationship,
     section-targeted, memory follow-up, out-of-scope probe). Routing picks the
     strategy; we grade whether it chose right.
   - **manual rows** (`mode: manual`, half the corpus): shaped from the Step 3M
     technique catalogue, since Engine A is the only surface where a named
     strategy actually executes. Spread across techniques — never one technique
     twice while others go untested.
   A mode named on the command line narrows which rows this tick WORKS ON, never
   which rows get built — the corpus always holds both, or the regression check
   in T6 has nothing to catch cross-engine damage with.
4. Fold in the real-session failures from `harvest-sessions` (below) as rows with
   `origin: real:<user>`.
5. When a `focus` is set on the tick that builds the corpus, bias question
   selection toward it (roughly two thirds focus-related, one third spread) and
   store it as `corpus.focus` — but keep every rubric dimension and both modes
   represented. Record it so a later run knows why these questions exist.
6. Write `corpus/questions.json` with `"frozen": true` and a `corpus_sha256` over
   the question texts. Later ticks verify that hash and STOP if it moved.

Row shape: `id`, `question`, `mode` (auto|manual — an older corpus may say
`agentic`, read it as `auto`), `origin` (`generated` | `real:<user>`),
`workspace_id`, `collection_id`, `document_id`,
`source_passage` (the chunk it was written from), `technique` or `dimension`,
`expected_dimensions`, `attempts`, `status`.

**Real-session harvest.** `harvest-sessions` returns every assistant turn real
users got, ranked by `reask_overlap` (how much the user's NEXT message repeats
the one that produced the answer). High overlap = the user asked the same thing
again = that answer failed them. Also weigh `feedback == -1`, `n_citations == 0`
on a document question, and a next message that reads as a complaint. Judge WHY
with the model; the metric only ranks WHERE to look — never keyword-match
(`feedback_no_keyword_matching_in_prompts`). Only re-ask another user's question
against a collection the admin owns — reproduce the SHAPE, not their private
data; admin's own failures replay directly. Harvested conversations are real user
content: they stay under `rag-test/`, never in a commit, PR, or external surface.

**T2b — BASELINE: measure production BEFORE touching anything.**
On the first tick, with prompts **untouched**, ask the entire frozen corpus and
grade it. Write `corpus/baseline.json`: per question, per dimension, the verdict
production gives TODAY. This is the contract: **no edit may take any question
below its baseline.** Without a baseline "no regression" is an opinion. A row
that already fails at baseline is a defect to fix; a row that passes at baseline
is a promise you must keep.

**T3 — pick ONE defect** (worst-ranked row whose current grade is below
baseline, or which fails baseline). Never batch. Skip rows at `attempts >= 3` —
park them in STATE Backlog instead of grinding: three failed attempts on one
question means the cause is not where you are looking.
With a `focus`, rank focus-related defects first — and when a mode was named,
prefer that mode's rows. If nothing focus-related is failing, say so plainly and
take the worst remaining defect anyway; a focused tick still has to leave
production better than it found it, not idle.

**T4 — attribute it: prompt or code?** This is the step that keeps the loop
honest. Read the run log and the retrieved chunks:
- Content was retrieved but the answer hedged, refused, ignored it, padded, or
  embellished beyond it → **prompt defect** → `scrapalot:prompt-tuner`.
- Retrieval found nothing, the router chose the wrong strategy, a tool crashed,
  or the stream errored → **code defect** → `scrapalot:devops-fixer` +
  `scrapalot:devops-verifier` (Step 4a). **A prompt cannot fix missing data** —
  never paper over a retrieval bug with prompt text.
Example from the live corpus: the `Treći pokušaj` medication turn routed to
`RAGGraphSearch` and returned 0 citations — that mix is a routing/retrieval
smell (code), while a hedged answer over good chunks is prompt.

**T5 — tune, then let someone else decide it worked.** Dispatch
`scrapalot:prompt-tuner` with the defect, the retrieval facts proving content was
available, and the regression set. It edits ONE key, principle-level (never the
specific drug/horse/book/word that failed), applies it via `prompt-set` (atomic,
backed up, minimal diff, YAML-validated), re-asks, and reverts itself on any
regression.

**The tuner does not pass its own fix.** It gathers evidence; the verdict goes to
`scrapalot:rag-tester` with **fresh context**, given the question, the new answer
and the dimension to grade — and NOT told that a prompt was edited, which key, or
what anyone believed was wrong. A grader that knows a fix was attempted grades
the effort instead of the answer.

- Grader says the dimension passes → the edit stands, move on.
- Grader says it does not → its sentence is the tuner's next input. Loop.
- **The same objection surviving two different edits** → stop. Record it as
  needing an idea we do not have, name both attempts, and move to the next
  defect. That is a result, not a failure.

No round cap beyond that rule. The exit is the grader passing it or the owner
stopping the run — never "we tried, ship it".

**T6 — NO REGRESSION. This rule outranks fixing the defect.**
Prompts are shared, so sharpening `rag_agent.system_prompt` for one question
breaks another very easily. An edit is accepted ONLY if, re-measured against
`baseline.json`:
- the target defect now passes, AND
- **every other corpus row scores >= its baseline, on every dimension** — both
  `mode: auto` and `mode: manual` rows, not just the ones near the defect, and
  regardless of which mode or focus this tick was run with. Narrowing the
  re-measurement to the focused rows is the one shortcut that voids the whole
  loop: prompts are shared, so the damage always shows up somewhere you were not
  looking.

Any row below baseline = REGRESSION = revert immediately (restore the tuner's
backup), mark the attempt `reverted`, record what broke, and let the next tick
try a different edit. **A reverted attempt is a good outcome. Shipping a fix that
costs a working answer is not** — the user's rule is that this loop must never
break what already works in production.

**Blast radius before you edit.** Some prompt keys are read outside RAG chat —
`shared_intent_principles` is shared with the voice agent, and `notes_assistant`,
`document_qa`, `direct_chat_persona` serve their own surfaces. Grep the key's
readers first:
`grep -rn 'resolved_prompts.get("<key>"' /opt/scrapalot/scrapalot-chat/src/main`.
If a reader lives outside the corpus's coverage, either extend the regression to
that surface (voice and text are different paths — verify BOTH) or pick a
narrower key. Never edit a key whose blast radius you have not measured.

**T7 — commit the accepted edit.** A prompt edit is a small change: commit
`configs/prompts.yaml` straight to `main` with a message naming the defect and
the rule, so any edit can be reverted later by revert of one commit. **The live
checkout may sit on someone else's feature branch** — check
`git branch --show-current` first; if it is not `main`, commit through an
isolated worktree on `main` (a concurrent session has wiped uncommitted edits in
this checkout before) and leave the working-tree copy live.

**T8 — scoreboard, history, convergence, CAPS.** Append one row per tick to
`corpus/history.jsonl` (`tick`, per-question grid, edit accepted/reverted, pass
rate) — that file is how a later run verifies this one, since the questions never
change. Update `corpus/scoreboard.json`:
`{tick, max_ticks, total, pass, fail, reverted, edits_accepted, ticks_without_edit}`.

**Stop — whichever comes first:**
- every corpus row is `pass` AND two consecutive ticks accepted no edit → DONE;
- `tick >= max_ticks` (default 20) → STOP and report honestly, done or not;
- every remaining row sits at `attempts >= 3` → STOP, backlog them;
- the same key was edited three ticks running with a flat pass rate → STOP and
  escalate: that is the prompt fighting itself, and the cause is usually code or
  a bad rubric, not more prompt text.

Report the pass rate against baseline every tick — "calibrated" is a number, not
a feeling.

## Step 3K — Kotlin Spring AI prompts (secondary lane)
`scrapalot-backend/src/main/resources/prompts.yaml` governs describe / suggest /
summarize / notes-translate / collection-description. Not RAG — grade these by
whether the output matches the requested language, length, and format, not by
the 7 RAG dimensions. There is **no hot reload**: each edit needs commit + push
+ a CI deploy, so batch several edits per deploy and poll inline
(`until [ "$(gh run list --limit 1 --json status -q '.[0].status')" = "completed" ]; do sleep 15; done`),
never `ScheduleWakeup`. Do this lane only after the RAG lane converges.

## Step 4 — ask & grade, ONE question at a time
For each question in order, in the SAME session, delegate to the
**`scrapalot:rag-tester`** agent (Agent tool). Give it: the session_id, the mode
(`auto` → the agent passes `--mode auto`; `manual` → no `--mode`, strategy pinned
per Step 3M), workspace/collection/document ids, the question, its target
dimension, the **focus text verbatim** when one is set, and the book context.
The agent runs `ask` + `analyze`, then returns a structured verdict:
per-dimension `pass|fail|n/a` with evidence, plus — on failure — a harvested
defect (`signature`, likely `source_file`, `sample`, whether it was a
`stream_error` or a `quality_fail`).

Grade the focus dimensions strictly, and grade **all** the others anyway — a
focused run reports everything it saw, it just leads with the focus.

Append one ledger line to STATE.md per question:
`idx | mode | status | strategy | sources | n_cit | n_graph | note`.

### Step 4a — HARD STOP on streamingError (stream_error verdict)
The moment the tester reports a stream error (`verdict.error` set):
1. **Do not ask the next question.** Snapshot the failure.
2. Harvest the backend error: `docker logs --since 5m scrapalot-chat 2>&1 |
   grep -iE 'error|traceback|exception' | tail -40` (and `scrapalot-backend`
   if the gateway/Kotlin layer is implicated). Build a `{signature, source,
   sample}` triple.
3. Delete the failed assistant message (and its user message if it should be
   re-asked): `del-message --message <mid>` for each id from `analyze`.
4. **Fix** — launch `scrapalot:devops-fixer` (Agent) with the harvested error.
   It root-causes in an isolated clone and commits a minimal fix on a branch.
5. **Verify** — launch `scrapalot:devops-verifier` on the fixer's branch.
   `reject` → escalate to STATE Backlog, ask the user (AskUserQuestion), stop.
6. **Ship & resume** (verifier `approve`):
   - **Python non-gRPC** (`scrapalot-chat/src` not under `main/grpc/services`):
     the prod container hot-reloads — apply the same edit to the LIVE checkout
     (the fixer worked in a clone), confirm reload, then **resume immediately**.
     gRPC service file → `docker restart scrapalot-chat` first.
   - **Kotlin / UI / Gateway**: push the feature branch, open a PR (NEVER merge
     `main`), then poll until deployed:
     `until [ "$(gh run list --limit 1 --json status -q '.[0].status')" = "completed" ]; do sleep 15; done`
     then confirm the deploy job `conclusion == success`. Only then resume.
   - Record the fix under STATE `## Recently shipped fixes`.
7. **Re-ask the SAME question** in the SAME session and re-grade. Loop until it
   passes or the verifier/user blocks it.

### Step 4b — unsatisfactory answer (quality_fail, no stream error)
If the answer streamed fine but fails a rubric dimension (wrong source routing,
hallucinated citation, ignored memory, missing graph/hierarchy when expected):
1. `del-message --message <assistant_mid>` (remove the bad turn from history).
2. Fix the root cause (same fixer/verifier flow; or a direct minimal Python edit
   when the cause is obvious and local — still commit it).
3. Re-ask the SAME question; re-grade. A dimension flips to `pass` only with
   evidence.
Borderline/subjective failures (style, completeness) that are NOT a real defect:
log under STATE Backlog and move on — do not invent bugs.

## Step 5 — close out
- Update STATE.md: `last_run`, `mode`, `activity`, `focus`, ledger, any parked
  findings, shipped fixes.
- Final report (concise): the resolved run header (mode / activity / focus /
  collection / caps), book, per-question dimension grid (✅/❌/—), any
  streamingError caught + fix shipped, any backlog finding, and whether the
  session is fully clean. When a focus narrowed the run, name what it left
  untested — a narrowed run reported as a full one is worse than no run.
- **Not done until every planned question is `pass`.** If questions remain or a
  fix is mid-CI, say so plainly and leave STATE resumable.
- **Run the ledger before the report; close it only when the run really ends:**
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py run
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py close gates/active/ragtest-<mode>-<activity>.md
  ```
  A tick that stops with questions still open leaves the ledger **open** and
  resumable — that is the honest state, and the next tick picks it up. Close it
  only on a clean session or at `max_ticks`, and put the `N/M met` summary plus
  every `ABANDON:` line in the report.

## Running autonomously (/goal + /loop)
There is no `/goal` command in this environment — the GOAL is encoded in
`rag-test/GOAL.md` and the persistent `STATE.md`. To run the whole thing to
completion unattended, drive THIS command under `/loop`:
```
/loop /scrapalot:rag-test                       # DEFAULT: calibration over both RAG agents
/loop /scrapalot:rag-test max_ticks=10 questions=12
/loop /scrapalot:rag-test auto                  # narrower: self-routing agent, one session, one book
/loop /scrapalot:rag-test manual focus=graph    # narrower still: only the graph/entity techniques
/loop /scrapalot:rag-test tune focus="every claim must carry a citation"
```
Each tick reads STATE, inherits the stored focus when none is passed, resumes the
active session, asks the next unpassed question (or re-asks a failed one after
its fix deployed), and stops when the session is clean. Use the dynamic
(no-interval) form so ticks self-pace around CI waits; poll CI inline with
`gh run list` (never ScheduleWakeup).

A default (`tune`) tick is: gate on `busy-check` → reuse the frozen corpus
(generate + baseline it on tick 1) → pick the worst defect → attribute
prompt-vs-code → tune or fix → **re-measure the whole corpus against baseline** →
revert on any regression → commit → score → append history. It stops itself when
the corpus is green with two quiet ticks, or at `max_ticks` (default 20), or when
everything left has burned 3 attempts. A tick that skips because real users are
active is a SUCCESS, not a failure — never tune under a live conversation just to
keep the loop moving.

## Hard rules (restate)
- ONE session, ONE book, questions asked sequentially in it (memory depends on
  order). Never spread the plan across multiple sessions.
- ONE mode per session — `auto` and `manual` are different engines and never
  share a chat history.
- Distinct question per dimension — never 1 question reused across techniques.
- A `focus` steers WHAT gets attention first; it never shrinks what gets graded,
  never shrinks the regression re-measurement, never rewrites a frozen corpus,
  and never gets encoded into a prompt. Every narrowing it causes (technique
  subset, mode subset) is named in the report.
- HALT on streamingError; root-cause fix; branch+PR for CI code, hot-reload for
  Python; resume the SAME session; never push/merge `main`.
- Delete-bad-message-then-re-ask is the retry primitive — never edit the DB to
  fake a good answer.
- Evidence-based grading: every `pass` is backed by the verdict JSON / run log.
- `tune` (default activity) only:
  - **NO REGRESSION ON PRODUCTION — outranks fixing the defect.** Every corpus
    row must stay >= its `baseline.json` grade on every dimension. Below baseline
    anywhere → revert. Never trade a working answer for a fixed one.
  - The corpus is generated ONCE from real documents and then FROZEN — same
    questions every tick, or nothing is verifiable. Never regenerate or reword;
    `new-corpus` is the only escape hatch and it resets the baseline.
  - Both engines in every corpus: `mode: auto` AND `mode: manual` rows.
  - Never tune while `busy-check` reports active users.
  - Never fix a retrieval defect with prompt text. Never encode the failing case
    (drug, horse, book, word) into a prompt — principles only.
  - Measure a key's blast radius before editing it; voice and text are different
    paths, so verify both when the key is shared.
  - One key, one edit, one defect per tick. Caps: `max_ticks` (default 20),
    3 attempts per question.
- The live `scrapalot-chat` checkout is bind-mounted into the container, so it —
  not the CI-deployed image — is the code and prompts production runs. Check
  `git branch --show-current` before trusting that what you read is what ships.
