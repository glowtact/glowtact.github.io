# GlowTact Results Section Design

**Date:** 2026-08-14
**Status:** approved (approach D)
**Supersedes:** the `record` capability cards and the retired `evidence` section

## Objective

Give the published site a results region that presents five results — sensitivity,
3D reconstruction, shear tracking, force prediction, endurance — as the paper's
own argument rather than as a capability inventory.

## The organizing principle

The paper does not claim a list of capabilities. It claims a trade-off: prior VBTS
buy their capability with multicolor directional illumination, photometric
calibration, heavy computation and a delicate gel; GlowTact removes all of it and
loses nothing. The abstract states it in one clause — this simple sensing principle
enables compact, customizable sensors *while preserving* high sensitivity and rich
spatial detail. Related work sharpens it: prior sensors never observe pressure, they
infer it from geometry. The conclusion lists the ledger: easier optical design,
lower computational demands, more durable skin.

Each result therefore answers one doubt about the simplified design. The doubt lives
in the eyebrow label; headlines stay declarative, per `design.md`'s "restrained".

| # | Doubt answered | Module |
|---|---|---|
| DAT / 01 | Strip the sensor to one flat colour and it must go numb | Sensitivity |
| DAT / 02 | Drop photometric stereo and you lose geometry | 3D reconstruction |
| DAT / 03 | One scalar image cannot give you direction | Shear tracking |
| DAT / 04 | Darkening is qualitative; you cannot get newtons | Force prediction |
| DAT / 05 | A nitrile membrane must be fragile | Endurance |

Rejected alternatives. **Signal chain** (presence → shape → motion → magnitude →
survival) describes any VBTS — GelSight does all four — so it produces a competent
page that never says why this sensor matters. **Two tiers** demotes force
prediction, the paper's most rigorous result, for lacking imagery: a design decision
overriding a scientific one.

## Page architecture

Before: hero → mechanism → record → forms → reconstruction → research.
After:  hero → mechanism → forms → **results (DAT / 01–05)** → research.

- **`record` dissolves.** Its three capability cards (`PASSIVE CONTACT`,
  `FINE GEOMETRY`, `FORCE CUE`) are the results asserted without evidence. Its
  video is kept: `mms-contact.mp4` is the M&M clip, 1.0 g / 9.8 mN, which is the
  gram-scale passive-contact demonstration, and moves into DAT / 01.
- **`forms` moves ahead of the results.** The paper evaluates "using a basic flat
  sensor"; the reader meets the three bodies first, and the results region states
  once that every measurement below is from the flat sensor. That qualification is
  absent from the current page.
- **Numbering** reuses the existing label grammar (`SYS / 01`, `CFG / 01`,
  `DOC / 01`). Reconstruction moves from `DAT / 01` to `DAT / 02`.
- **Navigation** stays three items: Mechanism · Results · Research. The results
  region opens with the thesis stated once plus a five-item index. Plain anchors.
- **Hero** secondary action becomes "See the results" → `#results`; it currently
  points at `#record`, which is being removed.

## Module contract

Every module has the same skeleton, so the region stays coherent and extensible:

1. eyebrow `DAT / 0n` + the doubt, one line
2. declarative headline
3. one-sentence claim carrying the module's headline number
4. evidence stage (the module's own layout)
5. scope footnote — what the evidence is, and what it is not

## Per-module content

### DAT / 01 — Sensitivity
Headline number: **0.12 N vs 0.23 N** median minimum detectable force (n = 10
probes, SNR >= 3, 0–20 N).
Evidence: redrawn Fig. 10 (three panels); the passive-contact trio from Fig. 9
(M&M 1.0 g / 9.8 mN, M6 nut 2.0 g / 20.0 mN, M5x6 2.4 g / 23.5 mN) against
GelSight Mini on matched apparatus; the fingerprint series at 0.3 / 1.0 / 2.0 N
(Fig. 5, asset already committed); the M&M contact video.
Scope: passive placement is a demonstration, not a calibrated minimum-force
measurement. GelSight Mini is a representative geometry-based baseline on the same
rig — no blanket superiority claim.

### DAT / 02 — 3D reconstruction
Headline number: **M1 threads at 0.25 mm pitch**; 9DTact's published limit is M4
(0.7 mm).
Evidence: the existing seven-object turntable gallery (built 2026-08-13), unchanged
in form. Framing added: GlowTact is designed to visualise pressure, not to
reconstruct geometry — the meshes come from applying *9DTact's* pipeline to GlowTact
frames, so the shape is present without having been designed for.
Scope: qualitative reconstruction; no quantitative height validation. 9DTact figures
are qualitative context — implementations and object sets differ.

### DAT / 03 — Shear tracking
Headline number: **phase correlation 0.79** aggregate vs 0.42 / 0.39 / 0.37 for
Lucas–Kanade, DIS and Farneback.
Evidence: the five arrow-field clips (marker-free, with the per-frame shear, rot,
div and slip readout burned in); the four-tracker comparison over five metrics.
Scope: **not in the paper** — later work, labelled as such. Ground-truth-free
evaluation. This is an optical shear estimate, not calibrated shear force;
`SCIENTIFIC_CONSTRAINTS.md` bars shear-force claims without results.

### DAT / 04 — Force prediction
Headline number: **0.106 N vs 0.145 N** macro-average MAE across four everyday
objects.
Evidence: Table I, both halves. Controlled probes by force bin (MAE): 0–0.5 N
0.056 vs 0.067, 0.5–2 N 0.058 vs 0.088, 2–20 N 0.209 vs 0.185; overall RMSE 0.276
vs 0.285. Everyday objects: balloon 0.087 / 0.134, light bulb 0.093 / 0.151, pipe
0.127 / 0.142, rope 0.117 / 0.153.
Scope: **the 2–20 N bin is stated, not hidden** — GlowTact is behind there. The
trade-off framing carries this: strongest where it was designed to be strong. Method
line: identical ResNet-18 regressors, ImageNet-pretrained, 90/10 split by spatial
location with all depths of one indentation kept in one split.

### DAT / 05 — Endurance
Two placeholder clips: one cut, one puncture.
Scope: a qualitative demonstration with no protocol. No lifetime, durability-margin
or maintenance claim — `SCIENTIFIC_CONSTRAINTS.md` treats durability as an
implication unless validated. It exists to discharge the conclusion's "more durable
skin", which the page otherwise asserts with nothing.

## One claim, one source

Per the `results-site` skill, no quantitative claim is typed loose into the markup.

- `design/data/results.json` is the single source for every published number.
- Each quantitative span in the HTML carries `data-metric="<json.path>"` alongside
  its literal text.
- `design/tools/audit_metrics.py` asserts literal == JSON for every marked span, and
  fails if a `data-metric` path does not resolve. `design/verify.py` gates on it.

Build-time injection was rejected: it would make `concept-03/index.html` generated,
breaking the established "edit the concept, re-run publish" workflow and adding a
second generated file. A checker achieves the same guarantee — stale prose becomes a
build failure — while the markup stays readable and crawlable.

Guarding the guard (`verification-that-can-fail`, rule 5): the checker asserts it
matched a non-zero number of spans, so a markup change cannot make it pass vacuously.

## Asset pipeline

| Asset | Source | Work |
|---|---|---|
| Shear clips x5 | `tactile_data/glowtact/analysis/shear_tracking/hicolor_mp4/` | Re-encode to H.264 High **yuv420p**. Present renders are unplayable in browsers: three `field_videos` are MPEG-4 Part 2, all `hicolor_mp4` are High 4:4:4 Predictive. Check arrow legibility at CRF before committing — the thin saturated strokes are what 4:2:0 damages. Posters extracted per clip. |
| SNR chart | `glowtact_materails/SNR.png` | Rebuild as inline SVG in the site's palette. Source data does not exist on disk and cannot be re-derived: SNR's denominator is the unloaded-frame standard deviation, and the `I0` references are absent for both sensors. Summary layer only — median curves, SNR = 3 threshold, the two box plots — digitized and labelled "redrawn from Fig. 10". Stated values (0.12 / 0.23 N, n = 10, SNR = 3) are exact. |
| Passive-contact trio | `tactile_data/glowtact/analysis/sensitive_pad/`, `gelsight_mini/analysis/sensitivity_test/` | Derive matched raw / diff / 3x panels for M&M, M6 nut, M5x6 |
| Endurance x2 | not yet supplied | Placeholders with the final aspect ratio and caption structure |
| Fingerprint series | `design/assets/images/fingerprint-pressure.jpg` | Already committed; currently unreferenced |

`design/ASSET_MANIFEST.md` records provenance for every new file.

## Verification

Extends the existing battery rather than adding a parallel one.

- `design/verify.py` — new metric-contract gate; prohibited-phrase list extended
  with the durability and superiority vocabulary this section could invite
  ("proven durable", "maintenance-free" already present, "outperforms").
- `design/browser_check.py` (`design` mode) — the results routes join the
  route x viewport matrix at 375 / 768 / 1280 / 1920: zero sub-AA contrast, zero
  interactive elements under 44 px, font-size census under the per-route ceiling,
  zero horizontal overflow, media aspect ratio preserved.
- New semantic assertions: every `<video>` in the results region resolves and has a
  browser-decodable codec; the SNR chart's drawn box-plot medians match the values
  in `results.json`; the shear clip selector switches source and poster together.
- Red-green each new assertion before committing it (`verification-that-can-fail`,
  rule 3): watch it fail against the defect it targets, then restore.
- `measured-design-audit` before and after; report deltas, not vibes.

## Out of scope

Re-deriving the SNR curves from the CNC dataset. Any lifetime or durability-margin
claim. Shear-force calibration. Publishing the raw datasets.
