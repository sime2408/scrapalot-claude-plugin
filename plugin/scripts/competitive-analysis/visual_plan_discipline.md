# PRD Authoring Standard — Visual-Plan Discipline

Distilled from BuilderIO's `visual-plan` skill (README + SKILL.md + references
`document-quality.md`, `wireframe.md`, `canvas.md`, `exemplar.md`,
github.com/BuilderIO/skills). The competitive-analysis PRD is a **visual review
surface a human can scan and approve**, not a wall of markdown prose. Apply this
to every PRD (`competitive_analysis_{product}.md` + its wireframes + the rendered
review surface). We adopt the *methodology*, rendered with our own pipeline — no
external Plan app/connector required.

## 1. Document discipline (the `.md` body)

- **Outcome-first, prose-first, self-contained, specific.** Open with the
  objective and what "done" means, the scope and non-goals, the approach with the
  key decisions and their rationale, ordered moves naming real files/symbols/
  RPCs/data shapes, risks, and a closing verification. Never ship a vague step
  ("make it work"); replace prose with specifics (`file:line`, RPC names).
- **Concrete snapshot before abstraction.** For a broad/strategic PRD, put ONE
  concrete "what this looks like in the app" snapshot (a wireframe + a sentence on
  what the user sees and what changes under the hood) near the top, *before* dense
  architecture, mode tables, or roadmaps. A reviewer who never saw the chat must
  get it from the top.
- **Reuse-first.** For each move, name what it **reuses** (existing RPC, table,
  component, service) *before* what it adds — so the plan explains the genuinely
  new delta, not what already exists. (This is also Rule #9 / as-built grounding.)
- **Decide the hard-to-reverse bets first.** Call out decisions expensive to undo
  once data/callers depend on them — wire format, public ids, data-model shape,
  auth & ownership boundaries — and get those right in the plan even if most ships
  later. Then scope the smallest first cut that proves the approach; state what is
  in and what is explicitly deferred.
- **Keep examples at the right altitude.** Separate the core abstraction from
  motivating examples and per-app adapters; label examples as examples unless the
  example is the whole requested scope.
- **Stand alone — no revision/changelog language.** Never write "preserve the
  prior plan", "unlike the previous version", "this revision", "as discussed
  above". Fold the right decisions into normal objective/architecture/roadmap
  prose. (Dated update notes at the very top are fine as provenance, but the body
  reads as one standalone proposal.)

## 2. Use the right block — and make it carry substance

Map each block to our markdown/HTML equivalent. Pick the block that carries the
most signal; never emit a block with only prose.

| Visual-plan block | Use it for | Our rendering |
|---|---|---|
| `diagram` | 2-D architecture / data-flow / state / ownership | a `mermaid` block **local to the claim it supports** |
| `annotated-code` | the file-map of load-bearing files | fenced code with line-anchored `file:line` margin notes; only files worth reading |
| `api-endpoint` / `openapi-spec` | a callable surface (tool/REST/gRPC contract) | a contract **table** (name → does → backing RPC → status) |
| `data-model` | schema / table shape | a fenced schema or table |
| `columns` | side-by-side before/after, option A vs B | a 2-col markdown table or paired blocks |
| `callout tone="decision"` | a **settled** decision | a bold "Decision:" line / blockquote |
| `tabs` | multiple states/comparisons | grouped sections (a tab that is prose-only = under-specified) |
| `question-form` "Open Questions" | genuinely-open decisions | the single bottom section (see §4) |

- **`diagram`: 2-D, local, not a left-to-right chain.** Prefer paired before/after
  panels, layered diagrams, swimlanes, dependency maps, matrices, grouped regions.
  Use a line only when the relationship is truly a sequence. Put each diagram
  **next to the recommendation it supports**, not all dumped in one section. Keep
  labels short so they never overlap nodes/connectors.
- **Recommendation rhythm (architecture/backend PRDs):** repeat a section shape —
  title → confidence/category badge → real `file:line` evidence → one local 2-D
  before/after or layered diagram → terse Problem / Solution / Why in the
  codebase's vocabulary.

## 3. Wireframes (the canvas)

The skill's existing Scrapalot design-system rules (sharp corners, `#09090B`/
`#3B82F6`, Inter, 4px grid, borders-over-shadows, 2px gradient accent, `--wf`-style
tokens) ARE our renderer — keep them. Fold in these visual-plan rules:

- **Match the real footprint — never default to desktop+mobile.** Choose the
  surface for what the user actually sees: a settings page = `desktop`/`browser`;
  a dropdown/menu = `popover`; an inspector/side panel = `panel`; only a genuinely
  mobile screen = `mobile`. A sidebar popover renders small, not a desktop page +
  a phone frame. Emit responsive pairs only when the layout truly changes.
- **Modify, don't redesign.** When the feature changes an existing Scrapalot
  screen, reproduce the current screen's real layout FIRST (read the actual
  component source), then change only the delta and call it out with one
  annotation. Compose net-new surfaces from the real app shell.
- **Keep product screens pure.** A wireframe shows the app state a user sees — do
  NOT embed file contracts, architecture arrows, repo pills, gRPC names, or
  implementation callouts inside the screen. Those go in the diagram, the document
  body, or a note beside the frame.
- **Real content, not lorem.** Real labels, counts, dates, button text grounded in
  the screen you read; never gray placeholder bars on a non-skeleton frame.
- **Icons, not icon-words.** Where the product shows an icon, draw an icon (inline
  SVG / icon badge), not the word "search"/"more".
- Each wireframe gets a short **"UX Rationale"** paragraph in the `.md` (what the
  user sees / can do / gets — use-case framing, no code/PR refs).

## 4. Open Questions — one bottom form, with recommended defaults

Surface genuinely-unresolved decisions (would change architecture, scope, UX, data
shape, or rollout) in a SINGLE bottom `## Open Questions` section — the ONLY place
they are enumerated. Each as a one-line question with 2-4 concrete options, each
with a short detail, and **mark the recommended default**. Do not scatter
mid-document forms for choices you have already settled (state those as decisions).
If you have committed to an approach, it is settled prose, not a question.

## 5. The unified visual review surface (the deliverable)

The point is a **scannable, commentable review surface**, not prettier prose. After
writing the `.md` + wireframes, render the whole PRD into ONE self-contained HTML
review page (markdown + rendered mermaid diagrams + inline wireframe PNGs, GitHub-
dark docs theme) with `render_prd.js`, and screenshot the key sections to verify it
reads top-to-bottom. This is our local equivalent of the Agent-Native Plan surface
— no external app, content stays private (important for PRDs with internal
`file:line` / security detail).

```
node ${CLAUDE_PLUGIN_ROOT}/scripts/competitive-analysis/render_prd.js <product_slug>
# → writes prd_<product>_review.html (self-contained) + prd_<product>_NN.png segments
```

## 6. Gate / discipline (carried from visual-plan)

- **Planning is read-only** until the user approves the direction.
- **Clarify vs. assume:** don't ask how to build it — explore and present the
  approach + options in the plan. Ask a clarifying question only when an ambiguity
  would change the design and you cannot resolve it from the code; batch 2-4. State
  other assumptions explicitly and proceed; keep anything truly open in the bottom
  Open Questions form with a recommended default.
- **Self-review pass** for high-stakes PRDs (architecture/data/multi-file): spawn
  one skeptical reviewer to find hard-to-reverse decisions made implicitly, steps
  not anchored in real files, option-menus where the plan should commit, and
  padding. Fix clear-cut issues; route genuine judgment calls to the Open Questions
  form. (This is the same adversarial-verify pattern already used elsewhere.)
