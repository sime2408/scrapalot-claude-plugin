---
description: Analyze closed-source SaaS competitors via their websites, docs, and feature pages
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
user-invocable: true
---

# Competitive Analysis — Closed-Source SaaS Products

Analyze closed-source commercial products by scraping their websites, documentation, feature pages, pricing, changelogs, and help centers. Extract feature ideas for Scrapalot.

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

## Input Parameter

The argument `$ARGUMENTS` controls which products to analyze:
- If empty/omitted: analyze ALL products from the registry that haven't been analyzed yet
- If a number (e.g. `5`): analyze up to N unanalyzed products
- If a product name (e.g. `elicit`): analyze that specific product (even if already done — forces re-analysis)

## Memory: Previously Analyzed Products

Before starting, read the tracking file to avoid re-analyzing:
- **Tracking file**: `${CLAUDE_PROJECT_DIR}/.claude/competitive-analysis/analyzed_closed_source.txt`
- Each line = `<product_slug>|<date_analyzed>|<status: done|failed|skipped>`
- If this file doesn't exist, create it with a header comment
- **SKIP** any product already listed as `done` (unless forced by name in $ARGUMENTS)

## Product Registry

These are the closed-source SaaS products to analyze. Grouped by domain relevance to Scrapalot.

### Tier 1: Direct Feature Competitors (AI Research & Document Intelligence)

| Slug | Product | Website | Domain |
|------|---------|---------|--------|
| `elicit` | Elicit | https://elicit.com | AI research assistant, literature review, data extraction |
| `scispace` | SciSpace (Typeset) | https://typeset.io | AI reading copilot, paper understanding, citations |
| `consensus` | Consensus | https://consensus.app | AI search engine for scientific papers |
| `scite` | Scite | https://scite.ai | Smart citations, citation context analysis |
| `researchrabbit` | ResearchRabbit | https://researchrabbit.ai | Paper discovery, citation graph visualization |
| `litmaps` | Litmaps | https://litmaps.com | Literature mapping, citation networks |
| `inciteful` | Inciteful | https://inciteful.xyz | Citation network analysis, paper discovery |
| `paperpal` | Paperpal | https://paperpal.com | AI academic writing assistant |
| `semantic-scholar` | Semantic Scholar | https://semanticscholar.org | AI-powered academic search engine |
| `connected-papers` | Connected Papers | https://connectedpapers.com | Visual paper exploration graph |

### Tier 2: AI Writing & Editing Tools

| Slug | Product | Website | Domain |
|------|---------|---------|--------|
| `notion-ai` | Notion AI | https://notion.so | AI workspace, notes, docs, knowledge management |
| `jasper` | Jasper | https://jasper.ai | AI writing assistant, content generation |
| `copy-ai` | Copy.ai | https://copy.ai | AI copywriting, workflow automation |
| `writesonic` | Writesonic | https://writesonic.com | AI writing + chat + search |
| `grammarly` | Grammarly | https://grammarly.com | AI writing assistant, grammar, tone |
| `quillbot` | QuillBot | https://quillbot.com | AI paraphrasing, summarization, grammar |
| `lex` | Lex | https://lex.page | AI-native writing editor |
| `sudowrite` | Sudowrite | https://sudowrite.com | AI creative/fiction writing |
| `jenni-ai` | Jenni AI | https://jenni.ai | AI writing assistant for academics |
| `wordtune` | Wordtune | https://wordtune.com | AI rewriting, summarization |

### Tier 3: AI Chat & Knowledge Platforms

| Slug | Product | Website | Domain |
|------|---------|---------|--------|
| `perplexity` | Perplexity | https://perplexity.ai | AI search + deep research + citations |
| `you-com` | You.com | https://you.com | AI search, research mode, code |
| `chatpdf` | ChatPDF | https://chatpdf.com | Chat with PDF documents |
| `humata` | Humata | https://humata.ai | AI document analysis, Q&A |
| `unriddle` | Unriddle | https://unriddle.ai | AI reading copilot, research assistant |
| `afforai` | Afforai | https://afforai.com | AI document chat, cross-reference |
| `docanalyzer` | DocAnalyzer | https://docanalyzer.ai | AI document analysis |
| `notebooklm` | NotebookLM | https://notebooklm.google.com | Google's AI notebook, audio overview |

### Tier 4: Collaboration & Team Knowledge

| Slug | Product | Website | Domain |
|------|---------|---------|--------|
| `clickup` | ClickUp | https://clickup.com | Project management + AI + docs |
| `coda` | Coda | https://coda.io | All-in-one doc + spreadsheet + AI |
| `slite` | Slite | https://slite.com | AI-powered team knowledge base |
| `guru` | Guru | https://getguru.com | AI enterprise knowledge management |
| `mem` | Mem | https://mem.ai | AI-powered self-organizing workspace |
| `craft` | Craft | https://craft.do | AI document editor, collaboration |
| `scrintal` | Scrintal | https://scrintal.com | Visual knowledge management, mind mapping |
| `heptabase` | Heptabase | https://heptabase.com | Visual note-taking for learning |

### Tier 5: Science & Lab Tools (Non-AI)

| Slug | Product | Website | Domain |
|------|---------|---------|--------|
| `benchling` | Benchling | https://benchling.com | Cloud lab notebook, biotech R&D |
| `labarchives` | LabArchives | https://labarchives.com | Electronic lab notebook |
| `protocols-io` | Protocols.io | https://protocols.io | Open method sharing, lab protocols |
| `readcube` | ReadCube Papers | https://readcube.com | Reference manager, PDF reader |
| `endnote` | EndNote | https://endnote.com | Reference management, bibliography |
| `r-discovery` | R Discovery | https://discovery.researcher.life | AI paper recommender |

## Workflow

### Phase 1: Select Products

1. Read `analyzed_closed_source.txt`
2. Filter based on `$ARGUMENTS` (all unanalyzed, N unanalyzed, or specific product)
3. Create task list

### Phase 2: Deep Scrape (parallel agents, max 3 concurrent)

For each product, launch an Agent that does:

1. **WebSearch** for `"<product> features"`, `"<product> pricing"`, `"<product> changelog"`, `"<product> documentation"`
2. **WebFetch** these pages from the product website (in order of priority):
   - Main landing/features page (e.g. `https://example.com/features` or homepage)
   - Pricing page (e.g. `https://example.com/pricing`)
   - Documentation/help center root (e.g. `https://docs.example.com` or `https://example.com/docs`)
   - Changelog/what's new page (e.g. `https://example.com/changelog`)
   - Blog (latest 2-3 posts about features, e.g. `https://example.com/blog`)
   - Integration/API docs page if available
3. **WebSearch** for `"<product> review"`, `"<product> vs <competitor>"` to find third-party reviews with detailed feature breakdowns
4. **WebFetch** 2-3 top review/comparison articles

**IMPORTANT**: Be thorough. Scrape at least 5-8 pages per product. Don't stop at the homepage — dig into docs, help center articles, feature sub-pages. The goal is to find EVERY feature, not just the marketing headlines.

### Phase 3: Feature Extraction & Comparison

For each product, extract and categorize EVERY feature into:

**Feature Categories** (map to Scrapalot's architecture):
1. **Document Processing** — upload, parsing, OCR, format support
2. **Search & Retrieval** — RAG strategies, semantic search, filtering
3. **AI/LLM Features** — chat, summarization, writing assistance, agents
4. **Knowledge Graph** — entity extraction, relationships, visualization
5. **Collaboration** — real-time editing, sharing, comments, teams
6. **Editor/Writing** — rich text, markdown, templates, formatting
7. **Citations & References** — bibliography, citation styles, linking
8. **Visualization** — charts, graphs, knowledge maps, mind maps
9. **Integrations** — connectors, API, import/export, plugins
10. **UX/UI Patterns** — onboarding, navigation, mobile, accessibility
11. **Billing & Plans** — pricing tiers, usage limits, enterprise features
12. **Unique/Novel** — features that don't fit above categories

For each feature, assess:
- **Scrapalot status**: `has` / `partial` / `missing`
- **Integration idea**: Where in Scrapalot UI + which service owns it
- **Effort**: XS (< 1 day) / S (1-3 days) / M (3-7 days) / L (1-3 weeks) / XL (> 3 weeks)
- **Impact**: Low / Medium / High / Critical

### Phase 4: Write Analysis Document

Create/update:
```
/opt/scrapalot/scrapalot-chat/docs/prd-competitive/competitive_analysis_{product_slug}.md
```

Document structure:
```markdown
# Competitive Analysis: {Product Name}

**Type**: Closed-source SaaS
**Website**: {url}
**Analyzed**: {date}
**Domain**: {domain description}

## Executive Summary
2-3 paragraphs: what they do, who they target, what makes them unique, how they compare to Scrapalot.

## Pricing
| Plan | Price | Key Limits |
|------|-------|------------|
(extract from pricing page)

## Complete Feature Catalog

### {Category Name}
| # | Feature | Description | Scrapalot Status | Integration Idea | Effort | Impact |
|---|---------|-------------|-----------------|------------------|--------|--------|

(repeat for each category)

## Top 10 Features Worth Adopting
Ranked by impact × feasibility. For each:
1. **Feature name** — What it does (2-3 sentences)
   - **Where in Scrapalot**: Specific UI placement + service
   - **Effort**: XS/S/M/L/XL
   - **Why**: User value proposition

## Features NOT Worth Implementing
List with reasoning (too niche, wrong audience, requires proprietary data, etc.)

## UX/Design Inspiration
Screenshots descriptions, interaction patterns, navigation ideas worth borrowing.

## Scrapalot Advantages
Features where Scrapalot is clearly ahead of this product.
```

### Phase 5: Generate Wireframes

For each analyzed product, create **2-3 HTML wireframe mockups** showing how the top features would look integrated into Scrapalot's actual UI. Wireframes must be **pixel-accurate** to the real Scrapalot design system — NOT generic dark-theme mockups.

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

### Phase 6: Update Registry & Push

1. Update `prd-competitive/README.md` — add product to the **Closed-Source SaaS Competitors** section
2. Update `analyzed_closed_source.txt` with result
3. **Commit and push** all new/updated files (including wireframe HTML + PNG) to git (scrapalot-chat repo)
4. Print summary: products analyzed, top features found, total new feature ideas

## Guardrails

- **DO NOT** re-analyze products already marked `done` (unless forced by name)
- **DO NOT** scrape login-required pages — only public content
- **DO NOT** copy marketing copy verbatim — extract features in your own words
- **ALWAYS** verify features from multiple sources (not just homepage marketing)
- **ALWAYS** update tracking file after each product
- **MAX 3 parallel agents** (web scraping is slower than git clone)
- **ALWAYS** include pricing information — helps understand market positioning
- If a website blocks scraping (403/captcha), mark as `failed` in tracking file and move on
