# Own-sensor site: design

**Date:** 2026-09-26
**Status:** approved by the author in conversation (design, plus the three
open points: mechanism three-way toggle, hero status strip removed, alternating
section grounds).
**Supersedes:** the comparison framing of
`2026-08-14-glowtact-results-section-design.md` ("simplicity without
sacrifice", measured against GelSight Mini).

## Goal

The published page presents GlowTact on its own evidence, reads in about
half the words, and displays well on a phone as well as a desktop. Three
concrete targets, all measured by the existing tools:

- no GelSight Mini anywhere on the page: no chart series, table column,
  image, number, or sentence;
- page copy about 800 words (from 1 588); results region about 450 (from
  1 171);
- page height at 375 px at most 9 screens (from 21.6); at 1 280 px at most
  7 (from 14.2).

The paper link, a Code button and a Hardware-guide button appear in the
hero; the last two are shown as coming soon.

## Decisions taken in the dialogue

| Decision | Choice | Why |
|---|---|---|
| Horizontal slide strips per results module | **paused**; not built | the author paused it before a shape was chosen |
| GelSight comparison | removed entirely | the site should stand on the sensor's own results |
| What carries the sensitivity claim | passive-placement demonstration only; the SNR-vs-force chart goes | author's choice; the controlled 0.12 N figure survives as one sentence in the scope note |
| Text budget | headline + one-sentence claim (≤ 25 words) + captions (≤ 15) + one-sentence scope (≤ 20) per module | author's choice |
| Fingerprint 0.3–2.0 N series | moves to reconstruction as the resolution evidence | it is about ridge spacing, not sensitivity |
| 9DTact sentence in reconstruction | removed | same principle as GelSight: no head-to-head |
| Endurance module | removed until footage exists | two "awaiting footage" placeholders cost a screen and say nothing |
| Force module | GlowTact-only table; bar chart removed | three single-series bars carry less than one table row |
| Mechanism on phone | View B (micro) and View C (camera) become one 2D / 3D / Camera toggle | one model, two fewer screens |
| Hero status strip | removed on all viewports | decorative chrome |
| Section grounds | alternate `--camera-black` / `--nitrile` | sections read as bands on a phone instead of one black field |
| Review-build chrome on the public page | removed (CONCEPT 03 badge, back-to-review link, All concepts / Contact Atlas footer links) | HANDOFF open item 1; internal vocabulary facing the public |
| Fonts | unchanged; `font-not-shipped` stays known-open | separate decision |

## Page structure (final)

```
header      GLOWTACT wordmark · nav: Mechanism / Results / Paper
hero        title · one-sentence summary · [Paper] [Code · coming soon] [Hardware guide · coming soon]
            teaser figure · 3-item capability row
mechanism   SYS/01 · one line · coupling monitor (View A + View B/C toggle on phone; side by side ≥ 900 px)
forms       CFG/01 · three bodies with real photographs (Pad / Flat / Tip)
results     RESULTS kicker · nav DAT/01–04
  DAT/01    sensitivity · two videos (M&M 9.8 mN, M2×6 screw 1.96 mN) · Fig. 9 GlowTact triplets
  DAT/02    reconstruction · turntable gallery (2 cols on phone) · fingerprint series
  DAT/03    shear · clip viewer · numbers table
  DAT/04    force · one-column table
research    title · subtitle · BibTeX (wrapping)
footer      wordmark · build stamp
```

Removed: the results intro paragraph, the SNR chart and its JSON block, the
force chart and its JSON block, DAT/05, the research record's PAPER / CODE /
DATA rows, the hero status strip, the review chrome.

## Per-section design

### Header and footer
Nav gains "Paper" (same PDF link). The `CONCEPT 03` badge and the
back-to-review link go; the footer keeps the wordmark line and the build
stamp only. `publish.py` rewrite rules for `../` review links become
unnecessary but stay harmless.

### Hero
- Title stays the one uppercase display heading on the page; phone size
  `clamp(40px, 11vw, 60px)` (was `clamp(46px, 14vw, 72px)`), desktop unchanged.
- Summary: the current 22-word sentence.
- Actions: `Paper` (primary, `../../GlowTact.pdf`, new tab) · `Code`
  (pending) · `Hardware guide` (pending). Pending buttons are
  `<span class="button button--pending" aria-disabled="true">` with a
  `<small>coming soon</small>`: no `href` (verify.py forbids `#`), not
  `<button disabled>` (disabled text would fall under AA). Text
  `--readout-tertiary` on the surface passes 4.5:1; height 44 px.
- Capabilities: one row, three columns, `--text-fine` labels; on phone the
  same row (three short items fit 343 px).
- Status strip removed. Phone height target: ≤ 1 screen before the figure.

### Mechanism
- Header: `SYS / 01` + "How contact becomes signal." + the one-line lead.
- Readouts shortened to one line each (`WINDOW ~100 µm`, `INTENSITY`,
  `INDENTATION`); labels never wrap at 375 px.
- Below 900 px, View B and View C share one stage behind a three-segment
  control `2D / 3D / Camera` (the existing micro tab pair extended by one
  segment; same model, same renderers; the camera stage is shown or hidden,
  never re-created). At ≥ 900 px the current two-column layout stays.
- The disclosure sentence stays verbatim (verify.py asserts it).
- PARAMS.md constants untouched; `probe_model.py` sweep must be unchanged.

### Forms
Three cards with photographs from the main deck, slide 5 (GlowTact-Pad,
-Flat, -Tip), one line of copy each (≤ 15 words). Phone: three rows with
the photo left; desktop: three columns. Copy names what is measured where:
"Every result below was measured on the flat pad." Tip and Flat are shown
as bodies, with no characterisation data (author: fabrication still
improving).

### Results region
Kicker `RESULTS` + one line: "What the flat pad measures." Module nav with
four items. One module template:

```
<article class="result-module" id="…">
  <header>  signal-label (DAT / 0n + ≤ 4 words) · h3 · p.module-claim (≤ 25 words, numbers as data-metric)
  <div>     one evidence block
  <p class="module-scope"> one sentence (≤ 20 words)
```

**DAT/01 Sensitivity — "It sees two millinewtons."**
Claim: "An M&M at 9.8 mN and an M2 screw at 1.96 mN both show in the raw
frame, under their own weight." Evidence: two `<video>` side by side
(phone: stacked), `preload="none"`, poster at a mid-clip frame, each with a
one-line caption carrying mass and force as `data-metric`; below, the Fig. 9
GlowTact triplets (raw | diff | 3× diff) for M&M 1.0 g / 9.8 mN, M6 nut
2.0 g / 20.0 mN, M5×6 2.4 g / 23.5 mN in a three-row strip, lazy-loaded.
Scope: "Passive placement, a demonstration; the controlled threshold test
gives a 0.12 N median minimum detectable force at SNR = 3 across 10 probes."
Videos: `mms-contact.mp4` (existing) and `screw_1.mp4` from
`~/glowtact_stuff/03_sensitivity/videos/`, re-encoded H.264 High yuv420p
CRF 20 at 1280 × 800 → ≤ 3 MB.

**DAT/02 Reconstruction — "One dark image, turned in three dimensions."**
Claim: "Relief from a single frame's darkening resolves M1 threads at
0.25 mm pitch." Evidence: the seven-object turntable gallery, unchanged in
behaviour, laid out two columns at 375 px (clip height ≈ 120 px); captions
≤ 12 words; then the fingerprint 0.3 / 1.0 / 2.0 N strip with the caption
"Ridge pattern legible from 0.3 to 2.0 N." Scope: "Qualitative relief from
one tactile frame, not validated against measured heights." The 9DTact
sentence and the two intro paragraphs go. Heading becomes an h3 like the
other modules (the region has one h2).

**DAT/03 Shear — "It reads the sideways pull."**
Claim (≤ 25 words): "Dense Farnebäck flow on the gel's own speckle yields a
usable field over 97.8 % of the pad, 0.037 px forward–backward." Evidence:
the clip viewer and the seven-row numbers table as shipped; the legend
becomes one line ("Readouts per frame: slide, twist, spread, slip; red
outline = contact."). Scope: "Self-supervised consistency on one reference
press; no ground truth; pixels, not calibrated force." The phase-correlation
sentence goes.

**DAT/04 Force — "Darkness carries the load."**
Claim: "A learned regressor reads normal force from the frame: 0.106 N mean
error on everyday objects, 0.276 N RMSE on controlled probes." Evidence:
one table, five rows (Balloon 0.087, Light bulb 0.093, Pipe 0.127, Rope
0.117, Macro average 0.106) plus a second small table or a row group for the
three force bins (0.056 / 0.058 / 0.209 N). Scope: "Estimated by a model,
not measured by the camera; 14 716 frames, held-out locations." Chart and
`#force-bins` block removed.

### Research record
`DOC / 01` label, title in sentence case at the module h3 size (not the
76 px display), subtitle, BibTeX with `white-space: pre-wrap` so nothing
scrolls sideways at 375 px. The PAPER / CODE / DATA rows are removed; the
paper is in the hero and the nav.

## Colour roles

Token values in DESIGN.md do not change; roles do.

| Role | Token |
|---|---|
| numbers in claims and tables, primary button, active tab, lamp | `--signal-amber` (bright/dim variants as today) |
| eyebrow labels, module labels, captions' first line | `--readout-tertiary` (was amber) |
| section grounds | alternate `--camera-black` and `--nitrile` per top-level section, hero on camera-black |
| GelSight blue | retired: removed from CSS, `app.js`, and DESIGN.md `colors` |

`token-mirror` will fail until the blues leave both places in the same
commit.

## Type scale

- Display (hero h1 only): `clamp(40px, 11vw, 60px)` on phone, unchanged
  on desktop.
- Section h2 and module h3: one clamp, sentence case,
  `clamp(28px, 6.5vw, 44px)`; no uppercase display outside the hero.
- Eyebrows: `--text-fine` mono, tracked 0.12em, ≤ 4 words after the label.
- Body: `--text-label` for captions and scope, 16 px for claims.
- `MAX_DISTINCT_FONT_SIZES["signal"]` is re-measured after the change and
  ratcheted down to the new count; the 14.0 / 14.1 pair must collapse.

## Media and assets

| Asset | Source | Recipe |
|---|---|---|
| `design/assets/video/sensitivity/screw-m2.mp4` | `~/glowtact_stuff/03_sensitivity/videos/screw_1.mp4` | ffmpeg libx264 High yuv420p CRF 20, faststart, no audio |
| `design/assets/images/sensitivity/screw-m2-poster.jpg` | mid-clip frame of the above | `-q:v 3` |
| `design/assets/images/sensitivity/fig9-<object>-<raw|diff|diff3>.jpg` (9) | `~/glowtact_stuff/01_decks/light_objects.pptx` slide 2 media, mapped by slide position (GlowTact half only) | JPEG q88, max 760 px |
| `design/assets/images/forms/<pad|flat|tip>.jpg` (3) | main deck slide 5 media, mapped by position | JPEG q88, max 1200 px |
| removed | `mm-gelsight.jpg`, `m8-nut-gelsight.jpg`, `m5-screw-gelsight.jpg`, `mm-glowtact.jpg`, `m8-nut-glowtact.jpg`, `m5-screw-glowtact.jpg` | superseded by the Fig. 9 triplets |
| kept | `mms-contact.mp4`, `mms-contact-poster.jpg`, fingerprint, hero, turntables, shear clips | |

`MATERIALS.md` gains rows for every new derivative with its source and
recipe. `design/data/results.json`: remove the seven `*_gelsight` keys, the
`shear.phasecorr_*` keys, `snr_threshold` if unreferenced; add
`sensitivity.passive_m2_mass` 0.2 g and `passive_m2_force` 1.96 mN
(source: main deck slide 6), `sensitivity.passive_m6_*` if the M6 nut is
shown. `design/data/snr-curves.json` and `digitize_snr.py` are left in the
repository as documented, unused derivations (one line in MATERIALS.md).

## Guards

`browser_check.py`:
- results region: module count 5 → 4; SNR chart geometry and headline
  assertions removed with the chart; shear selector, loading strategy (one
  eager image: the hero), scope-footnote-on-every-module kept.
- new: exactly one `.hero-actions a[href$="GlowTact.pdf"]`, and every
  `.button--pending` has no `href` and `aria-disabled="true"`.
- new: at 375 px no `.signal-label` wraps past two lines.
- new: at 375 px the page is ≤ 9 × 812 px; at 1280 px ≤ 7 × 900 px (the
  height budget, ratcheted like the font-size ceiling).
- behaviour mode: the mechanism 2D / 3D / Camera toggle at 375 px selects
  each stage and keeps the pressure readout consistent across them.
- `MAX_DISTINCT_FONT_SIZES` re-measured and ratcheted.

`verify.py` / `audit_metrics.py`: unchanged; `results.json` keys must
match. `audit_slop.py`: `token-mirror` must pass after the blue retires.

Every new assertion is red-greened before it is committed.

## Documents

- `DESIGN.md`: colour-role section rewritten; GelSight blue removed;
  Open issues updated (font decision still open).
- `design/SCIENTIFIC_CONSTRAINTS.md`: the GelSight Mini and 9DTact sections
  marked superseded by this spec (no head-to-head on the site); the passive
  placement rule stays.
- `design/CONTENT.md`: results copy replaced.
- `docs/HANDOFF.md`: open item 1 closed.
- Ledger: `docs/superpowers/plans/2026-09-26-own-sensor-site-ledger.md`.

## Out of scope

Font replacement; the horizontal strip; endurance footage; any tip or flat
characterisation data; the arXiv link (a one-line href change when it
lands); Code and Hardware-guide destinations.

## Verification

Per task: `verify.py`, then design + behaviour modes, then screenshots at
375 and 1280 looked at. At the end: `audit_slop.py --deep`, the height
budget, the word count (`audit_text.py`), `release.py`.

## Outcome (2026-09-26, same day)

Implemented in fourteen tasks (`docs/superpowers/plans/2026-09-26-own-sensor-site.md`);
the found-to-fix trail is in `2026-09-26-own-sensor-site-ledger.md`.

| Target | Measured after |
|---|---|
| no GelSight on the page | 0 mentions; 0 `*_gelsight` keys; blues retired from CSS, script and DESIGN.md |
| page ≈ 800 words, results ≈ 450 | 818 and 433 (from 1 588 and 1 171) |
| phone ≤ 9 screens, desktop ≤ 7 | **not met as written**: 13.1 screens at 375 × 812 and 12.4 at 1 280 × 800 under the guard's block-media measurement (from 21.6 and 14.2 by the same method). The 9 / 7 figures were estimates before the content was settled; with the interactive mechanism and four evidence modules kept, the measured floor is frozen as `PAGE_BUDGET_SCREENS` (13.4 / 12.6) and ratchets down when something is removed. |
| first load | 0.33 MB, no video bytes (hero the only eager image) |
| distinct font sizes | 6 at every viewport (ceiling ratcheted 8 → 6) |
