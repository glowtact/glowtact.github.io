# Design Workflow — Debug Ledger (2026-09-26)

What was built to bring the design workflow level with impeccable, every
defect the build exposed, and the check that proved each fix. Companion to
`DESIGN.md` (the design system) and `design/tools/audit_slop.py` (the
detector). Kept here so the decisions survive the session.

**Status:** DESIGN.md at the repo root; detector with 17 static rules in two
tiers; three hooks (SessionStart / PostToolUse / Stop); `verify.py` gates the
immediate tier with a dated `known_open` list; one rendered rule
(`flat-type-hierarchy`) in `browser_check.py` design mode; project skill
`glowtact-design`. Full design mode passes; `verify.py` passes with 5 WARN
(`font-not-shipped`, awaiting a font decision). Nothing committed.

## Ledger

| found | evidence | fix | verified by |
|---|---|---|---|
| `design/design.md` described a light Inter/`#E9A000` site; the shipped concept-03 is dark, `#d89122`, Bahnschrift | `:root` in `styles.css` vs the spec, side by side | rewrote as `DESIGN.md` at the root, tokens mirrored from `:root`, light spec archived as "Review build" | `token-mirror` finds 0 in both directions |
| Shipped fonts are Windows-only with no webfont; hub uses Aptos/Segoe/Iowan | no `@font-face`, no font `<link>`; `fc-list` on this Linux box matches 0 of them | recorded as `detector.known_open` with reason and date; face choice is a design decision left to the owner | `font-not-shipped` x5 print as WARN, gate stays live for everything else |
| Font rule saw nothing on concept-03 | stacks live in `--font-ui`/`--font-mono` custom properties, never in `font-family:` | font rules read `--*font*` custom properties too | baseline went 0 → 2 on `styles.css:2-3` |
| Glow rule flagged solid rings | `0 0 0 24px rgba(...)` reported as "24px blur": the regex took the spread as blur | positional shadow parser (`shadow_blur`), colour-first layers handled, `inset` skipped | `.ring-no-blur` silent, `.glow-plain` / colour-first / `inset` / `text-shadow` fire |
| Glow rule flagged near-black depth shadows | `rgba(4,6,5,.8)` counted as "coloured" | `is_chromatic` = channel spread > 24 | `.dark-shadow-ok` silent |
| Side-tab rule flagged a CSS-drawn glyph | `.form-glyph i:nth-child(2)`: 4px border-left + padding is a picture | selectors ending in `i`, `::before/::after`, `glyph`, `icon` are drawings | `.glyph i` silent, `.callout` fires |
| Tracking rule flagged display tightening | `.form-comparison h3` at `-0.045em`, which DESIGN.md allows | negative tracking exempt; only positive label tracking is snapped to steps | `.tight-display` silent, `.loose-label` fires |
| Rendered hierarchy rule failed on a real page | `signal@phone: h1 58px vs h2 52.5px = 1.10x` | rule scoped: h1 ≥ h2; the 1.15× step applies from h2 down (a phone h1 is already sized by the viewport) | real pages pass; injected `h2,h3,h4{font-size:20px}` fails at 1.00× |
| Four amber glows in the frozen review concepts | `.aperture-contact`, `.step-visual--dark::after`, `.overlay-coupling`, `.signal-core`; concept-03 has none | sanctioned by selector in DESIGN.md with the reason; a new glow anywhere still fires | `audit_slop.py design/shared/review.css` reports 0 for `.signal-core` |
| Detector drift rules skip `:root`, so a retuned token would leave DESIGN.md stale silently | reasoning from the rule scope | `token-mirror`: forward (`:root` hex ∈ DESIGN.md) and reverse (DESIGN.md colour ∈ some stylesheet) | mutated copy: `--signal-amber: #d80000` fires; injected `#0102fa` in DESIGN.md fires |
| One known defect would have switched the whole gate off | gating `font-not-shipped` blocks every release until a font is chosen | `detector.known_open` with `since`/`reason` → WARN, not FAIL | probe `gradient-text` still fails `verify.py` (exit 1) while the 5 WARN print |
| Stop-hook deep pass could nag the same finding every turn | design of the hook | per-session ledger of touched files + reported keys in `$TMPDIR/glowtact-slop/`; each finding once | synthetic session: run 1 reports `em-dash-density`, run 2 silent |
| `.claude/` did not exist at session start | update-config watcher caveat | proved live anyway: a Write of `design/_hook_probe.css` returned the `glass-blur` finding as context | in-session |

## Decisions

- **DESIGN.md wins over a skill's generic advice.** `frontend-design` lists
  mono data labels, tracked caps and a near-black ground with one accent as
  tells; here they are the instrument-panel vocabulary and are recorded as
  such. The skill's own rule ("the brief wins") is the justification.
- **Deep tier does not gate.** Taste and cadence are reviewed (Stop hook,
  `--deep`, and a report in `release.py`), not enforced. The immediate tier
  gates because every rule in it is mechanical.
- **Sanctions are narrow and reasoned.** By selector or inline, never by
  rule, and never to push an edit through. `known_open` is for a defect that
  needs a decision, not for a pattern that is merely inconvenient.
- **Bounded verification.** One batched inspection round, one fix batch, at
  most one confirmation round. Written into CLAUDE.md conventions.

## Rejected

| variant | why not |
|---|---|
| Gate the deep tier | `em-dash-density` at 1.09/100 on shipped copy would block every release over cadence |
| Lower `MIN_HEADING_STEP` to 1.10 so the real page passes | tuning a threshold to the current value proves nothing; scoping the rule to the reading hierarchy is a definition with a reason |
| Sanction the review-build glows by rule (`ignore-rule glow-shadow`) | would silence a new glow in concept-03; by-selector keeps the rule live |
| A `kicker-above-heading` rendered rule | concept-03 puts a `DAT/0x` label above every module heading on purpose; the rule would fire on the design system itself |
| Install `ui-ux-pro-max` | its style catalogue (glassmorphism, claymorphism, bento) is the vocabulary this site avoids |

## Open

1. **Font decision** (`DESIGN.md` Open issues 1). Cascadia Mono is OFL and can
   be self-hosted; Bahnschrift cannot. Until decided, five `font-not-shipped`
   WARN lines print on every `verify.py`.
2. Em-dash density on concept-03 copy: 1.09 per 100 words against a 0.5
   budget (deep tier).
3. Seventeen colour literals outside `:root` are in the DESIGN.md palette but
   not yet tokens.
4. The Stop and SessionStart hooks were added after this session started and
   have not yet been observed firing in a live session (the PostToolUse hook
   has). Watch for the SessionStart digest at the next launch.
