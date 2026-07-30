# GlowTact Website Project Plan

## Goal
Build a polished, responsive research website for **GlowTact: Simple and Compact Vision-Based Tactile Sensing with High Sensitivity and Spatial Resolution**.

The site should combine strong visual hierarchy, real research imagery, concise scientific storytelling, and one central interactive mechanism explanation. It must clearly distinguish real measurements from conceptual illustrations.

## Stack
- Next.js
- TypeScript
- Tailwind CSS
- Framer Motion
- Responsive SVG for the mechanism
- Plotly, Recharts, or D3 for data plots
- Playwright for testing
- Vercel for deployment

Do not start with Three.js. The core mechanism is clearer as an interactive cross-section.

## Repository Structure
```text
glowtact-site/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   ├── Navigation.tsx
│   ├── Hero.tsx
│   ├── ResearchSummary.tsx
│   ├── MechanismDemo.tsx
│   ├── ConventionalVBTSComparison.tsx
│   ├── SensorImplementations.tsx
│   ├── LightweightObjectDemo.tsx
│   ├── SensitivityResults.tsx
│   ├── ReconstructionExplorer.tsx
│   ├── ForceEstimation.tsx
│   ├── Citation.tsx
│   └── Footer.tsx
├── public/
│   ├── images/
│   ├── videos/
│   ├── data/
│   └── paper/
├── content/paper.ts
├── PROJECT_PLAN.md
├── design.md
├── MECHANISM_SPEC.md
├── CONTENT.md
├── ASSET_MANIFEST.md
└── SCIENTIFIC_CONSTRAINTS.md
```

## Page Architecture
1. Navigation
2. Hero with LEAP-hand teaser and tactile inset
3. Short research summary
4. Interactive GlowTact mechanism
5. Comparison with geometry-based VBTS
6. Flat, omnidirectional, and humanoid fingertip implementations
7. Passive lightweight-object comparison
8. Interactive force-sensitivity plots
9. Contact-geometry reconstruction explorer
10. Force-estimation summary
11. Paper, code, data, video, and BibTeX

## Interactive Mechanism
Controls:
- pressure slider
- probe selector: flat, sphere, edge
- reset button

Synchronized outputs:
- indenter motion
- membrane deformation
- air-gap closure
- reduced reflected-light opacity
- expanding optical-coupling region
- growing and darkening tactile patch

Mandatory disclosure:
> Conceptual visualization. Geometry and optical paths are schematic and are not a calibrated mechanical or ray-tracing simulation.

## Development Phases

### Phase 0 — Setup
Initialize Next.js, TypeScript, Tailwind, linting, formatting, responsive containers, and Vercel configuration.

### Phase 1 — Static Page
Implement all sections with supplied assets and placeholders. Do not invent data or links.

### Phase 2 — Mechanism
Implement the responsive SVG interaction and verify scientific constraints.

### Phase 3 — Real Data
Load source JSON for response, SNR, detection threshold, and force-estimation results.

### Phase 4 — Media Explorers
Implement lightweight-object selection and reconstruction comparison.

### Phase 5 — Polish
Accessibility, SEO, Open Graph, performance, Playwright testing, and deployment.

## First Release Scope
Ship:
- hero
- short abstract
- interactive SVG mechanism
- three form factors
- lightweight-object comparison
- force-sensitivity plots
- reconstruction explorer
- paper and BibTeX

Delay:
- full 3D model
- browser physics
- Blender animation
- complex scroll hijacking
- dataset browser

## Success Criterion
A visitor should understand the sensing mechanism within 20 seconds and remember:
1. gram-scale passive-contact sensitivity
2. simple single-color illumination
3. M1-thread reconstruction
