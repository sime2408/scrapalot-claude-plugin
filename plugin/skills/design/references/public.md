# Public pages: distinctive, and honest about it

Here design is the product's first argument. A visitor decides in seconds whether Scrapalot is
a serious research instrument or one more AI wrapper, and a page that looks generated answers
that question for them. So this is the one surface where "make it distinctive" beats "match
the existing system": a point of view, art direction, one memorable moment per page. Two
things never bend: the page stays honest (real product, real claims, real imagery) and it
stays usable (contrast, keyboard, phone, speed).

Scope: the public routes in SKILL.md, `src/components/landing/`, `src/styles/landing.css`.
None of this aesthetic leaks into the app.

## What already exists

Reach for the kit before writing new effects.

| Need | Use |
|---|---|
| section background | `aurora-background`, `cinematic-ribbons`, `.landing-grid`, `.landing-noise` |
| card with a cursor spotlight | `spotlight-card` (`.landing-spotlight-card`) |
| word-by-word reveal | `blur-words` |
| continuous row | `marquee` (at most one per page) |
| count-up number | `animated-counter` (only for a real number) |
| section title block | `section-heading` |
| product screens | `screenshot-frame`, `image-zoom`, and the animated line drawings in `landing/wireframe/` that mirror real captures |
| buttons | `.landing-btn-primary`, `.landing-btn-ghost` |
| glass header | `.landing-glass-nav` |

- **Motion engine is Framer Motion** (`whileInView` with `viewport={{ once: true }}`,
  `useScroll`/`useTransform`, `AnimatePresence`). There is no GSAP; do not add it.
- **Accent follows the user's choice** through `hsl(var(--primary))` and `hsl(var(--glow-2))`
  (partner hues per `[data-accent]` in landing.css). Never branch on the accent in code.
- **Fonts are self-hosted** in `public/fonts.css` (Inter, Newsreader, JetBrains Mono), no
  Google Fonts requests. A family named in CSS that fonts.css does not declare silently falls
  back to the system font, which differs per machine (San Francisco on a Mac, Segoe on
  Windows, DejaVu on this host). Check what a page actually renders with
  (`getComputedStyle(h1).fontFamily`, `document.fonts`), not what the config says.
- **Traps:** `src/styles/base.css` sets `#root { text-align: center }` (`.landing-page` resets
  it); `.landing-btn-*` selectors are doubled on purpose to beat shadcn utilities; below
  1200 px the document is locked and `.landing-page` itself scrolls, so never put
  `overflow-hidden` on a `.landing-page` root; wide wire scenes overflow phones unless their
  section clips; a full-page screenshot leaves `whileInView` sections at opacity 0 (the capture
  scrolls in slices for this reason).
- Public routes must be in `PUBLIC_PATHS` or they bounce to /login; wrap pages in
  `overflow-x-hidden w-full`; every string through `t()` in all six locales.

## The design read

Before touching a page, write one line:

> Reading this as: *page kind* for *audience*, with a *voice* language, leaning toward
> *direction*.

Scrapalot's audience is researchers and deep readers: people with a library, a question, and
low tolerance for hype. Trust is the currency, so claims need proof and the tone is confident,
not loud. Then set three dials, 1 to 10, and say why:

- **Variance** (1 symmetric and quiet … 10 asymmetric and experimental). Marketing default
  6–8; legal pages, login and sign-up 3–4.
- **Motion** (1 static … 10 cinematic). Home and about 5–7; pricing 3–4; legal 1–2.
- **Density** (1 gallery … 10 cockpit). Most public pages 3–5; pricing tables 5–6.

Ask one question only when the read genuinely forks (for example editorial calm versus
cinematic), otherwise declare it and proceed.

## Playbooks

### explore

For a new page, a replaced section or a page that reads as generic.

1. Establish what is already true: content, claims, product screens, the kit, what the owner
   has approved before. The old look is evidence of what the subject is, not a rule.
2. Derive five to seven structures from the content and the reader's path, not from a
   template, and keep the three that differ most in kind. Name each with a direction from the
   vocabulary below and describe it in one paragraph: the hero, how the sections pace, the one
   signature moment, what it costs (dependencies, performance, work).
3. Show them. A quick way: build each hero as a throwaway branch or a local-only route and
   capture it; or generate one reference image per direction when an image tool is available.
   Three full-width images beat one board of thumbnails.
4. The owner picks one (a question with the three as options, the recommended one first).
5. Record the choice in `scrapalot-ui/docs/README_STYLE.md`, in a "Public pages" section
   (add it the first time): direction, dials, type, the signature motif. The next page
   inherits it instead of re-inventing.
6. Build it with full commitment, then the pre-flight check below.

**Direction vocabulary** (starting points to name and combine, not templates to copy):
*editorial* (magazine grid, serif display, long reading), *refined* (restrained, precise,
generous air), *storytelling* (a narrative scroll, one idea per screen), *immersive* (the
product itself leads the first viewport), *paper* (print and archive materials, grain,
footnotes), *instrument* (measured, technical, data drawn as data), *spacious* (few elements,
much room), *dramatic* (dark, high contrast, one light source). A direction states what it
refuses as clearly as what it does.

### bolder

"Bolder" is almost always about one section of a page whose world already exists. Everything
else stays literally as it is.

- Look at what the rest of the page does that this section does not: display type at full
  strength, the page's motif, its pacing. A flat section usually opts out of the page's own
  strongest moves; bring it up to them in the same vocabulary.
- Commit to one decisive move and quiet everything around it, so the move reads. If every
  element got louder, the section got flatter.
- Skeleton test: strip the copy. Does the structure alone still say what the section is? If
  not, the boldness is only in the font size.
- No new colour, font or primitive without asking. Existing claims stay true.

### quieter (public)

More restrained palette, more air, lighter weights, shorter motion, fewer effects; the point
of view survives. Remove glows, halos and decorative gradients first, then reduce saturation
(to roughly 70–85 %), then weight (900 → 600). Never grey, never everything the same size.

### motion (public)

The rules are in `scrapalot-ui/docs/README_MOTION.md` (read it in full first); this is the
public lens on them. The owner wants public pages rich and alive, so motion is welcome here,
as long as each piece of it has a job.

- The moment belongs to the story: the hero assembling, a product screen drawing itself,
  a transition from question to answer. Everything else arrives from an already visible
  default or does not animate.
- Timing: interface feedback under 300 ms; a once-per-visit hero may take longer. The more
  often something happens, the less it moves.
- Easing: ease-out (exponential) for arrival, shorter and subtler for exit; in Framer
  prefer `{ type: 'spring', duration: 0.45, bounce: 0 }`; bounce only for a genuinely playful
  moment, never on a call to action.
- Palette beyond transform and opacity: blur, clip-path, mask and shadow, as long as they
  stay smooth at 60 fps on a mid-range phone.
- Reduced motion: gate variants with `useReducedMotion()`; the final state must survive.
  Scroll-driven CSS (`animation-timeline`) needs a static fallback.
- Never: pulsing dots or buttons, blur-in on every paragraph, `hover:scale` on everything,
  animating width/height/top/left, scroll listeners on `window`.
- A scroll story is a pure function of scroll progress, deterministic (seeded, no
  `Math.random`/`Date.now` in the choreography), gliding while scrolling and landing on jumps;
  the text is real DOM and the page is complete without WebGL (README_MOTION.md §5).
- Audit before shipping: `motion-audit` returns a ranked list, worst first; nothing from tier 1
  (feel-breaking) ships.

### 3d

A procedural Three.js object as a page's centrepiece, rebuilt from one reference image with
the img2threejs method. **The object is the brand's own, not a metaphor**: the owner turned
down an armillary sphere and asked for "3D madness with the logo itself", built from its
measured vector drawing. For the Scrapalot mark that is done: `src/components/landing/story/`
(`logo-spec.ts` measured from `public/logo-black.svg`, `logo-scene.ts`, `logo-story.tsx`);
connections are drawn as electricity through the mark's own circuit, never as a web of
threads between the terminals (owner's call). Worth it only when the object carries the message (a book opening
into a graph, the Scrapalot mark as a physical object), never as scenery. Always a proposal
first, because it adds a dependency (Three.js is about 150 KB gzipped) and real work.

1. **Propose** two or three options with what the visitor sees, the cost and the fallback.
   Owner approval covers the dependency.
2. **Method:** clone `https://github.com/img2threejs/img2threejs` into the scratchpad and
   follow its `SKILL.md`: validate that the image is a good 3D target, write a quality
   contract, spec the component hierarchy and materials, then build in passes (blockout,
   structure, form, material, lighting, interaction, optimisation), comparing a render with
   the reference after every pass and failing a pass when an identity-defining feature is
   wrong. State plainly what is approximate: one image cannot show the hidden side.
3. **Integrate:** `React.lazy` + dynamic `import('three')` only when the section nears the
   viewport; a static poster image (the object rendered to PNG/AVIF) as the first paint and
   the LCP element; `IntersectionObserver` pauses rendering off screen; WebGL2 check with the
   poster as the fallback; reduced motion shows the poster or a still frame; cap device pixel
   ratio at 2.
4. **Verify:** the capture on laptop and phone, frame rate on a throttled CPU, and page
   weight before and after.

### delight

Small, memorable touches that fit the brand: a precise empty state, a well-timed moment when
research finishes, an easter egg in the docs. Delight is earned by the basics being right
first, and it never costs clarity or speed.

## Tells to refuse

These are what generated pages default to. The brief can earn any of them back; reaching for
one when nothing asked for it means no decision was made.

**Structure:** three identical icon-plus-heading cards as the page's backbone; the same
section layout repeated (no two neighbouring sections in the same layout family); split
headers with a tiny paragraph floating top right; bento grids with empty cells; cards inside
cards; a modal where a section would do.

**Labels and scaffolding:** a small tracked uppercase kicker above every heading (at most one
per three sections, never on every one); section numbers (01 / 02) that carry nothing;
"NEW" / "BETA" / version pills in the hero unless something really launched; scroll cues;
decorative status dots; micro-sentences under eyebrows that explain the section.

**Claims:** hero metrics (big number, small label, three stats) unless each number is real,
current and sourced; fake-precise figures; testimonials without a real person behind them;
div-built fake product screens (use real captures or the wire scenes drawn from them);
logo walls of logos nobody agreed to show.

**Surfaces:** gradient text as emphasis; purple-to-blue or cyan-on-dark "AI" gradients;
zero-offset coloured glows and radial halos behind everything; glass as decoration;
decorative grid or stripe backgrounds with nothing under them; a colored stripe down one side
of a card; hard offset shadows outside a truly brutalist direction.

**Type and copy:** a headline that wraps to four lines or more (constrain the width, shrink
the font); body under 16 px; all-caps paragraphs; tracking tighter than -0.04em; filler
verbs (elevate, seamless, unleash, supercharge, next-gen); exclamation marks in success
messages; two buttons with the same intent.

**Remove a tell by replacing it, never by leaving a gap.** The owner read a homepage stripped
of its bento, marquee, showcase and aurora as "a cheap WordPress template"; richness is the bar
for public pages. Keep the sections and upgrade their craft; ask before deleting one.

**Look before you build.** Our kit first, then [21st.dev](https://21st.dev) (a community
registry with many variants of every kind of section) for ideas; rebuild what you take in the
house style and never paste a component in unread.

**Scrapalot's own vocabulary is allowed** when it is chosen on purpose: the mono label, the
italic accent word, the aurora background and the marquee are ours. The rule is one of each
per page and each doing a job, not all of them on every section.

## Pre-flight

Before calling a public page done:

- [ ] design read and dials written down; for an approved direction, every ingredient present
- [ ] hero: headline two or three lines at laptop width, sub-text 20 words or fewer, the call
      to action visible without scrolling at 1512×860 and 390×844
- [ ] no two neighbouring sections share a layout; bento cells interlock with none empty
- [ ] every claim true and current; every image real (product captures, wire scenes, sourced
      photography), none decorative filler
- [ ] one accent, one radius system, one theme per page (no section flipping to inverted)
- [ ] every button readable (4.5:1) in light and dark and in all six accents; no button label
      wraps at desktop width
- [ ] one authored motion moment; reduced motion keeps the final state
- [ ] phone: nothing wider than the viewport, 44 px targets, the page scrolls
- [ ] performance: largest paint under 2.5 s, no layout shift from late images or fonts
      (explicit sizes, `font-display: swap` with metric-close fallbacks), heavy effects lazy
- [ ] SEO basics untouched or better: title, description, Open Graph image, headings
      (`scrapalot:seo-optimizer`); routes, anchors and form field names unchanged unless asked

## Scoring a page

| Dimension | 4 means |
|---|---|
| **Distinctiveness** | unmistakably Scrapalot; could not be swapped onto another AI product |
| **Message** | in five seconds a visitor knows what it is, for whom, and what to do next |
| **Craft** | type, spacing, colour and imagery deliberate at every width |
| **Motion and speed** | the motion tells the story once; fast first paint; smooth on a phone |
| **Accessibility** | WCAG 2.2 AA in both themes and every accent; keyboard and zoom work |

Out of 20, bands as in the app rubric. Distinctiveness is judged from the screenshots
before reading any detector output.
