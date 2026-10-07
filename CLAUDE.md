# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The public website for the GlowTact tactile-sensing paper, served by GitHub Pages from `main:/` at
https://glowtact.github.io/. It is a dependency-free static site (HTML, CSS, vanilla JS, inline SVG) plus
Python tooling that measures and gates it. There is no build step, bundler, or package manager.

## Commands

Run everything from the repository root. `python3` is 3.13 (miniconda); Playwright + Chromium, NumPy, Pillow,
and `ffprobe` are installed and required by the browser checks and `digitize_snr.py`. `design/verify.py` and
`tools/*.py` are stdlib-only.

```bash
# Serve. From design/ for the concept routes; from the repo root to see the published page as Pages serves it.
python3 -m http.server 4173 --directory design      # http://127.0.0.1:4173/concept-03/
python3 -m http.server 4173                         # http://127.0.0.1:4173/  (published root)

# Static gate: one h1, alt text, no placeholder links, disclosure copy, prohibited phrases,
# reduced-motion CSS, no console.log, and every data-metric number == design/data/results.json.
python3 design/verify.py
python3 design/tools/audit_metrics.py               # the numbers check alone, while iterating on copy

# Slop / design-system drift detector (static, stdlib, reads DESIGN.md). verify.py gates on its
# immediate tier (--gate); the hooks run it per edit, at Stop, and at SessionStart.
python3 design/tools/audit_slop.py [--deep] [paths...]

# Browser gate (needs the server on 4173, or set GLOWTACT_BASE_URL). Three modes; release runs all.
GLOWTACT_CHECK_MODE=visual   python3 design/browser_check.py   # 4 routes x 2 viewports, screenshots, console/HTTP errors
GLOWTACT_CHECK_MODE=behavior python3 design/browser_check.py   # interactions, keyboard focus, reduced motion
GLOWTACT_CHECK_MODE=design   python3 design/browser_check.py   # contrast, touch targets, type scale, overflow, media, results region, type hierarchy
python3 design/browser_check.py                                # all three

# Regenerate the published root from concept-04 (link-checks; refuses to write a broken page).
python3 design/tools/publish.py

# Full release: stamp -> publish -> verify -> browser_check (all) -> commit -> stamp commit -> push origin main.
python3 design/tools/release.py "type(scope): subject" [--body file] [--skip-checks]
```

There is no way to run a single browser check by name; the unit of selection is the mode. To iterate on one
assertion, call its `check_*` function from a scratch script or temporarily edit `main()` — do not commit that.

Exploratory, verbose counterparts to the gates live in `design/tools/audit_*.py` and `capture_pages.py`
(see `design/tools/README.md`); each starts its own server on a private port. `design/probe_model.py` sweeps
concept-03's contact model in page scope and `design/shots.py` takes mechanism screenshots across compression.

## Architecture

### Two-level page structure, one generated file

- `design/` is the review build: `design/index.html` is a hub comparing three concepts; `concept-01/`
  (Optical Coupling), `concept-02/` (Contact Atlas) and `concept-03/` (Signal Chamber) each hold
  `index.html` + `styles.css` + `app.js`. `concept-04/` is the same page as concept-03
  in a light figure-page register; it has been the published root since 2026-10-07 (concept-03 before, now
  noindex). `/v2/` is a redirect to the root that keeps old links working (see DESIGN.md).
- The repository-root `index.html` is **generated** by `design/tools/publish.py` from
  `design/concept-04/index.html`: it prepends a DO-NOT-EDIT banner and applies the textual `REWRITES` list so
  `./styles.css` → `./design/concept-04/styles.css`, `../assets/` → `./design/assets/`, etc. Nothing else is
  copied; the root page references CSS/JS/media where they already live under `design/`. **Never edit the root
  `index.html` — edit concept-04 and re-run `publish.py`.**
- Consequences of that design:
  - Adding a new top-level asset or stylesheet/script to concept-04 requires a new entry in `publish.py`'s `REWRITES`.
  - `app.js` must not build asset paths from `'../assets/'` literals — `publish.py`'s `check_runtime_paths()`
    rejects them, because the rewrite is textual and cannot see JS. Derive asset directories from the markup
    (e.g. an existing `src`) so the same script resolves from both `/design/concept-03/` and `/`.
  - Bugs of the "works on the concept route, 404s on the published root" kind are the expected failure mode;
    test interactive media on both routes.

### Single source of truth for published numbers

Every scientific number shown on the page is marked `data-metric="dotted.path"` and must equal the value at
that path in `design/data/results.json` (values transcribed from the paper). Numbers a script reads from the
page live in `<script type="application/json" id="...">` blocks, which `audit_metrics.py` also walks. Editing a
number in only one place fails `verify.py`. Add new claims to `results.json` first, then mark them in the markup.
A number shown in another unit carries `data-metric-scale` (0.12 N shown as 120 mN uses `1000`); the gate
checks the page against the value times that factor, and checks that the unit printed after every number is the
data's unit, re-prefixed by the scale (so "0.12 mN" with the scale forgotten fails).

`design/data/snr-curves.json` is digitized from the paper's Fig. 10b by `design/tools/digitize_snr.py`
(the raw SNR data does not exist; the site says so). It needs `materials/figures/SNR.png`, which is untracked.

### Concept-03's contact model

`design/concept-03/app.js` is one physical model feeding three synchronized views (macro device section,
micro 2D section, micro 3D field, plus a simulated camera patch). The tunable constants and their accepted
bounds are frozen in `design/concept-03/PARAMS.md`; everything else is derived. Cross-view consistency is
enforced by `browser_check.py` (design mode) — e.g. the device chord and camera patch both consume
`contactChordUnits()`, the amber ink equals the coupled fraction within 3 pp. When retuning a knob, update
PARAMS.md and run the design-mode check.

### Scientific and copy constraints

`design/SCIENTIFIC_CONSTRAINTS.md` is normative: the mechanism is pressure-induced optical coupling with
single-colour non-directional light (not RGB photometric stereo); the interactive demo is conceptual and must
carry the exact disclosure sentence that `verify.py` checks for (on concept-04, the published root, by the author's decision of 2026-10-06,
the "Schematic" and "Simulated" panel labels stand in for it and are what `verify.py` checks there); passive-object demos are not calibrated
minimum-force measurements; GelSight Mini is a representative baseline, never "cannot detect contact".
`verify.py` also rejects a `PROHIBITED` phrase list.

### DESIGN.md is the design system

`DESIGN.md` at the repository root is the single design-system source. Its YAML frontmatter holds the
tokens (colours, fonts, type scale, tracking steps, motion) **mirrored from `design/concept-03/styles.css`
`:root`**; its body holds the rationale and a `## Don't` list. It is read by `design/tools/audit_slop.py`,
by the design skills in `.claude/skills/`, and by any DESIGN.md-aware tool. Rules that follow from it:

- When a token changes in `styles.css`, change `DESIGN.md` in the same commit; the detector's drift rules
  (`off-palette-color`, `off-scale-font-size`, `tracking-off-step`) fire on the gap.
- DESIGN.md beats a skill's generic advice. The dark ground, single amber accent, monospace readouts and
  tracked-caps labels are the subject's vocabulary (the camera's view of a black membrane), recorded there
  deliberately — not "AI tells" to be corrected. `frontend-design`'s own rule is that the brief wins.
- Amber = GlowTact, blue = GelSight, nothing else gets a hue. A new colour or fixed type size is added to
  DESIGN.md first, then to CSS.
- The `## Open issues` section is live: as of 2026-09-26 the shipped fonts (`Bahnschrift`, `Cascadia Mono`)
  are Windows-only with no webfont, so non-Windows visitors — and the Linux browser checks — see fallbacks.

### Regression-guard discipline

The project's working method, visible in git history and `docs/superpowers/plans/*-ledger.md`: every defect
found is frozen as an assertion in `browser_check.py` or `verify.py`, and every new check is red-greened
(break the thing it guards, watch it fail, restore) before committing. Keep doing this; a check that cannot
fail is treated as a bug.

### Untracked source materials

`materials/` (~467 MiB of figures, slides, captures, meshes, video) is deliberately **not in git** and must
not be added — see `MATERIALS.md` for the layout, the SHA-256 manifest, and `tools/materials_sync.py`
(`push`/`pull`/`status`) and `tools/materials_check.py --verify`. `design/assets/` holds the committed
derivatives the site actually serves. The decisions behind this are recorded in `docs/HANDOFF.md`
("Decisions worth not re-litigating").

## Design skills and the slop hook

Two third-party skills are vendored (copied, not symlinked) under `.claude/skills/` and pinned in
`skills-lock.json`; update with `npx skills update`:

- `frontend-design` (Anthropic) — direction and typography guidance when building or reshaping UI. Defer to
  DESIGN.md where they disagree (see above).
- `web-design-guidelines` (Vercel) — an audit pass over UI files against 100+ a11y/UX/perf rules; it fetches
  the rule list from GitHub at run time, so it needs network access. It reviews; `browser_check.py` gates.

`.claude/settings.json` wires three hooks, all non-blocking:

- `SessionStart` → `audit_slop.py --session`: a digest of DESIGN.md (tokens, baseline, open issues) so the
  design context is loaded before the first edit.
- `PostToolUse` on `Edit|Write` → `audit_slop.py --hook`: for a `.html`/`.css`/`.js` file under `design/`,
  the immediate tier comes back as additional context (plus `token-mirror` when the file is the `:root`
  stylesheet). Silent when clean. It also records the file in a per-session ledger.
- `Stop` → `audit_slop.py --stop`: the deep tier over the files that ledger names, each finding reported
  once, as a system message.

Triage every finding one of three ways: fix it; sanction it with named evidence (`slop-ok: <rule> --
reason` inline, or `detector.sanctioned` in DESIGN.md); or ask the user in one line. A defect that needs a
decision goes under `detector.known_open` with `since` and `reason` — the gate then prints it as WARN
instead of failing. Never widen a sanction to push an edit through.

The project skill `glowtact-design` (`.claude/skills/glowtact-design/SKILL.md`) routes design work through
these gates in order and maps impeccable's verbs (critique, audit, polish, typeset…) onto the tools this
repo already has. Load it for any UI change rather than re-deriving the procedure.

## Conventions

- Design passes are bounded, not loops: build fully, inspect once with a batched round (all routes ×
  viewports, screenshots at 1280 and 375, the design-mode checks), fix everything it shows in one batch,
  confirm with at most one more round, and stop. Open-ended self-QA costs more than the finish gates catch.
- Commit subjects are conventional-commit style with the area as scope: `feat(concept-03):`,
  `test(design):`, `docs(ledger):`, `perf(concept-03):`, `chore(design): stamp <sha>`.
- `release.py` pushes to `origin main` and appends its own `Co-Authored-By` trailer; do not run it for
  intermediate work — commit normally and release once at the end.
- Build stamps (`<span class="build-stamp">` in every page footer, written by `design/tools/stamp.py`) are how
  reviewers tell which deployment they are looking at; `release.py` refreshes them, so stamp diffs in the
  four pages and the root `index.html` are expected noise around a release.
- Design specs and task plans live in `docs/superpowers/specs/` and `docs/superpowers/plans/`, dated
  `YYYY-MM-DD-<slug>.md`; ledgers of found→fixed→verified sit beside the plans.
- Below-fold `<img>` use `loading="lazy"` and `<video>` use `preload="none"` (bytes-on-load is measured and
  guarded); new clips must be H.264 yuv420p (checked with `ffprobe`), not 4:4:4.
- Line endings are normalized to LF via `.gitattributes`; the project moved from Windows to Linux, so a few
  older scripts still carry Windows default paths that are being replaced as touched.
