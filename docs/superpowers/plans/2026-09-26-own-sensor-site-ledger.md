# Own-Sensor Site — Debug Ledger

Companion to [`2026-09-26-own-sensor-site.md`](2026-09-26-own-sensor-site.md)
and the spec `../specs/2026-09-26-own-sensor-site-design.md`. Every defect
the pass found, the evidence, the fix, and the check that proved it.

**Status:** fourteen tasks committed on `main`; `verify.py`, design and
behavior modes green at every commit; released with `release.py`.

## Baseline → final

| | before | after |
|---|---|---|
| page words / results words | 1 588 / 1 171 | 818 / 433 |
| phone height (375 × 812) | 17 537 px, 21.6 screens | 13.1 screens by the guard's block-media measure |
| desktop height (1 280 × 800) | 14.2 screens | 12.4 screens |
| distinct font sizes (laptop) | 8 incl. a 14.0 / 14.1 pair | 6 |
| first load at 1 280 | 1.34 MB (Aug optimisation) | 0.33 MB |
| GelSight mentions on the page | 25 lines | 0 |
| result modules | 5 (one all placeholders) | 4 |

## Ledger

| found | evidence | fix | verified by |
|---|---|---|---|
| Shear module quoted a tracker ranking for a method not used | package README: `metrics.json` is an earlier run; phase correlation rejected | rewritten around the shipped pipeline's figures; clips replaced from the current package | `audit_metrics` 42 keys; design + behavior; screenshots |
| GelSight comparison throughout DAT/01 and DAT/04 | author decision: own sensor only | chart, stat pair, passive grid, force bars and table column removed; 7 keys deleted | `grep -ci gelsight` = 0; guards 6 and 8 |
| Removing the SNR block broke the force chart | `pageerror: svgNode is not defined` in behavior mode | helper re-homed into the force block for one task, then removed with it | behavior mode green at both commits |
| `token-mirror` failed the moment the blues left CSS | `verify.py` FAIL on `#2f95d0`, `#6bbef0` | blues retired from DESIGN.md in the same commit | `verify.py` PASS |
| Fig. 9 rows in the deck are not in the paper's order | pptx slide 2: nut label above row 1, but row 1's raw frame shows the M&M dot | rows assigned by image content against the PDF | the three raw frames read |
| M2-screw poster at 2.0 s showed the hand still releasing | frame reviewed | cut at 3.5 s | frame reviewed |
| Task scripts anchored on guessed text | `results.json` last key has no trailing comma; forms `</section>` indentation | anchors read first, then edited | scripts assert every anchor |
| Section h2 at 375 outsized the new 41 px h1 | `flat type hierarchy` guard: 0.79× | h2 phone clamp lowered, then unified in Task 11 | design mode |
| Viewport-edge guard fired on the review hub | its comparison table scrolls by design | guard scoped to the published route | design mode |
| Results index kept five columns for four modules | an empty cell on a desktop; four 64 px rows on a phone | 4-up / 2 × 2 | screenshot; budget guard |
| Phone macro stage held a 380 px floor around a 200 px schematic | `stage_h 380, svg_h 201` | floor removed | budget guard |
| Gallery captions doubled card height in two columns | phone screenshot | descriptor line hidden below 640 px | budget guard |
| Height budget in the spec (9 / 7) unreachable with the content kept | measured 13.1 / 12.4 after the trims | frozen at the measured floor + 0.2, recorded as a revision in the spec | guard red-greened at 1.0 |

## Decisions

- Tip and Flat bodies are shown as photographs only; no characterisation
  data from them (author: fabrication still improving). The form cards are
  titled Flat pad / Fingertip / Humanoid finger; the mapping of deck images
  to those titles was made by content (exploded flat build, exploded dome,
  fingertips in hand) and is the one thing here the author should glance at.
- The 0.12 N controlled figure survives as the sensitivity scope sentence;
  2 mN is worded as a demonstration.
- `snr-curves.json` and `digitize_snr.py` stay as documented, unused
  derivations.

## Open

1. Font decision (DESIGN.md Open issues 1) — unchanged, five WARN lines per
   `verify.py`.
2. Code and Hardware-guide destinations; the arXiv link (one href).
3. Endurance footage.
4. The height budget can only ratchet down from here; the next candidates
   are the shear viewer's near-square clip (1 552 px on a phone) and the
   reconstruction gallery.
