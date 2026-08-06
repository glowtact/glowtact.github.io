# Design workflow tools

Measurement-first audits used to build and now to guard the site's design.
Each serves its own copy of `design/` on a private port; run from repo root.

| Tool | Question it answers |
|---|---|
| `audit_layout.py` | Overflow, tiny text, touch targets, font-size census — 4 routes × 4 viewports |
| `audit_contrast.py` | Does every text node meet WCAG AA against its real composited background? |
| `audit_consistency.py` | Do the device chord, camera patch and microscope agree at 8 pressures? |
| `audit_text.py` | Words per section; paragraphs worth trimming |
| `capture_pages.py` | Full-page screenshots, desktop + mobile (`P=<port> O=<outdir>`) |

The pass/fail versions of these live in `design/browser_check.py`
(`GLOWTACT_CHECK_MODE=design`); these scripts are the exploratory,
verbose-output counterparts. Accepted parameter baseline:
`design/concept-03/PARAMS.md`.
