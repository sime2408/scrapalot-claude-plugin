---
name: competitive-impl
description: >
  Turn finished research (competitive analyses, PRD backlog categories, partner PRDs) into
  shipped features. Owns three things the research skills do NOT: (1) the FILE-NAMING LAW —
  every research artifact has exactly one canonical path, and strays get renamed and relinked
  instead of quietly lost; (2) the INTERVIEW — the owner is questioned feature by feature in
  plain Croatian, with zero codenames, abbreviations or file paths, because they never read
  the research context; (3) the BUILD — worktree, feature branch, tests, PR, close-out.
  Invoked by /scrapalot:competitive-impl. Never invents work, never batches decisions.
---

# Competitive implementation — from research file to shipped feature

The research commands (`/scrapalot:competitive-analysis`,
`/scrapalot:competitive-analysis-closed-source`) produce documents. This skill consumes
them. It is the only sanctioned path from "an analysis exists" to "the feature is live and
the analysis file is gone".

**The three failures this exists to stop:**

1. **Lost files.** Agents saved research output under invented names, so a later session
   could not find it and the backlog looked smaller (or bigger) than it was. Fixed by §1,
   which is a law, not a preference.
2. **Codename questions.** The owner was asked to decide on "FIM #10", "PixelRAG Phase 0",
   "F0 → 14.2". They do not read the PRD backlog, the analyses, the audits or the logs.
   Fixed by §5, which forbids that vocabulary in every user-facing sentence.
3. **Decided but never built.** Analyses carry a Decision Log with ten accepted features
   and no commits behind them. Fixed by §3 (finish before start) and §7.

---

## §1 — The file-naming law

Every research artifact has **exactly one** canonical path. There are no alternates, no
"_v2", no dated copies, no per-session variants. `<slug>` is lowercase ASCII
`[a-z0-9_]+`, derived from the product or repo name (`owner/repo` → `repo`),
**underscores, never hyphens** — `open_notebook`, `agent_native_visual_plan`,
`connect_your_agent`. The same slug is reused byte-for-byte across every artifact of that
source and its tracker line.

| Artifact | Canonical path |
|---|---|
| Competitor analysis (open **and** closed source) | `scrapalot-chat/docs/prd-competitive/competitive_analysis_<slug>.md` |
| Rendered visual review surface | `scrapalot-chat/docs/prd-competitive/prd_<slug>_review.html` |
| Review screenshots (local only, gitignored) | `scrapalot-chat/docs/prd-competitive/prd_<slug>_NN.png` |
| Wireframes | `scrapalot-chat/docs/prd-competitive/wireframes/<slug>_<feature>.html` + `.png` |
| Backlog category | `scrapalot-chat/docs/prd-scrapalot-mix/CATEGORY_NN_<AREA>.md` (`NN` two digits, `<AREA>` UPPER_SNAKE) |
| Partner codex | `scrapalot-chat/docs/prd-*-partner/README_NN_<AREA>.md` |
| Index — competitive | `scrapalot-chat/docs/prd-competitive/README.md` |
| Index — backlog | `scrapalot-chat/docs/prd-scrapalot-mix/README.md` |
| Close-out log — competitive | `scrapalot-chat/docs/prd-competitive/resolved_analyses.txt` |
| Close-out log — other Python-side PRDs | `scrapalot-chat/docs/resolved_prds.txt` |
| Close-out log — Kotlin-side PRDs | `scrapalot-backend/docs/resolved_prds.txt` |
| Analysis that did NOT earn a PRD | `scrapalot-chat/docs/prd-competitive/NO_PRD_LOG.md` |
| Kotlin/gateway PRD | `scrapalot-backend/docs/README_PRD_<TOPIC>.md` |
| Cross-repo status snapshot | `/opt/scrapalot/PRD_STATUS.md` |
| Source trackers | `${CLAUDE_PROJECT_DIR}/.claude/competitive-analysis/analyzed_repos.txt`, `analyzed_closed_source.txt` |
| This tool's own state | `${CLAUDE_PROJECT_DIR}/.claude/competitive-impl/STATE.md` |

**Two companions are keyed differently — do not report these as violations:**

- **The tracker line.** For a GitHub repo it is keyed by `owner/repo`
  (`lfnovo/open-notebook`), not by the slug — that is the tracker's own format and it is
  correct. Only closed-source products are keyed by `<slug>`. What the law requires is that
  a line **exists** for every analysis; a missing line is the real defect (as of
  2026-08-18: `agent_native_visual_plan` and `connect_your_agent` have none).
- **The rendered review HTML.** Required only for analyses written after the visual-plan
  discipline was adopted. Several older analyses were never rendered, and that is not a
  stray — report it as "not rendered" and leave it alone unless the analysis is being
  reworked.

**Everything else that looks like research output is a stray.** Patterns that mark one:
`PRD_*.md`, `prd_*.md` outside the table above, `*_PRD.md`, `ANALYSIS_*.md`,
`*_analysis.md` outside `prd-competitive/`, `plan_*.md`, `FEATURES_*.md`, `research_*.md`,
anything of that shape sitting in a subproject root, in `docs/` next to the
`README_*.md` files, in `/tmp`, in a scratchpad, or inside `.claude/worktrees/*`.

**Repair, do not report.** A stray is renamed to its canonical path in the same pass that
found it, every link pointing at the old name is fixed, and the move is stated to the
owner in one plain sentence. A stray that duplicates a canonical file is deleted, not
merged, once its content is confirmed to be a subset. A stray whose subject has no
canonical home gets one — pick the row of the table it belongs to, do not invent a new
row. When a worktree copy under `.claude/worktrees/` is the only place a file exists, copy
it out to the canonical path before anything else; those directories get deleted by CI.

**No new file types.** Decisions are recorded inside the artifact that already exists
(§6). A new tracking file is how the last graveyard started.

---

## §2 — What counts as the queue

Three sources, in this order of precedence:

1. **`prd-competitive/*.md`** — live analyses. Each file with no matching entry in
   `resolved_analyses.txt` is open work. Today that is the largest pile.
2. **`prd-scrapalot-mix/CATEGORY_*.md`** — the numbered backlog. Each numbered feature
   inside carries its own status; the file stays until every feature in it is done.
3. **`prd-*-partner/`** and `scrapalot-backend/docs/README_PRD_*.md` — partner
   and infrastructure PRDs. Only touched when the owner names them.

A **half-open** item is one where some features are decided and some are not, or where
everything is decided and nothing is built. Those outrank untouched items — see §3.

---

## §3 — Selection: what "the next feature" means

Resolve in this order, stop at the first that matches:

1. **The owner named something** — a slug, a product name, a category number, or a plain
   description of the feature. Take it, no questions.
2. **`STATE.md` has work in flight** — an interview partway through, or approved features
   with no PR. Resume exactly there. Never start a second item while one is open.
3. **Decided but unbuilt** — an analysis whose Decision Log holds accepted features with
   no commit or PR behind them. Finishing beats starting; this is the default pick.
4. **Otherwise, the owner chooses.** Present at most four candidates, one plain-Croatian
   line each — what the product would gain, not what the competitor is called — with a
   recommendation. Priority is the owner's call, never the tool's.

---

## §4 — Ground truth before the first question

A status line in a PRD is a claim, not a fact. Nothing is presented to the owner until it
has been checked against the code, because reality has repeatedly been ahead of the
document (features written as "5% done" that shipped months ago, "we don't have X" claims
that were false three separate times).

Run `scrapalot:prd-auditor` agents in parallel, split by feature groups, never fewer than
two, never more than five. Each returns, per feature:

- `state` — `MISSING` / `PARTIAL` / `ALREADY_SHIPPED`, each backed by a `file:symbol` hit
  or an explicit "searched X, Y, Z — nothing". A grep is mandatory before writing
  `MISSING`.
- `already_in_scrapalot` — the `file:symbol` that proves we ship it, or `none`.
- `measurable_via` — the existing harness that would show it working (a pytest path, a
  Playwright spec, `/scrapalot:rag-test`, a SQL count), or `none`.
- `new_dependencies` — GPU, container, paid API, library, ongoing maintenance, or `none`.
- `reversibility` — `easy` or `hard`, naming what gets locked in (wire format, schema,
  public ids, stored user data).
- `cheaper_substitute` — the 20%-effort version worth most of the benefit, or `none`.
- `effort` — XS / S / M / L / XL, and which subprojects it touches.

Features that come back `ALREADY_SHIPPED` are **never put to the owner**. They are marked
done in the document with their evidence, and reported as one line: "this one already
exists, here is where you can see it in the app."

---

## §5 — The interview (the part that matters)

The owner knows Scrapalot. They have not read the analysis, the audit, the papers or this
session's logs, and they will not. Assume zero recall of any identifier, every single time.

### 5.0 The context turn — mandatory before ANY question

**No question of any kind reaches the owner before this turn has happened.** Not the item
choice, not a feature, not a defect, not a branch question. The owner has not read the
analysis, the audit or the logs, does not remember decisions taken in past sessions, and
will not go looking. A question asked without this turn is unanswerable, and asking it
anyway is the single most common way this tool wastes their time.

The context turn establishes four things, in plain Croatian, assuming zero recall:

1. **Odakle ovo dolazi.** Where the thing on the table came from — one or two sentences, no
   document names, no dates the owner did not live through. Not *"deset stvari odobrenih u
   lipnju"* but *"netko je davno pregledao jedan sličan proizvod i zapisao popis ideja;
   nitko ih otad nije napravio"*. If a past decision matters, **restate what it actually
   was, in plain words** — never invoke it as a shared memory.
2. **Što je stanje danas.** What genuinely works right now, checked against the code — not
   what any document claims.
3. **Zašto to gledamo baš sada.** What put this in front of them this minute.
4. **Što je konkretno na stolu.** Only now, the thing itself — feature card (§5.2), defect
   card (§5.2b), or choice card (§5.2c).

Then **end the turn**. The question comes next turn.

**Forbidden openers**, in any form: *"kako smo se dogovorili"*, *"odobreno u lipnju"*, *"iz
analize X"*, *"kao što sam ranije rekao"*, *"sjećaš se"*, *"prema PRD-u"*, *"nastavljamo
gdje smo stali"*. Read every sentence as if someone joined the conversation one second ago.
If it would confuse them, rewrite it.

### 5.0b Who writes the words

**The explainer agent writes EVERY user-facing decision text** — the context turn, the
feature card, the defect card, the choice card, and the wording of the question and its
options. The orchestrator presents them verbatim and never composes them itself.

This is not ceremony. The orchestrator holds the audit findings, the file paths and the
history, and it leaks them: on 2026-08-18 the orchestrator wrote a Phase 2 choice question
by hand and produced exactly the failure this section exists to prevent — an option reading
*"prvo popravi pokvareno"* with no statement of what was broken, no evidence, and three
appeals to a June the owner does not remember. The owner rejected it outright. Route it
through the explainer, every time, including the options.

### 5.1 Banned in every user-facing sentence

Not "avoid" — banned. If a sentence needs one of these to make sense, the sentence is
wrong and gets rewritten:

- Codenames and shorthand: "FIM #10", "Phase 0", "F0", "C1/C2", "rank #3", "Theme B",
  "tier-0", the competitor's product name as the subject of the sentence.
- File paths, `file:line`, symbol names, table and column names, packet names, PR numbers,
  commit SHAs, branch names.
- Machine-learning and pipeline jargon: chunk, embedding, reranker, entity, node, graph
  tier, orchestrator, retrieval, groundedness, hallucination, context window.
- Infrastructure and operations jargon: circuit breaker, gateway, worker, queue, SAGA,
  cache invalidation, sliding window, container.
- Metric names and benchmark scores, confidence intervals, verdict codes
  (MISSING/PARTIAL/ALREADY_SHIPPED).
- Untranslated English terms dropped into Croatian sentences.
- **Appeals to history the owner did not live through**: a date ("u lipnju", "2026-06-08"),
  a past decision ("odobreno", "greenlit", "dogovorili smo"), a document, an earlier session,
  or anything in this conversation they have not read this minute. If the history matters,
  restate what it was in plain words as new information.
- **A claim with no evidence behind it.** "Ovo je pokvareno" without saying what happens on
  screen is not a finding, it is an assertion. See §5.2b.

The codename may appear **once**, in parentheses, after the plain description, and only if
it helps the owner find the thing later. Preferably not at all.

Everything banned above belongs in the written record — the document, the commit, the PR.
Never in the conversation.

### 5.2 The explanation turn

`scrapalot:prd-explainer` writes the card from the auditor's technical findings; the
orchestrator presents it **verbatim**. This separation exists because the orchestrator has
the technical context and will leak it.

One feature per turn. The card, in Croatian:

1. **Što je to** — two or three sentences, everyday words, what the person using
   Scrapalot gets. Start from the problem they would recognise, not from the mechanism.
2. **Gdje bi to vidio** — the actual screen and the actual click. "U bilješkama, kad
   označiš rečenicu, pojavi se…" — a place they can picture.
3. **Priča** — one concrete run-through: korisnik radi X → dobije Y. Real content, not
   "lorem ipsum" and not a generic user.
4. **Što već imamo od toga** — honest. If seventy percent exists, say seventy percent
   exists and that the work is the remaining thirty.
5. **Što nas košta** — čekanje na ekranu, novac za AI pozive, novi vanjski servis,
   održavanje. Say the number when there is one.
6. **Manja verzija** — if a cheaper version buys most of the value, describe it here as a
   real option, not as a footnote.
7. **Preporuka** — what you would do and the one reason why. Always present. A question
   without a recommendation pushes the decision back onto someone with less context than
   you have.

Optional, clearly demoted at the very bottom, only when it adds something:
**📐 Tehnički detalji (ako te zanima):** — file paths, symbols and numbers are allowed
*here* and nowhere else.

**Then end the turn.** Close with a line like *"Javi kad si spreman za odluku."* The
question dialog covers the terminal; asking in the same turn buries the text the owner is
supposed to read first. This has been corrected twice; it is not negotiable.

### 5.2b The defect card — when the thing is broken, not missing

A defect is never presented as "popravi pokvareno". It is presented as a thing that happens
on screen. Same rules as §5.2, different shape:

1. **Što se dogodi.** The reproduction, in clicks the owner can repeat right now: *"otvoriš
   bilješku, označiš rečenicu, klikneš 'Poboljšaj tekst' — i dobiješ tekst spušten na
   jednostavniji jezik umjesto uglađenog."* If it cannot be written as clicks, it is not
   yet understood well enough to present.
2. **Što bi trebalo biti.** What the person reasonably expected instead.
3. **Kako to znamo.** The proof, one line, plain: what was read, run or observed. *"Provjerio
   sam: ta radnja nikad nije dobila svoj naputak, pa tiho pada na onaj za pojednostavljivanje."*
   Never a bare assertion, never a file path in this sentence.
4. **Koga pogađa i otkad**, when it can be said honestly.
5. **Što bi popravak značio** for the person using it.
6. **Cijena i rizik** — including the risk of *not* fixing it.
7. **Preporuka.**

A defect the tool has already fixed under the fix-immediately rule is reported the same way,
in the past tense, with what changed and how it was proven. The owner still gets the full
story — "fixed it" without the symptom and the proof is the same failure.

### 5.2c The choice card — when the owner picks what we work on

Each candidate gets its own short block, and every block must stand alone for someone who
has never heard of any of it:

- **Što bi dobio** — two to four sentences on what the product gains, in things a person
  does and sees. Never "ten features", never the competitor's name as the subject, never a
  count of anything.
- **Gdje bi to živjelo** — which screen.
- **Što je danas** — the honest current state of that area.
- **Koliko posla i koliko rizika**, roughly.

Then one recommendation with one reason. If one candidate is broken-things-first, its block
must name the broken things as symptoms (§5.2b step 1), not as a category.

### 5.3 The decision turn

After the owner replies, one `AskUserQuestion`, one question, self-contained — written as
if it is the first thing they ever saw. Standard options:

- **Prihvati — napravi to** (marked `(Preporuka)` when it is the recommendation)
- **Napravi manju verziju** — describe it concretely in the option description
- **Odgodi — ostavi za kasnije**
- **Ne treba — preskoči**

The owner can always type their own answer, which covers "prihvati ali promijeni ovo" and
"objasni mi to drukčije". When they ask for a better explanation, go back to 5.2 and
re-explain with a **different frame** — an everyday metaphor works where a second
technical pass does not. Re-explaining is free; a decision made on a card the owner did
not follow is not.

### 5.4 Branch drilling (the grilling)

An accepted feature is not a decision, it is a branch. Walk the tree until nothing
undecided is left that would change what gets built. **One question per turn, each with
your recommended answer.**

**Answer it from the codebase instead of asking, whenever the codebase can answer it** —
then state the answer in one plain line rather than spending the owner's attention on it.

The branches worth walking, in the order they usually bite:

| Branch | The question in plain words |
|---|---|
| Tko ga vidi | Svi, samo plaćeni planovi, ili samo administrator? |
| Gdje živi | Koji ekran, koji klik — i što se miče da bi to stalo? |
| Sam ili na zahtjev | Radi li se automatski u pozadini ili tek kad korisnik klikne? (Standing constraint: nothing that makes the normal answer slower.) |
| Opseg | Nad svime, nad jednom zbirkom, ili samo nad onim što je korisnik označio? |
| Kad zakaže | Šuti, javi upozorenje, ili prekine posao? |
| Što ostaje zapisano | Čuvamo li rezultat, gdje, i može li ga korisnik obrisati? |
| Jezik | Hrvatski, engleski, makedonski — i nikad jezik zapisan u kodu. |
| Povratak | Zaključava li nas ovo u nešto (format podataka, javni link, shema baze)? |
| Dokaz | Čime ćemo vidjeti da radi — koji test, koja provjera? |

The last row is not optional. A feature with no way to tell better from worse is a feature
whose "done" is a matter of opinion.

Stop drilling when the remaining questions would not change a line of code. Say so and
move on — endless drilling is its own failure.

---

## §6 — Recording decisions

The moment a decision lands, write it down. Two places, both immediately:

1. **In the artifact itself** — a `## Decision Log (user review, YYYY-MM-DD)` table at the
   top of the analysis (the convention already used by several files), one row per
   feature: feature in plain words | decision | one-line reason | PR or commit once built.
   For a backlog category, update that feature's status block in place.
2. **In `STATE.md`** — the in-flight item, which features are decided, which are built,
   the branch and PR numbers, and where the interview stopped. This is what makes a
   context reset survivable.

Never let a session end with decisions living only in the conversation.

---

## §7 — Building

**Standing rules, from the owner, that override the global defaults:**

- **Worktree from the first edit.** Never the shared checkout — several sessions and CI
  deploys share it, and both have eaten uncommitted work. Recipe:
  ```bash
  REPO=/opt/scrapalot/<subproject>
  git -C "$REPO" fetch -q origin main
  git -C "$REPO" worktree add "$REPO/.claude/worktrees/<topic>" -b <type>/<topic> origin/main
  git config --global --add safe.directory "$REPO/.claude/worktrees/<topic>"
  ln -s "$REPO/node_modules" "$REPO/.claude/worktrees/<topic>/node_modules"   # ui only
  ```
- **Branch + PR only. Never push `main`, never merge.** A push to main triggers a deploy
  that restarts containers and wipes other sessions' state. PRs are assigned to `sime2408`.
- **Push the feature branch immediately after every commit** in `scrapalot-backend` — its
  deploy does `sudo rm -rf` on the whole checkout and takes unpushed worktree commits with
  it.
- **One feature per PR.** Big-bang has never worked here; the smallest change that gives a
  measurable result goes first, and its result is the argument for the next one.
- **No tests, not done.** A feature with zero integration tests and zero end-to-end tests
  is not complete, whatever the summary says. Python: `docker exec scrapalot-chat python
  -m pytest`, real database and real model calls, no mocks. Frontend: Playwright on the
  host, strict assertions, no tolerant skips.
- **Chrome before Playwright.** Verify new UI in the browser and take a screenshot before
  writing the automated test.
- **Watch CI inline** — `until ... gh run list --json status ... do sleep 15; done`. Do
  not schedule a wake-up for it.
- **Fix the root cause.** A workaround in a test, a disabled feature, or a manual database
  update to paper over a bug is not a fix.

**The loop per approved feature:**

1. `scrapalot:prd-builder` implements it in the worktree, writes the tests, commits.
   Commit messages in `scrapalot-chat` must carry a conventional prefix (`feat`, `fix`,
   `docs`, …) or the hook silently rejects them. No Claude attribution or co-author lines
   in any repo.
2. `scrapalot:prd-reviewer` reviews the diff read-only against the *approved scope* and
   the subproject's rules, and votes. Hand it the diff and the approved scope — never the
   builder's account of how hard it was.
3. `REJECT` → the objection, and only the objection, goes back to the builder on the same
   worktree. Stop when the reviewer approves, or when **two different attempts hit the same
   objection** — then it goes to the owner, not into a PR.
4. `APPROVE` → push the branch, open the PR against `main` assigned to `sime2408`, wait
   for CI green, verify in the browser if it has a UI.
5. Update the Decision Log row with the PR number, and `STATE.md`.

---

## §8 — Close-out (the file must disappear)

An artifact is deleted only when **every** feature in it is decided and every accepted one
is merged. A finished PRD is deleted, not archived — the knowledge moves into the code and
the official `docs/README_*.md`. In one PR:

1. Write the record into `resolved_analyses.txt` (or `resolved_prds.txt`): source, dates,
   what was adopted, what was rejected and why, what was deferred, and the PR/commit
   numbers. This is the durable trace; assume the file is gone forever afterwards.
2. Document what shipped in the internal `docs/README_*.md` that owns the area, and — only
   when it is user-facing and safe to publish — in the public `scrapalot-docs`. Never
   publish internal paths or security detail.
3. Delete `competitive_analysis_<slug>.md`, its wireframes and its `prd_<slug>_review.html`.
4. Remove or mark the row in `prd-competitive/README.md`; a row with no file behind it must
   read CLOSED or DELIVERED, never point at a dead link.
5. Update the tracker line: `<slug>|<date>|done + implemented`.
6. Update `/opt/scrapalot/PRD_STATUS.md` — the counts and the "what to do next" list.
7. Clear the item from `STATE.md`.

Dead links are how the last queue grew to look twice its real size. Check every relative
link you touch still resolves before committing.

---

## §9 — Hard rules

- Plain Croatian to the owner, always. The banned list in §5.1 is a list, not a hint.
- **The context turn (§5.0) happens before ANY question.** Item choice included. An owner
  who has to ask "what are you asking me?" was asked too early.
- **Never appeal to history the owner did not live through.** No dates, no "odobreno", no
  document names. Restate what the decision was, as new information, or leave it out.
- **Never name something as broken without the symptom and the proof** (§5.2b).
- **The explainer agent writes every user-facing decision text, including the options.**
  The orchestrator presents it verbatim and never writes a question itself (§5.0b).
- Explanation and question are **separate turns**. Never both in one.
- One feature at a time, one PR at a time, smallest step first.
- Never ask about something already shipped — check first, then say it exists.
- Never claim a gap without a grep behind it.
- Never invent work. "Everything in the queue is decided and merged" is a successful run.
- Never delete an artifact before its record is written and its knowledge relocated.
- Report honestly: what was built, what was skipped, what failed. A rejected feature and a
  blocked build are results, not embarrassments.
