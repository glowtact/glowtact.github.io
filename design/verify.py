from html.parser import HTMLParser
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent
ROUTES = [
    ROOT / "index.html",
    ROOT / "concept-01" / "index.html",
    ROOT / "concept-02" / "index.html",
    ROOT / "concept-03" / "index.html",
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
    return errors


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

js_text = "\n".join(
    path.read_text(encoding="utf-8") for path in ROOT.rglob("*.js")
)
if re.search(r"\bconsole\.(?:log|debug)\s*\(", js_text):
    failures.append("scripts: debug console call found")

if failures:
    print("\n".join(f"FAIL {item}" for item in failures))
    sys.exit(1)
print(f"PASS: audited {len(ROUTES)} routes")
