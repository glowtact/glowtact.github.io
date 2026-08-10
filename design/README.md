# GlowTact Codex Design Pack

This pack contains the specifications needed to build the interactive GlowTact project website with Codex.

Files:
- PROJECT_PLAN.md
- design.md
- MECHANISM_SPEC.md
- CONTENT.md
- ASSET_MANIFEST.md
- SCIENTIFIC_CONSTRAINTS.md

Recommended workflow:
1. Copy these files into a new Next.js repository.
2. Add high-resolution figures and source JSON according to ASSET_MANIFEST.md.
3. Ask Codex to read all six files before editing.
4. Build the static page first.
5. Build the SVG mechanism second.
6. Add real data and media explorers.
7. Review all scientific behavior before deployment.

Initial Codex prompt:

Create a production-ready website for the robotics paper “GlowTact: Simple and Compact Vision-Based Tactile Sensing with High Sensitivity and Spatial Resolution.”

Read and follow PROJECT_PLAN.md, design.md, MECHANISM_SPEC.md, CONTENT.md, ASSET_MANIFEST.md, and SCIENTIFIC_CONSTRAINTS.md.

Use https://younghyopark.me/tune-to-learn/ only as a broad visual reference for hierarchy, whitespace, large research visuals, responsive layout, and interactive scientific storytelling. Do not copy its design.

Implement with Next.js, TypeScript, and Tailwind CSS. Use supplied assets and data only. Do not invent statistics, authors, links, or scientific behavior. Run linting and type checking and report remaining placeholders.

## Three-Concept Review Build

This directory now also contains three dependency-free website concepts:

- `concept-01/` — Optical Coupling
- `concept-02/` — Contact Atlas
- `concept-03/` — Signal Chamber

Start a local server from the repository root:

```powershell
python -m http.server 4173 --directory design
```

Review:

- `http://127.0.0.1:4173/`
- `http://127.0.0.1:4173/concept-01/`
- `http://127.0.0.1:4173/concept-02/`
- `http://127.0.0.1:4173/concept-03/`

Run the static contract check with:

```powershell
python design/verify.py
```

The review build is intentionally plain HTML, CSS, and JavaScript so every
direction can be opened without installing a framework. The original Next.js
recommendation above remains the production path after a direction is selected.

## Published Site Root

GitHub Pages serves this repository from `main:/`, so the bare domain needs a
root page. `design/tools/publish.py` generates the repository-root
`index.html` from `concept-03/index.html`, rewriting its relative references
to resolve from the root:

```powershell
python design/tools/publish.py
```

Only `index.html` is generated. CSS, JS, images, and video are referenced
where they already live under `design/`, so nothing is duplicated and the
published page cannot drift from the reviewed one. The generated file carries
a DO-NOT-EDIT banner; change `concept-03` and re-run the tool instead.

`design/tools/release.py` runs the publish step automatically after each stamp
and stages the root page alongside `design/`. To preview the published root
exactly as Pages serves it, run the server from the repository root rather
than from `design/`:

```powershell
python -m http.server 4173
```
