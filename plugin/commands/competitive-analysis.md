---
description: Analyze GitHub competitors — batch (auto-search by stars) OR single-repo strategy-first deep-dive when given a repo URL. Decides for itself whether the findings justify a PRD, and always states why.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList, AskUserQuestion
user-invocable: true
---

# Competitive Analysis — GitHub Open Source Discovery

Automatically search GitHub for competitor repos by stars, triage, deep-analyze, and generate PRD documents.

## File-naming law (binding — read before writing any file)

Every artifact this command produces has **exactly one** canonical path, defined in
`${CLAUDE_PLUGIN_ROOT}/skills/competitive-impl/SKILL.md` §1. Read that table
before the first `Write`. No alternates, no `_v2`, no dated copies, no per-session
variants, no invented directory.

`<slug>` = lowercase ASCII `[a-z0-9_]+` from the product or repo name (`owner/repo` →
`repo`), **underscores, never hyphens**, and byte-for-byte identical across the analysis,
the review HTML, the wireframes and the tracker line.

A file saved under any other name is lost work: a later session cannot find it, the index
points at nothing, and the queue stops reflecting reality. `/scrapalot:competitive-impl`
sweeps for strays and renames them, but that is a repair, not a licence.

## Input Parameter & Mode Detection

The argument `$ARGUMENTS` selects ONE of two modes — detect it before doing anything else:

| `$ARGUMENTS` looks like… | Mode | What happens |
|---|---|---|
| empty, or a **number** (e.g. `10`) | **BATCH** (default) | Search GitHub by stars, triage many, analyze up to N. Run Phases 1→6 below. |
| a **GitHub URL** (`https://github.com/owner/repo`) or **`owner/repo`** slug | **SINGLE-REPO DEEP-DIVE** | SKIP discovery/triage. Analyze exactly that one repo, with a deeper, strategy-first lens. Run the **Single-Repo Deep-Dive Workflow** section, then Phases 4→6. |

If the user passes a URL while invoking `/scrapalot:competitive-analysis`, do NOT treat it as a repo count and do NOT search GitHub — they want a focused deep-dive on that specific project. (This command does both modes; single-repo mode is just a branch. Formerly named `/scrapalot:competitive-analysis-batch`.)

In BATCH mode, `$ARGUMENTS` is the **maximum number of repos** to analyze (default: 10), searched sorted by **stars descending** and filtered by **recent push date**.

## Memory: Previously Analyzed Repos

Before starting, read the tracking file to avoid re-analyzing repos:
- **Tracking file**: `${CLAUDE_PROJECT_DIR}/.claude/competitive-analysis/analyzed_repos.txt`
- Each line = `<full_name>|<date_analyzed>|<verdict: relevant|irrelevant|skipped>`
- If this file doesn't exist, create it with a header comment
- **SKIP** any repo already listed as `relevant` or `irrelevant` in this file
- Only re-analyze repos marked `skipped` (those that failed previously)

## Scripts Available

Helper scripts are in `${CLAUDE_PLUGIN_ROOT}/scripts/competitive-analysis/`:
- `search_repos.sh <max_repos> [sort_by]` — Search GitHub for competitor repos (outputs JSON lines)
- `clone_repo.sh <full_name> [branch]` — Shallow clone to `/tmp/git/<owner>__<repo>`
- `extract_features.sh <clone_dir>` — Extract README, structure, configs from cloned repo

**ALWAYS use these scripts** — do NOT write custom search/clone commands inline.

## Single-Repo Deep-Dive Workflow (when `$ARGUMENTS` is a URL / `owner/repo`)

In this mode the goal is **not** "catalog every feature vs Scrapalot". It's: **understand the deeper capability this project signals and decide where Scrapalot should head because of it.** One repo, analyzed harder, with a strategy-first lens.

1. **Resolve + record**: derive `owner/repo` from the argument. Read `analyzed_repos.txt`. If already `relevant`/`irrelevant`, tell the user and ask whether to re-analyze anyway (the user explicitly named it, so default to YES — re-analyze and update the existing PRD rather than skipping). Append/refresh the `<full_name>|<date>|<verdict>` line.

2. **Clone + structure**: `clone_repo.sh owner/repo` then `extract_features.sh <clone_dir>`. Skip the relevance gate — the user already decided it's worth a look. (Still honor the size/star guardrails for sanity, but a user-named repo is never rejected on stars alone.)

3. **Deep code analysis (3–5 parallel agents over SUBSYSTEMS, not files)**: split the repo into coherent subsystems and launch one Agent per subsystem (max 5 concurrent). Each agent reads ACTUAL source (not just READMEs), cites `file:symbol`, and returns: concrete mechanisms, the *non-obvious* design decisions, and how each maps onto Scrapalot's architecture (Python gRPC / Kotlin / React / Neo4j / pgvector / Celery / Redis Streams). **Every agent must also return the five Decision Gate fields** (`already_in_scrapalot` with a mandatory grep, `measurable_via`, `new_dependencies`, `reversibility`, `cheaper_substitute` — defined in Phase 3 step 5) for each mechanism it proposes we adopt; without them the gate in step 4.5 has nothing to weigh. If an agent dies on a transient API error (429/529), retry it once or do that subsystem inline.

4. **Find the THESIS, not just the feature list.** A single-repo deep-dive must answer: *what is the one capability that makes this project matter, and what does adopting its spirit (not its code) unlock for Scrapalot?* Write this as a **"Strategic Direction for Scrapalot"** section near the top of the PRD — 3–5 plain-language paragraphs (Croatian-friendly framing per `feedback_plain_language_first.md`) that name the deeper bet, BEFORE the technical feature catalog. Examples of a thesis:
   - *Hermes Agent* → the thesis is the **agentic loop**: persistent memory + the flexibility to spin up purpose-built agents that run in a loop until a task is done. For Scrapalot that's the natural evolution of **deep research** and of **background Science research** — long-running autonomous investigations that keep working while the user focuses on something else, then surface results. Frame features around *that* direction (autonomy, memory, loop-until-done, background execution, self-improvement), not around "they have a Telegram bridge."
   - Always tie the thesis back to Scrapalot's existing moat (RAG, Neo4j graph, deep research, notes) and to where the user wants the product to go.

4.5. **Run the Decision Gate** (see the `## Decision Gate` section). A thesis worth naming
   does not automatically deserve a plan — a repo can matter, teach us something real, and
   still leave nothing worth building. Answer the seven questions against the agents' five
   fields, pick one of the three outcomes, and write the reasoning paragraph. **If the
   outcome is TASK or NOTHING, stop here**: write the NO-PRD log entry, skip steps 5–6 and
   Phases 4/5/5c, and go straight to Phase 6 for tracking + push. Report the thesis and the
   verdict to the user in plain language regardless — a well-argued "not worth a plan" is
   the successful ending of a deep-dive, and single-repo mode reaches it often, because the
   user usually names a repo out of curiosity rather than intent to build.

5. **Only when the gate returned PRD:** produce the full Phase 4 PRD (feature catalog, ranked top 10, NOT-worth, architecture comparison, advantages) **to the visual-plan discipline** (`${CLAUDE_PLUGIN_ROOT}/scripts/competitive-analysis/visual_plan_discipline.md`: outcome-first, reuse-first, hard-to-reverse bets first, right-block-real-substance, one bottom Open Questions form) — but keep every ranking subordinate to the thesis from step 4. Features that serve the strategic direction rank above incidental nice-to-haves even if the latter are lower effort. Continue to Phase 5 (wireframes + mermaid + the Phase 5c unified review surface) and Phase 6 (registry + push).

6. **Verify the thesis with the user.** After writing the PRD, surface the "Strategic Direction" thesis in your final summary and, if the direction is non-obvious or branches (e.g. "background Science agents" vs "interactive deep-research agents"), use AskUserQuestion to confirm which direction to emphasize — one question, plain-language options. Do not silently pick.

## Decision Gate — is a PRD justified?

**A PRD is an outcome, not a deliverable.** Both modes run this gate after the deep code
analysis and before writing anything. Most analyses should NOT end in a PRD — the default
is the cheapest artifact that carries the finding. Writing a PRD nobody asked for costs a
wireframe pass, a render pass, a commit and, worse, a `prd-competitive/` graveyard that
turns the index into broken links.

Answer all seven questions **in writing** before choosing an outcome. Each answer needs
evidence, not an impression: a `file:symbol` from a grep, a measured number, a named user
request. "Probably" on a question means the answer is NO.

| # | Question | Evidence required | If YES |
|---|---|---|---|
| 1 | **Do we already ship this?** | `Grep`/`Glob` hit in `scrapalot-chat/src/main/`, `scrapalot-ui/src/`, `scrapalot-backend/src/main/` | Not a PRD. The real gap is audience, exposure, or one sub-feature — write that as a task, not a plan |
| 2 | **Can the improvement be measured on infrastructure we already have?** | Name the harness (`tests/`, `/scrapalot:rag-test`, an existing eval set, a SQL count) | Continue. If NO → the honest first step is building the measurement, and THAT is the finding |
| 3 | **What does adopting it cost?** | New GPU, new container, new paid API, new dependency, ongoing maintenance | Cost drives the bar upward, it does not veto by itself |
| 4 | **Has anyone actually asked for it?** | A named user, a support thread, an observed failure in prod logs | Speculative demand is the single most common reason to NOT write a PRD |
| 5 | **Is it hard to reverse?** | Wire format, DB schema, public ids, auth/ownership, anything users see and keep | Hard-to-reverse RAISES the bar for a PRD and simultaneously makes a PRD the right vehicle if the bar is cleared |
| 6 | **Is this our job?** | Does it serve RAG / research / documents / the graph, or is it someone else's product | NO → record and move on |
| 7 | **Is there a 20%-effort substitute worth 80% of the benefit?** | Name it concretely | YES → ship the substitute as a task; the PRD is the wrong size |

### The three outcomes

Pick exactly one and **write one short paragraph of reasoning naming the questions that
decided it**. The reasoning is mandatory in every mode, including when the answer is a
full PRD — "I wrote a PRD" without a stated why is a gate failure.

1. **PRD** — the finding is multi-part, hard-to-reverse, or touches several services, AND
   questions 2 and 4 both answered YES. Run Phases 4 → 6 in full.
2. **TASK, no PRD** — the finding is real but is one concrete change (question 1 or 7
   answered YES, or the whole thing fits in a single commit). Do NOT build wireframes or a
   review surface. Write the task into the NO-PRD log below, and offer to implement it.
3. **NOTHING** — the finding does not survive the gate. Log the reason and stop. This is a
   successful analysis, not a failed one.

For outcomes 2 and 3, append one entry to
`/opt/scrapalot/scrapalot-chat/docs/prd-competitive/NO_PRD_LOG.md` (create with a heading
if missing) in this shape, and skip Phases 4, 5, 5c entirely:

```markdown
## <owner/repo> — <YYYY-MM-DD> — <TASK|NOTHING>
**Thesis**: <the one capability that made this project worth reading, one sentence>
**Verdict**: <which of the seven questions decided it, with the evidence>
**If TASK**: <the single concrete change, with the file(s) it touches>
```

Then still run Phase 6 for the tracking file and the push — the log entry is the
deliverable in place of the PRD. Record the verdict as `relevant` (a real finding, no PRD)
or `irrelevant` in `analyzed_repos.txt`, and append `|no-prd:<reason-tag>` so a later run
can see why. Reason tags: `already-shipped`, `unmeasurable`, `no-demand`, `out-of-scope`,
`cheaper-substitute`, `cost-exceeds-benefit`.

### Surfacing it to the user

Report the outcome in plain language before doing the work, per
`feedback_plain_language_first.md`: what the project does that matters, what it would cost
us, and why it does or does not deserve a plan. When the gate is genuinely close — a real
finding whose demand is unproven — use AskUserQuestion with the recommendation first,
rather than defaulting to a PRD to look productive.

## Workflow (BATCH mode)

### Phase 1: Discovery (search GitHub)

1. Run `search_repos.sh $ARGUMENTS stars` to find repos
2. Parse the JSON output — each line is a repo object with: `full_name`, `html_url`, `description`, `stargazers_count`, `pushed_at`, `language`, `topics`
3. Filter out repos already in `analyzed_repos.txt`
4. Sort remaining by `stargazers_count` descending
5. Create a task list with all repos to analyze

### Phase 2: Triage (README evaluation)

For each repo, run IN PARALLEL (use Agent tool, max 5 concurrent):

1. Run `clone_repo.sh <full_name>` to get the clone path
2. Read the README.md from the clone path (first 500 lines)
3. **Evaluate relevance** — is this project a PRODUCT (not framework/library) in a similar domain to Scrapalot?

Scrapalot is a **full-stack enterprise RAG platform** with:
- 19 RAG strategies + 11 orchestrators + 16 agentic agents
- Tri-modal fusion search (dense + sparse + graph)
- Deep research (5-phase, multi-agent, 49 streaming packets)
- 16 chunking strategies, document processing (Docling + RapidOCR)
- Knowledge graph (Neo4j, 6 entity types)
- Multi-provider LLM support (10 providers via Pydantic AI)
- Collaborative notes (TipTap + Y.js)
- PDF/EPUB/DOCX viewers with annotations
- 10 data connectors + external book providers
- Stripe billing, multi-workspace, admin panel
- React + Kotlin + Python + Gateway microservice architecture

**Relevant if** the project is a PRODUCT doing ANY of:
- RAG / retrieval augmented generation platform
- AI research assistant / document QA system
- AI-powered enterprise search
- Knowledge management + AI
- AI assistant with document understanding
- Deep research / AI scientist system
- Text editor / writing tool (rich text, markdown, collaborative editing, AI-assisted writing)
- Science / academic tool (lab notebooks, bibliography, reference managers, experiment tracking)
- Chat / messaging platform (team chat, AI chat, real-time collaboration)
- Collaboration tool (shared workspaces, real-time co-editing, project management for teams)
- Note-taking with AI or knowledge graph features
- Document management / digital workspace

**Irrelevant if**:
- Framework/library (LangChain, AutoGen, GraphRAG, LightRAG, etc.)
- Tool we already use (Firecrawl, Crawl4AI, PaperQA2)
- Simple chatbot wrapper or LLM API wrapper
- Pure CLI tool with no UI/UX
- Unrelated domain (gaming, IoT, DevOps, monitoring, etc.)
- Code editor / IDE (VS Code, Zed, etc. — not our domain)

3. Record verdict in `analyzed_repos.txt`

### Phase 3: Deep Analysis (parallel agents)

For each **relevant** repo, launch an Agent to do EXHAUSTIVE code analysis:

1. Run `extract_features.sh <clone_dir>` to get structural overview
2. **Read actual source files** — not just directory listings:
   - Read ALL service/controller/route files
   - Read ALL RAG/retrieval/chunking/agent code
   - Read ALL frontend component directories
   - Read config/prompt files
3. **Extract EVERY feature** with source file reference
4. For each MISSING/PARTIAL feature vs Scrapalot, describe:
   - What it does (2-3 sentences from code)
   - How it could integrate into Scrapalot UI (specific placement)
   - Which Scrapalot service would own it
   - Effort estimate (XS/S/M/L/XL)
5. **Return the five Decision Gate fields for every feature** (the agent, not the
   orchestrator, does this — it is the one that read the code). An agent that returns a
   feature list without these fields has not finished; send it back:
   - `already_in_scrapalot` — `file:symbol` proving we ship it, or the literal `none`.
     **The grep is mandatory before writing `none`** (`feedback_competitive_analysis.md` §3:
     three separate "we don't have X" claims turned out false). Search
     `scrapalot-chat/src/main/`, `scrapalot-ui/src/components/`, `scrapalot-backend/src/main/`.
   - `measurable_via` — the existing harness that would show this working
     (`tests/integration/...`, `/scrapalot:rag-test`, a SQL count, an eval set), or `none`
     if no current tooling can tell better from worse.
   - `new_dependencies` — GPU, container, paid API, library, ongoing maintenance, or `none`.
   - `reversibility` — `easy` or `hard`, naming what gets locked in (wire format, schema,
     public ids, stored user data).
   - `cheaper_substitute` — a 20%-effort version worth most of the benefit, or `none`.
6. Rank features by impact × feasibility
7. List features NOT worth implementing (and why)

### Phase 3.5: Decision Gate (mandatory, both modes)

Run the `## Decision Gate` section against what the agents returned, per repo. Only repos
whose gate returned **PRD** continue to Phase 4. Repos that returned **TASK** or **NOTHING**
get a NO-PRD log entry and jump straight to Phase 6. In BATCH mode this is where most repos
should stop — analyzing ten repos and writing ten PRDs means the gate was not applied.

### Phase 4: Write Results — visual-plan discipline

**Only for repos whose Decision Gate returned PRD.** The gate's reasoning paragraph goes in
the PRD immediately under the Executive Summary, as a `## Why this deserves a plan` section
naming the questions that carried it — a reader who disagrees with the reasoning can then
reject the whole plan in one step instead of reading forty features first.

**READ FIRST:** `${CLAUDE_PLUGIN_ROOT}/scripts/competitive-analysis/visual_plan_discipline.md`. The PRD is a **scannable visual review surface a human can approve**, not a wall of prose. Author the `.md` to that standard (it adapts BuilderIO's `visual-plan` methodology to our pipeline).

For each analyzed repo, create/update:
```
/opt/scrapalot/scrapalot-chat/docs/prd-competitive/competitive_analysis_{product_name}.md
```

Include: Executive Summary, Complete Feature Catalog (each feature with integration description), Ranked Top 10, NOT worth implementing, Architecture Comparison, Scrapalot Advantages — but write them to the discipline:
- **Outcome-first + reuse-first + concrete snapshot near the top** before abstraction; name what each feature **reuses** (existing RPC/table/component) before what it adds; decide the **hard-to-reverse bets** (wire format, public ids, data-model, auth/ownership) explicitly.
- **Right block, real substance** (`visual_plan_discipline.md` §2): a callable surface → a contract **table** (name → does → backing RPC → status); a load-bearing file → line-anchored `file:line` notes; a settled choice → a **Decision:** line; each diagram **local to the claim it supports**, 2-D not a left-to-right chain.
- **Self-contained** — no "revision of the prior chat" language in the body (dated provenance note at the very top is fine).
- **One bottom `## Open Questions`** form for genuinely-open decisions, each with 2-4 options and a **recommended default** (§4) — the ONLY place they are enumerated.
- For high-stakes PRDs run the cheap **self-review pass** (§6) — one skeptical reviewer finds implicit hard-to-reverse decisions, unanchored claims, option-menus that should commit, and padding.

### Phase 5: Generate Wireframes + Mermaid Use Case Diagrams

For each analyzed product, produce **both** of these artifacts:

1. **2-3 HTML wireframe mockups (pixel-accurate PNG)** — 1:1 mockups of how the top features would look inside Scrapalot's actual UI. These MUST look like real production screens — NOT generic dark-theme mockups. Before drawing, read the relevant Scrapalot component source files so the wireframe matches current reality (toolbar icons, section labels, spacing). Wireframes answer **"what does the screen look like?"**.

2. **Mermaid use case diagrams** — flowcharts showing **how** the competitor's features activate inside Scrapalot's existing UI surfaces (chat toolbar → popover → panel, notes selection → AI action → gRPC → result panel, etc.). Append these as a `## Use Case Diagrams` section in the product's `.md` file OR to `/opt/scrapalot/scrapalot-chat/docs/prd-competitive/USE_CASE_DIAGRAMS.md`. Use `mermaid` fenced code blocks with `flowchart TD`. Mermaid diagrams answer **"which screen and which button triggers this feature?"**.

**Rule**: wireframes and mermaid diagrams are complementary, not interchangeable. Wireframes = 1:1 screen mockups. Mermaid = abstract flow/trigger relationships. Never use wireframes to draw flow diagrams, and never use mermaid to draw screens.

**Visual-plan wireframe discipline** (`visual_plan_discipline.md` §3): **match the real footprint** — a settings page = desktop/browser, a dropdown = popover, an inspector = side panel; never default to a desktop+mobile pair. **Modify, don't redesign** — reproduce the current Scrapalot screen's real layout FIRST (read the actual component source), then change only the delta and annotate it. **Keep screens pure** — no file contracts, gRPC names, repo pills, or architecture arrows inside a product screen (those go in the mermaid diagram or the document body). **Icons, not icon-words**; real labels/counts/dates, never gray placeholder bars. **Diagrams local to the claim**: place each mermaid diagram next to the recommendation it supports (2-D layout, not a left-to-right chain), not all dumped in one section.

**Scrapalot UI layout context**:
- Left sidebar: session list, folders, new chat button
- Main area: chat messages with citations, streaming responses
- Below input: toolbar (provider selector, knowledge stacks popover, search options, settings, prompts, attach)
- Notes drawer: slides from right, TipTap rich text editor with AI actions
- Knowledge panel: collection list, document grid, file uploader
- PDF/EPUB/DOCX viewers: slide-out drawer with annotations
- Admin panel: tabs for users, settings, tracing
- Deep research: multi-phase streaming panel with progress + sections

**For each wireframe**:
1. Create an HTML file at `/opt/scrapalot/scrapalot-chat/docs/prd-competitive/wireframes/{product}_{feature}.html`
2. Render to PNG using the Playwright render script (see below)
3. Add image reference in the product's `.md` file under `## Wireframes`

**CRITICAL: Scrapalot Design System Rules** (from `scrapalot-ui/docs/README_STYLE.md`):

All wireframes MUST follow these rules exactly. Do NOT use generic dark theme colors.

```css
/* ─── DARK THEME (default for wireframes) ─── */
--background: #09090B;           /* Main background (zinc-950) */
--foreground: #FAFAFA;           /* Main text (zinc-50) */
--card: #09090B;                 /* Card background */
--muted: #27272A;                /* Muted backgrounds (zinc-800) */
--muted-foreground: #71717A;     /* Secondary text (zinc-500) */
--border: #27272A;               /* Borders (zinc-800) */
--primary: #3B82F6;              /* Blue accent (default, hsl 217 91% 60%) */
--primary-foreground: #1E293B;   /* Text on primary */
--destructive: #EF4444;          /* Red */
--success: #10B981;              /* Green */
--warning: #F59E0B;              /* Amber */

/* ─── TYPOGRAPHY ─── */
font-family: Inter, system-ui, -apple-system, sans-serif;

/* ─── BORDER RADIUS: NONE ─── */
/* Scrapalot uses SHARP CORNERS on everything (no rounded-md/lg/xl) */
/* ONLY rounded-full (9999px) for circular elements like avatars */
border-radius: 0;

/* ─── SPACING: 4px grid ─── */
/* All spacing in multiples of 4: 4, 8, 12, 16, 20, 24, 32, 40, 48 */

/* ─── BORDERS OVER SHADOWS ─── */
/* Use border: 1px solid #27272A — NOT box-shadow */

/* ─── ACCENT LINES ─── */
/* 2px gradient lines at top of cards: background: linear-gradient(to right, #3B82F6, rgba(59,130,246,0.3), transparent) */

/* ─── ICON BADGES ─── */
/* 32x32px squares with bg: rgba(59,130,246,0.1), icon centered inside */

/* ─── LABELS ─── */
/* Section labels: 10px, font-weight: 600, uppercase, letter-spacing: 0.1em, color: #71717A */

/* ─── BUTTONS ─── */
/* Primary: bg #3B82F6, text #1E293B, no border-radius */
/* Secondary: bg transparent, border 1px solid #27272A, text #71717A, hover text #FAFAFA */

/* ─── HOVER STATES ─── */
/* Cards: border-color transitions from #27272A to #3F3F46 */
/* Text: color transitions to #3B82F6 (primary) */
```

**Layout conventions**:
- Stat grids use layered backgrounds (`rgba(39,39,42,0.3)` with `border: 1px solid rgba(39,39,42,0.5)`)
- Section lists have 2-digit mono numbering (font: monospace, color: `rgba(113,113,122,0.6)`)
- Tags/badges: `background: rgba(39,39,42,0.5); border: 1px solid rgba(39,39,42,0.3); font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em`
- Confidence bars: inline colored fill (`#10B981` >=80%, `#F59E0B` >=50%, `#EF4444` <50%)
- Empty states: centered icon (32x32, muted) + text below
- Tabs: active = primary color text + 2px bottom border, inactive = muted-foreground

**Render script** (`/tmp/wireframes/render.js` — create if not exists):
```javascript
const { chromium } = require('/opt/scrapalot/scrapalot-ui/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const OUT_DIR = '/opt/scrapalot/scrapalot-chat/docs/prd-competitive/wireframes';
async function render(htmlFile, outName, width = 900) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height: 800 } });
  await page.setContent(fs.readFileSync(htmlFile, 'utf-8'));
  await page.waitForTimeout(300);
  const body = await page.$('body');
  const box = await body.boundingBox();
  await page.setViewportSize({ width, height: Math.ceil(box.height) + 40 });
  await page.screenshot({ path: path.join(OUT_DIR, outName), fullPage: true, type: 'png' });
  await browser.close();
  console.log('done: ' + outName);
}
async function main() {
  const dir = OUT_DIR;
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));
  for (const f of files) await render(path.join(dir, f), f.replace('.html', '.png'));
}
main().catch(console.error);
```
Run: `node /tmp/wireframes/render.js`

**Wireframe quality checklist**:
- [ ] Sharp corners on ALL elements (no border-radius except circular avatars)
- [ ] Correct dark theme colors from the CSS variables above
- [ ] Inter font loaded from Google Fonts CDN
- [ ] 4px spacing grid
- [ ] Borders (1px solid #27272A), NOT shadows
- [ ] 2px gradient accent line at top of feature cards
- [ ] Realistic data (not "Lorem ipsum")
- [ ] Watermark: "Scrapalot AI — {Feature Name} (inspired by {Product})"
- [ ] Include a "UX Rationale" paragraph after each wireframe in the .md file

### Phase 5c: Render the unified visual review surface (the deliverable)

The point of visual-plan is a **scannable review surface**, not prettier prose. After the `.md` + wireframes are written, render the whole PRD into ONE self-contained HTML review page (markdown + rendered mermaid + inline base64 wireframes, GitHub-dark docs theme) and screenshot it to verify it reads top-to-bottom:

```bash
node ${CLAUDE_PLUGIN_ROOT}/scripts/competitive-analysis/render_prd.js {product_slug}
# → prd-competitive/prd_{slug}_review.html  (portable single file — scp it, open locally; private)
# → prd-competitive/prd_{slug}_NN.png        (~2600px segments to eyeball the flow)
```

Read 2-3 segment PNGs to confirm: mermaid diagrams render as real flowcharts (not raw code), wireframes appear inline, tables/code/blockquotes are styled, the concrete snapshot sits near the top, and the Open Questions form is at the bottom. The self-contained `_review.html` is **committed in the PRD directory** (Phase 6) as the persistent visual review surface — the repo is private, so it stays private. Open it locally (or `scp` it); it is NOT meant for a PUBLIC docs site.

### Phase 6: Update Registry & Push

**When the gate returned TASK or NOTHING**, this phase is short: commit the `NO_PRD_LOG.md`
entry and the updated `analyzed_repos.txt` line (with its `|no-prd:<reason-tag>`), print the
verdict and reasoning, and stop. Do not touch `prd-competitive/README.md` — nothing was
added to the index. If the outcome was TASK, end by offering to implement it, without
starting the work uninvited.

**When the gate returned PRD**, run the full sequence:

1. Update `prd-competitive/README.md` with new products and status
2. Update `analyzed_repos.txt` with results
3. **Commit and push** all files (wireframe HTML + PNG; the PRD `.md`; **and the `prd_{slug}_review.html` visual review surface** — the repo is private, so this self-contained rendered plan is committed *in the PRD directory for review*). Keep only the `prd_{slug}_*.png` segment screenshots local (regenerable eyeball checks — gitignore `docs/prd-competitive/prd_*[0-9].png`). NEVER publish a PRD carrying internal `file:line` / security detail to a PUBLIC site.
4. Print final summary, and surface the committed `_review.html` path so the user can open the visual plan.

## Guardrails

- **DO NOT** analyze repos with < 20 stars
- **DO NOT** clone repos larger than 500MB
- **DO NOT** re-analyze repos already in `analyzed_repos.txt` (unless `skipped`)
- **DO NOT** include frameworks/libraries — only products
- **ALWAYS** clean up `/tmp/git/` clones after analysis
- **ALWAYS** update `analyzed_repos.txt` after each repo
- **MAX 5 parallel agents** at a time
- **NEVER write a PRD without stating why** — the Decision Gate reasoning paragraph is
  mandatory in all three outcomes, and lands in the PRD as `## Why this deserves a plan`
- **NEVER claim a gap without a grep** — `already_in_scrapalot` must carry a `file:symbol`
  or a searched-and-found-nothing `none`
- **DEFAULT to no PRD.** A deep-dive that ends in a logged reason is a finished analysis.
  Producing a plan for every repo analyzed is the failure mode this gate exists to stop
