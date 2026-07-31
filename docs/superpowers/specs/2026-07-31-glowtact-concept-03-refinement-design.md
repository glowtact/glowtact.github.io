# GlowTact Concept 3 Refinement Design

## Objective

Refine the existing Signal Chamber concept into a coherent research narrative
that explains how a P2500-molded silicone texture and an unbonded black nitrile
membrane convert contact into a dark tactile signal. The page must lead with the
paper teaser, make the mechanism the second focal point, and compare 2D and 3D
microscopic explanations without presenting either as calibrated simulation.

## Audience and Comprehension Goal

The primary visitor is a robotics researcher, reviewer, or engineer seeing
GlowTact for the first time. Within the hero and mechanism section, the visitor
should understand:

1. the black nitrile membrane rests mainly on microtexture asperity peaks;
2. microscopic air gaps diffusely reflect light at the gel-air interface;
3. indentation closes local gaps and increases membrane-gel optical coupling;
4. coupled regions absorb more light and appear darker to the camera.

## Source Facts and Boundaries

The local paper specifies P2500 aluminum-oxide sandpaper, a 4 mm XP-565 clear
silicone gel layer mixed 10:1 by weight, and a thin black nitrile glove membrane
for the flat implementation. It does not provide surface profilometry, PSD,
RMS roughness, constitutive material parameters, membrane pre-tension, or a
calibrated mapping from indentation to contact area.

The website must therefore describe the interaction as:

> Physically informed qualitative visualization based on the reported P2500
> mold texture and optical-coupling mechanism; not calibrated to measured
> surface topography, force, or light transport.

The existing disclosure remains present:

> Conceptual visualization. Geometry and optical paths are schematic and are
> not a calibrated mechanical or ray-tracing simulation.

No synthetic field may be labeled as experimental data.

## Page Composition

### Header

Keep the compact instrument header, but reduce its visual competition with the
hero. Navigation points to `Mechanism`, `Evidence`, and `Research`.

### Hero

Use an asymmetric two-column first viewport:

- left: live-status label, title, concise mechanism statement, primary research
  actions, and three compact capability readouts;
- right: the supplied paper teaser as a large, uncropped scientific figure;
- caption: explicitly identify it as the supplied paper teaser and summarize the
  hardware-contact-output relationship.

The teaser's red annotations remain confined to the figure. The website accent
remains LED amber.

### Mechanism

Replace the three equal panels and separate mechanism-state rail with one
integrated system titled `How contact becomes signal`.

Desktop composition:

- left 64%: macro membrane-gel cross-section;
- right 36%, top: microscopic view with `2D Cross-section` and
  `3D Contact field` tabs;
- right 36%, bottom: synchronized camera output;
- full-width bottom: pressure control, finite playback button, state rail, and
  qualitative readouts.

Mobile composition stacks macro, microscope, camera output, and controls.

### Supporting Narrative

After the mechanism:

1. experimental manipulation video paired with three concise capabilities;
2. sensor forms shown as one horizontal comparison rather than three repeated
   instrument cards;
3. evidence images presented at larger scale with one dominant result and two
   supporting results;
4. compact research record and citation.

Remove the duplicate static state section and the repeated teaser image.

## Shared Coupling Model

The browser uses a deterministic model; no Python runtime is required.

### Rough Surface

Create a fixed P2500-inspired normalized height field from several spatial
frequencies and seeded phases. The field is visually representative, not a
reconstruction of the physical sandpaper.

### State

One normalized `pressure` value in `[0, 1]` drives:

- indenter displacement;
- macro membrane deformation;
- macro coupling-region width;
- reflected-ray opacity;
- 2D local gap closure;
- 3D contact-mask growth;
- camera-output darkness and area;
- state label and explanatory copy.

Thresholds:

- `pressure < 0.10`: `Air gap`;
- `0.10 <= pressure < 0.58`: `Local coupling`;
- `pressure >= 0.58`: `Expanded coupling`.

These thresholds are presentation states, not measured force transitions.

### 2D Microscope

The default view is a legible side section through the shared rough field:

- black nitrile membrane;
- cyan-gray XP-565 texture;
- visible air gap;
- amber local coupling regions;
- limited labels for membrane, air gap, asperity peak, and optical coupling.

The view emphasizes cause and effect over numerical geometry.

### 3D Microscope

The comparison view uses the same field as a projected mesh:

- fixed oblique camera to prevent disorientation;
- height-based cyan-gray surface shading;
- amber contact islands;
- subtle grid and scale-free coordinates;
- no free orbit controls;
- accessible toggle and textual summary.

The 3D view shows that contact begins as separated islands and becomes a larger
connected area.

## Visual System

- Background: camera black `#090b0a`.
- Surfaces: a restrained charcoal ladder with 3-5% lightness differences.
- Primary accent: LED amber; use it for active state, coupling, and focus only.
- Scientific teaser red: image content only.
- Typography: keep a wide technical display treatment for major claims and a
  compact mono readout treatment for labels.
- Spacing: 8 px section grid with intentionally uneven rhythm.
- Depth: surface shifts and low-opacity rings; no large drop shadows.
- Radius: small, consistent instrument radii; the teaser remains rectangular.

## Motion and Interaction

- The finite demonstration runs once and stops at full coupling.
- Direct slider input immediately cancels playback.
- View-toggle transitions use opacity and transform only.
- Macro deformation and camera response remain directly tied to the slider.
- `prefers-reduced-motion` removes translates, sweeps, and stagger while
  preserving immediate state updates.
- Interactive targets are at least 44 px and have visible focus states.

## Failure and Fallback Behavior

- Without JavaScript, scientific copy, static view labels, and the teaser remain
  readable.
- If canvas is unavailable, the 3D view retains a textual fallback and the 2D
  view remains usable.
- If the video is unsupported, its poster/context frame and caption remain.
- Missing assets must not collapse layout.

## Verification

1. Run `python design/verify.py`.
2. Run the existing Playwright interaction and visual checks.
3. Extend signal checks to cover the 2D/3D toggle and synchronized pressure state.
4. Capture desktop `1440x1000` and mobile `390x844` screenshots.
5. Inspect hero crop, text contrast, mechanism hierarchy, toggle state, evidence
   scaling, horizontal overflow, and reduced-motion behavior.
6. Review the full diff and stage only Concept 3, scoped tests, and design docs.

## Acceptance Criteria

- The paper teaser dominates the first viewport without being cropped.
- The former mechanism and state sections are one coherent interaction.
- The 2D and 3D microscopic views share one deterministic state.
- The 2D view is the default and the 3D view is keyboard-accessible.
- All simulator language remains qualitative and scientifically bounded.
- The page works from 320 px to wide desktop without horizontal overflow.
- Existing review index and Concepts 1 and 2 remain functionally unchanged.
- Static verification and Playwright checks pass before push.
