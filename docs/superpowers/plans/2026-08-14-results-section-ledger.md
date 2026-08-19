# Results Section — Debug Ledger

Companion to [`2026-08-14-glowtact-results-section.md`](2026-08-14-glowtact-results-section.md).
Every defect found while building the results region, the evidence that exposed
it, and the check that proved the fix. Kept in the repo rather than in a session
transcript so it survives context loss.

**Status:** all five modules built and committed; 21 commits, unpushed.
`design/verify.py` passes with 36 metrics bound; `browser_check.py` passes in
all three modes.

## Ledger

| found | evidence | fix | verified by |
|---|---|---|---|
| Shear clips 404 on the published root after the first switch | 2 failed requests to `/assets/video/shear/…` on the root page; the concept route was clean | derive the asset directory from the markup instead of hardcoding `../`, which `publish.py` rewrites | 5 clip switches on both routes, 0 failed requests, `readyState` 4 each |
| `publish.py` cannot see runtime-built paths at all | the above shipped past a link checker that passes | `check_runtime_paths()` rejects `'../assets/'` string literals in `app.js` | red-green: reintroduced the literal, publish aborted |
| Codec assertion could not discriminate | mutation shipping a 4:4:4 master still PASSED | replaced the runtime `readyState` check with a static `ffprobe` profile check | red-green: same mutation now fails on `High 4:4:4 Predictive` |
| Chart-geometry assertion compared a function against itself | offsetting `snrScaleX` by 12 px moved both the path and the expectation; test PASSED | share only the axis constants; re-derive the log mapping independently in the test | red-green: same mutation fails with drawn 125.80 vs expected 113.75 |
| Reconstruction module had no scope footnote | the scope-footnote assertion listed `['reconstruction']` | moved its caveat onto the shared `.module-scope` contract | assertion passes across all 5 modules |
| Microscope tabs wrapped into the shear selector | `ArrowLeft from 2D did not wrap to 3D` | scope the tab query to `.micro-tabs`; the shear tablist was being swept into it | existing behaviour suite passes |
| Chart headline stated a claim the chart did not show | "two decades below" vs measured 304× SNR at 0.1 N | generate the headline from the plotted series | assertion that the headline carries the plotted ratio |
| 9 distinct font sizes against a ceiling of 8 | `signal@phone: [12,13,14,15,16,22,32,38,54]` | snap 13/15 px to the declared fine/label steps; hero number rides the headline clamp | design-mode type-scale gate passes |
| `.chart-figure` full-bleed leaked into the force layout | chart and table stacked instead of sitting side by side | scope the rule to `.sensitivity-layout` | render check at 1280 |
| Caption eyebrow rule stacked inline metrics | "An M&M at / 1.0 / g — / 9.8 / mN" | scope `display:block` to `:first-child` | caption reads as one line |
| Passive grid lost its sensor labels below 700 px | header row hidden; columns unlabelled | drop the spacer cell instead of the header | header reads "GLOWTACT \| GELSIGHT MINI" at 375 px |
| 4.1 MB of turntables fetched on load, 6 below the fold | 6.0 MB first load, all 7 clips buffered 11.5 s | `preload="none"`, autoplay removed; the existing observer loads on view | 6.0 MB → 1.9 MB, 0 video bytes on load |
| 1.5 MB of images fetched on load | measured transfer by type | `loading="lazy"` on 14 of 15; hero stays eager as LCP | 1.9 MB → 1.34 MB, hero still completes |
| Lazy loading hung the harness | `wait_for_function` timeout: below-fold images never complete | harness opts images into eager before waiting | full suite exit 0 |
| Force-bin numbers forked into `app.js` | same 6 values in `results.json`, prose, and `FORCE_BINS`; only 2 of 3 checked | bins read from an in-page JSON block; `audit_metrics.py` walks embedded JSON | 30 → 36 metrics; red-green on 3 failure modes |
| A commit was made against a red build | `&&` chained on `tail`'s exit code, not the checker's | capture and test the checker's exit code explicitly | subsequent commits gated on `$?` |
| `digitize_snr.py` crashed instead of reporting | colour-collapse mutation raised `IndexError` | report and return before the range checks index empty lists | red-green: reports "0 amber, 397 blue columns" |

## Rejected ideas

| variant | motivation | measured result | verdict |
|---|---|---|---|
| Re-derive the SNR curves from the CNC dataset | avoid digitizing a raster | SNR's denominator is the unloaded-frame standard deviation; the `I0` references are absent for both sensors | **rejected** — not computable from released data |
| Runtime `readyState` check for video codecs | catch undecodable files in a real browser | this Chromium decodes High 4:4:4 Predictive in software: readyState 4, videoWidth 492 | **rejected** — cannot discriminate; use a static profile check |
| Scroll the document to prime lazy images | keep the harness testing the real loading path | Chromium decides what to fetch on a later frame than a scripted scroll; 14 images stayed unfetched | **rejected** — opt them into eager instead |
| Signal-chain ordering (presence → shape → motion → magnitude) | a clean narrative order for the five results | describes any VBTS — GelSight does all four — so it never says why this sensor matters | **rejected** in favour of the trade-off framing |
| Two-tier layout demoting force prediction | match layout weight to available material | Table I is the paper's most rigorous result; demoting it for lacking imagery is a design decision overriding a scientific one | **rejected** |
| `diff_x3` frames for the passive comparison | match the paper's Fig. 9 presentation | the two sets are not comparable: `sensitive_pad` is `diff_mode: dark`, the GelSight set is signed and centred at 128 | **rejected** — raw frames are the only matched representation |
| Validator-passing amber (`#c07d1e`) | clear the lightness-band check | breaks colour identity with the rest of the page; `SCIENTIFIC_CONSTRAINTS.md` fixes GlowTact = amber | **rejected** — pay with secondary encoding instead |

## Model probe after the cusp change

Sweeping the page's own model (`in-page-model-probe`) after sharpening the
grain profile, to confirm the contact law was not disturbed:

- coupled area monotonic in pressure: **true**
- contact chord monotonic in pressure: **true**
- saturation 98.509 % against `CONTACT_SATURATION` 0.985
- camera patch at full compression 45.1 %, against PARAMS' "~45 % of frame"
- state transitions: 00 → 01 at p = 0.27, 01 → 02 at p = 0.53, each entered once

Grain statistics over a 240×240 sampling, dome → cusp:
flat land 13 % → 7 %, p99/median 2.38× → 2.27×.

## Open

1. **Nothing is pushed.** 21 commits sit on `main` locally.
2. **`a34aef8` is a mixed commit** — it includes a concurrent session's work
   (reconstruction re-encodes, `audit_layout.py`, `capture_pages.py`) alongside
   the regression guards, and its message does not say so.
3. **Endurance footage does not exist.** DAT/05 holds two placeholders with no
   `<video>` element so the link checker stays green. New clips need CRF 20 /
   yuv420p and `preload="none"`, both of which are now asserted.
4. **The passive comparison uses an M8 nut**, not the paper's M6, because the
   released matched set has no M6. No mass is claimed for it.

## Shear preprocessing A/B (2026-08-14)

Asked whether CLAHE is the right enhancement for the marker-free shear
pipeline (`TheProbe/ProbingPi/glowtact_camera/shear.py`, `enhance()`,
currently `clip=3.0, tiles=8`). Twelve variants, identical frames, scored with
the module's own ground-truth-free harness.

`score` is deliberately unused: it is normalised within the set of trackers
evaluated, so it reads 1.0 for a lone tracker and cannot compare preprocessing
at all. The comparison uses the absolute metrics.

Phase correlation, 5 clips, stride 2:

| variant | coherence | max shear px | noise floor | indent intrusion |
|---|---|---|---|---|
| clahe 3.0/8 (current) | 0.5444 | 2.280 | 0.0335 | 0.490 |
| clahe 5.0/8 | 0.5660 | 2.363 | 0.0336 | 0.506 |
| local normalisation | 0.6084 | 2.470 | 0.0334 | **0.524** |

Ranked on coherence over 3 clips, both trackers: local norm +11.2 %,
clahe 5.0/8 +4.0 %, equalizeHist +1.5 %, clahe 3.0/4 +0.7 %, **current**,
clahe 3.0/16 −0.5 %, bilateral+clahe −3.7 %, clahe 1.5/8 −6.4 %, unsharp
−11.1 %, **no enhancement −19.6 %**, high-pass only −20.4 %, gamma 0.5 −26.5 %.

Findings:

1. **Enhancement earns its place.** Removing it costs 19.6 % coherence, and
   corner count drops 1500 → 1346. CLAHE beats every alternative tried except
   local normalisation.
2. **`clip=3.0` is slightly conservative.** `clip=5.0` gives +4 % coherence and
   +4 % recovered shear at an unchanged noise floor — same algorithm, one
   constant.
3. **Local normalisation is the strongest for phase correlation, and is not a
   drop-in.** It raises coherence 12 % and recovered shear 8 % at the same
   noise floor. The obvious objection — that dividing by local standard
   deviation homogenises the field and inflates *agreement* while erasing
   motion — was tested and refuted: max shear rises with coherence, so it
   recovers more motion rather than smoothing. But it worsens
   `indent_intrusion` 0.490 → 0.524, which is the failure mode the module is
   built around (a straight press must not read as shear), and it degrades LK
   coherence badly (0.2974 → 0.2055). It is a phase-correlation-specific
   option, not a general improvement.

Caveats: all metrics are ground-truth free; five clips from one session; no
change has been made to the pipeline, which lives in another repository.
