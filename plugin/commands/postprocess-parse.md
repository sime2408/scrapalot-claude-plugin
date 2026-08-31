---
description: Parse-only audit of ONE book (no graph). Sweeps the corpus book by book so parser bugs get fixed at source before any graph is built.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Task
---

# One book. Parse layer only. Fix the parser, not the row.

**Read `.claude/postprocess/GAUNTLET.md` first and follow it.** This command runs
as a gauntlet loop: the bar is the book's own printed structure, a separate
critic with fresh context judges the result blind, and the exit is that critic
saying it matches — never a round count, never "diagnosed, halting".

## DIRECTION — restate this at the start of every run

> **We are auditing the PARSE layer of ONE book, to find and fix bugs in the
> parser, and looping until a separate critic agrees the stored structure is the
> book's structure. The graph is explicitly OUT OF SCOPE. When the critic says
> yes — or the loop runs out of ideas — we STOP and report.**

This is the corpus-sweep half of `/scrapalot:book`. The owner's sequence
(2026-08-15) is: **parse across every remaining book first, fix parser bugs to
the maximum, and only then build graphs.** Building a graph on a book whose
chapters are wrong bakes the wrong names in permanently — Chapter nodes merge
with `ON CREATE SET` and no `ON MATCH SET`, so a bad title needs a
`DETACH DELETE` to correct, never a re-run.

So: **never dispatch a graph build from this command.** If a reprocess is
needed, pass `skip_graph_build=True`. Graph comes later, as its own pass.

## Phase 0 — resolve ONE book

`$ARGUMENTS` may be a document id, a title fragment, or a collection name.

- Exactly one match → use it. Print id + title + collection.
- Ambiguous → list at most 8 candidates and ask. Do not guess.
- Empty → take the **alphabetically-first book not yet in
  `.claude/postprocess/progress.txt`** (order: `collection_name`, then `title`),
  announce it, and proceed. No menu — the owner asked for straight alphabetical
  order.

Unlike `/scrapalot:book`, **tier is irrelevant here**. A book that builds no
graph still has a parse layer worth fixing, and its defects still teach us about
the parser. Do not skip a book for its tier.

## Phase 0.5 — open the gate ledger, BEFORE the first fix

**Read `.claude/gates/CONTRACT.md` and follow it.** The gauntlet says who judges;
the ledger says what a judgement may rest on. Write the gates now, while the run
is still honest about what it owes.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py open \
    --run parse-<short-doc-id> --command /scrapalot:postprocess-parse \
    --scope "<title> — parse layer only, until a critic says the stored structure is the book's"
```

Starter gates. Adapt them to the book you resolved; the `<document_id>`
placeholders must be gone before the first `run`.

```markdown
- [ ] G1: the book's own printed structure is extracted and written down (the bar)
  EVIDENCE: pending
- [ ] G2: content-sound or content-suspect is decided, with the quote that decided it
  EVIDENCE: pending
- [ ] G3: a critic with fresh context, given both chapter lists unlabelled, says they are the same book
  EVIDENCE: pending
- [ ] G4: the stored chunks come from this document's text and the ranges are contiguous
  EVIDENCE: pending
- [ ] G5: every source fix in this run carries a corpus regression scan in BOTH directions
  EVIDENCE: pending
- [ ] G6: no graph build was dispatched — every reprocess in this run passed skip_graph_build=True
  EVIDENCE: pending
- [ ] G7: the ledger row for this book is in progress.txt
  CHECK: grep -c "<document_id>" ${CLAUDE_PROJECT_DIR}/.claude/postprocess/progress.txt
  EXPECT: /[1-9]/
  EVIDENCE: pending
```

A book with no recoverable structure ends the run at G1 — `ABANDON: G1 no TOC and
no headings in the text`, and the same for G3, said plainly in the report. That is
a result. Quietly dropping the comparison and reporting the rest as clean is not.

## Phase 1 — the audit

Delegate to the **`scrapalot:postprocess-parse` agent** (Agent tool,
`subagent_type: scrapalot:postprocess-parse`), scoped to this document_id.
That agent is 68 KB of hard-won forensics — do NOT reimplement or thin it out.
Its Phase 2 runs seven sub-audits: content fidelity, chapter detection,
source-code path forensics, metadata-stub detection, `document_hierarchy`
integrity, status/chunk consistency, Cat-I eligibility.

Tell it explicitly: **parse only, do not touch Neo4j, do not advance to a second
book, do not write the ledger row** (this command writes it).

## Phase 2 — read the text yourself

The agent proves the chunks MATCH `documents.content`. It does not prove the
content is worth anything. Read a sample — start, middle and end, never just the
first chunk — plus the detected chapter titles as a plain list, and judge in
sentences with a quote as evidence:

- coherent knowledge, or noise / boilerplate / repetition?
- do the chapter titles reflect what the text is actually about?
- is this even the book the metadata claims?

Emit **content-sound** or **content-suspect** plus the quote that decided it.

**Bad scan → look for a cleaner copy BEFORE patching.** Garbled letters,
watermark-only text, an appended bookseller's catalog, plainly the wrong scan:
most of this corpus is old public-domain material, so a cleaner copy usually
exists (archive.org, HathiTrust, Wikisource, Gutenberg, sacred-texts). Dispatch
a web search, report the candidates and how clean each looks, and let the owner
decide. Truncation or hand-editing is the fallback when nothing cleaner exists.

## Phase 2.7 — extract the bar, before any fixing

Independently of anything the pipeline stored, read the book's **own** structure
out of `documents.content`: its table of contents if it prints one, and the
chapter headings as they appear in the body. Write that list down. It is the bar
for every round that follows, and every later comparison is against it, not
against a description of it.

If the book genuinely has no recoverable structure — no TOC, no headings — say
so plainly and stop. A gauntlet without a bar approves everything.

## Phase 3 — fix the PARSER, not the row, and LOOP

A defect found here is a bug that will hit the next thousand books. Trace it to
source and fix it there:

- chapter detection → `chunking_enhanced_markdown.py`, `document_processor.py`
- the bulk importer's own detector → `scripts/dataset/extract/chapters.py`
  (a DIFFERENT code path — `grep -rn "from scripts\." src/` returns zero, and
  `rechunk_imported_document.py` refuses production-chunked documents)
- graph-side title handling → `node_factory.py` (fix it, do not build a graph)

**Every source fix needs a corpus-wide regression scan before it ships**, in
both directions: what it rescues AND what it newly breaks. Three fixes in a row
were caught or reshaped by that scan — one would have wrongly renamed 8,226
chapter titles. Stream the query (`cursor(name=...)`, `itersize`); loading every
document's content at once OOM-kills the container.

Worktree + PR only. Never push to main. Destructive data fixes (reprocess,
content edits, re-ingest) are approval-gated — propose, do not apply.

### The loop

After each fix, run the **critic** — a separate agent, fresh context, told
nothing about how the fix was reached:

> Here are two chapter structures for one book. List A is what the book itself
> prints (extracted from its text). List B is what the pipeline stored after
> processing. Do they describe the same book — yes or no? If no, name the single
> biggest difference. Do not score, do not soften: "mostly" is a no.
>
> [for a source fix, also:] Here is the raw output of a corpus regression scan,
> old behaviour versus new, over N documents. Does anything get worse? Name the
> worst case.

Give it the extracted list and the stored list, **unlabelled where the
comparison allows it**. Never hand it the builder's summary of the scan — hand
it the scan.

If the critic says no, its one sentence goes back to the builder and the round
repeats. **The exit is the critic saying yes, or the owner stopping.** Not a
round count.

If two different fixes hit the same gap, stop and report it as needing an idea
we do not have — name what was tried. That is a result, not a failure. Printed
chapters 7 and 10 of `2cdd2f36` are the standing example: both candidate
mechanisms were measured, one harmed 3 of 25 books, and saying so was worth more
than a third attempt.

## Phase 4 — report and STOP

**No report until the gate ledger is full.**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gate-check.py close gates/active/parse-<short-doc-id>.md
```

Every `ABANDON:` line is named in the report as something this run did not
settle. The gate summary is re-measured at report time, never recalled.

- ledger row appended to `.claude/postprocess/progress.txt`
- anything real but off-topic goes to `.claude/postprocess/side_findings.txt` —
  write it down and keep going, never chase it
- in chat: plain Croatian, no pipeline jargon (no "chunk", "tier", "entity",
  `file:line`, table names — those belong in the ledger, not in what the owner
  reads), findings and the single recommended next action

Then stop. Do not start the next book unprompted.
