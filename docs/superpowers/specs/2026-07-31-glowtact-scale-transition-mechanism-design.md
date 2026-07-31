# GlowTact Scale-Transition Mechanism Revision

## Decision

Implement visual direction C, `Explicit microscope transition`, in the deployed
Concept 3 mechanism. The global cross-section and the local roughness view must
read as two different spatial scales rather than two competing illustrations of
the same geometry.

The visualization remains physically informed and qualitative. The local paper
reports a P2500 aluminum-oxide sandpaper mold and the optical-coupling mechanism,
but it does not provide profilometry, material calibration, or a measured
pressure-to-contact mapping. The website must not imply those missing data.

## User-facing outcome

At a glance, a reader should understand this sequence:

1. an indenter depresses the black membrane at the horizontal center;
2. a camera below the clear gel observes the same centered region;
3. the global gel surface is almost flat because the reported texture amplitude
   is approximately 9 micrometers relative to the millimeter-scale gel layer;
4. a microscope callout opens a separate approximately 100 micrometer window;
5. within that window, a spatially distributed set of asperities progressively
   contacts the descending membrane and darkens the centered camera output.

## Global 2D cross-section

### Geometry

- Preserve the existing SVG coordinate system and mechanism panel.
- Place the indentation axis at the exact horizontal midpoint of the global
  view. The indenter, deepest membrane point, microscope origin, camera lens,
  optical cone, and camera-output dark region share that axis.
- Render the clear gel as the dominant millimeter-scale body.
- Replace the current visibly wavy top boundary with a near-flat interface. A
  bold 6-8 px light line represents the P2500-molded surface for legibility; a
  label states `~9 um texture / thickness exaggerated for visibility`.
- The bold line is a display convention, not a to-scale rendering of 9 um.
- Keep membrane deformation smooth and symmetric around the center. It may
  contact the global surface over a widening central band, but no large global
  asperities may be drawn.

### Camera and optics

- Add a compact camera body beneath the gel, centered on the indentation axis.
- Show a circular lens with two concentric glass rings, a dark aperture, and a
  subtle amber sensor reflection.
- Draw a symmetric field-of-view cone from the lens to the observed surface
  region. Use low-opacity solid edges instead of multiple decorative rays.
- Include two restrained illumination paths that reach the gel-air interface and
  visibly weaken where membrane-gel coupling develops.
- Use labels `camera`, `field of view`, and `coupled interface`; avoid hardware
  specifications not stated in the paper.

## Explicit microscope transition

- Add a circular or bracketed sampling marker on the global surface close to the
  center but offset enough that it does not obscure the indentation axis.
- Connect the marker to the existing local-view panel with two amber leader
  lines. The transition must visually explain that the local panel magnifies the
  near-flat bold interface.
- Label the local panel `~100 um qualitative window` and keep the existing
  non-calibrated-model disclosure.
- On mobile, the leaders may become a short vertical scale-transition strip
  between the stacked global and local panels; they must not cross text or
  controls.

## Local 2D roughness model

### Surface construction

- Replace the current smooth correlated slice with a deterministic, seeded
  angular profile containing approximately 45-65 visible asperities across the
  panel.
- Combine a weak low-frequency baseline with dominant short-wavelength peaks.
  Vary peak height, width, and asymmetry within bounded ranges so the profile is
  irregular but not periodic or sawtooth-like.
- Avoid a broad central hill. The height statistics and peak density must remain
  comparable across the left, middle, and right thirds of the window.

### Contact behavior

- Model the local membrane as a nearly horizontal compliant envelope descending
  uniformly with pressure. It must not form a centered bowl in the local window.
- Determine contact from a global height threshold shared by the full local
  field. At intermediate pressure, visible contact points must appear in all
  three horizontal thirds when the deterministic field permits it.
- Render contact as short amber interface segments following asperity tips,
  rather than oversized circular dots.
- As pressure increases, existing segments widen and additional spatially
  distributed tips enter contact. Full pressure may leave small isolated gaps;
  it must not turn the whole field into a uniform amber slab.

## Local 3D contact field

- Rebuild the deterministic field from spatially distributed asperity centers
  with bounded random spacing and multi-scale height variation.
- Increase local sharpness by using compact, asymmetric peaks blended with a
  weak correlated base field. Do not render a regular cone lattice.
- Normalize broad spatial bias so no quadrant becomes the default contact origin.
- Use the same height threshold as the 2D profile. Contact islands should appear
  across the projected surface, then grow and merge locally with pressure.
- Preserve the fixed camera and keyboard-accessible 2D/3D tabs.

## Centered tactile camera output

- Replace any offset or asymmetric dark-mask positioning with a coordinate model
  centered at `50% 50%` of the camera-output viewport.
- Tie the dark region radius and opacity to pressure while keeping its centroid
  fixed within one rendered pixel of the viewport center.
- Add a faint center reticle so alignment can be judged visually.
- Introduce low-amplitude deterministic texture inside the dark region to avoid
  a perfectly synthetic radial gradient. Texture moves in intensity, not
  position, so the indentation never drifts.

## Shared state and rendering boundaries

One normalized pressure value continues to drive the entire mechanism. Refactor
only the geometry helpers necessary to expose clear responsibilities:

- `renderMacro(pressure)` owns global membrane, bold interface, coupling band,
  camera, optics, and microscope sampling marker;
- `renderMicro2D(pressure)` owns the local profile, membrane threshold, gaps, and
  contact segments;
- `renderMicro3D(pressure)` owns the local height field and contact mask;
- camera-output CSS variables own centered radius, darkness, and texture
  intensity.

No Python runtime, external renderer, WebGL dependency, or network-loaded asset
is added. SVG and Canvas remain the production renderers.

## Accessibility and fallback

- Preserve semantic tab roles, arrow-key navigation, pressure input labeling,
  visible focus states, and minimum 44 px interactive targets.
- `prefers-reduced-motion` keeps immediate state changes but removes animated
  sweeps and transforms.
- Without JavaScript, the global camera, scale-transition label, and qualitative
  explanation remain visible as static SVG content.
- If Canvas is unavailable, the 2D local view remains the primary explanation
  and the existing 3D textual fallback remains visible.

## Files in scope

- `design/concept-03/index.html`
- `design/concept-03/styles.css`
- `design/concept-03/app.js`
- `design/browser_check.py`
- this design specification and the later implementation plan

The review index, Concepts 1 and 2, paper PDF, supplied video, and source material
folders remain unchanged. The temporary `design/review-realism/` route is removed
after the selected design is deployed and verified.

## Verification

1. Extend the browser check to assert the global camera and scale-transition
   labels exist.
2. Assert the computed camera-output center remains within one pixel of the
   viewport center at 0%, intermediate, and 100% pressure.
3. Assert the deterministic local 2D field produces contact in the left, middle,
   and right thirds at the designated intermediate test pressure.
4. Assert 2D/3D tabs share pressure state and the 3D accessible summary updates.
5. Run `python design/verify.py` and `python design/browser_check.py`.
6. Capture and inspect desktop `1440x1000`, mobile `390x844`, and a focused 3D
   mechanism screenshot.
7. Push the implementation, wait for the exact GitHub Pages commit to reach
   `built`, then repeat the browser checks against the public URL.

## Acceptance criteria

- The tactile indentation and camera output are visibly centered.
- The global view includes a recognizable centered camera and symmetric field of
  view.
- The global silicone surface reads as a near-flat bold interface and clearly
  discloses that its approximately 9 um thickness is visually exaggerated.
- The scale transition from the global interface to the approximately 100 um
  local window is explicit.
- Local 2D and 3D asperities are visibly sharper, irregular, deterministic, and
  free of a dominant central mound.
- Intermediate local contact is distributed across the viewing window rather
  than growing only from its center.
- The visualization remains labeled qualitative and does not claim calibrated
  surface reconstruction, force, or light transport.
- Desktop, mobile, keyboard, reduced-motion, console, and network checks pass on
  both local and deployed pages.
