# GlowTact Results Section Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the site's thin evidence with a five-module results region that presents sensitivity, 3D reconstruction, shear tracking, force prediction and endurance as the paper's trade-off argument — simplicity without sacrifice.

**Architecture:** Stays a dependency-free static site. Semantic HTML in `design/concept-03/index.html` carries the modules; `styles.css` and `app.js` are extended, never joined by new files (every new top-level asset would need a rewrite rule in `publish.py`). Published numbers live in `design/data/results.json` and are cross-checked against the markup by a new gate in `design/verify.py`. Each fixed defect class is frozen as an assertion in `design/browser_check.py`.

**Tech Stack:** HTML5, CSS custom properties, vanilla JS, inline SVG, Python 3 stdlib, Playwright, ffmpeg, Pillow/NumPy.

**Design doc:** `docs/superpowers/specs/2026-08-14-glowtact-results-section-design.md`

**Skills:** @superpowers:test-driven-development @superpowers:verification-before-completion, plus `results-site`, `measured-design-audit`, `design-regression-guard`, `verification-that-can-fail`, `render-verify` from `Yuxiang-Ma/agent-skills`, and `dataviz` before writing any chart code.

---

## Conventions for every task

- Run from the repository root, `/home/yxma/website/glowtact.github.io`.
- Serve with `python3 -m http.server 4173 --directory design` for concept routes; from the repo root for the published root page.
- Commit at the end of every task. Never use `design/tools/release.py` until Task 12 — it pushes.
- After any check you add, red-green it: break the thing it guards, watch it fail, restore.

---

## Task 1: Baseline

**Files:** none created; establishes the starting numbers.

**Step 1: Confirm the tree is green before touching it**

```bash
python3 design/verify.py
python3 design/tools/publish.py
```
Expected: `PASS: audited 4 routes` and `index.html: unchanged`.

**Step 2: Separate the pre-existing work**

The tree carries uncommitted 3D-reconstruction work from 2026-08-13 (`design/assets/images/reconstruction/`, `design/assets/video/recon/`, and edits across `concept-03`, `concept-01`, `concept-02`, `design/index.html`, `index.html`). It is coherent and complete. Commit it on its own so the results work is separable:

```bash
git add design index.html
git commit -m "feat(concept-03): publish the 3D reconstruction turntable gallery"
```

**Step 3: Record the before-audit**

```bash
(python3 -m http.server 4173 --directory design >/dev/null 2>&1 &) ; sleep 1
python3 design/tools/audit_layout.py    | tee /tmp/audit-layout-before.txt
python3 design/tools/audit_contrast.py  | tee /tmp/audit-contrast-before.txt
python3 design/tools/audit_text.py      | tee /tmp/audit-text-before.txt
```
Keep the three files. Task 11 reports deltas against them, per `measured-design-audit` rule 1.

**Step 4: Commit** — nothing to commit beyond Step 2.

---

## Task 2: The metric contract

Every published number gets one source. Build the gate before the content that depends on it.

**Files:**
- Create: `design/data/results.json`
- Create: `design/tools/audit_metrics.py`
- Modify: `design/verify.py`

**Step 1: Write `design/data/results.json`**

Values are transcribed from `glowtact_materails/GlowTact.pdf` (Table I, Fig. 10) and `tactile_data/glowtact/analysis/shear_tracking/eval/metrics.json`. Each leaf is `{value, unit, source}`.

```json
{
  "sensitivity": {
    "min_detectable_force_median_glowtact": {"value": 0.12, "unit": "N", "source": "Fig. 10c"},
    "min_detectable_force_median_gelsight": {"value": 0.23, "unit": "N", "source": "Fig. 10c"},
    "snr_threshold": {"value": 3, "unit": "", "source": "Sec. V-C"},
    "probe_count": {"value": 10, "unit": "", "source": "Sec. V-A"},
    "force_range_max": {"value": 20, "unit": "N", "source": "Sec. V-A"},
    "passive_mm_mass": {"value": 1.0, "unit": "g", "source": "Fig. 9"},
    "passive_mm_force": {"value": 9.8, "unit": "mN", "source": "Fig. 9"},
    "passive_m6_mass": {"value": 2.0, "unit": "g", "source": "Fig. 9"},
    "passive_m6_force": {"value": 20.0, "unit": "mN", "source": "Fig. 9"},
    "passive_m5_mass": {"value": 2.4, "unit": "g", "source": "Fig. 9"},
    "passive_m5_force": {"value": 23.5, "unit": "mN", "source": "Fig. 9"}
  },
  "reconstruction": {
    "finest_thread": {"value": "M1", "unit": "", "source": "Sec. V-B"},
    "finest_thread_pitch": {"value": 0.25, "unit": "mm", "source": "Sec. V-B"},
    "ninedtact_limit": {"value": "M4", "unit": "", "source": "Sec. V-B"},
    "ninedtact_limit_size": {"value": 0.7, "unit": "mm", "source": "Sec. V-B"}
  },
  "shear": {
    "score_phasecorr": {"value": 0.79, "unit": "", "source": "eval/metrics.json aggregate"},
    "score_lk": {"value": 0.42, "unit": "", "source": "eval/metrics.json aggregate"},
    "score_dis": {"value": 0.39, "unit": "", "source": "eval/metrics.json aggregate"},
    "score_farneback": {"value": 0.37, "unit": "", "source": "eval/metrics.json aggregate"},
    "clip_count": {"value": 5, "unit": "", "source": "shear_tracking/hicolor_mp4"}
  },
  "force": {
    "rmse_glowtact": {"value": 0.276, "unit": "N", "source": "Table I-a"},
    "rmse_gelsight": {"value": 0.285, "unit": "N", "source": "Table I-a"},
    "mae_low_glowtact": {"value": 0.056, "unit": "N", "source": "Table I-a 0-0.5N"},
    "mae_low_gelsight": {"value": 0.067, "unit": "N", "source": "Table I-a 0-0.5N"},
    "mae_mid_glowtact": {"value": 0.058, "unit": "N", "source": "Table I-a 0.5-2N"},
    "mae_mid_gelsight": {"value": 0.088, "unit": "N", "source": "Table I-a 0.5-2N"},
    "mae_high_glowtact": {"value": 0.209, "unit": "N", "source": "Table I-a 2-20N"},
    "mae_high_gelsight": {"value": 0.185, "unit": "N", "source": "Table I-a 2-20N"},
    "macro_mae_glowtact": {"value": 0.106, "unit": "N", "source": "Table I-b"},
    "macro_mae_gelsight": {"value": 0.145, "unit": "N", "source": "Table I-b"},
    "frames_per_sensor": {"value": 14716, "unit": "", "source": "Sec. V-D"},
    "frames_controlled": {"value": 13116, "unit": "", "source": "Sec. V-D"},
    "frames_objects": {"value": 1600, "unit": "", "source": "Sec. V-D"}
  }
}
```

**Step 2: Write the failing checker**

`design/tools/audit_metrics.py` walks every route, finds elements carrying `data-metric="<dotted.path>"`, resolves the path in `results.json`, and compares the element's text to the value. Guard the guard: exit non-zero if zero spans matched.

```python
"""Assert every marked number in the markup matches design/data/results.json.

One claim, one source. A number edited in the HTML without editing the data
file -- or the reverse -- fails the build instead of shipping a stale claim.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "design" / "data" / "results.json"
ROUTES = [ROOT / "design" / "concept-03" / "index.html"]
NUMERIC = re.compile(r"-?\d+(?:\.\d+)?")


class MetricCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.found: list[tuple[str, str]] = []
        self._path: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        path = dict(attrs).get("data-metric")
        if path:
            self._path, self._text = path, []

    def handle_data(self, data):
        if self._path:
            self._text.append(data)

    def handle_endtag(self, tag):
        if self._path:
            self.found.append((self._path, "".join(self._text).strip()))
            self._path = None


def resolve(data: dict, path: str):
    node = data
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    failures: list[str] = []
    total = 0

    for route in ROUTES:
        collector = MetricCollector()
        collector.feed(route.read_text(encoding="utf-8"))
        total += len(collector.found)
        for path, text in collector.found:
            leaf = resolve(data, path)
            if leaf is None:
                failures.append(f"{route.name}: unknown metric path {path}")
                continue
            expected = str(leaf["value"])
            shown = NUMERIC.search(text)
            actual = shown.group(0) if shown else text
            if actual != expected:
                failures.append(
                    f"{route.name}: {path} shows {actual!r}, data says {expected!r}"
                )

    # Guard the guard: a markup change must not let this pass vacuously.
    if total == 0:
        failures.append("no data-metric spans found; the checker matched nothing")

    if failures:
        print("\n".join(f"FAIL {item}" for item in failures))
        return 1
    print(f"PASS: {total} metrics match {DATA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 3: Run it and watch it fail**

```bash
python3 design/tools/audit_metrics.py
```
Expected: `FAIL no data-metric spans found; the checker matched nothing` — no markup carries the attribute yet. This is the checker proving it can fail.

**Step 4: Add one real span, watch it pass**

In `design/concept-03/index.html`, the reconstruction section header already claims fine geometry. Add the thread claim with its attribute:

```html
<span data-metric="reconstruction.finest_thread_pitch">0.25</span>&nbsp;mm
```
Run again. Expected: `PASS: 1 metrics match design/data/results.json`.

**Step 5: Red-green it**

Change the span text to `0.35`, re-run, confirm `FAIL ... shows '0.35', data says '0.25'`, restore.

**Step 6: Gate it from `design/verify.py`**

Append before the final `if failures:` block:

```python
import subprocess
metrics = subprocess.run(
    [sys.executable, str(ROOT / "tools" / "audit_metrics.py")],
    capture_output=True, text=True,
)
if metrics.returncode != 0:
    failures.append(f"metrics: {metrics.stdout.strip()}")
```

Run `python3 design/verify.py`. Expected: `PASS: audited 4 routes`.

**Step 7: Commit**

```bash
git add design/data/results.json design/tools/audit_metrics.py design/verify.py design/concept-03/index.html
git commit -m "test(design): gate published numbers against one source of truth"
```

---

## Task 3: Page architecture

**Files:**
- Modify: `design/concept-03/index.html`
- Modify: `design/concept-03/styles.css`

**Step 1: Dissolve `record`**

Delete the `<section class="record">` wrapper and its three `capability-stack` articles. Keep the `<figure class="video-module">` — move it into the DAT / 01 stage built in Task 4. Its poster and source paths are unchanged.

**Step 2: Move `forms` above the results**

Relocate `<section class="forms">` so it precedes the results region. Add one line to its header noting that every measurement in the results below is from the flat sensor.

**Step 3: Wrap the results region**

```html
<section class="results" id="results" aria-labelledby="results-title">
  <header class="section-header results-header" data-reveal>
    <div>
      <p class="signal-label"><span>DAT</span> Results</p>
      <h2 id="results-title">Simple optics.<br>Nothing given up.</h2>
    </div>
    <p>
      Every result below tests the same doubt from a different side: whether a
      sensor this simple — one colour, no directional illumination, no
      photometric calibration — gives up what the complicated ones buy.
      All measurements are from the flat sensor.
    </p>
  </header>

  <ol class="results-index" aria-label="Results index">
    <li><a href="#sensitivity"><span>DAT / 01</span> Sensitivity</a></li>
    <li><a href="#reconstruction"><span>DAT / 02</span> 3D reconstruction</a></li>
    <li><a href="#shear"><span>DAT / 03</span> Shear tracking</a></li>
    <li><a href="#force"><span>DAT / 04</span> Force prediction</a></li>
    <li><a href="#endurance"><span>DAT / 05</span> Endurance</a></li>
  </ol>
  <!-- modules land here in Tasks 4-8 -->
</section>
```

**Step 4: Renumber reconstruction and move it inside**

Change its eyebrow from `DAT / 01` to `DAT / 02`; nest the existing section inside `.results`.

**Step 5: Fix the two dead references**

Header nav `#reconstruction` becomes `#results` with the label `Results`. The hero's secondary action `href="#record"` becomes `href="#results"` with the text `See the results`.

**Step 6: Style the region**

Add `.results`, `.results-header`, `.results-index` and a shared `.result-module` skeleton to `styles.css`, reusing the existing spacing scale and type variables. Do not introduce new colour tokens.

**Step 7: Verify**

```bash
python3 design/verify.py
grep -c 'href="#record"' design/concept-03/index.html   # expect 0
```

**Step 8: Commit**

```bash
git add design/concept-03/index.html design/concept-03/styles.css
git commit -m "feat(concept-03): open a results region and retire the record section"
```

---

## Task 4: DAT / 01 Sensitivity

Three steps, each committed: assets, chart data, module.

### Task 4a: Passive-contact assets

**Files:**
- Create: `design/assets/images/sensitivity/{mm,m6-nut,m5-screw}-{glowtact,gelsight}.jpg`
- Modify: `design/ASSET_MANIFEST.md`

**Step 1: Locate the matched frames**

```bash
grep -i -E "mms|m8_nut|m6|screw_m5" /home/yxma/tactile_data/glowtact/analysis/sensitive_pad/index.csv
ls /home/yxma/tactile_data/gelsight_mini/analysis/sensitivity_test/ | grep -iE "mm|nut|m5"
```
Pick the `_diff_x3` variant for both sensors so the amplification matches, and record which `id` each came from.

**Step 2: Derive the web assets**

```bash
python3 - <<'PY'
from PIL import Image
import pathlib
pairs = {...}  # {out_name: source_path} filled from Step 1
out = pathlib.Path("design/assets/images/sensitivity"); out.mkdir(parents=True, exist_ok=True)
for name, src in pairs.items():
    im = Image.open(src).convert("RGB")
    im.thumbnail((1400, 1400), Image.LANCZOS)
    im.save(out / f"{name}.jpg", quality=88, optimize=True)
PY
```

**Step 3: Record provenance in `design/ASSET_MANIFEST.md`** — one row per file, naming the source path and the `index.csv` id.

**Step 4: Commit**

```bash
git add design/assets/images/sensitivity design/ASSET_MANIFEST.md
git commit -m "feat(assets): matched passive-contact panels for both sensors"
```

### Task 4b: SNR chart data

**Files:**
- Create: `design/tools/digitize_snr.py`
- Create: `design/data/snr-curves.json`

**Step 1: Write the digitizer**

Panels separate by column in `glowtact_materails/SNR.png` (2205x975): panel a x 191-795, panel b x 984-1442, panel c boxes at x 1707-1798 and 1999-2085. Exclude y < 60 to drop the legend swatches. Amber is `r>200, 120<g<190, b<90`; blue is `b>140, r<90, 90<g<160`. For each column take the median y of matching pixels — the bold median line thresholds out while the alpha-blended scatter does not.

Calibrate with the axis decades: locate the x pixels of 10^-1, 10^0, 10^1 and the y pixels of the labelled ticks, then map linearly in log space. Write `{panel: {series: [[force, value], ...]}}` plus a `provenance` field reading `digitized from Fig. 10 of GlowTact.pdf; source data unavailable`.

**Step 2: Sanity-check the output**

```bash
python3 design/tools/digitize_snr.py --report
```
Assert before trusting it: both series are monotonically increasing in force over the decade above 1 N, the amber SNR curve sits above the blue one across the full range, and the extracted force range spans roughly 0.05-20 N. A digitizer that silently matched nothing returns empty series — fail loudly on fewer than 30 points per curve.

**Step 3: Cross-check against a stated value**

The paper states GelSight's median minimum detectable force is 0.23 N — the lowest force bin where its SNR reaches 3. Read the digitized blue SNR curve at SNR = 3 and confirm it lands within one force bin of 0.23 N. If it does not, the calibration is wrong; fix it before proceeding. This is the check that can actually fail.

**Step 4: Commit**

```bash
git add design/tools/digitize_snr.py design/data/snr-curves.json
git commit -m "feat(data): digitize the Fig. 10 summary curves"
```

### Task 4c: The sensitivity module

**Files:**
- Modify: `design/concept-03/index.html`, `styles.css`, `app.js`

**Step 1: Read the `dataviz` skill before writing any chart code.**

**Step 2: Markup**

```html
<article class="result-module" id="sensitivity" aria-labelledby="sensitivity-title">
  <header class="module-header" data-reveal>
    <p class="signal-label"><span>DAT / 01</span> Strip it to one colour and it should go numb</p>
    <h3 id="sensitivity-title">It resolves a gram.</h3>
    <p class="module-claim">
      Median minimum detectable force is
      <strong data-metric="sensitivity.min_detectable_force_median_glowtact">0.12</strong> N
      against <strong data-metric="sensitivity.min_detectable_force_median_gelsight">0.23</strong> N
      for GelSight Mini on the same apparatus, across
      <span data-metric="sensitivity.probe_count">10</span> probe geometries.
    </p>
  </header>
  <!-- chart, passive trio, fingerprint series, video -->
  <p class="module-scope">
    Passive placement is a demonstration, not a calibrated minimum-force
    measurement. GelSight Mini is a representative geometry-based baseline
    recorded on the same rig.
  </p>
</article>
```

**Step 3: Chart**

Embed the series inline so no `fetch` is needed and `publish.py` needs no new rewrite rule:

```html
<script type="application/json" id="snr-series">{ ...contents of snr-curves.json... }</script>
```
Render with a new `renderSnrChart()` in `app.js` building inline SVG: log-log axes, amber and blue median curves, the SNR = 3 threshold as a dashed rule, and a two-point median comparison replacing the original box plots — the ten per-probe values behind panel (c) are not available, so no quartiles are drawn. Title the chart with the finding, not the axes.

**Step 4: Verify**

```bash
python3 design/verify.py
```
Then render-verify: screenshot at 1280 and 375, look at the image, confirm both curves are visible and the threshold rule reads.

**Step 5: Commit**

```bash
git add design/concept-03 design/data
git commit -m "feat(concept-03): DAT/01 sensitivity, with the Fig. 10 summary redrawn"
```

---

## Task 5: DAT / 02 Reconstruction reframe

**Files:** Modify `design/concept-03/index.html`

**Step 1:** Add the framing paragraph — GlowTact is designed to visualise pressure, not reconstruct geometry; these meshes come from applying *9DTact's* pipeline to GlowTact frames, so the shape is present without having been designed for.

**Step 2:** Add the claim line with `data-metric` spans for `reconstruction.finest_thread_pitch` and `reconstruction.ninedtact_limit_size`.

**Step 3:** Add the scope footnote — qualitative reconstruction, no quantitative height validation; 9DTact figures are qualitative context with differing implementations and object sets.

**Step 4:** `python3 design/verify.py`, then commit.

```bash
git commit -am "copy(concept-03): frame reconstruction as geometry we did not design for"
```

---

## Task 6: DAT / 03 Shear tracking

**Files:**
- Create: `design/assets/video/shear/*.mp4`, `design/assets/images/shear/*-poster.jpg`
- Modify: `design/concept-03/index.html`, `styles.css`, `app.js`, `design/ASSET_MANIFEST.md`

**Step 1: Encode**

The masters are High 4:4:4 Predictive, which no browser decodes. CRF 20 yuv420p was compared against the master at 4x zoom and is visually indistinguishable.

```bash
SRC=/home/yxma/tactile_data/glowtact/analysis/shear_tracking/hicolor_mp4
mkdir -p design/assets/video/shear design/assets/images/shear
for f in "$SRC"/*.mp4; do
  n=$(basename "$f" .mp4)
  ffmpeg -v error -y -i "$f" -c:v libx264 -profile:v high -pix_fmt yuv420p \
         -crf 20 -preset slow -movflags +faststart "design/assets/video/shear/$n.mp4"
  ffmpeg -v error -y -i "$f" -vf "select=eq(n\,40)" -vframes 1 \
         -q:v 3 "design/assets/images/shear/$n-poster.jpg"
done
```

**Step 2: Assert the encode is web-playable**

```bash
for f in design/assets/video/shear/*.mp4; do
  ffprobe -v error -select_streams v:0 -show_entries stream=profile,pix_fmt \
          -of csv=p=0 "$f"
done
```
Expected: every line `High,yuv420p`. Any `4:4:4` or `Simple Profile` line is a failure.

**Step 3: Markup**

Five clips named `1_fingertip`, `2_coin`, `3_go_piece`, `4_phillips_head_screw_M5`, `5_pan_head_screw_M2`. One stage with a segmented selector; the selector swaps `<source>` and `poster` together. The burned-in readout already shows shear, rot, div and slip per frame, so no overlay is needed.

Add the tracker comparison as a compact four-row table with `data-metric` spans for the four scores, headed by the finding: phase correlation scores `0.79` against `0.42`, `0.39` and `0.37`.

**Step 4: Scope footnote**

Label the module **not in the paper** — later work. Ground-truth-free evaluation. An optical shear estimate, not calibrated shear force.

**Step 5: Verify, then commit**

```bash
python3 design/verify.py
git add design/assets/video/shear design/assets/images/shear design/concept-03 design/ASSET_MANIFEST.md
git commit -m "feat(concept-03): DAT/03 marker-free shear tracking"
```

---

## Task 7: DAT / 04 Force prediction

**Files:** Modify `design/concept-03/index.html`, `styles.css`

**Step 1:** Claim line — macro-average MAE `0.106` N against `0.145` N across four everyday objects, both `data-metric` spans.

**Step 2:** Force-bin comparison as a small grouped bar chart in inline SVG (three bins x two sensors), amber and blue. The 2-20 N bar is the one where GlowTact is higher; draw it plainly.

**Step 3:** Per-object table (4 rows) inline. Method line: identical ResNet-18 regressors, ImageNet-pretrained, 90/10 split by spatial location with all depths of one indentation kept in one split, `frames_per_sensor` frames per sensor.

**Step 4:** Scope footnote states the 2-20 N result explicitly: GlowTact's advantage is at low force, and it is behind above 2 N.

**Step 5:** Verify and commit.

```bash
git commit -am "feat(concept-03): DAT/04 force prediction, low-force strength stated honestly"
```

---

## Task 8: DAT / 05 Endurance

**Files:** Modify `design/concept-03/index.html`, `styles.css`

**Step 1:** Two placeholder figures — cut and puncture — at the final aspect ratio, each with a `data-pending="true"` attribute and visible `AWAITING FOOTAGE` state. No `<video>` element until the files exist, so the link checker stays green.

**Step 2:** Scope footnote — a qualitative demonstration with no protocol; no lifetime, durability-margin or maintenance claim. State why it exists: the paper's conclusion claims a more durable skin, and this is where that claim will be answered.

**Step 3:** Verify and commit.

```bash
git commit -am "feat(concept-03): DAT/05 endurance placeholders"
```

---

## Task 9: Freeze the regressions

**Files:** Modify `design/browser_check.py`

**Step 1:** Add the results routes to the `design` mode matrix at 375 / 768 / 1280 / 1920 — contrast, touch targets, font-size census, horizontal overflow, media aspect ratio.

**Step 2:** Add three semantic assertions:

- every `<video>` in `#results` has `readyState >= 1` after `loadedmetadata`, proving the codec decodes — a source that 404s or fails to decode is caught here rather than by a visitor;
- the SNR chart's drawn median markers equal `results.json`'s medians within 0.005 N, read via `page.evaluate` from the page's own scale function so the test and the page share one source of truth;
- the shear selector swaps `<source>` and `poster` together — assert both change, since swapping only one is the plausible bug.

**Step 3: Red-green each.** Break the thing each assertion guards, watch it fail, restore. An assertion that has never failed is not evidence.

**Step 4:**

```bash
(python3 -m http.server 4173 --directory design >/dev/null 2>&1 &) ; sleep 1
GLOWTACT_CHECK_MODE=all python3 design/browser_check.py
```

**Step 5: Commit**

```bash
git commit -am "test(design): guard the results region as regressions"
```

---

## Task 10: Measured design audit

**Files:** Modify `design/concept-03/styles.css` as the numbers convict.

**Step 1:** Re-run the three audits from Task 1 into `/tmp/audit-*-after.txt`.

**Step 2:** Fix only what the numbers convict. Contrast failures get a numerically solved minimum shift, never a hand-picked "bit darker". Watch for the polarity bug: a muted token tuned for light panels gets worse when darkened on an inverted panel.

**Step 3:** Font-size census must not have grown. The results region reuses the existing scale; any new distinct size is sprawl and gets snapped.

**Step 4:** Report deltas — failures before to after — not vibes.

**Step 5: Commit**

```bash
git commit -am "style(design): bring the results region to AA and one type scale"
```

---

## Task 11: Condensation and render-verify

**Step 1:** Word-count the page stripped of tags and scripts. Every paragraph: can a figure caption carry it? Then delete the paragraph. Every chart: does the title state the finding rather than the axes?

**Step 2:** Screenshot at 1280 and 375, full page, and **look at both**. Confirm no module's evidence is invisible, no chart curve is hidden under another, no placeholder renders literally.

**Step 3: Commit** any trims.

---

## Task 12: Publish

**Step 1:**

```bash
python3 design/tools/publish.py
python3 design/verify.py
```
`publish.py` link-checks every local reference and refuses to write a broken root.

**Step 2:** Serve from the **repository root** and confirm the published root resolves `design/assets/...`:

```bash
(python3 -m http.server 4173 >/dev/null 2>&1 &) ; sleep 1
curl -sI http://127.0.0.1:4173/design/assets/video/shear/1_fingertip.mp4 | head -1
```

**Step 3:** Release.

```bash
python3 design/tools/release.py "feat(site): publish the five-result evidence region"
```

**Step 4:** Verify the live deployment — fetch `https://glowtact.github.io/` and assert the new section strings and asset URLs return 200. Local success does not imply the deployment picked everything up.
