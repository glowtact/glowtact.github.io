---
name: glowtact-design
description: Use for any design, layout, typography, colour, motion, copy or UI change on the GlowTact site (design/concept-03/**), and whenever asked to check, audit, critique, polish, review, or release the site's design. Routes the work through the project's measured gates instead of re-deriving them: DESIGN.md → edit → hook → design-mode browser checks → deep pass → release.
---

# GlowTact design workflow

The measurements exist. Do not write a new probe for something a script already
measures; run the script and read its number.

## 0. Context (once per session)

- `DESIGN.md` (repo root): frontmatter = tokens mirrored from `styles.css :root`;
  body = rationale, `## Don't`, `## Open issues`. It beats any skill's generic
  advice — the dark ground, single amber, mono readouts and tracked caps are the
  subject's vocabulary, not tells.
- `design/SCIENTIFIC_CONSTRAINTS.md` for anything that touches a claim.
- `design/concept-03/PARAMS.md` before touching a mechanism constant.
- `frontend-design` for direction only where DESIGN.md leaves an axis free.

## 1. Edit

Only `design/concept-03/`. Never the root `index.html` (generated) and never a
`'../assets/'` literal in `app.js` (publish.py rejects it). New colour, fixed
type size, or tracking step → add to DESIGN.md frontmatter first, then CSS.
New number on the page → `design/data/results.json` first, then `data-metric`.

The PostToolUse hook returns the immediate-tier findings for the file you just
wrote. Triage each: fix; or sanction with named evidence (`slop-ok: <rule> --
reason`, or `detector.sanctioned`); or ask the user in one line. Never widen a
sanction to push an edit through.

## 2. Verify — one bounded round

```bash
python3 -m http.server 4173 --directory design &      # if not already up
python3 design/verify.py                               # contract + numbers + slop gate
GLOWTACT_CHECK_MODE=design python3 design/browser_check.py   # contrast, 44px, type census, overflow, media, ink==number, type hierarchy
P=4173 O=/tmp/gt-shots python3 design/tools/capture_pages.py # then LOOK at 1280 and 375
```

Batch every fix the round shows, run the round again once, stop. Interaction
or motion changes add `GLOWTACT_CHECK_MODE=behavior`. Report deltas
(failures 3 → 0), not impressions.

## 3. Freeze

Every defect class you fixed becomes an assertion in the same commit —
`browser_check.py` for anything rendered, `audit_slop.py` for anything in
source — and is red-greened: break it, watch it fail, restore.

## 4. Before release

```bash
python3 design/tools/audit_slop.py --deep     # taste + copy tier
python3 design/tools/release.py "type(scope): subject"   # stamp → publish → verify → all browser modes → commit → push
```

## Verb map (impeccable → here)

| Ask | Do |
|---|---|
| critique / review | `web-design-guidelines` on the changed files + `capture_pages.py` screenshots; write findings as deltas to measure |
| audit | `verify.py` + design-mode `browser_check.py` |
| polish | `audit_slop.py --deep`, then the bounded round in §2 |
| typeset / colorize / layout | change DESIGN.md first; the drift rules and `token-mirror` hold CSS to it |
| quieter / bolder | check `## Don't` and the palette rule (amber = GlowTact, blue = GelSight, nothing else) before adding anything |
| document / doctor | `audit_slop.py --gate` (token-mirror both ways); `## Open issues` in DESIGN.md |
| harden / adapt | behavior + design modes at 390/768/1280/1440; the media-scaling and touch-target guards |
| clarify (copy) | `PROHIBITED` in verify.py for claims; `marketing-cadence`, `em-dash-density` for register; numbers only via `data-metric` |
