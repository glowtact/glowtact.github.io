# GlowTact Scale-Transition Mechanism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved direction C so the global mechanism has a centered indentation and camera, a near-flat bold approximately 9 um interface, an explicit transition to a sharper approximately 100 um local field, and spatially distributed 2D/3D contact.

**Architecture:** Keep the existing static HTML, CSS, SVG, and Canvas stack. Add stable semantic hooks to the global SVG, replace the current broad correlated roughness with deterministic jittered asperity models, and preserve one normalized pressure value as the shared state for macro geometry, local contact, and centered camera output.

**Tech Stack:** Semantic HTML, inline SVG, CSS custom properties, Canvas 2D, vanilla JavaScript, Python Playwright verification, GitHub Pages.

---

## File map

- `design/browser_check.py`: executable acceptance checks for centering, scale labels, spatial contact distribution, tabs, shared pressure, reduced motion, and runtime errors.
- `design/concept-03/index.html`: static global camera, optical cone, scale-transition marker, local-window labeling, and contact-segment container.
- `design/concept-03/app.js`: deterministic macro geometry, jittered local 2D/3D asperity generation, threshold contact, and synchronized rendering.
- `design/concept-03/styles.css`: global camera craft, bold interface, scale-transition presentation, spiky local rendering, centered camera output, and responsive treatment.
- `design/review-realism/index.html`: temporary review route; delete only after the selected production design passes local verification.

### Task 1: Lock the approved visual contract in browser checks

**Files:**
- Modify: `design/browser_check.py:221-265`

- [ ] **Step 1: Add global-scale, camera-centering, and local-contact helpers**

Add these helpers above `check_signal_interactions`:

```python
def element_center(page: Page, selector: str) -> tuple[float, float]:
    box = page.locator(selector).bounding_box()
    if not box:
        raise AssertionError(f"signal: {selector} has no rendered bounding box")
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def assert_centered(page: Page, subject: str, container: str, tolerance: float = 1.0) -> None:
    subject_x, subject_y = element_center(page, subject)
    container_x, container_y = element_center(page, container)
    if abs(subject_x - container_x) > tolerance or abs(subject_y - container_y) > tolerance:
        raise AssertionError(
            f"signal: {subject} center {(subject_x, subject_y)} does not match "
            f"{container} center {(container_x, container_y)}"
        )


def assert_horizontally_centered(
    page: Page, subject: str, container: str, tolerance: float = 1.0
) -> None:
    subject_x, _ = element_center(page, subject)
    container_x, _ = element_center(page, container)
    if abs(subject_x - container_x) > tolerance:
        raise AssertionError(
            f"signal: {subject} horizontal center {subject_x} does not match "
            f"{container} horizontal center {container_x}"
        )


def contact_thirds(page: Page) -> set[int]:
    panel = page.locator("#micro-svg").bounding_box()
    if not panel:
        raise AssertionError("signal: 2D microscope has no rendered box")
    centers = page.locator(".micro-contact-segment").evaluate_all(
        "elements => elements.map(element => { const box = element.getBoundingClientRect(); return box.x + box.width / 2; })"
    )
    return {
        min(2, max(0, int((center - panel["x"]) / (panel["width"] / 3))))
        for center in centers
    }
```

- [ ] **Step 2: Extend `check_signal_interactions` with the approved requirements**

Immediately after navigation, assert the static hooks and labels. Then test three pressure values before switching to 3D:

```python
    for selector in (
        ".macro-camera-lens",
        "#macro-field-of-view",
        ".macro-scale-marker",
        ".macro-interface-note",
    ):
        if page.locator(selector).count() != 1:
            raise AssertionError(f"signal: missing approved global element {selector}")

    if "9" not in page.locator(".macro-interface-note").inner_text():
        raise AssertionError("signal: global interface does not disclose ~9 um scale")
    if "100" not in page.locator(".micro-window-label").inner_text():
        raise AssertionError("signal: microscope does not disclose ~100 um window")

    assert_horizontally_centered(page, "#macro-indenter", ".macro-stage svg")
    assert_horizontally_centered(page, ".macro-camera-lens", ".macro-stage svg")

    pressure = page.locator("#signal-pressure")
    for value in ("0", "55", "100"):
        pressure.fill(value)
        assert_centered(page, ".camera-contact", ".camera-stage")

    pressure.fill("55")
    if contact_thirds(page) != {0, 1, 2}:
        raise AssertionError("signal: intermediate 2D contact is not spatially distributed")
```

- [ ] **Step 3: Run the behavior check and confirm it fails for the missing direction C hooks**

Run:

```powershell
$env:GLOWTACT_CHECK_MODE='behavior'
python design/browser_check.py
```

Expected: FAIL containing `missing approved global element .macro-camera-lens`.

### Task 2: Build the global direction C cutaway and scale transition

**Files:**
- Modify: `design/concept-03/index.html:190-267`
- Modify: `design/concept-03/app.js:21-27,201-251`

- [ ] **Step 1: Replace large global asperities with a bold near-flat interface**

Keep `.macro-gel`, but replace the static `.macro-texture-line` path with a near-flat baseline and add a visible disclosure:

```html
<path class="macro-texture-line" d="M70 286 C260 284 660 288 850 286"></path>
<g class="macro-interface-note">
  <path d="M98 304H262"></path>
  <text x="98" y="320">~9 UM TEXTURE / EXAGGERATED</text>
</g>
```

The dynamic renderer will preserve only sub-pixel-to-low-pixel texture variation around this baseline.

- [ ] **Step 2: Replace the existing camera symbol with a centered optical assembly**

Use stable hooks for the test and renderer:

```html
<path id="macro-field-of-view" class="macro-field-of-view" d="M422 448L460 372L498 448Z"></path>
<g class="macro-camera" aria-label="Camera aligned with indentation axis">
  <path class="macro-camera-body" d="M408 482H512L528 536H392Z"></path>
  <circle class="macro-camera-ring" cx="460" cy="486" r="30"></circle>
  <circle class="macro-camera-lens" cx="460" cy="486" r="20"></circle>
  <circle class="macro-camera-aperture" cx="460" cy="486" r="8"></circle>
  <text x="460" y="540" text-anchor="middle">CAMERA / CENTER AXIS</text>
</g>
```

- [ ] **Step 3: Add the explicit microscope sampling marker**

Place it on the global interface without covering the center axis:

```html
<g class="macro-scale-marker" aria-label="Magnified local surface sample">
  <circle cx="626" cy="286" r="22"></circle>
  <path d="M642 270L716 196H844"></path>
  <text x="844" y="184" text-anchor="end">ZOOM TO ~100 UM WINDOW</text>
</g>
```

Update the microscope footer label to:

```html
<span class="micro-window-label">LOCAL WINDOW / ~100 UM / QUALITATIVE</span>
```

- [ ] **Step 4: Make the macro geometry centered and scale-separated**

Replace `macroSurfaceY` and adjust `renderMacro`:

```javascript
function macroSurfaceY(x) {
  return 286 + Math.sin(x * 0.047 + 0.8) * 0.9 + Math.sin(x * 0.131) * 0.45;
}

function macroIndentationWeight(x) {
  return Math.exp(-Math.pow((x - 460) / 172, 4));
}
```

Use `macroIndentationWeight(x)` for membrane displacement, remove pressure from
the gel surface, and set the field-of-view opacity from contact ratio rather than
moving it laterally. Every global center remains `x = 460`.

- [ ] **Step 5: Run the behavior check**

Run the same behavior command. Expected: the missing-global-element and scale-label assertions pass; the test still fails at `intermediate 2D contact is not spatially distributed`.

- [ ] **Step 6: Commit the global cutaway**

```powershell
git add design/concept-03/index.html design/concept-03/app.js design/browser_check.py
git commit -m "feat(design): add scale-transition camera cutaway"
```

### Task 3: Replace the local surface with spatially distributed asperities

**Files:**
- Modify: `design/concept-03/app.js:36-117,155-169,253-403`
- Modify: `design/concept-03/index.html:327-375`

- [ ] **Step 1: Replace the broad correlated field generator**

Use one jittered asperity per grid cell so peak locations cover the whole local
window without forming a central mound:

```javascript
const FIELD_SIZE = 41;
const PROFILE_SIZE = 65;

function generateAsperityCenters(columns, rows, random) {
  const centers = [];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      centers.push({
        x: (column + 0.2 + random() * 0.6) / columns,
        y: (row + 0.2 + random() * 0.6) / rows,
        sx: 0.018 + random() * 0.025,
        sy: 0.018 + random() * 0.025,
        height: 0.68 + random() * 0.32,
      });
    }
  }
  return centers;
}

function cuspHeight(x, y, center) {
  const dx = (x - center.x) / center.sx;
  const dy = (y - center.y) / center.sy;
  return center.height * Math.exp(-Math.sqrt(dx * dx + dy * dy) * 2.7);
}
```

Create an 8 by 8 jittered center set, add a base-field contribution no larger
than 15% of total amplitude, normalize to `[0, 1]`, and preserve seed `2500`.

- [ ] **Step 2: Generate a sharper deterministic 2D profile**

Use 13 jittered peak bins, triangular/cusp falloff, and a weak baseline:

```javascript
function generateAsperityProfile(size, seed) {
  const random = seededRandom(seed);
  const peaks = Array.from({ length: 13 }, (_, index) => ({
    x: (index + 0.18 + random() * 0.64) / 13,
    width: 0.012 + random() * 0.018,
    height: 0.72 + random() * 0.28,
  }));
  const values = Array.from({ length: size }, (_, index) => {
    const x = index / (size - 1);
    const baseline = 0.08 + Math.sin(x * Math.PI * 8 + 0.7) * 0.025;
    return peaks.reduce((height, peak) => {
      const distance = Math.abs(x - peak.x) / peak.width;
      return Math.max(height, peak.height * Math.exp(-distance * 2.9));
    }, baseline);
  });
  return values;
}
```

Set `surfaceSlice = generateAsperityProfile(PROFILE_SIZE, FIELD_SEED + 17)`.

- [ ] **Step 3: Render a uniformly descending local membrane and contact runs**

Remove `edgeLift`. Set every desired membrane point from the shared threshold,
clamped immediately above the local surface. Convert above-threshold samples into
contiguous runs and append SVG paths:

```javascript
function contactRuns(points, heights, threshold) {
  const runs = [];
  let run = [];
  points.forEach((point, index) => {
    if (heights[index] >= threshold) run.push(point);
    else if (run.length) { runs.push(run); run = []; }
  });
  if (run.length) runs.push(run);
  return runs;
}

contactRuns(surfacePoints, surfaceSlice, threshold).forEach((run) => {
  const segment = document.createElementNS(SVG_NS, "path");
  segment.setAttribute("class", "micro-contact-segment");
  segment.setAttribute("d", smoothPath(run.length === 1 ? [
    { x: run[0].x - 2.5, y: run[0].y },
    { x: run[0].x + 2.5, y: run[0].y },
  ] : run));
  microContactPoints.append(segment);
});
```

- [ ] **Step 4: Use the same threshold in the 3D renderer**

Retain the fixed projection, but compute contact from the new cusp field. Use
height-dependent facet shading and preserve the accessible label update:

```javascript
microCanvas.setAttribute(
  "aria-label",
  `3D contact field, ${stateFor(pressure).title}, ${Math.round(contactRatio(pressure) * 100)} percent qualitative contact`,
);
```

- [ ] **Step 5: Run the behavior check and confirm it passes**

Run:

```powershell
$env:GLOWTACT_CHECK_MODE='behavior'
python design/browser_check.py
```

Expected: `PASS: interactions, keyboard focus, reduced motion, console, network`.

- [ ] **Step 6: Commit the local model**

```powershell
git add design/concept-03/app.js design/concept-03/index.html
git commit -m "feat(design): distribute local asperity contact"
```

### Task 4: Polish the physical rendering and centered tactile output

**Files:**
- Modify: `design/concept-03/styles.css:730-1052,1764-1775,1920-1952`

- [ ] **Step 1: Style the global interface, camera, and scale transition**

Use the existing LED amber only for optical coupling and the scale leader:

```css
.macro-texture-line {
  stroke: rgba(222, 235, 230, 0.92);
  stroke-width: 7;
  stroke-linecap: round;
}

.macro-field-of-view {
  fill: rgba(227, 161, 40, 0.055);
  stroke: rgba(227, 161, 40, 0.34);
  stroke-width: 1.5;
}

.macro-camera-body { fill: #141a17; stroke: rgba(202, 224, 218, 0.42); }
.macro-camera-ring { fill: #0a0d0b; stroke: rgba(202, 224, 218, 0.74); stroke-width: 4; }
.macro-camera-lens { fill: #111b18; stroke: rgba(146, 177, 169, 0.7); stroke-width: 3; }
.macro-camera-aperture { fill: #020302; stroke: rgba(227, 161, 40, 0.45); }
.macro-scale-marker circle,
.macro-scale-marker path { fill: none; stroke: var(--signal-amber-bright); stroke-width: 1.5; }
```

- [ ] **Step 2: Replace dot contacts with short tip-following segments**

```css
.micro-contact-segment {
  fill: none;
  stroke: var(--signal-amber-bright);
  stroke-width: 5;
  stroke-linecap: round;
  filter: drop-shadow(0 0 5px rgba(227, 161, 40, 0.34));
}
```

- [ ] **Step 3: Center and texture the tactile camera output**

Remove the contact rotation and asymmetric border radius. Keep its centroid at
`50% 50%` while adding deterministic internal texture:

```css
.camera-contact {
  top: 50%;
  left: 50%;
  aspect-ratio: 1 / 0.74;
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 42%, rgba(188, 202, 194, 0.1) 0 2%, transparent 3%),
    radial-gradient(circle at 63% 58%, rgba(188, 202, 194, 0.08) 0 1.5%, transparent 2.5%),
    rgba(3, 4, 3, var(--camera-darkness));
  transform: translate(-50%, -50%);
}
```

- [ ] **Step 4: Add mobile-safe scale-transition styling**

At `max-width: 640px`, reduce label size, keep the marker inside the global SVG,
and hide only the long leader while retaining `ZOOM TO ~100 UM WINDOW` and the
local footer label. Confirm no label is removed by the existing `.macro-label`
rule.

- [ ] **Step 5: Run full local verification and capture focused screenshots**

Run:

```powershell
python design/verify.py
$env:GLOWTACT_CHECK_MODE='all'
$env:GLOWTACT_REVIEW_OUTPUT="$env:TEMP\glowtact-scale-transition-local"
python design/browser_check.py
git diff --check
```

Expected: static audit passes; 4 routes by 2 viewports pass; behavior, keyboard,
reduced-motion, console, and network checks pass; `git diff --check` is silent.

- [ ] **Step 6: Inspect screenshots and correct visible defects**

Inspect `signal-desktop.png` and `signal-mobile.png`. Also capture a desktop
screenshot after selecting 3D and setting pressure to 55%. Reject the render if
the camera axis drifts, the global interface looks like large roughness, the local
peaks form a regular lattice, contact is center-biased, or labels overlap.

- [ ] **Step 7: Commit the rendering polish**

```powershell
git add design/concept-03/styles.css design/concept-03/app.js design/browser_check.py
git commit -m "fix(design): center and sharpen coupling render"
```

### Task 5: Remove the temporary review route and deploy

**Files:**
- Delete: `design/review-realism/index.html`
- Verify: `design/concept-03/index.html`
- Verify: `design/concept-03/styles.css`
- Verify: `design/concept-03/app.js`
- Verify: `design/browser_check.py`

- [ ] **Step 1: Delete only the selected-design review page**

Use `apply_patch` to delete `design/review-realism/index.html`. Do not delete the
`design/` directory or any concept route.

- [ ] **Step 2: Run the final local checks from a clean server state**

```powershell
python design/verify.py
$env:GLOWTACT_CHECK_MODE='all'
$env:GLOWTACT_REVIEW_OUTPUT="$env:TEMP\glowtact-scale-transition-final"
python design/browser_check.py
git diff --check
```

Expected: all commands exit 0 with the same full coverage as Task 4.

- [ ] **Step 3: Review scope and commit**

```powershell
git status --short
git diff --stat HEAD~3
git add design/review-realism/index.html
git commit -m "chore(design): remove mechanism review route"
```

The only remaining untracked files may be the user's `glowtact_materials/`,
`mms_gt.mp4`, and `paper.pdf`; do not stage them.

- [ ] **Step 4: Push and verify the exact remote commit**

```powershell
git push origin main
$local = git rev-parse HEAD
$remote = (git ls-remote origin refs/heads/main).Split("`t")[0]
if ($local -ne $remote) { throw "Remote main does not match local HEAD" }
```

- [ ] **Step 5: Wait for GitHub Pages and rerun checks against production**

Poll `gh api repos/glowtact/glowtact.github.io/pages/builds/latest` until `status`
is `built` and `commit` equals local HEAD. Then run:

```powershell
$env:GLOWTACT_BASE_URL='https://glowtact.github.io/design'
$env:GLOWTACT_CHECK_MODE='all'
$env:GLOWTACT_REVIEW_OUTPUT="$env:TEMP\glowtact-scale-transition-live"
python design/browser_check.py
```

Expected: 4 routes by 2 viewports pass on the public site, including all Concept
3 centering, spatial-distribution, interaction, accessibility, console, and
network assertions.

- [ ] **Step 6: Complete the requirement-by-requirement audit**

Record evidence for: centered indentation, visible global camera, bold near-flat
approximately 9 um interface, explicit approximately 100 um transition, sharper
2D/3D asperities, contact in all three local thirds at intermediate pressure,
desktop/mobile screenshots, exact deployed commit, and untouched user assets.
