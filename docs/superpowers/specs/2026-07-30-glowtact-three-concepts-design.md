# GlowTact Three-Concept Website Design

## Objective

Build three distinct, polished, responsive website concepts for GlowTact under
`design/`. Each concept must explain the same research accurately while using a
different information architecture, visual language, and signature interaction.
A shared review page will let the researcher compare all three concepts.

## Audience and Primary Task

The primary visitor is a robotics researcher, reviewer, or engineer encountering
GlowTact for the first time. Within 20 seconds, the visitor should understand:

1. pressure closes microscopic air gaps at the membrane-gel interface;
2. increased optical coupling produces a locally darker tactile image;
3. the mechanism supports sensitive passive-contact detection and fine spatial
   reconstruction in compact form factors.

The researcher reviewing the concepts must be able to open all three from one
index and compare their hierarchy, interaction model, and motion character.

## Source and Scientific Boundaries

- Use `design/CONTENT.md`, `design/SCIENTIFIC_CONSTRAINTS.md`,
  `design/ASSET_MANIFEST.md`, `design/PROJECT_PLAN.md`, and `design/design.md`
  as the authoritative editorial constraints.
- Use only supplied project media or purpose-built schematic SVG/CSS graphics.
- Do not fabricate experimental plots, measurements, tactile images, authors,
  links, affiliations, venue information, or calibrated pressure values.
- GlowTact uses amber, tactile black, diffuse gray, and translucent gel tones.
  GelSight Mini uses blue only where a comparison requires it.
- Mechanism diagrams are conceptual rather than finite-element or ray-tracing
  simulations.
- Every mechanism interaction includes this disclosure:

  > Conceptual visualization. Geometry and optical paths are schematic and are
  > not a calibrated mechanical or ray-tracing simulation.

- Experimental media must be labeled separately from conceptual graphics.

## Deliverable Architecture

The `design/` directory becomes a dependency-free static review build:

```text
design/
├── index.html
├── shared/
│   ├── review.css
│   └── review.js
├── concept-01/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── concept-02/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── concept-03/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── assets/
    ├── images/
    └── video/
```

Existing Markdown source files remain intact. Only media required by the pages
is copied into `design/assets/`; the original root-level files and
`glowtact_materials/` remain untouched.

Each concept uses semantic HTML, CSS custom properties, native controls, and
small local JavaScript modules. No build step or external runtime dependency is
required. A local HTTP server is sufficient for review and testing.

## Shared Review Index

The review index is an intentionally neutral comparison surface rather than a
fourth design direction.

- A concise title and explanation establish that the pages are alternative
  treatments of the same research.
- Three asymmetric preview panels summarize each concept's primary visual,
  signature interaction, color treatment, and strongest use case.
- Each panel links to its complete concept.
- Keyboard-accessible links have visible focus states.
- A compact comparison matrix identifies differences in hierarchy, density,
  motion, and scientific storytelling.

## Concept 01: Optical Coupling

### Intent

Feel like a bright, quiet optics laboratory translated into an editorial
research page. The mechanism is the focal point; supporting evidence follows.

### Visual System

- Background: acrylic white and warm diffuse gray.
- Accent: LED amber used only for coupling, controls, and key evidence.
- Text: tactile black with four restrained hierarchy levels.
- Typography: expressive condensed display face backed by a neutral technical
  sans-serif stack; tabular numerals for measurements.
- Depth: borders and surface shifts only, with no floating card grid.
- Spacing: 8 px base, with long editorial gaps between major claims.

### Page Structure

1. Persistent minimal navigation and concept switcher.
2. Hero with title, concise mechanism statement, and animated contact aperture.
3. Interactive membrane-gel cross-section.
4. Three-step mechanism explanation: air gap, coupling, darkening.
5. Form-factor panorama.
6. Passive-contact and fine-geometry evidence.
7. Paper/citation area with unavailable links visibly disabled.

### Signature Interaction

A labeled pressure slider drives a responsive SVG cross-section. Increasing the
control:

- lowers the indenter;
- deforms the membrane without penetration;
- closes the visible air gap;
- expands the optical-coupling region;
- reduces reflected-ray opacity;
- expands and darkens the simulated tactile patch.

Probe buttons switch between flat, sphere, and edge profiles. Reset restores the
zero-pressure state. The interaction is monotonic and carries no invented force
unit.

### Motion

Editorial elements reveal once with short opacity/translate transitions.
Mechanism motion is direct and under user control. No parallax, scroll hijacking,
ambient pulsing, or exaggerated spring behavior is used.

## Concept 02: Contact Atlas

### Intent

Feel like a tactile-science field guide: warm, investigative, and materially
specific. Evidence is the focal point; the mechanism is explained through
annotated specimens.

### Visual System

- Background: warm paper and microtexture gray.
- Accent: measurement amber and restrained black annotation ink.
- Comparison accent: GelSight blue only in explicitly labeled comparisons.
- Typography: sturdy editorial serif for section leads and compact sans-serif
  labels for specimens and controls.
- Depth: inset paper layers and faint registration marks, not generic cards.
- Spacing: 8 px base with tighter specimen groups and larger chapter breaks.

### Page Structure

1. Atlas masthead and numbered chapter navigation.
2. Hero built from an annotated contact-imprint field.
3. Interactive three-layer specimen: membrane, coupling region, tactile output.
4. Form-factor catalog with exploded, assembled, and tactile states.
5. Lightweight-object comparison.
6. Reconstruction collection emphasizing M1 threads.
7. Methods and citation ledger.

### Signature Interaction

A comparison lens moves across a specimen stage. Native range controls and
segmented buttons reveal conceptual raw, coupled, and tactile-output layers.
Where real matched media exists, the same control compares supplied images.
Missing source media is represented by an explicit labeled placeholder, never a
synthetic experiment.

Selecting a specimen updates its label, annotation, and explanatory copy without
changing page position. Arrow keys operate every segmented control.

### Motion

Annotations enter in 30-50 ms staggered groups. The comparison lens and layer
changes animate with transforms and opacity only. Page transitions resemble
turning to a new specimen plate without literal page-flip effects.

## Concept 03: Signal Chamber

### Intent

Feel like a compact optical instrument running in a dark robotics lab. The
pressure-responsive signal is the focal point; supporting explanations behave
like instrument readouts.

### Visual System

- Background: camera charcoal and black nitrile.
- Accent: luminous but non-neon LED amber.
- Supporting surfaces: closely spaced charcoal elevation steps.
- Typography: wide technical display face with a compact monospace-inspired
  readout stack.
- Depth: surface lightness shifts plus a single quiet ring system.
- Spacing: 4 px component grid and 8 px section grid for a denser instrument
  character.

### Page Structure

1. Compact instrument header and concept switcher.
2. Full-height tactile-signal hero with concise title.
3. Scroll-linked but non-hijacking mechanism sequence.
4. Live conceptual signal panel synchronized to pressure.
5. Form-factor rail.
6. Passive-contact and reconstruction evidence chamber.
7. Research summary and citation console.

### Signature Interaction

A pressure control synchronizes three views:

- membrane-gel section;
- coupling aperture;
- simulated tactile signal.

A play/pause control can demonstrate one short automated pressure cycle. User
input immediately takes control, and the cycle never loops indefinitely.
Readouts use qualitative labels only: `air gap`, `partial coupling`, and
`expanded coupling`.

### Motion

The opening sequence runs once and remains below 700 ms in total. Scroll
observers reveal mechanism stages without controlling the scroll position.
Instrument controls respond within 160 ms. No animated glow continuously pulses.

## Shared Interaction and Accessibility Contract

- Use semantic landmarks, ordered heading levels, and descriptive labels.
- Native buttons, links, and range inputs retain keyboard behavior.
- Visible `:focus-visible` rings meet contrast requirements.
- Pointer targets are at least 44 px where practical and never overlap.
- Decorative SVG is hidden from assistive technology; explanatory diagrams have
  text alternatives.
- Images include useful alternative text; purely decorative media uses empty
  alternatives.
- All three concepts work from 320 px mobile width through wide desktop layouts.
- With `prefers-reduced-motion: reduce`, movement and stagger are removed while
  state changes remain understandable.
- JavaScript enhancement is progressive: core content and navigation remain
  readable if scripts fail.

## Media Handling

Before implementation, inventory `glowtact_materials/`, `mms_gt.mp4`, and
`paper.pdf`. Copy only intentionally used media into `design/assets/` and record
its origin in `design/ASSET_MANIFEST.md`.

Video must:

- be muted when autoplay is used;
- use `playsinline`;
- include a static fallback;
- avoid autoplay when reduced motion is requested;
- never block the page if unsupported.

Missing experimental assets use clearly labeled placeholders that state what
source export is needed.

## Error and Empty States

- Unsupported video displays its fallback frame and explanatory caption.
- Missing optional images display a neutral placeholder preserving aspect ratio.
- JavaScript errors must not hide scientific copy or navigation.
- Unavailable paper, code, data, or external links are rendered disabled and
  labeled “not yet available,” not pointed at invented destinations.

## Verification

Before commit and push:

1. Serve `design/` through a local HTTP server.
2. Open the review index and all three concepts in a real browser.
3. Capture and inspect desktop and mobile screenshots for every route.
4. Exercise sliders, probe/specimen switches, reset, play/pause, comparison lens,
   concept links, and keyboard focus.
5. Test reduced-motion behavior.
6. Check for horizontal overflow, missing local resources, console errors,
   broken links, and unreadable text.
7. Validate that the required conceptual disclosure is present wherever needed.
8. Search for prohibited claims, fabricated measurements, placeholder `href`
   targets, debug output, and accidental external dependencies.
9. Review the Git diff and stage only scoped design/specification files.
10. Commit with a Conventional Commit message and push the current branch.

## Acceptance Criteria

- `design/index.html` links to three complete, visually distinct concepts.
- Every concept is responsive, navigable, and scientifically consistent.
- Each concept has a different signature interaction and information hierarchy.
- Animations are purposeful, performant, finite, and reduced-motion aware.
- No experimental result, author identity, or external link is invented.
- All planned interactions pass browser verification on desktop and mobile.
- Unrelated root assets remain unchanged and uncommitted.
- The final scoped commit is successfully pushed to the configured Git remote.
