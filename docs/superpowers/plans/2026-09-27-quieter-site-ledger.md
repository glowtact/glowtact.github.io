# Quieter site, paper-parameter reconstructions, original shear clips: ledger

Session of 2026-09-27 on `design/concept-03/`. The brief, in the user's words:
less text and fewer labels everywhere, no white FOV triangle in the mechanism
drawing, only the first four reconstructions and with the paper's parameters,
the shear reliability table and the normal-force module gone, the copy in a
promotional register ("What GlowTact measures"), the fingerprint figure as a
row of smaller frames with intermediate presses, and the shear clips back to
the un-tuned originals.

Every row is found -> fixed -> verified. Rules are frozen in `browser_check.py`
unless the row says otherwise.

| Found | Measured | Fixed | Verified |
|---|---|---|---|
| Mechanism labels unreadable: SVG `<text>` at 12 viewBox units | 8.7 px rendered on the 1280 layout (920-unit viewBox in a 665 px stage) | two HTML labels per drawing (`.stage-label`, `--text-label`) in a `.stage-frame` that matches the svg box; FOV triangle, texture note, probe label, camera caption removed | design mode: zero `<text>` in `#macro-svg`/`#micro-svg`, four labels at >= 14 px; red-greened by inserting a `<text>` |
| Legend overlay covered the camera on a phone once set at 14 px | two rows of legend over the drawing at 375 px | legend in flow under the drawing; the phone rule that hid the air-gap entry removed | phone screenshot; design mode |
| Gel label unreadable on the light gel fill | contrast 1.01 against the panel ground | dark plate behind the label instead of dark text | design mode contrast pass |
| Rule drops left dangling selectors | `.micro-window-label,` joined the `.micro-panel` rule and sized the readout to 244 px, pushing the shell to 1115 px | rule restored; every dropped multi-selector rule audited against HEAD | `.mechanism-shell` height budget (920 px) green |
| Latent: `.mechanism,\n.forms,` dangling in HEAD gave the forms band the nitrile ground | forms rendered on nitrile, contradicting DESIGN.md's alternating bands | selector removed; the bands now carry their own head room (`padding-top` on mechanism, forms, results) | desktop screenshot |
| Reconstruction gallery: seven objects, the old speckled renders | site posters vs `gallery/<obj>/<obj>_shape3d.png`: pad speckle on every card, paper stills smooth | four cards (threads, Phillips, balls, Oreo) from `~/Desktop/glowtact_materials/gallery/gallery/` turntable GIFs -> H.264 720 px, posters and tactile inputs regenerated; card headers and second caption lines removed; each caption shows the object photograph beside the tactile input (photos cropped from the paper figure, the Oreo from the slide deck) | design mode: card order, photo, input and title asserted; `ffprobe` yuv420p |
| Shear: reliability table explained the method; normal-force module cancelled | user request | table dropped, claim shortened to the usable-field number, scope line rewritten as a positive fact; `#force` removed with its index entry and CSS | design mode: `#force` absent, index and modules are the three ids, no table in `#shear` |
| Shear clips too white | `videos/color_tuned/` vs `videos/original/` frame 60 of the M5 press | five originals re-encoded H.264 CRF 20; posters cut at each object's `peak_frame` from `shear_field/params.json` | `ffprobe`; behaviour mode selector check |
| Fig. 9 strip: nine frames, three label rows, repeating the two clips | user asked to arrange or take down | strip taken down; the two clips share one 16:10 box | design mode: no `.fig9-strip`, two clips |
| Fingerprint figure too large, three frames | one full-width image | five cropped frames of the same placement (0.25 -> 3 N nominal) in a `.press-series` grid, forces not printed per frame (the log's measured values differ from the nominal labels; the paper's 0.3-2.0 N claim stays in the caption) | scroll probe: five images at 238 px on desktop |
| Copy: section eyebrows, capability tiles, card indices, badges, "how we did it" | user request; DESIGN.md's own rule on structure that encodes nothing | removed; badges, eyebrows, state and clip labels demoted from amber to `--readout-tertiary`; `Pause rotation` outline | slop gate 0 open; contrast pass |
| Palette: green cast on every grey | `#171d18`, `#94a094`, sage gel `#9db3ad` | neutral greys, cool gel `#a3b4bf`; DESIGN.md mirrored in the same commit | `token-mirror` both ways, 15 -> 9 metrics still matching |

Not done, on purpose:

- `concept-02` still references `fingerprint-pressure.jpg`, so the file stays
  in the repo although concept-03 no longer uses it.
- The three retired reconstruction objects' assets were deleted; the gallery
  under `~/Desktop/glowtact_materials/gallery/` still holds them.
- The deep slop tier reports two pre-existing concept-02 copy findings
  (`marketing-cadence`, `em-dash-density`); frozen review artifact, untouched.
