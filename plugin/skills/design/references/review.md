# Capture, findings and the report

The review measures the screen the way people see it, at the widths they use, in every theme
and accent that ships, and writes the evidence to disk so it can be read in pieces instead of
streamed through the conversation. The capture lives in scrapalot-ui
(`tests/e2e/design/`, `playwright.design.config.ts`); the scripts here drive and read it.

## Running it

```bash
CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR}" bash ${CLAUDE_PLUGIN_ROOT}/scripts/design/review.sh <label> <screens> [widths] [themes] [accents]
```

| Argument | Values | Default |
|---|---|---|
| screens | names from `surfaces.ts` or paths, comma separated | required |
| widths | `laptop` 1512×860 (a 14-inch laptop's browser), `panel` 1100×860 (same with a side panel open), `desktop` 1920×1080, `tablet` 820×1180, `phone` 390×844, or `WxH` | `laptop,phone` |
| themes | `light`, `dark`, `hybrid` | `light,dark` |
| accents | `gray`, `blue`, `green`, `red`, `violet`, `orange`, `all` | `blue` |

Environment passed through: `SCRAPALOT_UI_DIR` (which checkout runs it, default
`${CLAUDE_PROJECT_DIR}/scrapalot-ui`), `E2E_DIST` (serve a local build), `DESIGN_LANG`
(`hr` for Croatian, whose longer strings break layouts English never does),
`DESIGN_SLICES` (viewport-height shots down a long public page, default 6),
`DESIGN_EMULATE` (`reduced-motion,forced-colors,more-contrast`: extra shots of the first
theme and accent).

Output goes to `${CLAUDE_PROJECT_DIR}/.claude/design/runs/<time>-<label>/`:

| Path | Holds |
|---|---|
| `shots/<screen>__<width>__<theme>__<accent>[__sN].png` | what a person sees; long public pages in slices `s1`, `s2`, … |
| `findings/<same name>.json` | axe violations, Impeccable findings, overflow, console errors, blocked writes |
| `aria/<screen>__<width>.yml` | the accessibility tree: names, roles, headings, landmarks |
| `report.json` | the matrix, every capture, and problems reaching a screen |
| `playwright.log` | the run itself |

The run prints the summary (`summarize.py`); read the PNGs with the Read tool. A matrix of
one screen, two widths and two themes takes about a minute. `all` accents with three themes
is eighteen captures per width: use it for colour work, not by default.

### What the capture does to the account

Nothing. It signs in once as the E2E admin account (`tests/e2e/utils/test-config.ts`),
and from then on every request that is not a read is answered with `423 Locked` and listed
under "Saved on open". A few reads travel as POST because they carry a list of ids; they are
allowed in `ALLOWED_POSTS` in the spec, after checking that the endpoint only reads. Theme,
accent and language are forced in local storage and rewritten in the settings responses, never
saved. So the owner's own theme and model choices are untouched, and a screen that tries to
save something when it is only opened shows up as a finding.

### Reaching a screen

Public screens are URLs. Private ones are the dashboard plus the clicks that open a dialog,
drawer or tab; on a phone those tools sit in the sidebar's "Go to" list
(`mobile-dest-<name>`). When a review needs a screen the list does not have, add an entry to
`surfaces.ts` with `data-testid` selectors only, detect dialogs by
`[role="dialog"][data-state="open"]`, and commit it with the change so the next review
reaches it the same way. A bare path works too: the capture opens it signed out and signs in
only when the app bounces it to /login.

### Before and after

- **Before** is the deployed build: run with no `E2E_DIST`.
- **After, private screens:** in the worktree, `scrapalot-build npm run build`, then
  `node scripts/prerender.mjs` (without it the signed-in routes still load the old bundle),
  then `E2E_DIST=<worktree>/dist SCRAPALOT_UI_DIR=<worktree> review.sh …`. The page keeps its
  real origin and the real API; only the bundle is local.
- **After, public screens:** `npx vite --port 5199 --strictPort` in the worktree, then
  `PLAYWRIGHT_BASE_URL=http://localhost:5199 SCRAPALOT_UI_DIR=<worktree> review.sh …`.
  No build needed; public pages do not call the API. Stop it afterwards with
  `pkill -f 'vite --port 519[9]'`.
- Compare: `summarize.py <after-run> --against <before-run>`. Only the same matrix compares.
- Never `docker cp` a build into the shared container to preview it: that is production.

## Reading the findings

- **axe** (WCAG 2.2 AA plus best practice). `critical` and `serious` are real barriers:
  contrast, missing names, target size, zoom disabled. `region` (content outside landmarks)
  on public pages usually means a missing `<main>`/`<nav>`/`<footer>`, one fix for hundreds of
  nodes.
- **Impeccable**, category `quality`: contrast measured on the rendered pixels (it catches
  text on gradients and images that axe skips), undersized and tiny text, overflow, clipped
  popovers, skipped headings, line length. Category `slop`: the generated-UI tells
  public.md lists. `advisory` findings are hints, not defects.
- **Overflow**: a page wider than the window, with the elements past the right edge.
- **Console errors**: anything the screen logs as an error while loading. Errors caused by the
  blocked writes (423) are expected; others are bugs.
- **Saved on open**: writes a screen attempts when it is merely opened. Each one is a question
  worth asking of the code: should looking at a screen change anything?
- **Aria snapshot**: read it for icon buttons without names, heading order and landmarks.

To find the code behind a finding: the build stamps elements with
`data-scr-src="<file>.tsx:<line>:<col>"` and axe quotes it in its targets; the
Impeccable selector usually includes a class list distinctive enough to grep. Otherwise grep
the nearest `data-testid`.

Then read the source of the screen with the lint, scoped to the files that render it:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/design/design-lint.py src/components/settings/settings-tab-general.tsx src/components/settings/settings.tsx
```

`--scope app|public` overrides the per-file guess, `--json` for machine use. A line that is a
deliberate exception carries `design-lint: ignore` and a comment saying why.

Before reporting a problem as new, check whether it is app-wide and already known: look at
earlier runs in `.claude/design/runs/` and at `git log` for the file. An app-wide issue (a
token, the viewport meta tag, a font that never loads) is reported once, as a system change
for the owner to approve, not on every screen.

## Motion audit (`motion-audit`)

What moves is judged in motion, never from a still. Play the flow at full speed, then at
10–25 % (DevTools → Animations, or CDP `Animation.setPlaybackRate` in a Playwright script),
step through it frame by frame, and capture it with `DESIGN_EMULATE=reduced-motion` and at
phone width. For WebGL scenes captured headless, wait several seconds per position: the
software renderer is slow and damped motion lags.

Write the result as README_MOTION.md §9 asks: **a ranked list of everything that feels off,
worst first**. Each line says what a person perceives, where it is (`file:line`), the rule it
breaks (easing, duration, origin, interruptibility, GPU, reduced motion, cohesion) and the fix,
chosen from the remedial order (delete, reduce, fix the easing, fix the origin, make it
interruptible, move it to the GPU, asymmetric timing, polish). Group by the six tiers
(feel-breaking, should not be there, performance, interruptibility and timing, space and
cohesion, accessibility) and close with a verdict: block or approve.

## Severity

| | Meaning | Examples |
|---|---|---|
| **P0** | blocks a task or excludes people | a control nobody can reach by keyboard, text unreadable in one theme, a dialog that cannot be closed on a phone, a write on open that loses data |
| **P1** | significant difficulty or a WCAG AA failure | contrast under 4.5:1 on body text, icon buttons without names, zoom disabled, overflow on a phone |
| **P2** | annoying, a workaround exists | inconsistent component, tinted fill, missing empty state, cramped spacing |
| **P3** | polish | radius drift, a heading one step off, an animation a little slow |

Not everything is a P0. Too many P3s are noise: report the few that matter.

## The report

For the owner, in Croatian, in this order:

1. **One sentence** on the overall state of the screen.
2. **What works**, two or three points, specific.
3. **The three to five things that matter most**, each told as what a person sees ("na
   mobitelu gumb za spremanje ispada izvan ekrana"), why it matters, and what the fix would
   change. Mark which ones need the owner's approval (a system change or anything visible
   beyond this screen).
4. **Screenshots**: two or three, sent with SendUserFile; before and after side by side when
   something changed.
5. **Technical detail**, clearly separated at the end: score per dimension, P0–P3 list with
   rule ids and source locations, the run directory, and anything the capture could not reach.

After `polish` or another editing command, the report adds the before and after scores and the
list of resolved and new findings from `summarize.py --against`.
