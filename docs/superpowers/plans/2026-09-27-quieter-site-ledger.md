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

## Third pass: the authored paper and the phone hero

The user's phone screenshot showed the hero floating in a 2000px void with a
tiny header; the paper PDF was still the anonymous review build.

| Found | Measured | Fixed | Verified |
|---|---|---|---|
| `/GlowTact.pdf` was the anonymous 2026-08-07 build | `pdftotext` diff against the supplied 2026-09-26 build: the author block and reflow only, 8 to 9 pages; every number the site quotes re-read on Figs. 5, 8, 9, 10 and Sec. V-B, unchanged | root PDF replaced; copy in `materials/paper/GlowTact-2026-09-27.pdf`, manifest rewritten (`materials_check.py --write`), MATERIALS.md tree updated | `materials_check.py --verify` OK |
| No author information on the site; BibTeX `author = {Anonymous}` on all three concepts | user request | research record carries the seven authors, the two institutions and the equal-contribution mark; BibTeX key `ma2026glowtact` with the author list, on concept-03 and the two frozen concepts | `verify.py` PROHIBITED gains `author = {anonymous}`; design mode asserts `.research-authors` names Adelson and the BibTeX is not anonymous; both red-greened |
| `.research-heading > p:last-child` styled the long title; the new author lines took it over | title lost its 580px measure | selector is `> h2 + p`; `.research-authors` at `--text-label`, affiliations at `--text-fine` tertiary | screenshots at 412 and 980 |
| Hero empty on the phone: the screenshot lays out at about 980px (desktop-site mode or a wide layout viewport) on a 2100px-tall viewport, and `min-height: calc(100svh - 72px)` with a centred copy put the copy 883px below the header | Playwright 980x2100 reproduced it: hero 2028px, copy top 883px | `min-height: min(calc(100svh - 72px), 860px)`; at 1280x900 the value is unchanged (828px) | `check_hero_height` at 980x2100 and 1280x2000: hero at most 900px, copy top at most 360px; red-greened by removing the cap; after: hero 860px, copy top 299px |
| True phone (412px): three stacked full-width buttons under the summary | 168px of buttons | Paper full width, the two pending items share a row with their `coming soon` on a second line | 412px screenshot |

## Fourth pass: the advisor's live clip

`GlowTact BW fingerprint.MOV`, a 29.9 s handheld phone clip (HEVC 10-bit,
1280x720, 30 fps, audio): a GlowTact on a desk, a tablet showing the raw feed,
a fingertip, then a coin pressed through denim. The user asked for it at the
end of the page in two versions, as shot and per-frame cropped against the
shake, with the resolution enhanced.

| Found | Measured | Fixed | Verified |
|---|---|---|---|
| Where to put it: a background or side video was the first idea | the signal (the tablet screen) is about a quarter of the frame; dimmed behind text it would be illegible, and a page-wide autoplaying background breaks the site's poster-and-preload-none discipline | a closing `Live` band before the research record, full content width, the shear clip selector reused (`initClipSelector` now serves both) with `Stabilized` default and `As shot` beside it | design mode: codec gate extended to `#live video`; selector moves source and poster; `preload="none"`; red-greened with `preload="metadata"` |
| Camera shake | tablet-corner template tracking on the source: dx +-16 px (range 79), dy +-22 px (range 69) | vidstab tripod mode locked to frame 1; a second pass gained nothing (3.5 to 3.4 px) and was dropped | after: dx +-3.5 px (range 16), dy +-2 px (range 11) |
| vidstab's default optimal zoom pushed the sensor off the right edge | about 7% zoom about the centre; the sensor pad sat 45 px from the edge in the reference frame | `optzoom=0`, `zoom=0`, `crop=black`, then a fixed 1168x657 window at (96, 63) chosen from the measured border maxima (left 20, right 13, top 34, bottom 0 px) so no frame shows a border; lanczos to 1280x720, `unsharp=5:5:0.5` | zero fully black edge columns across sampled frames; both versions 16:9 so the stage does not jump |
| `release.py`'s `git add design index.html` swept the untracked 21 MB source `.MOV` into the stamp commit `a874f06` and pushed it; the later `git mv` into `materials/` kept it tracked there | `git log --stat --follow` | untracked with `git rm --cached` (file kept on disk, listed in the materials manifest); `release.py` now stages tracked files only (`git add -u`) | `git ls-files materials/` empty; the blob remains in the pushed history unless the branch is rewritten |
| "Enhance resolution" | no super-resolution model on the machine (no torch, no `dnn_superres`) | a 1.1x lanczos resample with light sharpening, stated as such in `design/tools/live_clip.py`; the source stays in `materials/video/` with the manifest rewritten | `ffprobe` h264 yuv420p, 897 frames each; 5.7 MB and 6.7 MB, loaded only on play |

## Fifth pass: the locked view

The user kept only the stabilized version and asked for the zoom, and any
other change of view, to be compensated too, and for the idle seconds at
either end to go.

| Found | Measured | Fixed | Verified |
|---|---|---|---|
| vidstab's tripod mode left the view breathing | homography scale across the clip 0.968 to 1.003 (a 3% zoom drift); tablet corners still moved +-3.5 px | every frame registered to frame 0 by a SIFT and RANSAC homography on the static scene (screen content and the hand zone masked); 897 frames, 0 fallbacks, inliers min 56, median 214 | tablet-corner tracking on the output: +-0.5 px, range 2 to 3 px |
| Output window | the always-covered region is a perspective quadrilateral; a 16:9 window at (96, 63) left 39,840 uncovered pixels | the script picks the largest fully covered rectangle that keeps the tablet (x from 130) and the sensor (x to 1235) | asserted in `live_clip.py`; no black edge in the output |
| Idle seconds at both ends | bright fraction of the hand zone: baseline 0.24, up from 1.0 s, back at 28.0 s; screen contact from 1.7 s to 27.8 s | trimmed to 0.9 to 28.1 s (27.2 s) | frame count in `ffprobe` |
| The as-shot version and its selector | user: the stabilized one only | as-shot clip and poster removed, the page shows one figure, `initClipSelector` serves shear alone again | design mode: one video in `#live`, no tablist or button, `preload="none"`, poster present; red-greened with `preload="metadata"` and a stray button |

## Sixth pass: the arXiv link

| Found | Measured | Fixed | Verified |
|---|---|---|---|
| The paper was linked only as the local PDF | arXiv abs 2609.32471 confirmed by its page metadata: same title, seven authors, 2026-09-26 | `Paper` in the header and the hero goes to the arXiv abstract; the research record gains an `arXiv:2609.32471` link and a `PDF` link to the local copy; BibTeX carries `journal = {arXiv preprint arXiv:2609.32471}` | design mode asserts both `Paper` links point at the arXiv abstract and the record links at arXiv and the PDF |

Not done, on purpose:

- `concept-02` still references `fingerprint-pressure.jpg`, so the file stays
  in the repo although concept-03 no longer uses it.
- The three retired reconstruction objects' assets were deleted; the gallery
  under `~/Desktop/glowtact_materials/gallery/` still holds them.
- The deep slop tier reports two pre-existing concept-02 copy findings
  (`marketing-cadence`, `em-dash-density`); frozen review artifact, untouched.
- `design/assets/images/forms/{flat-exploded,tip-exploded,tips-in-hand}.jpg`
  (1200x900 re-renders of the exploded views, from the untracked
  `.impeccable/`) were held back from the two passes above and committed on
  the user's word afterwards; `.impeccable/`, `Screenshot from 2026-09-26
  23-42-08.png` and `webpage.jpg` stay untracked.
- The `Code` and `Hardware guide` pending buttons in the hero were not
  discussed and stay.
- The phone screenshot's 980px layout is the browser's, not the page's: the
  live page carries the viewport meta and lays out one column at 412px. The
  hero cap makes desktop-site mode tolerable; it does not switch it off.
- The live clip keeps the tablet's own UI chrome and the full 30 s; a trim or
  a true super-resolution pass (Real-ESRGAN, not installed) is the user's
  call.
