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

## Second pass, same day

The brief, in the user's words: no `PAPER TEASER` caption; the default
indenter a sphere, not the star; a `Why simple` section under the mechanism;
the fingerprint frames out of the geometry module, each with its force, as a
clip; the object photographs larger; shear down to fingertip, coin and the
M5 Phillips head; then "improve the colour" and the title hierarchy.

| Found | Measured | Fixed | Verified |
|---|---|---|---|
| Fingerprint series: five stills in the geometry module, no force per frame | user: not a reconstruction, one force per picture | the five frames encoded as one H.264 clip (0.25 to 3 N, 0.8 s per step), `fingerprint-progression.mp4`, in the light-touch row beside the two passive clips; the square source is cropped to the contact (`object-position: 50% 63%`) in the row's 16:10 box | `ffprobe` yuv420p; design mode: three clips |
| The clip first sat outside `.passive-pair` | 1216 px wide from a 434 px source at 1280 | moved into the pair; three columns | frozen: the three clips share one top and one height; red-greened with a two-column pair |
| Reconstruction thumbnails: 52 px, then fixed 150 px columns | caption 320 px in a 303 px card at 1280; 36x150 on a phone from a stale override that set width only | two fluid columns, `aspect-ratio: 1 / 1`; the stale phone rules removed | 132 px on a laptop, 71 px on a phone, overflow 0; frozen: square, overflow 0, at least 100 px on a laptop; red-greened with fixed columns |
| Probe picker: `Sphere` marked pressed while `app.js` loaded `star` | `.camera-contact` reported `star` | picker removed (one lonely pressed toggle is dead UI); `activeProbe = "round"`; the `PROBES` table stays for a future picker | frozen: no picker element, camera reports round, clip-path none; red-greened both ways |
| `Why simple` shipped as a band on the same transparent ground as `.forms`; the bare `dl` grid split titles from their lines; its `display: grid` never reached the browser | `.principles-list` absent from `cssRules`; two black bands read as one | closing module of the mechanism band (`.module-header` h3), each dt/dd pair wrapped in a div, titles `--text-title` amber, lines `--text-label` | frozen: `.mechanism .principles`, four wrapped pairs, four columns on a laptop, no `section.principles`; red-greened by unwrapping a pair |
| Latent since e5cb62d: a comment for the retired passive table had lost its closer and selector line, so the browser read 67 lines as one comment up to the next `*/` and the media block's `}` became a stray brace that ate the following rule | comment 2616 to 2682; harmless until a rule was appended after it | the dead block deleted | `verify.py` `stylesheet_syntax`: unclosed comment, stray brace, comment over 20 lines; red-greened with an unclosed `/*` |
| Shear: five clips | user: keep three | Go piece and M2 pan head tabs and files removed | behaviour mode selector check; `verify.py` local references |
| Colour and hierarchy | user: "improve the color", titles not prominent | `.signal-label` amber again for the three results eyebrows; h3 above its eyebrow in `.module-header`; DESIGN.md amber rule updated | contrast pass; slop gate 0 open |
| `git add -A` in a local commit swept in `.impeccable/`, a screenshot, `webpage.jpg` and the forms re-renders | commit `f54a282`, unpushed | commit reset and redone with named files | `git show --stat` |

Not done, on purpose:

- `concept-02` still references `fingerprint-pressure.jpg`, so the file stays
  in the repo although concept-03 no longer uses it.
- The three retired reconstruction objects' assets were deleted; the gallery
  under `~/Desktop/glowtact_materials/gallery/` still holds them.
- The deep slop tier reports two pre-existing concept-02 copy findings
  (`marketing-cadence`, `em-dash-density`); frozen review artifact, untouched.
- `design/assets/images/forms/{flat-exploded,tip-exploded,tips-in-hand}.jpg`
  are modified in the working tree (1200x900 re-renders of the exploded
  views, from the untracked `.impeccable/`), not part of this brief and left
  uncommitted; `.impeccable/`, `Screenshot from 2026-09-26 23-42-08.png` and
  `webpage.jpg` stay untracked.
- The `Code` and `Hardware guide` pending buttons in the hero were not
  discussed and stay.
