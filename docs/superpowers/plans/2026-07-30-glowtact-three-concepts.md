# GlowTact Three-Concept Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three complete, visually distinct, interactive GlowTact research-site concepts plus a neutral comparison index under `design/`, verify them in a real browser, then commit and push the scoped result.

**Architecture:** Use dependency-free semantic HTML, CSS custom properties, responsive SVG, and small local JavaScript modules. Each concept is isolated in its own directory and owns its visual system and signature interaction; copied project media lives in `design/assets/`, while the review index uses a separate neutral stylesheet.

**Tech Stack:** HTML5, CSS3, SVG, vanilla JavaScript, Python local HTTP server and static verifier, browser automation for desktop/mobile/reduced-motion checks, Git.

---

## File Map

| Path | Responsibility |
|---|---|
| `design/index.html` | Neutral review index and concept comparison matrix |
| `design/shared/review.css` | Review-index-only visual system |
| `design/shared/review.js` | Preview pointer response and reveal enhancement |
| `design/concept-01/index.html` | Optical Coupling editorial research page |
| `design/concept-01/styles.css` | Bright optics-lab tokens, layout, states, motion |
| `design/concept-01/app.js` | Pressure cross-section, probe selection, reset, reveals |
| `design/concept-02/index.html` | Contact Atlas specimen-led page |
| `design/concept-02/styles.css` | Warm field-guide tokens, layout, states, motion |
| `design/concept-02/app.js` | Comparison lens, layer tabs, specimen selection, reveals |
| `design/concept-03/index.html` | Signal Chamber instrument-led page |
| `design/concept-03/styles.css` | Dark optical-instrument tokens, layout, states, motion |
| `design/concept-03/app.js` | Synchronized pressure views, finite playback, reveals |
| `design/assets/images/*` | Deliberately copied and web-sized source imagery |
| `design/assets/video/mms-contact.mp4` | Supplied muted contact video |
| `design/verify.py` | Static path, disclosure, semantics, and prohibited-claim checks |
| `design/ASSET_MANIFEST.md` | Existing asset specification plus implemented asset provenance |
| `design/README.md` | Existing design-pack context plus local review instructions |

## Task 1: Establish the Media Set and Verification Skeleton

**Files:**
- Create: `design/assets/images/hero-teaser.jpg`
- Create: `design/assets/images/fingerprint-pressure.jpg`
- Create: `design/assets/images/reconstruction-overview.jpg`
- Create: `design/assets/images/contact-geometry.jpg`
- Create: `design/assets/images/thread-mesh.png`
- Create: `design/assets/images/phillips-mesh.png`
- Create: `design/assets/images/ball-array-mesh.png`
- Create: `design/assets/video/mms-contact.mp4`
- Create: `design/verify.py`
- Modify: `design/ASSET_MANIFEST.md`

- [ ] **Step 1: Add the failing static verifier**

Create `design/verify.py` with checks for the four HTML routes, their local CSS and
JavaScript dependencies, mandatory mechanism disclosure, one `h1` per route,
meaningful image alternatives, non-empty link destinations, reduced-motion CSS,
and prohibited scientific phrases:

```python
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
ROUTES = [
    ROOT / "index.html",
    ROOT / "concept-01" / "index.html",
    ROOT / "concept-02" / "index.html",
    ROOT / "concept-03" / "index.html",
]
DISCLOSURE = (
    "Conceptual visualization. Geometry and optical paths are schematic and "
    "are not a calibrated mechanical or ray-tracing simulation."
)
PROHIBITED = (
    "revolutionary",
    "pixel-wise pressure",
    "calibrated pressure map",
    "indestructible",
    "maintenance-free",
)

class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_count = 0
        self.local_refs: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "img" and "alt" not in values:
            self.errors.append("image without alt")
        for key in ("href", "src"):
            value = values.get(key)
            if value == "#":
                self.errors.append(f"{tag} has placeholder {key}")
            if value and not value.startswith(("http:", "https:", "mailto:", "#", "data:")):
                self.local_refs.append(value.split("?", 1)[0].split("#", 1)[0])

def audit(route: Path) -> list[str]:
    text = route.read_text(encoding="utf-8")
    parser = AuditParser()
    parser.feed(text)
    errors = list(parser.errors)
    if parser.h1_count != 1:
        errors.append(f"expected one h1, found {parser.h1_count}")
    if route.name == "index.html" and route.parent.name.startswith("concept-"):
        if DISCLOSURE not in text:
            errors.append("missing conceptual visualization disclosure")
    lowered = text.lower()
    for phrase in PROHIBITED:
        if phrase in lowered:
            errors.append(f"prohibited phrase: {phrase}")
    for ref in parser.local_refs:
        target = (route.parent / ref).resolve()
        if not target.exists():
            errors.append(f"missing local reference: {ref}")
    return errors

failures: list[str] = []
for route in ROUTES:
    if not route.exists():
        failures.append(f"{route.relative_to(ROOT)}: missing route")
        continue
    for issue in audit(route):
        failures.append(f"{route.relative_to(ROOT)}: {issue}")

css_text = "\n".join(path.read_text(encoding="utf-8") for path in ROOT.rglob("*.css"))
if "@media (prefers-reduced-motion: reduce)" not in css_text:
    failures.append("styles: missing reduced-motion handling")

if failures:
    print("\n".join(f"FAIL {item}" for item in failures))
    sys.exit(1)
print(f"PASS: audited {len(ROUTES)} routes")
```

- [ ] **Step 2: Run the verifier and confirm the expected failure**

Run:

```powershell
python design/verify.py
```

Expected: exit code `1` with missing-route failures for all four HTML files.

- [ ] **Step 3: Prepare web media without changing source assets**

Use PowerShell and `System.Drawing` to create high-quality JPEG derivatives sized
for the page while retaining the original PNGs:

```powershell
New-Item -ItemType Directory -Force -Path design/assets/images,design/assets/video
Copy-Item -LiteralPath mms_gt.mp4 -Destination design/assets/video/mms-contact.mp4
Copy-Item -LiteralPath glowtact_materials/single_meshes_gt/single_meshes/glowtact_1_steep_01_screw_threads_mesh.png -Destination design/assets/images/thread-mesh.png
Copy-Item -LiteralPath glowtact_materials/single_meshes_gt/single_meshes/glowtact_1_steep_04_philips_head_mesh.png -Destination design/assets/images/phillips-mesh.png
Copy-Item -LiteralPath glowtact_materials/single_meshes_gt/single_meshes/glowtact_1_steep_03_cali_balls_mesh.png -Destination design/assets/images/ball-array-mesh.png
```

Create the four JPEGs at a maximum dimension of 2200 px from:

- `glowtact_materials/figures/teaser.png`
- `glowtact_materials/figures/fingerprints.png`
- `glowtact_materials/figures/3d_recon.png`
- `glowtact_materials/figures/glowtact_h.png`

Save them as `hero-teaser.jpg`, `fingerprint-pressure.jpg`,
`reconstruction-overview.jpg`, and `contact-geometry.jpg`, using JPEG quality 88.

- [ ] **Step 4: Record provenance**

Append an “Implemented review assets” table to `design/ASSET_MANIFEST.md` mapping
every derivative to its exact source path and noting that the originals are
unchanged.

## Task 2: Build the Neutral Review Index

**Files:**
- Create: `design/index.html`
- Create: `design/shared/review.css`
- Create: `design/shared/review.js`

- [ ] **Step 1: Create the semantic comparison page**

Create one `main` containing an intro, three linked `article` previews, and a
comparison table. Each concept card must name its signature:

```html
<article class="concept-card concept-card--optical" data-preview>
  <p class="concept-index">Concept 01</p>
  <h2>Optical Coupling</h2>
  <p>Mechanism-first editorial storytelling built around a pressure-driven cross-section.</p>
  <ul aria-label="Concept characteristics">
    <li>Bright optics lab</li>
    <li>Spacious editorial rhythm</li>
    <li>Interactive membrane–gel section</li>
  </ul>
  <a class="concept-link" href="./concept-01/">Review concept <span aria-hidden="true">↗</span></a>
</article>
```

Repeat with materially different previews for Contact Atlas and Signal Chamber.
Add a visually hidden skip link and exactly one page-level `h1`.

- [ ] **Step 2: Implement the neutral visual system**

In `review.css`, define review-only tokens, an asymmetric three-column composition
at wide widths, stacked mobile previews, 44 px focusable controls, explicit
hover/focus/active states, and a reduced-motion media query. Preview visuals use
CSS/SVG marks rather than screenshots so the index remains lightweight.

- [ ] **Step 3: Add progressive preview response**

In `review.js`, use `pointermove` only on fine pointers to update `--pointer-x`
and `--pointer-y` for a subtle transform capped at 6 px. Use
`IntersectionObserver` for one-time reveals. Do nothing when reduced motion is
requested.

- [ ] **Step 4: Run the verifier**

Run `python design/verify.py`.

Expected: the review index passes while the three concept routes remain missing.

## Task 3: Build Concept 01 — Optical Coupling

**Files:**
- Create: `design/concept-01/index.html`
- Create: `design/concept-01/styles.css`
- Create: `design/concept-01/app.js`

- [ ] **Step 1: Write the mechanism-first document**

Create semantic sections for hero, mechanism, principle, embodiments, evidence,
and citation. The mechanism contains:

```html
<input id="pressure" type="range" min="0" max="100" value="22"
       aria-describedby="pressure-state mechanism-note">
<output id="pressure-state" for="pressure">Light contact</output>
<div class="probe-switch" role="group" aria-label="Probe profile">
  <button type="button" data-probe="flat" aria-pressed="false">Flat</button>
  <button type="button" data-probe="sphere" aria-pressed="true">Sphere</button>
  <button type="button" data-probe="edge" aria-pressed="false">Edge</button>
</div>
```

The SVG includes named groups `probe-shape`, `membrane-path`, `air-gap`,
`coupling-patch`, `reflected-rays`, and `tactile-patch`. Use the exact mandatory
disclosure in `mechanism-note`.

- [ ] **Step 2: Apply the bright optics-lab visual contract**

Use product-specific CSS tokens such as `--acrylic`, `--diffuse`, `--nitrile`,
`--led-amber`, and `--coupling-amber`. Use borders plus surface shifts as the
single depth strategy. The focal mechanism must occupy at least half the desktop
hero width, while text stays below 68 characters per line.

- [ ] **Step 3: Implement pressure and probe behavior**

In `app.js`, map the range value to CSS variables and SVG attributes:

```javascript
function renderPressure(value) {
  const pressure = Number(value) / 100;
  root.style.setProperty("--pressure", pressure.toFixed(3));
  root.style.setProperty("--contact-width", `${18 + pressure * 62}%`);
  output.value =
    pressure < 0.08 ? "Air gap" :
    pressure < 0.55 ? "Partial coupling" :
    "Expanded coupling";
}
```

Probe selection updates `aria-pressed`, the SVG probe path, and a
`data-probe` attribute. Reset returns to sphere at value `0`. Reveal observers
are progressive and skipped in reduced-motion mode.

- [ ] **Step 4: Verify the route**

Run `python design/verify.py`.

Expected: concept 01 has no route-specific failure; concepts 02 and 03 remain
missing.

## Task 4: Build Concept 02 — Contact Atlas

**Files:**
- Create: `design/concept-02/index.html`
- Create: `design/concept-02/styles.css`
- Create: `design/concept-02/app.js`

- [ ] **Step 1: Write the specimen-led document**

Create semantic chapters for mechanism plate, form-factor catalog, pressure
imprints, geometry specimens, and methods ledger. The comparison stage contains
a native range input with `min="0"`, `max="100"`, and `value="52"`, plus buttons
for `membrane`, `coupling`, and `tactile` layers.

Use real `thread-mesh.png`, `phillips-mesh.png`, and `ball-array-mesh.png` images
as selectable specimens and label them “Qualitative reconstruction.”

- [ ] **Step 2: Apply the tactile field-guide visual contract**

Use `--paper`, `--paper-warm`, `--graphite`, `--registration`, and
`--measure-amber` tokens. Use faint inset paper layers as the single depth
strategy. Use serif section leads, compact sans-serif annotations, chapter
numbers, microtexture marks, and uneven editorial spacing.

- [ ] **Step 3: Implement the comparison lens and specimen model**

The lens control updates `--lens-position`. Layer buttons update `aria-pressed`
and `data-layer`. Specimen buttons update the active figure, title, and
description from an in-file immutable array:

```javascript
const specimens = Object.freeze({
  thread: {
    image: "../assets/images/thread-mesh.png",
    title: "M1 screw threads",
    note: "Fine repeated geometry remains spatially legible."
  },
  phillips: {
    image: "../assets/images/phillips-mesh.png",
    title: "Phillips head",
    note: "A recessed cross profile appears in the qualitative reconstruction."
  },
  balls: {
    image: "../assets/images/ball-array-mesh.png",
    title: "Calibration ball array",
    note: "Separated circular contacts preserve their spatial arrangement."
  }
});
```

- [ ] **Step 4: Verify the route**

Run `python design/verify.py`.

Expected: concepts 01 and 02 pass; concept 03 remains missing.

## Task 5: Build Concept 03 — Signal Chamber

**Files:**
- Create: `design/concept-03/index.html`
- Create: `design/concept-03/styles.css`
- Create: `design/concept-03/app.js`

- [ ] **Step 1: Write the instrument-led document**

Create an instrument header, tactile-signal hero, synchronized mechanism module,
form-factor rail, evidence chamber, and citation console. Include a pressure
range, play/pause button, three qualitative readouts, and the exact mandatory
disclosure.

The supplied video is muted, loop-free, `playsinline`, posterless with an adjacent
static fallback image, and never autoplayed when reduced motion is active.

- [ ] **Step 2: Apply the dark optical-instrument visual contract**

Use tokens `--camera-black`, `--nitrile`, `--optic-surface-1`,
`--optic-surface-2`, `--signal-amber`, and `--readout-dim`. Use close charcoal
surface shifts and one quiet ring as the single depth strategy. Keep amber below
roughly ten percent of visible area so signal remains meaningful.

- [ ] **Step 3: Implement synchronized pressure and finite playback**

Use one `render(value)` function to update the section, aperture, tactile signal,
readout copy, and range control. Automated playback uses `requestAnimationFrame`,
runs from zero to one in 2200 ms, stops at the end, and never loops:

```javascript
function tick(now) {
  if (!startedAt) startedAt = now;
  const progress = Math.min((now - startedAt) / 2200, 1);
  render(progress);
  if (progress < 1 && isPlaying) {
    frame = requestAnimationFrame(tick);
  } else {
    stopPlayback();
  }
}
```

Pointer or keyboard input cancels playback immediately. The video play state is
not coupled to the conceptual mechanism playback.

- [ ] **Step 4: Run the complete static verifier**

Run `python design/verify.py`.

Expected: `PASS: audited 4 routes`.

## Task 6: Add Review Instructions and Perform Static Quality Checks

**Files:**
- Modify: `design/README.md`
- Modify: `design/ASSET_MANIFEST.md`

- [ ] **Step 1: Add local review instructions**

Document:

```powershell
python -m http.server 4173 --directory design
```

and the four routes:

- `http://127.0.0.1:4173/`
- `http://127.0.0.1:4173/concept-01/`
- `http://127.0.0.1:4173/concept-02/`
- `http://127.0.0.1:4173/concept-03/`

- [ ] **Step 2: Check source quality**

Run:

```powershell
python design/verify.py
rg -n "TODO|FIXME|console\\.log|transition:\\s*all|href=\"#\"|photometric stereo|direct pressure measurement|calibrated pressure" design -g "*.html" -g "*.css" -g "*.js"
git diff --check
```

Expected: verifier passes; search returns no implementation defects or prohibited
claims; diff check has no whitespace error.

## Task 7: Browser Verification and Visual Refinement

**Files:**
- Modify if required: `design/index.html`
- Modify if required: `design/shared/review.css`
- Modify if required: `design/shared/review.js`
- Modify if required: `design/concept-01/*`
- Modify if required: `design/concept-02/*`
- Modify if required: `design/concept-03/*`

- [ ] **Step 1: Serve the site**

Run `python -m http.server 4173 --directory design` as a hidden background
process and confirm `http://127.0.0.1:4173/` returns status 200.

- [ ] **Step 2: Inspect desktop views**

Capture full-page screenshots at 1440 × 1000 for the review index and all three
concepts. Inspect focal hierarchy, type wrapping, image cropping, surface
strategy, visual distinction, missing resources, and horizontal overflow.

- [ ] **Step 3: Inspect mobile views**

Capture full-page screenshots at 390 × 844 for all four routes. Confirm every
control remains visible, content order makes sense, media preserves aspect ratio,
and no horizontal scrollbar appears.

- [ ] **Step 4: Exercise interactions**

Verify:

- Concept 01 pressure, three probes, reset, and output label;
- Concept 02 lens, three layers, and three specimens;
- Concept 03 pressure, finite play/pause, user cancellation, and non-looping end;
- concept navigation, skip links, and visible keyboard focus on every route.

- [ ] **Step 5: Verify reduced motion and console state**

Emulate reduced motion, reload each route, and confirm no translated or staggered
entrance remains. Collect browser console messages and network failures; expected
counts are zero.

- [ ] **Step 6: Refine and repeat**

Patch every observed overlap, weak hierarchy, unreadable label, missing state,
generic composition, or motion defect, then repeat Steps 2–5 until the evidence
is clean.

## Task 8: Completion Audit, Commit, and Push

**Files:**
- Stage: `design/`
- Stage: `docs/superpowers/plans/2026-07-30-glowtact-three-concepts.md`
- Preserve untracked: `glowtact_materials/`
- Preserve untracked: `mms_gt.mp4`
- Preserve untracked: `paper.pdf`

- [ ] **Step 1: Run fresh completion verification**

Run:

```powershell
python design/verify.py
git diff --check
git status --short
```

Re-open the final desktop and mobile screenshots and compare every acceptance
criterion in the approved specification to direct evidence.

- [ ] **Step 2: Review the exact staged scope**

Run:

```powershell
git add -- design docs/superpowers/plans/2026-07-30-glowtact-three-concepts.md
git diff --cached --check
git diff --cached --stat
git status --short
```

Confirm the three root source assets remain untracked and unstaged.

- [ ] **Step 3: Commit**

Run:

```powershell
git commit -m "feat(design): add three GlowTact website concepts"
```

- [ ] **Step 4: Push and verify**

Run `git push -u origin main`.

Expected: the remote reports the new `main` branch, and
`git status --short --branch` shows local `main` tracking `origin/main` with only
the intentionally preserved root source assets untracked.
