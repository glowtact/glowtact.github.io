# GlowTact Concept 3 Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild Concept 3 around the supplied teaser and a shared qualitative
coupling model with comparable 2D and 3D microscopic views.

**Architecture:** Keep the dependency-free static-site structure. Semantic HTML
defines the narrative and controls, CSS renders the macro and 2D mechanism, and
local JavaScript owns one deterministic state model plus a canvas-based 3D
projection. Existing verification scripts are extended before implementation so
the new interaction contract is test-driven.

**Tech Stack:** HTML5, CSS custom properties, Canvas 2D, vanilla JavaScript,
Python static audit, Playwright.

---

## File Structure

- Modify `design/concept-03/index.html`: teaser-led information architecture,
  integrated mechanism, accessible microscope tabs, evidence composition.
- Modify `design/concept-03/styles.css`: harmonious layout, macro and microscope
  rendering, responsive states, reduced motion.
- Modify `design/concept-03/app.js`: shared pressure state, deterministic
  P2500-inspired height field, 2D/3D view switching, canvas rendering.
- Modify `design/browser_check.py`: interaction and accessibility regression
  checks for the new microscope controls.
- Modify `design/ASSET_MANIFEST.md`: document that the existing teaser is used
  as the Concept 3 hero.
- Create `docs/superpowers/specs/2026-07-31-glowtact-concept-03-refinement-design.md`:
  approved design and scientific boundary.
- Create `docs/superpowers/plans/2026-07-31-glowtact-concept-03-refinement.md`:
  executable implementation plan.

## Task 1: Lock the New Interaction Contract

**Files:**
- Modify: `design/browser_check.py`

- [ ] Add Playwright assertions that the default microscope tab has
  `aria-selected="true"` and identifies the 2D panel.
- [ ] Add a click on the 3D tab and assert that the selected state and visible
  panel change.
- [ ] Move the pressure slider to `80` and assert that the toolbar state is
  `Expanded coupling`, the 3D canvas carries the updated accessible summary,
  and playback remains finite.
- [ ] Run `python design/browser_check.py` against the current page.
- [ ] Confirm the new assertions fail because the microscope tabs and canvas do
  not exist yet.

## Task 2: Rebuild the Semantic Page Structure

**Files:**
- Modify: `design/concept-03/index.html`
- Modify: `design/ASSET_MANIFEST.md`

- [ ] Replace the synthetic hero signal with
  `../assets/images/hero-teaser.jpg`, an explicit paper-teaser caption, and
  concise capability readouts.
- [ ] Rename the integrated mechanism section to `How contact becomes signal`.
- [ ] Replace the three equal view articles with a macro article, a microscope
  article containing accessible 2D/3D tabs, and a camera-output article.
- [ ] Move `Air gap`, `Local coupling`, and `Expanded coupling` into the control
  state rail and remove the separate duplicate sequence section.
- [ ] Recompose media, sensor forms, evidence, and research sections without
  altering scientific claims or unavailable-resource states.
- [ ] Record the hero use in `design/ASSET_MANIFEST.md`.
- [ ] Run `python design/verify.py`; expect all four routes to pass the static audit.

## Task 3: Implement the Shared Coupling Model

**Files:**
- Modify: `design/concept-03/app.js`

- [ ] Create a deterministic pseudo-random generator with a fixed integer seed.
- [ ] Generate a normalized `surfaceField` from bounded sinusoidal frequencies,
  seeded phases, and a small grain component.
- [ ] Expose one `render(value)` path that updates pressure, qualitative state,
  readouts, CSS variables, microscope summary, and canvas.
- [ ] Add a tab controller that preserves pressure state while switching between
  2D and 3D panels.
- [ ] Render the 3D contact field to canvas using a fixed oblique projection,
  height shading, amber contact cells, and device-pixel-ratio scaling.
- [ ] Preserve finite playback, direct-input cancellation, reveal behavior, and
  reduced-motion behavior.
- [ ] Run the focused Playwright signal interaction check; expect the new
  contract to pass.

## Task 4: Build the Harmonious Visual System

**Files:**
- Modify: `design/concept-03/styles.css`

- [ ] Establish a 1560 px maximum canvas, asymmetric hero ratio, restrained
  charcoal surface ladder, amber coupling accent, and four-level text hierarchy.
- [ ] Make the teaser fully visible with an intrinsic aspect ratio and a quiet
  instrument caption.
- [ ] Render the macro cross-section with visible gel, acrylic, membrane,
  indenter, air-gap, coupling, and finite reflected rays.
- [ ] Render the 2D microscope with asperities, local gap, contact markers, and
  labels controlled by shared CSS variables.
- [ ] Style the 3D canvas, accessible tabs, camera output, state rail, and
  pressure controls as one coherent instrument.
- [ ] Recompose supporting sections with alternating open and dense rhythm.
- [ ] Add desktop, tablet, `390px`, and `320px` layouts without structural hacks.
- [ ] Preserve focus-visible, pointer target, print-safe image behavior, and
  reduced-motion rules.

## Task 5: Verify and Iterate Visually

**Files:**
- Modify as needed: `design/concept-03/index.html`
- Modify as needed: `design/concept-03/styles.css`
- Modify as needed: `design/concept-03/app.js`
- Modify as needed: `design/browser_check.py`

- [ ] Run `python design/verify.py`; require exit code 0.
- [ ] Run `python design/browser_check.py`; require interaction, keyboard,
  reduced-motion, console, network, and visual checks to pass.
- [ ] Inspect `signal-desktop.png` at `1440x1000`.
- [ ] Inspect `signal-mobile.png` at `390x844`.
- [ ] Fix any hero crop, hierarchy, unreadable labels, overlap, overflow,
  excessive density, blank canvas, or generic repeated-card composition.
- [ ] Re-run both verification commands after the final visual change.

## Task 6: Review, Commit, and Push

**Files:**
- Stage only the files listed in this plan plus `task_plan.md` and `notes.md` if
  they remain useful to the repository.

- [ ] Run `git status --short` and confirm root-level `paper.pdf`,
  `mms_gt.mp4`, and `glowtact_materials/` remain unstaged.
- [ ] Review `git diff --check`, `git diff --stat`, and the scoped full diff.
- [ ] Commit with `feat(design): refine GlowTact signal chamber`.
- [ ] Push the current branch to its configured upstream.
- [ ] Report the commit SHA, branch, verification results, and GitHub Pages URL.
