---
name: design
description: >
  Make Scrapalot look better one screen at a time, and prove it: capture, judge, fix, capture
  again. Two worlds with opposite goals. PUBLIC pages (home, pricing, about, contact, desktop,
  shop, blog, legal, login, sign-up) should be distinctive and art-directed. The APP (chat,
  knowledge, notes, settings, admin, everything behind the login) should be calm, simple,
  accessible and consistent. Measures instead of guessing: a Playwright capture at real widths,
  themes and accents with axe and Impeccable findings, plus a source lint for the house rules.
  Use for any request to review, polish, simplify, align, make accessible, reword, adapt to
  mobile, make bolder or quieter, or animate a Scrapalot page, and to audit an animation
  (a ranked list of everything that feels off, worst first); motion follows
  scrapalot-ui/docs/README_MOTION.md. Invoked as /scrapalot:design [command] [screen]. Replaces scrapalot:landing-design. For building new product components use
  scrapalot:ui-component-developer alongside it.
argument-hint: "[review|polish|distill|align|a11y|clarify|adapt|explore|bolder|quieter|motion|motion-audit|3d] [screen]"
---

# Design

One skill, two worlds. Outside the login, a page has to earn attention and make a reader
act, so it gets a point of view, art direction and one memorable moment. Inside, a person is
in the middle of a task, so the screen should disappear into it: fewer things, the same things
in the same places, readable by everyone. Most bad design decisions here come from applying
one world's instincts to the other.

The work is always the same loop: capture the screen as it is, judge it, change it in a
worktree, capture the local build, compare, ship. Nothing is "better" until the second
capture says so.

## 1. Pick the world

| World | Screens | Lens | Read before editing |
|---|---|---|---|
| **Public** | `/`, `/home`, `/pricing`, `/about`, `/contact`, `/desktop`, `/shop`, `/buy-license`, `/blog`, `/privacy`, `/terms`, `/login`, `/sign-up`, `/invite`, `/team-invite`, `/delete-account`; `src/components/landing/`, `src/styles/landing.css` | persuade: creativity with honesty | [references/public.md](references/public.md) |
| **App** | everything else: dashboard, chat, knowledge stacks and library, notes, research, settings, providers, admin inspector, dialogs and drawers | operate: tidy, simple, accessible, consistent | [references/app.md](references/app.md) |

The list is `PUBLIC_PATHS` in `scrapalot-ui/src/lib/navigation.ts`; that file wins if they
differ. `/login` and `/sign-up` are public in voice but their forms follow the app's
discipline (labels, errors, focus). A shared conversation (`/shared/*`) is public but reads
like the app, so it takes the app lens. Load one lens per task, never both at once.

## 2. Commands

`/scrapalot:design <command> <screen>`. A screen is a name the capture knows
(`home`, `pricing`, `settings`, `settings-account`, `library`, `notes`, `admin`, ... — the full
list is `scrapalot-ui/tests/e2e/design/surfaces.ts`) or a path starting with `/`.

| Command | World | What it does | Edits? |
|---|---|---|---|
| *(none)* | both | Looks at what changed recently and at the last runs, and recommends two or three next commands with the exact line to type. Never runs one by itself. | no |
| `review` | both | Capture, lint, judge; a scored report ranked P0–P3 with screenshots. | no |
| `polish` | both | Fixes what a review found, inside the existing system. Refinement, never a hidden redesign. | yes |
| `distill` | app | Removes what does not earn its place: duplicate actions, repeated text, decoration, needless containers. | yes |
| `align` | app | Puts the screen back on the shared components and tokens, so the same thing looks and behaves the same everywhere. | yes |
| `a11y` | both | Contrast in every theme and accent, keyboard and focus, names for icon buttons, target size, zoom, reduced motion, landmarks. | yes |
| `clarify` | both | Rewrites labels, empty states and errors in all six locales. | yes |
| `adapt` | both | Phone and tablet layout, touch targets, scrolling. | yes |
| `explore` | public | Three materially different directions for a page or section; the owner picks one, then it is built. | after the pick |
| `bolder` | public | Raises one flat section to the conviction the rest of the page already has, in its own vocabulary. | yes |
| `quieter` | both | Tones down what is loud: saturation, weight, motion, decoration. | yes |
| `motion` | public (app: state changes only) | One authored motion moment, or purposeful state transitions, by `scrapalot-ui/docs/README_MOTION.md`. | yes |
| `motion-audit` | both | Plays the screen's motion for real (full speed, 10–25 %, frame by frame, reduced motion, phone) and returns a ranked list of everything that feels off, worst first, each with the rule it breaks and the fix, then a block or approve verdict (README_MOTION.md §9, Apple's fluid-interface rules). | no |
| `3d` | public | A procedural Three.js centrepiece rebuilt from a reference image. Proposal first. | after approval |

The playbook for each command is in the world's reference file. Free text after the screen
narrows it: `/scrapalot:design polish settings typography only`.

**No argument.** Run `git -C "${CLAUDE_PROJECT_DIR}/scrapalot-ui" log --since=10.days --name-only
--format= -- src/components src/pages src/styles | sort | uniq -c | sort -rn | head`, list
`${CLAUDE_PROJECT_DIR}/.claude/design/runs/` newest first, and recommend two or three commands:
a `review` of a screen that changed and was never captured, a `polish` of the last review's
open P0/P1 items, an `a11y` pass when the last run shows contrast or naming failures. One line
of reason each. The user types the one they want.

## 3. The loop

Every command that edits runs this loop. `review` stops after step 4.

1. **Read the world.** `scrapalot-ui/docs/README_STYLE.md` (design system), the screen's
   components, `scrapalot-ui/CLAUDE.md` rules 9–30, and the lens file. Before designing,
   generating or animating anything that moves, `scrapalot-ui/docs/README_MOTION.md` in full:
   it decides whether something may move at all, and how. The capture's findings
   name source locations: the build stamps elements with `data-scr-src="<file>.tsx:<line>:<col>"`
   (for the superadmin code agent) and axe examples quote it. Otherwise grep the `data-testid`.
2. **Capture before.**
   `CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR}" bash ${CLAUDE_PLUGIN_ROOT}/scripts/design/review.sh <label> <screens> [widths] [themes] [accents]`
   (defaults `laptop,phone`, `light,dark`, `blue`). For `a11y`, `align` and anything that
   touches colour, use accents `all` and add `hybrid`. Details, options and how to reach a new
   screen: [references/review.md](references/review.md).
3. **Diagnose in two separate passes.** First look at the screenshots yourself, before reading
   any finding: the squint test (with detail blurred, can you still name the primary element,
   the secondary one and the groups, in order?), grouping, rhythm, density, the one primary
   action, what repeats. Then read the mechanical evidence: the run summary and
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/design/design-lint.py <the screen's files>`. Note what
   each pass caught alone. A clean scan is a floor, not proof of good design.
4. **Report.** Rank everything P0–P3 (definitions in review.md) and score the screen with the
   world's rubric. Tell the owner in plain Croatian (section 6) and send two or three
   screenshots with SendUserFile. `review` ends here.
5. **Scope.** The command itself is the owner's request for that screen: polish, distill,
   align, a11y, clarify, adapt, quieter and bolder go ahead on it. Stop and ask one question,
   with a recommendation, before anything that changes other screens or the shared system
   (tokens, fonts, accent colours, a component used elsewhere), before a new dependency, and
   before any public redesign.
6. **Build** in a scrapalot-ui worktree, never the shared checkout. Fix at the narrowest level
   that removes the cause: a missing token, then a shared component, then the local code.
7. **Capture after** against the local build and compare:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/design/summarize.py <after> --against <before>`.
   Same screens, widths, themes and accents on both sides, or the comparison means nothing.
8. **Stop polishing.** Build once fully, inspect with one batched capture, fix everything it
   shows in one batch, confirm with at most one more capture. Open-ended self-review costs
   more and ends worse than a second opinion.
9. **Click it for real.** Anything interactive gets real clicks in Chrome
   (`mcp__claude-in-chrome__computer` `left_click`, then the persisted effect). Widths and
   screenshots come from the capture: the Chrome MCP tab renders at an emulated 2560 px and
   caps screenshots at 1568 px. Anything that moves is also watched at 10–25 % speed
   (DevTools → Animations, or CDP `Animation.setPlaybackRate`) and with reduced motion on
   (`DESIGN_EMULATE=reduced-motion`), and passes a `motion-audit` with no tier-1 item.
10. **Ship.** `npm run typecheck`, `npm run lint`, `scrapalot-build npm run build`; commit and
    push straight to `main` for a screen-sized change, branch and PR for a redesign or a
    system change. After the deploy, check the served bundle carries the change, capture the
    screen once more on the deployed build and send the owner the before and after pair.

## 4. The floor

Both worlds, every screen, checked on the built result rather than intended:

- **Contrast** in every theme and accent that ships: body text 4.5:1, large text 3:1,
  controls, icons and focus rings 3:1. Secondary text on a coloured surface takes its tint
  from that surface, never plain grey.
- **Keyboard.** Visible `focus-visible` rings, tab order that follows the reading order, no
  `outline-none` without a ring, no traps. Every icon-only button has an accessible name.
- **Targets** at least 24×24 px (WCAG 2.2 AA), 44 px where touch comes first.
- **Zoom and text.** Pinch zoom stays enabled; functional text 11 px or more (12 is better),
  body 14 px in the app and 16 px on public pages; prose 45–75 characters per line.
- **States.** Default, hover, focus, active, disabled, loading (a skeleton in the shape of the
  content, not a spinner inside it), empty (explains and offers the next step), error (what
  failed and how to recover), success (short).
- **Motion** follows `scrapalot-ui/docs/README_MOTION.md`: it conveys state or space, or
  tells the story once; never decorates on a loop; UI motion under 300 ms on a strong ease-out
  (never `ease-in`); interruptible where it is triggered rapidly; transform and opacity only;
  and a `prefers-reduced-motion` path that keeps the state change and drops the travel.
- **Themes.** Light, dark and hybrid (dark base with grey overrides) each look composed, not
  mechanically inverted; all six accents stay legible.
- **Browser surfaces** carry the design too: text selection colour, caret, scrollbars, focus
  rings, tabular numerals (`tabular-nums`) wherever numbers line up.
- **Copy** in the product's words; buttons name their action; every string through `t()` in
  all six locales. Croatian runs 15–30 % longer than English: capture with `DESIGN_LANG=hr`
  when a layout is tight.
- **Honest content.** No invented metrics, no lorem, no emoji standing in for icons
  (`lucide-react` is the icon set), no div-built fake screenshots.

## 5. Guardrails

- **Refinement preserves; redesign replaces.** Polish keeps the look, content and behaviour,
  and changes nothing outside the named screen. When the concept itself is wrong, say so and
  propose `explore` instead of smuggling a new look in through polish.
- **The brief wins.** A reference, mock or direction the owner approved is a contract; a
  saturated-pattern warning never overrides it. Missing a major ingredient of an approved
  direction is a blocking defect, not a variation.
- **Never modify existing UI design without a request** (scrapalot-ui rule 14). The request
  covers the named screen, not its neighbours.
- **The capture never writes** to the account: every non-read request is answered with 423
  and listed. A screen that writes when it is only opened is itself a finding.
- **The E2E account is the owner's own.** Existing specs that save settings (language,
  theme, accent, simple mode) must wrap their block in `keepGeneralSettings(test)` from
  `tests/e2e/utils/account-settings.ts`; run no spec that writes the account without it.
  The capture itself never writes, but running the regression specs after a change can.
- **Private screenshots stay private.** They show real titles and names: send them to the
  owner, never into a commit, PR, issue or public repo.
- **No docker cp into the shared container** to preview; serve the worktree build to the
  capture with `E2E_DIST`, or a Vite dev server for public pages (review.md). Only when the
  owner asks to see a build on production: back up `/app/dist` first, build with the same
  `.env.production` as CI plus `node scripts/prerender.mjs`, check no scrapalot-ui run is in
  progress, copy over without deleting, verify through the domain, and say plainly that the
  next deploy from `main` reverts it until the branch is merged.
- **Host memory.** `review.sh` refuses to start a browser under 1.5 GB available; one capture
  at a time; not while a scrapalot-ui deploy runs (`gh run list -R sime2408/scrapalot-ui
  --limit 1`).
- **No silent dependencies.** A new font, icon set, animation or 3D library is the owner's
  call: ask first, with the cost in kilobytes and what it buys.
- **Look before you build.** Before hand-building a named look (a hero, a pricing table, a
  text effect, a testimonial row), check our kit (`src/components/landing/`,
  `src/components/ui/`), then [21st.dev](https://21st.dev), the community registry with many
  variants of each kind of section. Take the idea and build it in the house style (tokens,
  fonts, flat buttons, accessibility, reduced motion); never paste a component in unread.
- **Richness is the public bar, not minimalism.** The owner read a homepage stripped of its
  sections as "a cheap WordPress template". Remove a tell by replacing it with something
  better, never by leaving a gap; ask before deleting a whole section.
- A bug found while reviewing (broken layout, a write on open, a console error) is fixed at
  its root, not styled around.

## 6. Talking to the owner

- Plain Croatian about what a person sees and gets: "gumb za prijavu na plavoj pozadini teško
  se čita" rather than "low-contrast 3.0:1 on `.landing-btn-primary`". Rule ids, class names,
  scores and file paths go in a short technical block at the end.
- Show instead of describing: two or three screenshots, before and after side by side when
  something changed. Use the capture's PNGs, never Chrome MCP screenshots.
- One decision at a time. Explain first and end the turn; ask in the next one, with a
  recommendation labelled as such and options phrased by what the user will see.
- When the owner asks "čemu ovo?" about an element, remove it first, then explain in one
  sentence.

## 7. Tools

| Tool | Use |
|---|---|
| `scripts/design/review.sh` | the capture; writes `.claude/design/runs/<time>-<label>/` and prints the summary |
| `scripts/design/summarize.py` | the summary of a run, `--against` an earlier one, `--json` |
| `scripts/design/design-lint.py` | house rules in the source: raw palette colours, tinted fills, side stripes, rounded and shadow drift, tiny text, removed focus outlines, Radix traps, disabled zoom |
| `scripts/design/fetch-detectors.sh` | fetches the pinned Impeccable and axe scripts (review.sh calls it) |
| Chrome MCP | real clicks and the persisted result; not for widths or marketing-grade screenshots |
| `scrapalot-ui/docs/README_MOTION.md` | the motion rules: when to move, timing tables, springs, gestures, scroll-driven and 3D, reduced motion, the audit format |
| [21st.dev](https://21st.dev) | ideas for public components; its CLI/MCP (`npx @21st-dev/cli@latest init --client claude`) is the owner's call to install |
| `scrapalot:ui-component-developer` | Radix, state, i18n and layout gotchas when building components |
| `scrapalot:i18n-translator`, `scrapalot:seo-optimizer`, `/scrapalot:mobile-fix` | translations, meta and structured data, one-component mobile fixes |

## 8. Sources

Rewritten for Scrapalot from ideas in these projects; their texts are not included here, and
the two detector scripts are fetched at run time from their own releases.

- **Impeccable** (Paul Bakaus, Apache-2.0) — the persuade/operate split, the command
  vocabulary, the craft floor, audit scoring and severity, bounded verification, and the
  in-page anti-pattern detector the capture injects.
- **Taste Skill** (Leonxlnx, MIT) — the design read, the three dials, the catalogue of
  generated-UI tells, the redesign protocol and the pre-flight check.
- **Playwright CLI** (Microsoft, Apache-2.0) — capture-then-read instead of streaming the page
  into context, emulation passes (reduced motion, forced colours, more contrast) and aria
  snapshots.
- **img2threejs** (Apache-2.0) — rebuilding an object from one reference image as procedural
  Three.js in staged, visually verified passes.
- **Awesome Design Skills** (Bergside, MIT) — naming directions, and keeping agent rules apart
  from the human rationale.
- **axe-core** (Deque Systems, MPL-2.0) — the accessibility rules.
- **Emil Kowalski's skills** (MIT) — `apple-design` (Apple's fluid-interface talks for the web:
  response, interruptibility, springs, velocity handoff, spatial consistency, materials,
  reduced motion) and `review-animations` (frequency table, timing, escalation triggers,
  remedial order, tiered verdict): the `motion-audit` command and README_MOTION.md.
- **HyperFrames** (HeyGen, Apache-2.0) — the motion contract: state as a pure function of the
  timeline, deterministic choreography, transform-only motion, capped stagger, a named motion
  vocabulary, and searching the registry before hand-building a look.
- **21st.dev** — the community component registry used for public-page ideas.
