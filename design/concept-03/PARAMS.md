# Concept-03 design parameters — accepted baseline

Frozen 2026-08-06 after interactive review. Each row is a knob a future
session may retune; everything else in `app.js` is derived. When changing a
value, run `GLOWTACT_CHECK_MODE=design python design/browser_check.py` —
the guards encode the acceptance criteria below.

## Contact physics (drives all three views)

| Constant | Value | Meaning | Accepted bounds / notes |
|---|---|---|---|
| `CONTACT_SATURATION` | 0.985 | Coupled-area fraction at full compression | Do not exceed 0.99: a real P2500 interface always traps some air, and the STATE 02 copy says so |
| `CONTACT_ONSET` | 2 | Logistic steepness of the contact law | Raised mid-range coupling so number and picture grow together |
| `CONTACT_BIAS` | 1.4 | Logistic midpoint bias | Lower = more mid-range coupling |
| `INTIMACY_DEPTH` | 0.055 | Penetration for full optical intimacy | Measured to act as near-pure gain (0.055–0.22 all give the same curve shape); low end maximizes saturation |
| `CONTACT_FLOOR` | 0.55 | Optical coupling of a barely-touching patch | |
| `FIELD_SIZE` / `PROFILE_SIZE` | 61 / 97 | Field & section sampling | Resolves the 12×12 grain population without aliasing |
| grain falloff / `cuspPower` | 1.1 / 1.8–2.3 | Grain profile shape | At the old 2.7 falloff a grain kept only 7% of its height at its nominal radius, so grains never met: 60% flat land, p99 = 5.5× median. At 1.1 with dome-shaped cusps: 19% land, p99 = 2.6× median (sieve-graded grit is ~2×) |
| `height` spread | 0.82–1.00 | Grain height band | Sieve-graded abrasive has a narrow height distribution |
| `gridSize` (createRoughness) | 12 | Grains per axis | = ~9 µm period in the ~100 µm window; radii sized so grains abut (sieve-graded sandpaper, no flat land) |

## Cross-view consistency (single source of truth)

| Constant | Value | Meaning | Accepted bounds / notes |
|---|---|---|---|
| `contactChordUnits(area)` | 14 + √area·104 | THE contact-width law at device scale | Consumed by the device chord AND the camera patch; never fork it |
| `CAMERA_VIEW_SPAN` | 260 | Membrane width the camera images (device units) | Full-compression patch = ~45 % of frame; guard asserts camera = chord/span at 60 % and 100 % |
| `MACRO_MEMBRANE_THICKNESS` | 22 | Drawn 3 mil membrane band | Ordering constraint: thicker than the rest air gap (18) |
| `MACRO_INDENTER_TRAVEL` | 34 | Post-contact indenter travel | Gel depth is derived from it; tip stays on the membrane to 0.001 px |

## Rendering conventions (display only — bit-exact to physics)

| Constant | Value | Meaning | Accepted bounds / notes |
|---|---|---|---|
| `MICRO_HEIGHT_EXAGGERATION` | 0.12 | 3D vertical exaggeration, canvas fraction per unit roughness | Measured: 0.24 drew grains at 1:1 (tall ones 2.35:1) against a ~0.2:1 physical aspect and read as needles; 0.12 gives ~0.5:1; below ~0.10 grains merge and the truncation stops reading |
| `MIN_SEAM` (2D) | 1.7 px | Minimum drawn thickness of the coupled seam | The seam physically closes to a hairline at full coupling; this keeps it legible without detaching it from the gel contour it follows |


- 2D section: gamma-stretched vertical exaggeration (`SECTION_DISPLAY_GAMMA`
  0.45); any strictly increasing map keeps the coupled fraction identical.
- 3D deformation: per-vertex truncation at the membrane plane (`min(h, plane)`),
  never a blend — partially coupled grains show a flat cap on intact flanks.
- Amber ink == coupled fraction exactly (no gamma); the readout and the
  picture must not disagree (guarded at 3 pp).
- Membrane grid and uncoupled edges fade with `1 − area·1.05`: once contact is
  near-complete there is no gap for the lattice to hover in.
- 2D membrane standoff: 2.5 px → 0.5 px as coupling completes (sliding
  legibility contract; clearance metric covers the uncoupled region only).

## Known, accepted approximations

- 2D slice vs field: worst ≈ 5 pp — the variance floor of a genuine 1-D slice
  (360 and 720 candidate rows find the same optimum). Kept honest on purpose.
- Camera beyond ~80 % pressure reads fully dark while the model says 91–98 %:
  footprint saturates; the remaining distinction is carried by grey level,
  as on a real sensor.
