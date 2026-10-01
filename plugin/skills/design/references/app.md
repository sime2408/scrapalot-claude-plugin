# The app: tidy, simple, accessible, consistent

Inside the login a person is reading a book, following a research run or filing notes. The
screen succeeds when it disappears into that task. Its failure mode is not blandness but
strangeness without a purpose: a decorated button, a control that behaves unlike its twin on
the next screen, an animation that makes someone wait, a second way to do the same thing.
The bar is earned familiarity: a person fluent in tools like this trusts every control at
first sight and never pauses on one that is subtly off.

## The house style

The source of truth is `scrapalot-ui/docs/README_STYLE.md` and rules 9–14 of
`scrapalot-ui/CLAUDE.md`. What a review checks against:

- **Semantic tokens only**: `bg-background`, `bg-card`, `bg-muted`, `text-foreground`,
  `text-muted-foreground`, `border-border`, `bg-primary`, `text-destructive`, `text-success`,
  `text-warning`. The zinc greys in README_STYLE are sanctioned; chromatic palette classes
  (`bg-blue-500`) and hex values are not, because the six accents and three themes cannot
  follow them. The accent swatches in settings are the one legitimate exception and carry a
  `design-lint: ignore` comment.
- **Accent is dynamic.** `data-accent` on the root picks gray, blue, green, red, violet or
  orange; `bg-primary` follows it. Anything coloured is checked in all six.
- **Sharp and flat.** Minimal radius (`rounded-full` only for circles), borders instead of
  shadows for elevation, spacing on the 4 px grid. Around sixty legacy files still carry
  `rounded-md/lg`; fix them in the files you touch, never propagate them.
- **Restraint the owner has asked for explicitly:**
  - No tinted background fills in the product (`bg-info/10`, `bg-primary/10` pills, icon tiles,
    banners). Colour lives in text, icons and `border-*/40` outlines; surfaces stay `bg-card`
    or `bg-muted/30`. Exceptions: data ink (the fill of a meter or progress bar) and real
    buttons.
  - No decorative marks that repeat what a name, avatar or icon already says: accent stripes
    down the side of a row, badges restating a label, a coloured dot before every item.
  - A success or error banner is an outline and coloured text, not a filled box.
  - Emphasis comes from type and from elements already there (the name in `text-primary`, the
    avatar), not from new graphic devices.
- **Type.** The product uses one sans family on a fixed rem scale with a tight ratio (1.125 to
  1.2 between steps); no fluid `clamp()` headings, no display faces in labels, buttons or data.
  Chat answers have their own reading surface (`src/styles/chat-reading.css`) with a user-
  selectable face. Numbers that line up get `tabular-nums`.
- **Motion** by `scrapalot-ui/docs/README_MOTION.md`: 150–250 ms, only for state (something
  opened, arrived, changed, finished) and space (from its trigger, back the way it came). No
  entrance choreography when a screen loads, no loops except for something genuinely live,
  nothing on a keyboard shortcut or a 100+/day action.
- **Density is allowed.** Tables with many rows and panels with many labels are fine when the
  task needs them; the test is whether a person finds what they need, not how airy it looks.

## Scoring a screen

Five dimensions, 0–4 each, named after what the owner asked the app to be:

| Dimension | 4 means | Evidence |
|---|---|---|
| **Tidiness** (urednost) | clear reading order, related things grouped, deliberate rhythm, aligned edges | squint test on the shots; spacing values in the source |
| **Simplicity** (jednostavnost) | one obvious primary action, four or fewer choices at a decision point, nothing said twice, complexity revealed when needed | count actions and repeated text on the shot |
| **Accessibility** (dostupnost) | WCAG 2.2 AA met in every theme and accent, full keyboard path, named controls, zoom works | axe + Impeccable quality rules + a keyboard walk |
| **Consistency** (konzistentnost) | shared components and tokens throughout; the same action looks and behaves the same as elsewhere | design-lint on the screen's files; compare with sibling screens |
| **States and words** | loading, empty, error and success designed; labels name actions; all six locales | open the states; read every string |

Total out of 20: 18–20 excellent, 14–17 good, 10–13 needs work, below 10 needs a rethink.
Most real screens land between 11 and 16; a 4 means genuinely excellent. Keep the scores in
the technical block of the report and lead with the three things that matter most.

Walk the screen as four people before scoring, and write down only what broke for each:

- **the reader** — an hour into a book in dark mode: glare, tiny text, controls that jump;
- **the first-timer** — has not learned the icons: unlabeled buttons, jargon, no way back;
- **the keyboard and screen-reader user** — tab order, focus, names, announcements;
- **the phone user** — one thumb, poor light: targets, reach, scrolling, text that overflows.

## Playbooks

### polish

Refinement, never a hidden redesign: the look, content and behaviour stay, and nothing
outside the named screen changes. First classify each drift, because the fix lives at a
different level:

- **missing token** — the system needs a reusable value (add it once, use it everywhere);
- **one-off** — a shared component already does this (replace the local copy);
- **conceptual mismatch** — the flow or hierarchy differs from sibling screens (say so; that
  may be `distill` or a question for the owner);
- **local defect** — simply unfinished (fix it there).

Fix in this order: broken or blocked tasks and inaccessible paths; missing loading, empty,
error, disabled and permission states; hierarchy, responsive and system drift; visual and
motion inconsistencies; leftover code. Then check the whole path, not just the first
screenshot: every width, both themes, long and missing content, keyboard.

### distill

Simplicity removes obstacles, not features. Name the screen's one job, then:

- **Actions:** one primary, one or two secondary, the rest in a menu. Two buttons that do
  nearly the same thing become one.
- **Say it once:** a heading that explains the state makes the intro under it redundant;
  helper text answers a question the label leaves open or goes.
- **Containers:** cards are not layout. Remove a card whose only job is to hold a group that
  spacing could hold; never nest cards. Flatten wrappers that exist for styling alone.
- **Disclosure:** rarely used settings behind an "Advanced" section, not deleted.
- **Modals last:** inline editing or an expanding row before a dialog.
- **Palette and type:** one accent plus neutrals, three or four sizes, two or three weights.

Never remove information a person needs to decide, or labels a screen reader needs. Record
what was removed and where it went in the commit message.

### align

Consistency is a property of the whole app, so the check is comparative:

1. List the screen's controls (buttons, inputs, selects, tabs, toggles, badges, empty states,
   dialogs) and find the shared primitive for each in `src/components/ui/`.
2. Find two sibling screens that do the same kind of thing (another settings tab, another
   list) and compare: same button variant for the same action, same header anatomy, same
   empty-state pattern, same spacing between sections, same icon for the same meaning.
3. Replace local re-implementations with the primitive; move a value repeated in three places
   into a token; delete a variant nobody else uses.
4. Run design-lint on the screen's files and clear raw colours, tinted fills, stripes, radius
   and shadow drift there.

A difference that carries meaning stays; a difference that is only history goes.

### a11y

Measure with the capture in every theme (`light,dark,hybrid`) and accent (`all`), then walk
it by hand:

- **Contrast:** axe `color-contrast` and Impeccable `low-contrast`. A failure on
  `bg-primary text-primary-foreground` is a token problem (the accent's lightness), not a
  per-button one; fixing it changes every primary button in the app, so it is a system change
  the owner approves.
- **Names:** axe `button-name`, `link-name`, `label`, `image-alt`. Icon-only buttons get an
  `aria-label` through `t()`; decorative icons `aria-hidden`.
- **Keyboard:** tab through the screen in Chrome with real key presses; focus must be visible,
  follow the reading order, enter and leave dialogs correctly (Radix does this when used
  as intended) and never get trapped.
- **Targets:** axe `target-size`; small icon buttons get padding, not a bigger icon.
- **Zoom and reflow:** pinch zoom must stay enabled; at 200 % text size nothing is cut off.
- **Structure:** one `main` landmark, headings in order, lists as lists, tables as tables.
- **Motion and colour:** `DESIGN_EMULATE=reduced-motion,forced-colors,more-contrast` and look
  at the extra shots; state that is shown only by colour also needs a shape, icon or text.
- **Status:** changes that happen out of sight (saved, failed, finished) are announced
  (`role="status"` or the toast system), not only painted.

### clarify

Read the whole path, not isolated strings. For each state decide the one fact the person needs
now, the action available next, and the context that changes the decision; say each once.

- Buttons name what happens ("Delete collection", not "OK"); destructive confirmations name
  the object and the consequence, and undo beats confirmation where recovery is safe.
- Errors say what failed, why when it is known and useful, and how to recover. The backend
  sends status codes, not English: translate them through `lib/status-message-parser.ts`.
- Empty states tell first use, no results, filtered out and no permission apart, and offer
  the next step.
- Loading names the real operation and never invents progress.
- Placeholders are examples, not labels.
- Every string through `t()`, in all six locales (`en`, `es`, `fr`, `de`, `it`, `hr`); run
  `node src/i18n/translations-alignment.cjs --add-missing` and translate every placeholder it
  inserts. Keep variables whole so translators can reorder them. `scrapalot:i18n-translator`
  owns the mechanics.

### adapt

The app switches to its phone layout below 1080 px (`useIsMobile`, `isMobileOrTablet`).
Capture `phone` and `tablet`, then:

- dialogs go full screen on phones unless they are small confirmations
  (`disableFullscreenOnMobile`); nested Knowledge Stacks dialogs need more than 1400 px;
- touch targets 44 px, spaced; no hover-only affordances;
- one scrolling region per view, `flex-1 min-h-0 overflow-y-auto`, never Radix ScrollArea
  inside a flex column; a `position: sticky` header inside that scroller vanishes on real
  phones once the list scrolls a screen (emulation does not show it), so on phones render it
  above the scroller instead;
- the on-screen keyboard shrinks the visual viewport (the capture can fake it, see
  review.md) and must not hide the field being typed in;
- popovers over lists use the tap-versus-scroll threshold in rule 19 and survive parent
  re-renders (rule 20);
- rules 18–21 and the mobile patterns in `scrapalot:ui-component-developer`; one-component
  fixes can go through `/scrapalot:mobile-fix`.

### quieter (app)

Less noise, same function: fewer background accents, flatter surfaces, lighter weights
(700 → 600, 600 → 500), thinner or no borders between things spacing already separates,
shorter and gentler motion, one colour doing one job. Quiet is not grey: keep the primary
action and the current selection unmistakable.

### motion (app)

Only for state: a panel opening from its trigger, a row arriving in a list, a save turning
into a check. Use the named patterns of README_MOTION.md §8 (`press`, `pop`, `sheet`,
`collapse`, `arrive`, `status`, `live`) before inventing one: 150–250 ms on the strong
ease-out, shorter for leaving, a critically damped spring for things a person drags,
interruptible, `AnimatePresence` for anything that mounts and unmounts. Nothing animates on
page load, nothing loops unless it is live, and reduced motion keeps the state change without
the travel (the app root sets `MotionConfig reducedMotion='user'`; CSS motion needs its own
media query).

## Known traps

Radix composition (`asChild`), popover positioning, ScrollArea in flex, z-index above the
notes toolbar, portal containers, `DraggablePanel`, the chat-message extension rule: all in
`scrapalot-ui/CLAUDE.md` rules 22–30 and 41–45, with the reasoning in
`scrapalot:ui-component-developer`. Check them before inventing a fix; most "the design is
off" reports on overlays turn out to be one of them.
