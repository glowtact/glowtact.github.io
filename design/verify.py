from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
ROUTES = [
    ROOT / "index.html",
    ROOT / "concept-01" / "index.html",
    ROOT / "concept-02" / "index.html",
    ROOT / "concept-03" / "index.html",
    ROOT / "concept-04" / "index.html",
]
DISCLOSURE = (
    "Conceptual visualization. Geometry and optical paths are schematic and "
    "are not a calibrated mechanical or ray-tracing simulation."
)
PROHIBITED = (
    "revolutionary",
    "pixel-wise pressure",
    "calibrated pressure map",
    "indestructible",
    "maintenance-free",
    "author = {anonymous}",
)


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_count = 0
        self.local_refs: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "img" and "alt" not in values:
            self.errors.append("image without alt")
        for key in ("href", "src"):
            value = values.get(key)
            if value == "#":
                self.errors.append(f"{tag} has placeholder {key}")
            if value and not value.startswith(
                ("http:", "https:", "mailto:", "#", "data:")
            ):
                self.local_refs.append(value.split("?", 1)[0].split("#", 1)[0])


def audit(route: Path) -> list[str]:
    text = route.read_text(encoding="utf-8")
    parser = AuditParser()
    parser.feed(text)
    errors = list(parser.errors)
    if parser.h1_count != 1:
        errors.append(f"expected one h1, found {parser.h1_count}")
    if route.name == "index.html" and route.parent.name.startswith("concept-"):
        if DISCLOSURE not in text:
            errors.append("missing conceptual visualization disclosure")
    lowered = text.lower()
    for phrase in PROHIBITED:
        if phrase in lowered:
            errors.append(f"prohibited phrase: {phrase}")
    for ref in parser.local_refs:
        target = (route.parent / ref).resolve()
        if not target.exists():
            errors.append(f"missing local reference: {ref}")
    errors.extend(indexing(route, text))
    return errors


def indexing(route: Path, text: str) -> list[str]:
    """Search engines see one page: the published root. concept-03 is its
    source (and its own route), so it declares the root canonical and the
    article's structured data; the review hub and the other concepts are
    noindex. Added for Search Console on 2026-10-01."""
    errors: list[str] = []
    public = route.name == "index.html" and route.parent.name in ("concept-03", ROOT.parent.name)
    if public:
        if 'rel="canonical" href="https://glowtact.github.io/"' not in text:
            errors.append("missing canonical link to the published root")
        if 'property="og:image"' not in text or 'name="twitter:card"' not in text:
            errors.append("missing Open Graph or Twitter card tags")
        start = text.find('<script type="application/ld+json">')
        end = text.find("</script>", start)
        try:
            data = json.loads(text[start + len('<script type="application/ld+json">'):end]) if start >= 0 else None
        except json.JSONDecodeError:
            data = None
        if not data or data.get("@type") != "ScholarlyArticle" or len(data.get("author", [])) != 7:
            errors.append("structured data must be a ScholarlyArticle with the seven authors")
        if not (ROOT / "assets" / "images" / "og-image.jpg").exists():
            errors.append("og-image.jpg missing under design/assets/images")
    elif 'name="robots" content="noindex"' not in text:
        errors.append("review page must be noindex")
    return errors


def stylesheet_syntax(path: Path) -> list[str]:
    """Comment- and string-aware brace scan. A comment that loses its closer
    swallows every rule up to the next `*/` and leaves a stray brace that
    eats the rule after it; browsers report neither (2026-09-27: 67 lines of
    retired CSS hid `.principles-list`)."""
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    depth = 0
    line = 1
    state = "code"
    opened = 0
    i = 0
    while i < len(text):
        char = text[i]
        pair = text[i:i + 2]
        if char == "\n":
            line += 1
        if state == "code":
            if pair == "/*":
                state, opened, i = "comment", line, i + 2
                continue
            if char in "\"'":
                state = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    issues.append(f"stray closing brace at line {line}")
                    depth = 0
        elif state == "comment":
            if pair == "*/":
                if line - opened > 20:
                    issues.append(
                        f"comment of {line - opened} lines at line {opened}; a lost closer?"
                    )
                state, i = "code", i + 2
                continue
        else:
            if char == "\\":
                i += 2
                continue
            if char == state or char == "\n":
                state = "code"
        i += 1
    if state == "comment":
        issues.append(f"unclosed comment opened at line {opened}")
    if depth:
        issues.append(f"{depth} unclosed block(s) at end of file")
    return issues


failures: list[str] = []
for route in ROUTES:
    if not route.exists():
        failures.append(f"{route.relative_to(ROOT)}: missing route")
        continue
    for issue in audit(route):
        failures.append(f"{route.relative_to(ROOT)}: {issue}")

css_text = "\n".join(
    path.read_text(encoding="utf-8") for path in ROOT.rglob("*.css")
)
if "@media (prefers-reduced-motion: reduce)" not in css_text:
    failures.append("styles: missing reduced-motion handling")

for name, needle in (("robots.txt", "Sitemap: https://glowtact.github.io/sitemap.xml"),
                     ("sitemap.xml", "<loc>https://glowtact.github.io/</loc>")):
    path = ROOT.parent / name
    if not path.exists() or needle not in path.read_text(encoding="utf-8"):
        failures.append(f"{name}: missing or without {needle!r}")
for path in sorted(ROOT.rglob("*.css")):
    for issue in stylesheet_syntax(path):
        failures.append(f"{path.relative_to(ROOT)}: {issue}")

js_text = "\n".join(
    path.read_text(encoding="utf-8") for path in ROOT.rglob("*.js")
)
if re.search(r"\bconsole\.(?:log|debug)\s*\(", js_text):
    failures.append("scripts: debug console call found")

# Published numbers must agree with design/data/results.json. Kept as its own
# tool so it can be run alone while iterating on copy; gated here so a stale
# claim cannot reach a commit.
metrics = subprocess.run(
    [sys.executable, str(ROOT / "tools" / "audit_metrics.py")],
    capture_output=True,
    text=True,
)
if metrics.returncode != 0:
    failures.extend(
        line.removeprefix("FAIL ") for line in metrics.stdout.strip().splitlines()
    )

# The source must not reach for generated-page patterns or drift from
# DESIGN.md. Rules DESIGN.md lists as known_open (acknowledged, dated, with a
# reason) print as WARN and do not fail the gate, so a defect that is waiting
# on a decision stays visible in every run without switching the gate off.
slop = subprocess.run(
    [sys.executable, str(ROOT / "tools" / "audit_slop.py"), "--gate"],
    capture_output=True,
    text=True,
)
slop_lines = slop.stdout.strip().splitlines()
failures.extend(
    line.removeprefix("FAIL ") for line in slop_lines if line.startswith("FAIL ")
)
for line in slop_lines:
    if line.startswith("WARN "):
        print(line)
slop_summary = slop_lines[-1] if slop_lines else "slop: not run"

if failures:
    print("\n".join(f"FAIL {item}" for item in failures))
    sys.exit(1)
print(f"PASS: audited {len(ROUTES)} routes, {metrics.stdout.strip()}, {slop_summary}")
