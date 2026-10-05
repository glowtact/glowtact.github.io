"""Static AI-slop and design-system-drift detector for the site's source.

The browser checks measure what renders (contrast, type census, overflow);
this reads what was *written* and catches the patterns a generated page tends
to reach for before they render at all: gradient text, glass blur, glow
shadows, fonts nobody ships, colours and sizes off the declared system,
emoji in chrome, marketing cadence in copy. Every rule is calibrated against
DESIGN.md at the repository root, so a deliberate choice recorded there is
never a finding.

Two tiers, borrowed from impeccable's hook design:

  immediate  mechanical and unambiguous -- worth interrupting an edit for
  deep       taste and cadence -- reviewed once before a release, not per edit

Usage (from the repo root):

    python3 design/tools/audit_slop.py                 # immediate tier, all pages
    python3 design/tools/audit_slop.py --deep          # both tiers
    python3 design/tools/audit_slop.py path/to/file.css [more...]
    python3 design/tools/audit_slop.py --gate          # verify.py's entry: FAIL/WARN lines
    python3 design/tools/audit_slop.py --hook          # Claude Code PostToolUse hook
    python3 design/tools/audit_slop.py --stop          # Claude Code Stop hook: deep pass
    python3 design/tools/audit_slop.py --session       # Claude Code SessionStart digest

Exit 1 on open findings (so it can gate), 0 when clean. A rule listed under
`detector.known_open` in DESIGN.md -- a defect that is acknowledged, owned and
dated -- is printed as WARN and does not fail the gate, so one known problem
does not switch the whole detector off while it waits for a decision.

The three hook modes never exit non-zero and never block: --hook returns the
immediate tier for the edited file as additionalContext and records the file
in a per-session ledger; --stop runs the deep tier over the files that ledger
names and surfaces only what was not already reported; --session prints a
short digest of DESIGN.md and the baseline so a new session starts with the
design context loaded (impeccable's `context` step).

Silence a finding only with evidence. Either an inline comment on the same
or previous line --

    /* slop-ok: glow-shadow -- the coupling glow is the subject, not chrome */
    <!-- slop-ok: emoji-in-ui -- the glyph is data, see CONTENT.md -->

-- or an entry under `detector.sanctioned` in DESIGN.md with a reason.
Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN_MD = ROOT / "DESIGN.md"
DESIGN_DIR = ROOT / "design"
# The root index.html is generated from concept-03 by publish.py; the
# concept is the thing to check.
GENERATED = {ROOT / "index.html"}
SOURCE_EXTS = {".html", ".css", ".js"}

# Fonts that exist only on one vendor's OS. A stack built from these with no
# @font-face or <link> in the project renders as the generic fallback for
# every visitor on another platform -- which is most visitors.
PLATFORM_ONLY_FONTS = {
    "bahnschrift", "cascadia mono", "cascadia code", "segoe ui",
    "segoe ui variable", "aptos", "calibri", "cambria", "consolas",
    "sf pro", "sf pro text", "sf pro display", "sf mono", "-apple-system",
    "helvetica neue", "iowan old style", "avenir", "avenir next", "menlo",
    "monaco", "gill sans", "optima", "roboto", "product sans",
}
# The generated-page default stack. Allowed when DESIGN.md names them.
OVERUSED_FONTS = {
    "inter", "roboto", "arial", "space grotesk", "poppins", "montserrat",
    "open sans", "lato", "dm sans", "plus jakarta sans", "manrope",
}
# Copy cadence that reads as generated. Scientific claims are policed by
# verify.py's PROHIBITED list; this is register, not truth.
MARKETING_CADENCE = [
    r"\bisn'?t just\b", r"\bnot just\b", r"\bmore than just\b",
    r"\bseamless(?:ly)?\b", r"\beffortless(?:ly)?\b", r"\bunlock(?:s|ing)?\b",
    r"\belevat(?:e|es|ing)\b", r"\bempower(?:s|ing)?\b", r"\bdelv(?:e|es|ing)\b",
    r"\bgame-?chang(?:er|ing)\b", r"\bcutting-edge\b", r"\bbest-in-class\b",
    r"\bworld-class\b", r"\bnext-level\b", r"\bsupercharg(?:e|es|ed|ing)\b",
]
EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]"
)
PLACEHOLDER = re.compile(
    r"lorem ipsum|\bTODO\b|\bTBD\b|\{\{[^}]*\}\}|__[A-Z_]+__", re.I
)
HEX = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
COLOR_TOLERANCE = 6          # per channel, 0-255; impeccable uses the same
FONT_SIZE_TOLERANCE = 0.5    # px
GLOW_BLUR_PX = 20


@dataclass
class Finding:
    rule: str
    tier: str
    path: Path
    line: int
    message: str
    fix: str = ""

    def render(self) -> str:
        rel = os.path.relpath(self.path, ROOT)
        text = f"{self.rule:<22} {rel}:{self.line}  {self.message}"
        return f"{text}\n{'':<23} fix: {self.fix}" if self.fix else text


@dataclass
class Design:
    colors: list[tuple[int, int, int]] = field(default_factory=list)
    fonts: set[str] = field(default_factory=set)
    scale: list[float] = field(default_factory=list)
    tracking: list[float] = field(default_factory=list)
    applies_to: str = ""
    source_css: str = ""
    em_dash_per_100: float = 0.5
    sanctioned: list[dict] = field(default_factory=list)
    known_open: list[dict] = field(default_factory=list)
    loaded: bool = False

    def known_rules(self) -> dict[str, dict]:
        return {str(e.get("rule", "")).strip(): e for e in self.known_open if e.get("rule")}


# ---------------------------------------------------------------- DESIGN.md

def parse_frontmatter(text: str) -> dict:
    """A YAML subset: nested maps by indentation, `- item` lists, flow maps
    `{ k: v, k2: v2 }`, quoted scalars, `#` comments. Enough for DESIGN.md
    without a dependency; anything fancier belongs in the body prose."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    lines = text[3:end].splitlines()

    def strip_comment(s: str) -> str:
        out, quote = [], None
        for ch in s:
            if quote:
                out.append(ch)
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
                out.append(ch)
            elif ch == "#":
                break
            else:
                out.append(ch)
        return "".join(out).rstrip()

    def scalar(s: str):
        s = s.strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
            return s[1:-1]
        if s.startswith("{") and s.endswith("}"):
            body, items, depth, cur, quote = s[1:-1], [], 0, "", None
            for ch in body:
                if quote:
                    cur += ch
                    if ch == quote:
                        quote = None
                elif ch in "\"'":
                    quote = ch
                    cur += ch
                elif ch == "," and depth == 0:
                    items.append(cur)
                    cur = ""
                else:
                    cur += ch
            if cur.strip():
                items.append(cur)
            result = {}
            for item in items:
                k, _, v = item.partition(":")
                result[k.strip()] = scalar(v)
            return result
        if s.startswith("[") and s.endswith("]"):
            return [scalar(x) for x in s[1:-1].split(",") if x.strip()]
        return s

    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]
    for raw in lines:
        line = strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if content.startswith("- "):
            value = scalar(content[2:])
            if isinstance(parent, dict):
                # A list under a key whose value is still an empty dict.
                key = stack[-1][2] if len(stack[-1]) > 2 else None
                grand = stack[-2][1] if len(stack) > 1 else None
                if key is not None and isinstance(grand, dict):
                    grand[key] = [value]
                    stack[-1] = (stack[-1][0], grand[key], key)
                continue
            parent.append(value)
            continue
        key, sep, value = content.partition(":")
        if not sep:
            continue
        key = key.strip()
        if value.strip():
            parent[key] = scalar(value)
        else:
            parent[key] = {}
            stack.append((indent, parent[key], key))
    return root


def walk_strings(node):
    if isinstance(node, dict):
        for v in node.values():
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)
    elif isinstance(node, str):
        yield node


def parse_hex(value: str) -> tuple[int, int, int] | None:
    m = HEX.fullmatch(value.strip())
    if not m:
        return None
    h = value.strip()[1:]
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    elif len(h) == 8:
        h = h[:6]
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def parse_em(value: str) -> float | None:
    m = re.fullmatch(r"\s*(-?[0-9.]+)em\s*", value)
    return float(m.group(1)) if m else None


def load_design() -> Design:
    d = Design()
    if not DESIGN_MD.exists():
        return d
    fm = parse_frontmatter(DESIGN_MD.read_text(encoding="utf-8"))
    if not fm:
        return d
    d.loaded = True
    for s in walk_strings(fm.get("colors", {})):
        rgb = parse_hex(s)
        if rgb:
            d.colors.append(rgb)
    typo = fm.get("typography", {}) if isinstance(fm.get("typography"), dict) else {}
    for s in walk_strings(typo.get("fonts", {})):
        for fam in s.split(","):
            fam = fam.strip().strip("\"'").lower()
            if fam:
                d.fonts.add(fam)
    for s in walk_strings(typo.get("scale", [])):
        try:
            d.scale.append(float(str(s).replace("px", "")))
        except ValueError:
            pass
    for s in walk_strings(typo.get("tracking", [])):
        em = parse_em(str(s))
        if em is not None:
            d.tracking.append(em)
    det = fm.get("detector", {}) if isinstance(fm.get("detector"), dict) else {}
    d.applies_to = str(fm.get("applies_to", "")).strip()
    try:
        d.em_dash_per_100 = float(det.get("em_dash_per_100_words", d.em_dash_per_100))
    except (TypeError, ValueError):
        pass
    sanctioned = det.get("sanctioned", [])
    d.sanctioned = [x for x in sanctioned if isinstance(x, dict)] if isinstance(sanctioned, list) else []
    known = det.get("known_open", [])
    d.known_open = [x for x in known if isinstance(x, dict)] if isinstance(known, list) else []
    # "design/concept-03/styles.css (:root)" -> the path part
    d.source_css = str(fm.get("source_of_truth", "")).split()[0] if fm.get("source_of_truth") else ""
    return d


def near(rgb: tuple[int, int, int], refs) -> bool:
    return any(all(abs(a - c) <= COLOR_TOLERANCE for a, c in zip(rgb, ref)) for ref in refs)


def token_mirror(design: Design) -> list[Finding]:
    """DESIGN.md and the :root it mirrors must agree in both directions.

    The drift rules skip :root on purpose (that is where new tokens are
    declared), so without this a token retuned in CSS would leave DESIGN.md
    quietly describing the old site -- the exact failure this file replaced.
    Forward: every hex token in :root is in DESIGN.md. Reverse: every DESIGN.md
    colour still appears somewhere in the applies_to stylesheets."""
    if not (design.loaded and design.source_css):
        return []
    css_path = ROOT / design.source_css
    if not css_path.exists():
        return [Finding("token-mirror", "immediate", DESIGN_MD, 1,
                        f"source_of_truth {design.source_css} does not exist",
                        "point DESIGN.md source_of_truth at the published stylesheet")]
    text = css_path.read_text(encoding="utf-8", errors="ignore")
    out: list[Finding] = []
    seen: dict[tuple[int, int, int], tuple[str, str, int]] = {}
    for b in parse_css(text):
        if b.selector.strip() != ":root":
            continue
        for p, v, ln in b.decls:
            if not p.startswith("--"):
                continue
            for m in HEX.finditer(v):
                rgb = parse_hex(m.group(0))
                if rgb:
                    seen.setdefault(rgb, (p, m.group(0), ln))
    for rgb, (p, raw, ln) in seen.items():
        if not near(rgb, design.colors):
            out.append(Finding("token-mirror", "immediate", css_path, ln,
                               f":root {p}: {raw} is not in DESIGN.md colors; the mirror is stale",
                               "update the token in DESIGN.md frontmatter in the same commit"))
    scope = ROOT / design.applies_to if design.applies_to else css_path.parent
    css_files = list(scope.rglob("*.css")) if scope.is_dir() else [css_path]
    corpus = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in css_files)
    present = {parse_hex(m.group(0)) for m in HEX.finditer(corpus)}
    design_text = DESIGN_MD.read_text(encoding="utf-8")
    for ref in design.colors:
        if near(ref, present):
            continue
        hex6 = "#%02x%02x%02x" % ref
        line = next((i + 1 for i, l in enumerate(design_text.splitlines())
                     if any(parse_hex(m.group(0)) == ref for m in HEX.finditer(l))), 1)
        out.append(Finding("token-mirror", "immediate", DESIGN_MD, line,
                           f"DESIGN.md colour {hex6} appears in no stylesheet under {design.applies_to or css_path.parent.name}; stale token",
                           "remove it from DESIGN.md or restore it in CSS"))
    return out


# -------------------------------------------------------------- CSS parsing

@dataclass
class Block:
    selector: str
    line: int
    decls: list[tuple[str, str, int]]   # (property, value, line)

    def get(self, prop: str) -> list[tuple[str, int]]:
        return [(v, ln) for p, v, ln in self.decls if p == prop]

    def has(self, prefix: str) -> bool:
        return any(p.startswith(prefix) for p, _, _ in self.decls)


def strip_css_comments(text: str) -> str:
    # Keep line numbers stable: replace comment bodies with spaces/newlines.
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)


def parse_css(text: str) -> list[Block]:
    """Innermost rule blocks only; @media wrappers contribute no declarations."""
    clean = strip_css_comments(text)
    blocks: list[Block] = []
    i, n = 0, len(clean)
    stack: list[tuple[str, int, int]] = []   # (selector, start_line, body_start)
    while i < n:
        ch = clean[i]
        if ch == "{":
            j = i - 1
            while j >= 0 and clean[j] not in "{};":
                j -= 1
            selector = clean[j + 1:i].strip()
            stack.append((selector, clean.count("\n", 0, i) + 1, i + 1))
        elif ch == "}" and stack:
            selector, line, body_start = stack.pop()
            body = clean[body_start:i]
            if "{" in body:            # a wrapper (@media etc.); children handled
                i += 1
                continue
            decls = []
            offset = body_start
            for part in body.split(";"):
                if ":" in part:
                    prop, _, value = part.partition(":")
                    decls.append((prop.strip().lower(), value.strip(),
                                  clean.count("\n", 0, offset + part.find(prop.strip())) + 1))
                offset += len(part) + 1
            if decls:
                blocks.append(Block(selector, line, decls))
        i += 1
    return blocks


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def split_layers(value: str) -> list[str]:
    """Split a shadow list on top-level commas (not the ones inside rgba())."""
    layers, depth, cur = [], 0, ""
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            layers.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        layers.append(cur)
    return layers


def shadow_blur(layer: str) -> float:
    """The blur radius of one shadow layer, read by position.

    A shadow is `[inset] offset-x offset-y [blur [spread]] color`, and the
    colour may come first. `0 0 0 24px` is therefore a solid 24px ring with
    no blur at all -- the first version of this rule read that 24 as blur and
    flagged every hairline ring in the review build. Strip the colour, then
    the third length is the blur or there is none."""
    rest = re.sub(r"rgba?\([^)]*\)|hsla?\([^)]*\)|var\(--[^)]*\)|#[0-9a-fA-F]{3,8}\b", " ", layer)
    tokens = [t for t in rest.split() if t.lower() != "inset"]
    lengths = []
    for t in tokens:
        m = re.fullmatch(r"(-?[0-9.]+)(px|rem|em)?", t)
        if not m:
            break   # a named colour or keyword ends the length run
        n = float(m.group(1))
        lengths.append(n * 16 if m.group(2) in ("rem", "em") else n)
    return lengths[2] if len(lengths) >= 3 else 0.0


def is_chromatic(value: str) -> bool:
    """True when the value names a colour with hue -- channel spread over 24 --
    so near-black depth shadows and white rings stay out of the glow rule."""
    for m in re.finditer(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", value):
        r, g, bl = (int(x) for x in m.groups())
        if max(r, g, bl) - min(r, g, bl) > 24:
            return True
    for m in HEX.finditer(value):
        rgb = parse_hex(m.group(0))
        if rgb and max(rgb) - min(rgb) > 24:
            return True
    return False


def sanctioned(design: Design, text: str, rule: str, line: int, selector: str, path: Path) -> bool:
    lines = text.splitlines()
    for ln in (line, line - 1):
        if 1 <= ln <= len(lines) and re.search(rf"slop-ok:\s*{re.escape(rule)}\b", lines[ln - 1]):
            return True
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    for entry in design.sanctioned:
        if str(entry.get("rule", "")).strip() != rule:
            continue
        match = str(entry.get("match", "")).strip()
        if match and (match in selector or match in rel):
            return True
    return False


def in_scope(design: Design, path: Path) -> bool:
    """Design-system drift rules apply only to the published concept."""
    if not design.applies_to:
        return True
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    prefix = design.applies_to.rstrip("*").rstrip("/")
    return rel.startswith(prefix)


def page_ships_fonts(css_path: Path) -> bool:
    """Whether the page this stylesheet belongs to ships a webfont.

    Scoped to the stylesheet and the HTML beside it: one page loading a
    webfont does not fix another page whose stack names only OS faces.
    A project-wide test let concept-04's Geist link clear concept-03's
    font-not-shipped finding (2026-10-05).
    """
    if "@font-face" in css_path.read_text(encoding="utf-8", errors="ignore"):
        return True
    for html in css_path.parent.glob("*.html"):
        if re.search(r"fonts\.(googleapis|bunny)|rel=\"preload\"[^>]*as=\"font\"",
                     html.read_text(encoding="utf-8", errors="ignore")):
            return True
    return False


# ----------------------------------------------------------------- CSS rules

def css_rules(path: Path, text: str, design: Design, deep: bool) -> list[Finding]:
    out: list[Finding] = []
    blocks = parse_css(text)
    ships_fonts = page_ships_fonts(path)
    scoped = in_scope(design, path)

    def add(rule, tier, line, selector, message, fix=""):
        if tier == "deep" and not deep:
            return
        if sanctioned(design, text, rule, line, selector, path):
            return
        out.append(Finding(rule, tier, path, line, message, fix))

    for b in blocks:
        sel = b.selector
        # gradient text
        for v, ln in b.get("background-clip") + b.get("-webkit-background-clip"):
            if "text" in v:
                add("gradient-text", "immediate", ln, sel,
                    f"{sel}: background-clip: text (gradient headline)",
                    "set a solid colour from the palette; the amber ink is the accent")
        # glass
        for v, ln in b.get("backdrop-filter") + b.get("-webkit-backdrop-filter"):
            if "blur" in v:
                add("glass-blur", "immediate", ln, sel,
                    f"{sel}: backdrop-filter blur (glassmorphism)",
                    "use an opaque surface token (--optic-surface-*)")
        # glow shadows: large blur in a chromatic colour. Each comma-separated
        # layer is judged on its own so a hairline ring next to a glow still
        # names the glow.
        for prop in ("box-shadow", "text-shadow"):
            for v, ln in b.get(prop):
                for layer in split_layers(v):
                    blur = shadow_blur(layer)
                    if blur < GLOW_BLUR_PX or not is_chromatic(layer):
                        continue
                    add("glow-shadow", "immediate", ln, sel,
                        f"{sel}: {prop} layer '{layer.strip()}' is a {blur:g}px coloured blur (glow)",
                        "shadows here are hairline rings, not glows; use --optic-ring")
        # motion
        for v, ln in b.get("animation") + b.get("animation-iteration-count"):
            if re.search(r"\binfinite\b", v):
                add("infinite-motion", "immediate", ln, sel,
                    f"{sel}: infinite animation (constant pulsing)",
                    "motion answers the slider or a scroll reveal; nothing loops")
        for prop in ("transition", "transition-timing-function", "animation", "animation-timing-function"):
            for v, ln in b.get(prop):
                for m in re.finditer(r"cubic-bezier\(\s*[-0-9.]+\s*,\s*(-?[0-9.]+)\s*,\s*[-0-9.]+\s*,\s*(-?[0-9.]+)\s*\)", v):
                    y1, y2 = float(m.group(1)), float(m.group(2))
                    if y1 > 1 or y1 < 0 or y2 > 1 or y2 < 0:
                        add("bounce-easing", "immediate", ln, sel,
                            f"{sel}: overshooting easing {m.group(0)}",
                            "use var(--ease-out) = cubic-bezier(0.23, 1, 0.32, 1)")
        # fonts. This site declares its stacks as custom properties
        # (--font-ui, --font-mono) and only ever writes font-family: var(...),
        # so the custom properties are where the faces are named.
        font_decls = b.get("font-family") + [
            (v, ln) for p, v, ln in b.decls if p.startswith("--") and "font" in p
        ]
        for v, ln in font_decls:
            if v.startswith("var("):
                continue
            families = [f.strip().strip("\"'").lower() for f in v.split(",")]
            named = [f for f in families if f and f not in
                     ("sans-serif", "serif", "monospace", "system-ui", "ui-sans-serif", "ui-monospace", "ui-serif")]
            if named and not ships_fonts and all(f in PLATFORM_ONLY_FONTS for f in named):
                add("font-not-shipped", "immediate", ln, sel,
                    f"{sel}: font-family {v} names only platform-specific faces and the project ships no webfont; "
                    "renders as the generic fallback on every other OS",
                    "self-host the face (@font-face, woff2) or choose a cross-platform stack, then record it in DESIGN.md")
            for f in named:
                if f in OVERUSED_FONTS and f not in design.fonts:
                    add("overused-font", "immediate", ln, sel,
                        f"{sel}: {f!r} is the generated-page default; not in DESIGN.md",
                        "pick a face for this brief or add it to DESIGN.md typography.fonts with a reason")
        # design-system drift (published concept only)
        if scoped and design.loaded:
            for v, ln in b.get("font-size"):
                m = re.fullmatch(r"([0-9.]+)(px|rem)", v)
                if not m:
                    continue
                px = float(m.group(1)) * (16 if m.group(2) == "rem" else 1)
                if not any(abs(px - s) <= FONT_SIZE_TOLERANCE for s in design.scale):
                    add("off-scale-font-size", "immediate", ln, sel,
                        f"{sel}: font-size {v} is not on the DESIGN.md scale {sorted(design.scale)}",
                        "snap to --text-fine/label/title or a clamp(); a new fixed step is a design decision -- add it to DESIGN.md")
            if sel.strip() != ":root":
                for p, v, ln in b.decls:
                    for m in HEX.finditer(v):
                        rgb = parse_hex(m.group(0))
                        if rgb and not any(all(abs(a - c) <= COLOR_TOLERANCE for a, c in zip(rgb, ref)) for ref in design.colors):
                            add("off-palette-color", "immediate", ln, sel,
                                f"{sel}: {m.group(0)} is not within tolerance of any DESIGN.md colour",
                                "use a :root token; if the colour is intentional, add it to DESIGN.md colors")
            if design.tracking:
                upper = any("uppercase" in v for v, _ in b.get("text-transform"))
                if upper:
                    for v, ln in b.get("letter-spacing"):
                        em = parse_em(v)
                        # Negative tracking is display tightening, a different
                        # decision from label tracking; DESIGN.md allows it.
                        if em is not None and em > 0 and not any(abs(em - t) < 1e-6 for t in design.tracking):
                            add("tracking-off-step", "deep", ln, sel,
                                f"{sel}: caps label tracked {v}; DESIGN.md steps are {design.tracking}",
                                "snap to a declared tracking step")
        # taste tier. Glyphs drawn in CSS (an <i> with borders, a ::before)
        # are pictures, not cards; the side-tab rule is about text blocks.
        drawing = bool(re.search(r"(?:^|\s)i(?::|$)|::?(?:before|after)\b|glyph|icon", sel))
        lefts = [] if drawing else b.get("border-left")
        if lefts and not (b.has("border-top") or b.has("border-bottom")):
            for v, ln in lefts:
                m = re.match(r"([0-9.]+)px\s+solid", v)
                if m and float(m.group(1)) >= 3 and (b.has("padding") or b.has("background")):
                    add("side-tab", "deep", ln, sel,
                        f"{sel}: {v} accent bar on a padded block (side-tab card)",
                        "structure is information: use a hairline rule or a heading, not a coloured tab")
        for v, ln in b.get("border-radius"):
            if re.search(r"\b(999|9999)px\b|100vmax", v) and b.has("padding"):
                add("pill-radius", "deep", ln, sel,
                    f"{sel}: pill radius on a padded element (chip/badge)",
                    "this system has no rounded chrome; radius is 0 or 50% for dots and lenses")
    return out


# ---------------------------------------------------------------- HTML rules

def html_rules(path: Path, text: str, design: Design, deep: bool) -> list[Finding]:
    out: list[Finding] = []

    def add(rule, tier, line, message, fix=""):
        if tier == "deep" and not deep:
            return
        if sanctioned(design, text, rule, line, "", path):
            return
        out.append(Finding(rule, tier, path, line, message, fix))

    body = re.sub(r"<script.*?</script>|<style.*?</style>", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    for m in EMOJI.finditer(body):
        add("emoji-in-ui", "immediate", line_of(text, m.start()),
            f"emoji {m.group(0)!r} in markup", "the interface vocabulary is type and hairlines; no emoji")
    for m in PLACEHOLDER.finditer(body):
        add("placeholder-copy", "immediate", line_of(text, m.start()),
            f"placeholder text {m.group(0)!r}", "ship real copy or remove the element")
    for m in re.finditer(r"(→|&rarr;|&#8594;)\s*</a>", body):
        add("arrow-suffix-link", "deep", line_of(text, m.start()),
            "link text ends in an arrow", "the verb is the affordance; drop the arrow")

    # prose: strip tags, decode the few entities that matter
    prose = re.sub(r"<[^>]+>", " ", body)
    prose = prose.replace("&mdash;", "—").replace("&nbsp;", " ").replace("&amp;", "&")
    for pat in MARKETING_CADENCE:
        for m in re.finditer(pat, prose, re.I):
            add("marketing-cadence", "deep", line_of(text, m.start()),
                f"copy reads as generated: {m.group(0)!r}",
                "say the measured thing; verify.py's PROHIBITED list handles claims, this is register")
    words = len(re.findall(r"[A-Za-z][A-Za-z'-]+", prose))
    dashes = prose.count("—")
    if words >= 200 and dashes:
        per100 = 100 * dashes / words
        if per100 > design.em_dash_per_100:
            add("em-dash-density", "deep", 1,
                f"{dashes} em dashes in {words} words = {per100:.2f} per 100 (DESIGN.md allows {design.em_dash_per_100:g})",
                "a dash is a pause the sentence could not structure; recast the sentence")
    return out


# ------------------------------------------------------------------- driver

def targets_default() -> list[Path]:
    paths = []
    for p in sorted(DESIGN_DIR.rglob("*")):
        if p.suffix in SOURCE_EXTS and "assets" not in p.parts and p not in GENERATED:
            paths.append(p)
    return paths


def check(path: Path, design: Design, deep: bool) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix == ".css":
        return css_rules(path, text, design, deep)
    if path.suffix == ".html":
        return html_rules(path, text, design, deep)
    return []   # .js: publish.py guards runtime asset paths; verify.py guards console.*


def split_known(findings: list[Finding], design: Design) -> tuple[list[Finding], list[Finding]]:
    known = design.known_rules()
    return ([f for f in findings if f.rule not in known],
            [f for f in findings if f.rule in known])


def known_line(f: Finding, design: Design) -> str:
    e = design.known_rules().get(f.rule, {})
    rel = os.path.relpath(f.path, ROOT)
    return (f"WARN slop {f.rule} {rel}:{f.line} known-open since {e.get('since', '?')}: "
            f"{e.get('reason', 'no reason recorded')}")


def by_rule_summary(findings: list[Finding]) -> str:
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.rule] = counts.get(f.rule, 0) + 1
    return ", ".join(f"{k} x{v}" for k, v in sorted(counts.items()))


# ------------------------------------------------------------ session ledger
# The per-edit hook remembers which design files a session touched; the Stop
# hook reads that back and runs the deep tier over exactly those, reporting
# each finding once. Lives in the OS temp dir, keyed by Claude's session id.

LEDGER_DIR = Path(tempfile.gettempdir()) / "glowtact-slop"


def finding_key(f: Finding) -> str:
    return f"{f.rule}|{os.path.relpath(f.path, ROOT)}|{f.line}"


def ledger_files(session_id: str) -> tuple[Path, Path]:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:80] or "anon"
    return LEDGER_DIR / f"{safe}.paths", LEDGER_DIR / f"{safe}.reported.json"


def remember(session_id: str, path: Path | None, findings: list[Finding]) -> None:
    if not session_id:
        return
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    paths_file, reported_file = ledger_files(session_id)
    if path is not None:
        touched = set(paths_file.read_text().splitlines()) if paths_file.exists() else set()
        touched.add(str(path))
        paths_file.write_text("\n".join(sorted(touched)) + "\n")
    if findings:
        reported = set(json.loads(reported_file.read_text())) if reported_file.exists() else set()
        reported |= {finding_key(f) for f in findings}
        reported_file.write_text(json.dumps(sorted(reported)))


def read_payload() -> dict:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def hook_mode() -> int:
    payload = read_payload()
    session_id = str(payload.get("session_id", ""))
    file_path = (payload.get("tool_input") or {}).get("file_path") \
        or (payload.get("tool_response") or {}).get("filePath")
    if not file_path:
        return 0
    path = Path(file_path)
    if not path.is_absolute():
        path = ROOT / path
    try:
        path.relative_to(DESIGN_DIR)
    except ValueError:
        return 0
    if path.suffix not in SOURCE_EXTS or path in GENERATED or not path.exists():
        return 0
    design = load_design()
    findings = check(path, design, deep=False)
    if design.source_css and path.resolve() == (ROOT / design.source_css).resolve():
        findings += token_mirror(design)
    remember(session_id, path, findings)
    open_findings, known = split_known(findings, design)
    if not open_findings:
        return 0
    rel = os.path.relpath(path, ROOT)
    lines = [f"Design detector: {len(open_findings)} finding(s) in {rel} "
             f"(immediate tier; DESIGN.md is the reference)."]
    lines += ["  " + f.render().replace("\n", "\n  ") for f in open_findings]
    if known:
        lines.append(f"  (+{len(known)} known-open, listed in DESIGN.md detector.known_open: "
                     f"{by_rule_summary(known)})")
    lines.append("Fix each, or sanction it with evidence (`slop-ok: <rule> -- reason` inline, "
                 "or DESIGN.md detector.sanctioned). Do not silence a rule to push an edit through.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "\n".join(lines),
    }}))
    return 0


def stop_mode() -> int:
    """Deep pass over the files this session touched; each finding once."""
    payload = read_payload()
    session_id = str(payload.get("session_id", ""))
    if not session_id:
        return 0
    paths_file, reported_file = ledger_files(session_id)
    if not paths_file.exists():
        return 0
    touched = [Path(p) for p in paths_file.read_text().splitlines() if p.strip()]
    touched = [p for p in touched if p.exists() and p.suffix in SOURCE_EXTS]
    if not touched:
        return 0
    design = load_design()
    findings: list[Finding] = []
    for p in touched:
        findings += check(p, design, deep=True)
    if design.source_css and any(p.resolve() == (ROOT / design.source_css).resolve() for p in touched):
        findings += token_mirror(design)
    reported = set(json.loads(reported_file.read_text())) if reported_file.exists() else set()
    known = design.known_rules()
    fresh = [f for f in findings if finding_key(f) not in reported and f.rule not in known]
    if not fresh:
        return 0
    remember(session_id, None, fresh)
    lines = [f"Design deep pass: {len(fresh)} new finding(s) in the {len(touched)} design "
             f"file(s) touched this session [{by_rule_summary(fresh)}]."]
    lines += ["  " + f.render().split("\n")[0] for f in fresh[:12]]
    if len(fresh) > 12:
        lines.append(f"  ... {len(fresh) - 12} more")
    lines.append("Review with: python3 design/tools/audit_slop.py --deep")
    print(json.dumps({"systemMessage": "\n".join(lines)}))
    return 0


def session_mode() -> int:
    """SessionStart digest: the design context, loaded before the first edit."""
    design = load_design()
    if not design.loaded:
        return 0
    findings = [f for p in targets_default() for f in check(p, design, deep=False)] + token_mirror(design)
    open_findings, known = split_known(findings, design)
    text = DESIGN_MD.read_text(encoding="utf-8")
    m = re.search(r"^## Open issues[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    issues = re.findall(r"^\d+\.\s+\*\*([^*]+)\*\*", m.group(1), re.M) if m else []
    lines = [
        "GlowTact design context (DESIGN.md at the repo root is the design system; it beats a skill's generic advice):",
        f"  tokens: {len(design.colors)} colours, fonts {sorted(design.fonts)}, type scale {sorted(int(s) for s in design.scale)} px "
        f"+ clamp(), tracking {design.tracking} em; drift rules scoped to {design.applies_to or 'all'}",
        f"  detector baseline: {len(open_findings)} open finding(s)"
        + (f" [{by_rule_summary(open_findings)}]" if open_findings else "")
        + f", {len(known)} known-open" + (f" [{by_rule_summary(known)}]" if known else ""),
    ]
    if issues:
        lines.append("  open issues: " + "; ".join(issues))
    lines.append("  workflow: read DESIGN.md `## Don't` before a UI edit; the PostToolUse hook reports the immediate tier; "
                 "the Stop hook reports the deep tier once; `python3 design/tools/audit_slop.py --deep` before release.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n".join(lines),
    }}))
    return 0


def gate_mode() -> int:
    """verify.py's entry point: one FAIL line per open finding, WARN per known."""
    design = load_design()
    findings = [f for p in targets_default() for f in check(p, design, deep=False)] + token_mirror(design)
    open_findings, known = split_known(findings, design)
    for f in open_findings:
        rel = os.path.relpath(f.path, ROOT)
        print(f"FAIL slop {f.rule} {rel}:{f.line} {f.message}")
    for f in known:
        print(known_line(f, design))
    print(f"slop: {len(open_findings)} open, {len(known)} known-open"
          + (f" [{by_rule_summary(known)}]" if known else ""))
    return 1 if open_findings else 0


def main(argv: list[str]) -> int:
    if "--hook" in argv:
        return hook_mode()
    if "--stop" in argv:
        return stop_mode()
    if "--session" in argv:
        return session_mode()
    if "--gate" in argv:
        return gate_mode()
    deep = "--deep" in argv
    as_json = "--json" in argv
    paths = [Path(a).resolve() for a in argv if not a.startswith("--")]
    explicit = bool(paths)
    paths = paths or targets_default()
    design = load_design()
    if not design.loaded:
        print(f"WARN: {DESIGN_MD.relative_to(ROOT)} missing or without frontmatter; "
              "design-system drift rules are off", file=sys.stderr)
    findings: list[Finding] = []
    for p in paths:
        if p.is_dir():
            for q in sorted(p.rglob("*")):
                if q.suffix in SOURCE_EXTS and q not in GENERATED:
                    findings += check(q, design, deep)
        elif p.exists():
            findings += check(p, design, deep)
    if not explicit or any(design.source_css and p.resolve() == (ROOT / design.source_css).resolve() for p in paths):
        findings += token_mirror(design)
    open_findings, known = split_known(findings, design)
    if as_json:
        print(json.dumps([{**f.__dict__, "path": os.path.relpath(f.path, ROOT),
                           "known_open": f.rule in design.known_rules()} for f in findings], indent=1))
    else:
        for f in open_findings:
            print(f.render())
        for f in known:
            print(known_line(f, design))
    tier = "immediate+deep" if deep else "immediate"
    n_files = sum(1 for p in paths for _ in ([p] if p.is_file() else [q for q in p.rglob("*") if q.suffix in SOURCE_EXTS]))
    known_note = f"; {len(known)} known-open [{by_rule_summary(known)}]" if known else ""
    if open_findings:
        print(f"FAIL: {len(open_findings)} finding(s) across {n_files} files [{tier}]: "
              f"{by_rule_summary(open_findings)}{known_note}")
        return 1
    print(f"PASS: 0 open findings across {n_files} files [{tier}]{known_note}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
