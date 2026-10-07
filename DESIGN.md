---
name: GlowTact — Signal Chamber
description: "Dark instrument-panel register for the GlowTact tactile-sensing paper site: camera-black ground, neutral instrument greys, one amber signal, a cool grey-blue gel, monospace readouts and tracked caps as the device vocabulary. Restraint everywhere except the mechanism, which is the subject."
source_of_truth: design/concept-03/styles.css (:root)
applies_to: design/concept-03/
colors:
  # Ground and surfaces: the camera well
  camera-black: "#070908"          # page ground
  nitrile: "#131515"               # membrane, deepest panel
  optic-surface-1: "#121414"
  optic-surface-2: "#1a1c1c"
  optic-surface-3: "#242727"
  optic-surface-4: "#2f3333"
  depth-ramp:                      # literal steps for the camera-well vignette and lens bodies
    - "#0a0c0a"
    - "#121612"
    - "#101511"
    - "#0e130f"
    - "#0c100d"
    - "#0b0d0b"
    - "#070907"
    - "#030403"
    - "#020302"
    - "#010201"
    - "#000"
    - "#1d241f"
  # Signal (GlowTact). The accent, and the coupled-area ink: it equals the readout number exactly.
  signal-amber: "#d89122"
  signal-amber-bright: "#f4b840"
  signal-amber-dim: "#886421"
  signal-highlight: "#ffd077"      # literal in styles.css x3; candidate for a :root token
  focus: "#ffc04a"                 # focus ring only
  # Gel and air: the one cool note, so the clear gel reads as glass against the amber light
  gel: "#a3b4bf"
  gel-deep: "#536270"
  # Text
  readout: "#eef0ee"
  readout-secondary: "#c3c8c4"
  readout-tertiary: "#9da39f"
  readout-dim: "#939994"
  readout-paper: "#e9e9e5"         # literal x1
  readout-muted-green: "#7f8b80"   # literal x1
typography:
  fonts:
    ui: '"Bahnschrift", sans-serif'        # Windows-only and not shipped -- see Open issues
    mono: '"Cascadia Mono", monospace'     # same
  scale: [12, 14, 16, 22]         # px. 12 fine / 14 label / 16 title are the --text-* tokens; 22 is the form-card title's fixed floor
  fluid: clamp()                  # display and headline sizes interpolate; a clamp() is never a finding
  tracking: [0.08em, 0.12em, 0.14em, 0.16em]   # caps labels; display headings tighten -0.04 to -0.065em
radius:
  default: 0
  dot: 50%
motion:
  ease-out: cubic-bezier(0.23, 1, 0.32, 1)
  durations: 100-200ms
  reduced-motion: required
detector:
  em_dash_per_100_words: 0.5
  known_open:
    # A defect that is acknowledged, owned and dated. The gate prints it as WARN
    # instead of failing, so the rest of the detector keeps gating while this
    # waits for a decision. Remove the entry when the defect is fixed.
    - { rule: font-not-shipped, since: 2026-09-26, reason: "Bahnschrift/Cascadia Mono/Aptos are OS fonts with no webfont; replacement face is a design decision pending -- see Open issues 1" }
  sanctioned:
    # One entry per deliberate exception, with the evidence: who decided, on what.
    # The four amber glows below are the coupling metaphor of the frozen review
    # concepts (01, 02, hub), never shipped; concept-03 draws coupling as
    # darkening and has no glow. Sanctioned 2026-09-26 when the detector was
    # introduced, by selector, so a new glow anywhere still fires.
    - { rule: glow-shadow, match: ".aperture-contact", reason: "concept-01 coupling metaphor; frozen review artifact" }
    - { rule: glow-shadow, match: ".step-visual--dark::after", reason: "concept-01 coupling metaphor; frozen review artifact" }
    - { rule: glow-shadow, match: ".overlay-coupling", reason: "concept-02 coupling metaphor; frozen review artifact" }
    - { rule: glow-shadow, match: ".signal-core", reason: "review hub hero; frozen review artifact" }
---

# GlowTact Website Design System

One file, two audiences. The frontmatter above is the machine-readable
token set: it mirrors `design/concept-03/styles.css` `:root` and is read by
`design/tools/audit_slop.py` (the detector), by the design skills installed
under `.claude/skills/`, and by any DESIGN.md-aware tool. The body is the
rationale and the anti-patterns, for people and for agents. **When a token
changes in `styles.css`, change it here in the same commit.**

Precedence: this file wins over a skill's generic advice. `frontend-design`
lists "a monospace face for small data labels", "tracked ALL-CAPS labels",
and "near-black ground with one bright accent" as tells of a generated page.
Here they are the subject's vocabulary, chosen and recorded below. That skill's
own rule applies: where the brief pins the direction, follow it exactly.

## What shipped, and why it looks like this

The published site (`https://glowtact.github.io/`) is concept-03, "Signal
Chamber". The sensor images a black elastomer membrane through a clear
microtextured gel under single-colour, non-directional light; contact
darkens the image where the membrane couples to the gel. The site is the
camera's view: camera-black ground, one amber signal, grey gel, hairline
optics. Amber is GlowTact's colour in the paper. Nothing decorative is added
to that, and no second sensor is shown (decision of 2026-09-26: the site
stands on GlowTact's own evidence), so there is no second hue.

Until 2026-09-27 every grey carried a green cast (`#171d18`, `#94a094`, a sage
gel `#9db3ad`), which muddied the amber and made the small labels read as
olive on olive. The greys are now neutral and the gel is the one cool note
(`#a3b4bf`), so the palette is three temperatures with three jobs: black
membrane, amber light, cool clear gel.

This file described a light editorial brief (white and `#F6F6F3` grounds,
Inter or Geist, amber `#E9A000`) until 2026-09-26. That register survives in
the review hub (`design/index.html`, `design/shared/review.css`) and in
concepts 01 and 02, which are frozen review artifacts; it is recorded under
[Review build](#review-build-frozen) so the history is not lost. The
published concept never used it, and a design system that describes a site
other than the one shipped sends every agent the wrong way.

## Colour

| Token | Value | Role |
|---|---|---|
| `--camera-black` | `#070908` | page ground |
| `--nitrile` | `#131515` | membrane, deepest panel |
| `--optic-surface-1..4` | `#121414` → `#2f3333` | raised surfaces, in depth order |
| `--signal-amber` | `#d89122` | the accent; coupled-area ink; controls' active state |
| `--signal-amber-bright` / `-dim` | `#f4b840` / `#886421` | highlight and recessed amber |
| `--focus` | `#ffc04a` | focus ring, nothing else |
| `--gel`, `--gel-deep` | `#a3b4bf` / `#536270` | gel body and depth; the only cool hue |
| `--readout` … `--readout-dim` | `#eef0ee` → `#939994` | text, in four steps of emphasis |
| rings and grids | `rgba(255,255,255, 0.05–0.12)` | hairline structure; alpha neutrals, never a new hue |

Rules:

- Do not add unrelated decorative colours. A new hue is a design decision:
  add it to the frontmatter with a role before it appears in CSS.
- Amber means signal: the numbers in claims and tables, the primary action,
  the active state, the lamp, and, since 2026-09-27 at the author's request,
  the three results eyebrows (`DAT / 01-03`) and the `Why simple` titles, so
  each band has one amber entry point. Index, card, state and clip labels and
  the view badges stay `--readout-tertiary` (2026-09-26: five roles on one
  hue competed on a phone). One filled amber button per surface: `Paper` on
  the page, `Run once` in the instrument. Emphasis elsewhere is weight, size
  or the readout text steps.
- Amber ink equals the coupled fraction the readout prints, to 3 pp
  (`browser_check.py`, design mode). The picture and the number never disagree.
- Semi-transparent white and black are the only overlays. Gradients exist
  where the camera would produce them (vignette, sensor noise, the grid) and
  nowhere as decoration.

## Typography

Two faces, two jobs. The UI face carries prose and headings. The monospace
face carries everything the device would print: readouts, units, data
labels, state indices, the build stamp. Device labels and section labels are
set in tracked caps (`0.08em`, `0.12em`, `0.14em`, `0.16em`); display headings
tighten to `-0.04…-0.065em`. These are the instrument-panel conventions the
page is built on, not defaults.

Scale: three tokens, `--text-fine` 12 px (annotations), `--text-label` 14 px
(readouts, controls), `--text-title` 16 px (panel headings); the hero h1 is
the one uppercase display setting (`clamp(40px, 11vw, 48px)` on a phone,
`clamp(58px, 6.5vw, 108px)` above); section h2 `clamp(34px, 4vw, 52px)` and
module h3 `clamp(28px, 3.2vw, 44px)`, both sentence case; form-card titles
`clamp(22px, 1.8vw, 24px)`.
Every other literal `font-size` is a finding. `browser_check.py` (design mode)
also caps the number of distinct rendered sizes per route; a new step is
added here first, then there.

Reading measure stays narrow and figures stay wide: the old brief's
"narrow text, wide figures" holds. Preserve scientific figure aspect ratios.

## Layout

- Narrow text, wide figures; generous vertical space; no dashboard density.
- Sections alternate two grounds, full-bleed: hero, forms and the record on
  `--camera-black`; mechanism and results on `--nitrile`.
- No card kit. Radius is `0`; `50%` for dots and lenses; a pill only on a
  glyph that is literally that shape (`.camera-contact i`, `.form-glyph`).
- Structure is information: a hairline rule, a heading, a numbered state
  (`STATE 00 → 02`, `DAT/01 → 03`) encodes an actual sequence. Do not add
  numbering, eyebrows, or dividers that encode nothing. The section eyebrows
  (`SYS / 01`, `CFG / 01`, `DOC / 01`), the form-card indices and the hero
  capability tiles were removed on 2026-09-27 for exactly this reason; only
  the results index keeps its codes.
- Diagram labels are HTML (`.stage-label`, `--text-label`) positioned over the
  drawing in a `.stage-frame`, never SVG `<text>`: SVG text scales with the
  viewBox and measured 8.7 px on the 1280 layout. Two labels per drawing
  (membrane and gel; air gap and gel), the legend below carries the rest.
  `browser_check.py` (design mode) fails on any `<text>` in the mechanism
  drawings and on a label under 14 px.

## Motion

Allowed: subtle fades, one scroll reveal per element, slider-driven mechanism
changes, smooth figure transitions. `var(--ease-out)` =
`cubic-bezier(0.23, 1, 0.32, 1)`, 100–200 ms. Nothing loops, nothing
overshoots, nothing moves without a reason the visitor can see.
`prefers-reduced-motion` is respected everywhere (`verify.py` checks the
query exists; behaviour mode checks it acts).

Avoid: decorative parallax, scroll hijacking, springs, constant pulsing,
flashy gradients.

## Controls

Native, accessible controls: sliders, segmented selectors, buttons, select
menus. Visible labels, keyboard access, visible focus (`--focus`), 44 px
targets on touch (design mode measures them).

## Scientific presentation

- Preserve axes, labels, units and log scales. SNR threshold stays at 3.
- GlowTact remains amber; no comparison sensor is shown.
- Distinguish measured from simulated imagery; label conceptual
  visualizations. Interactive plots use the exact data in
  `design/data/*.json`; published numbers carry `data-metric` and match
  `design/data/results.json` (`verify.py` gates this).
- Everything in `design/SCIENTIFIC_CONSTRAINTS.md` applies.

Required mechanism note, verbatim (checked by `verify.py`):

> Conceptual visualization. Geometry and optical paths are schematic and are not a calibrated mechanical or ray-tracing simulation.

## Tone and copy

Scientific, confident, restrained. Say the measured thing. The site sells
the sensor (decision of 2026-09-27): every caveat that was copy became a
positive, measured statement or was cut, and only the mandatory
disclosures below and in `SCIENTIFIC_CONSTRAINTS.md` remain as caveats.
Method explanations stay to one line; the page shows results, it does not
explain how they were obtained. `verify.py`'s
`PROHIBITED` list polices claims ("revolutionary", "pixel-wise pressure", …);
the detector polices register: no "isn't just", "not just", "more than
just", "seamless", "effortless", "unlock", "elevate", "empower", "delve",
"game-changing", "cutting-edge", "best-in-class", "world-class",
"next-level", "supercharge". Em dashes are budgeted at 0.5 per 100 words of
page copy; a dash is a pause the sentence could not structure.

## Don't

Each of these is a detector rule; the id is in brackets.

- Gradient text, `background-clip: text` [gradient-text]
- Glassmorphism, `backdrop-filter: blur` [glass-blur]
- Glow shadows: coloured blur ≥ 20 px on `box-shadow`/`text-shadow` [glow-shadow]
- Fonts the project does not ship, named as the only faces in a stack [font-not-shipped]
- The generated-page fonts (Inter, Roboto, Arial, Space Grotesk, …) unless recorded here [overused-font]
- A colour literal off the palette above, outside `:root` [off-palette-color]
- A fixed `font-size` off the scale above [off-scale-font-size]
- Caps labels tracked at an undeclared step [tracking-off-step]
- Looping animation, overshooting easing [infinite-motion, bounce-easing]
- Emoji in the interface, placeholder copy, links ending in an arrow [emoji-in-ui, placeholder-copy, arrow-suffix-link]
- Coloured accent bar down the left of a padded block [side-tab]
- Pill-shaped chips and badges [pill-radius]
- Marketing cadence, em-dash overuse [marketing-cadence, em-dash-density]
- A `:root` token that this file does not mirror, or a colour here that no stylesheet uses [token-mirror]
- h2 → h3 → h4 rendered less than 1.15× apart, or an h1 smaller than the h2 — a flat hierarchy
  leaning on weight [flat-type-hierarchy; measured in `browser_check.py` design mode, since only
  computed styles know what a `clamp()` resolved to. The h1 is exempt from the 1.15× step: on a
  phone it is already sized by the viewport, and forcing a step there would shrink the h2]

## Light register: the published root (concept-04)

`design/concept-04/` is concept-03's content in a light figure-page
register. Added 2026-10-05 at /v2/ at the author's request: "the website
feels crowded … improve the layout, color, especially the text." On
2026-10-07 the author made it the current version: `publish.py` now
writes it to the root, concept-03 is noindex, and `v2/index.html` is a
redirect to the root so old links keep working.

- Closing band (2026-10-07): the live clip and the paper record sit side
  by side (5fr / 6fr, one column below 900px); the abstract is not shown;
  the BibTeX is broken by hand at about 55 characters and must not wrap at
  laptop widths.
- Captions cut (2026-10-07): the three module footnotes, the shear legend,
  the live clip's caption and the sentences after each sensitivity label are
  gone; the labels themselves stay. The sensitivity head's "Passive contact"
  and "Controlled threshold" still keep the two apart.
- No video captions (2026-10-07, author: "good videos should explain
  themselves"): every video's figcaption carries no text (the object and
  tactile thumbnails stay), and the live section shows its heading only.

- Same model and `data-metric` sources as concept-03; every page-level
  check in `browser_check.py` runs on both routes. The copy, the controls
  and one clip encode below diverge on purpose.
- Paper ground `#ffffff`, band `#f6f6f3`, ink `#171717`, secondary
  `#3d4044` / `#5f6368`, hairlines `rgba(23,23,23,.07-.12)`. Amber is
  `#e9a000` as a fill and `#8a5a00` as text (AA on paper). The mechanism
  band is `#111111` and re-declares concept-03's dark tokens, so the
  instrument is unchanged.
- Geist and Geist Mono from Google Fonts (shipped, so `font-not-shipped`
  does not apply; the detector now tests this per page). Mono for numbers,
  units and code only.
- Sentence case, no tracking, no eyebrows or `DAT` codes; captions in the
  reading face. Type steps 12 / 14 / 16 / 22 px plus the h2 and h1 clamps.
- The paper header (title, seven authors, affiliations, actions) leads the
  hero beside the teaser, as on a paper's project page.
- `noindex`, canonical to the root: one indexed page.

After the first critique (2026-10-06, 23/36), frozen in
`check_figure_round1`:

- Light touch leads with the placement demonstration ("A 0.2 g screw shows
  under its own weight"), and the controlled threshold sits beside it as a
  labelled claim. The claims are in mN; 0.12 N shows as 120 mN through
  `data-metric-scale="1000"`, and `audit_metrics.py` checks the printed
  unit. The fingerprint caption stays "0.25 to 3 N nominal": "3000 mN"
  would claim a precision the nominal steps do not have.
  `SCIENTIFIC_CONSTRAINTS.md`: passive placement is never a force floor.
- Evidence clips (light touch, shear) play muted while in view, never
  under reduced motion or Data Saver, and keep `preload="none"`. A pause
  the reader makes sticks until they play the clip again. The native
  control bar stays off the frame until hover, focus or touch, because it
  covered the tactile inset. The M&M clip ships as a 720p re-encode
  (10.1 MB -> 0.75 MB, CRF 20).
- The coupling states are buttons that set the slider (0 / 40 / 80 %),
  carry `aria-current`, wrap rather than spill at any width, and have no
  dead zone on their dot. The visible state appears once; a hidden live
  `<output id="toolbar-state">` names it for screen readers. The legend
  draws ray, gap and coupling as different marks (arrowed line, dashed
  line, thick seam), not only different colours.
- No zero-offset coloured glow on the interface or the coupling seam,
  `filter: drop-shadow` included: in this mechanism coupling is darkening,
  not emitted light. The LEDs keep their soft light, which is what they
  are.
- Phones keep the three-link nav, the shear tabs sit in one row, state
  names wrap instead of truncating, exploded views open full size, and
  BibTeX has a copy action.

Author's edits, 2026-10-06:

- The sensors are named Flat sensor, Omnidirectional fingertip and
  Humanoid fingertip (the names in `design/CONTENT.md`); "the pad" is gone
  from the page. The cards carry the photographs and the name only.
- No disclosure paragraph under the demo. Its panels stay labelled
  "Schematic" and "Simulated", and `verify.py` checks those labels on
  this page (`SCIENTIFIC_CONSTRAINTS.md`, Exception).

The `## Don't` list applies here too, except that this register has no
tracked caps.

## Review build (frozen)

The review hub and concepts 01/02 keep the original light brief. Recorded so
the history stays legible; not the published system.

- Grounds `#FFFFFF`, `#F6F6F3`, dark section `#111111`; hub canvas `#f2f1ed`,
  paper `#faf9f5`. Text `#171717`, secondary `#5F6368`; hub ink `#181817`,
  secondary `#55544f`, muted `#6e6c64`, focus `#a75f00`.
- GlowTact amber `#E9A000`, light amber `#FFF2CC`, tactile dark `#27231F`;
  GelSight blue `#0879B9`.
- Body Geist or Inter (brief); hub actually uses `"Aptos", "Segoe UI Variable",
  "Helvetica Neue"` and a serif `"Iowan Old Style", "Baskerville", Georgia`.
  Hub type scale 12 / 14 / 16 / 18 / 22 / 28 / 36 px. Radii 4 / 12 px.

## The detector

```bash
python3 design/tools/audit_slop.py            # immediate tier, every source page
python3 design/tools/audit_slop.py --deep     # + taste and copy rules; run before a release
python3 design/tools/audit_slop.py design/concept-03/styles.css
```

Two tiers. **Immediate** rules are mechanical and unambiguous and run after
every `Edit`/`Write` under `design/` through the `PostToolUse` hook in
`.claude/settings.json`; findings come back to the agent as context, they do
not block the edit. **Deep** rules are taste and cadence; the `Stop` hook
runs them once per turn over the files the session touched and reports only
what is new, and `--deep` runs them over everything on demand. The
`SessionStart` hook prints a digest of this file and the baseline so a new
session begins with the design context loaded. Design-system drift rules
(palette, scale, tracking, and `token-mirror` in both directions) apply only
under `applies_to`; the universal rules apply to every page under `design/`.
The generated root `index.html` is never checked: fix the concept.

The immediate tier is also a release gate: `design/verify.py` runs
`audit_slop.py --gate` and fails on any open finding. A rule listed under
`detector.known_open` above (with `since` and `reason`) prints as WARN
instead, so one acknowledged defect does not switch the gate off while it
waits for a decision. The entry is removed when the defect is fixed; the
gate then fails if the pattern returns.

Silence a finding only with evidence, and only as narrowly as the evidence
reaches: an inline `slop-ok: <rule> -- <reason>` comment on the same or the
previous line, or an entry under `detector.sanctioned` above with a `match`
(selector or file substring) and a `reason` naming who decided and on what.
Never silence a rule to push an edit through; a finding you are unsure about
is a one-line question to the user.

Red-green every rule you add: put the pattern in a scratch file under
`design/`, watch the rule fire, delete the file. A rule that has never
fired is not a rule.

## Open issues (2026-09-26)

1. **The fonts are not shipped.** `--font-ui: "Bahnschrift"` and
   `--font-mono: "Cascadia Mono"` are Windows system fonts; the hub's Aptos,
   Segoe UI Variable and Iowan Old Style are Windows and macOS system fonts.
   No `@font-face`, no font `<link>`. On Linux, Android, iOS and most Macs the
   site renders in the generic fallback, and `fc-list` on this machine finds
   none of them, so every `browser_check.py` measurement since the move from
   Windows has measured fallback fonts. Cascadia Code/Mono is SIL OFL and can
   be self-hosted as woff2; Bahnschrift is licensed with Windows and cannot.
   A cross-platform UI face (an OFL DIN-style such as D-DIN or Barlow is the
   nearest in spirit) is a design decision to take, then record here, then
   re-run the design-mode checks. The detector reports this as
   `font-not-shipped`.
2. Page copy runs 1.09 em dashes per 100 words against the 0.5 budget
   (deep tier, `em-dash-density`).
3. Seventeen colour literals live outside `:root` in `styles.css`
   (`#ffd077` ×3, the depth ramp). They are in the
   palette above so they are not findings; promoting them to tokens is the
   tidy fix.
4. `applies_to` covers concept-03 only. The hub and concepts 01/02 get the
   universal rules and nothing else.
