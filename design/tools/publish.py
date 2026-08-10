"""Generate the published site root from the selected concept.

GitHub Pages serves this repository from `main:/`, but every page lives
under `design/`, so the bare domain used to 404. This writes a root
`index.html` that IS the selected concept, with its relative references
rewritten to resolve from the repository root.

Only `index.html` is generated. The concept's CSS and JS are referenced in
place under `design/concept-03/`, and images/video in place under
`design/assets/`, so nothing is duplicated and the published page can never
drift from the reviewed one.

Run after `stamp.py` so the published page carries the same build stamp:

    python design/tools/publish.py

`release.py` wires this in automatically.
"""
from __future__ import annotations

import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
SOURCE = os.path.join("design", "concept-03", "index.html")
TARGET = "index.html"
SOURCE_DIR = os.path.dirname(SOURCE).replace(os.sep, "/")

BANNER = (
    "<!--\n"
    "  GENERATED FILE - DO NOT EDIT.\n"
    f"  Produced from {SOURCE_DIR}/index.html by design/tools/publish.py.\n"
    "  Edit the concept, then re-run the tool (or design/tools/release.py).\n"
    "-->"
)

# Applied in order. The concept's own stylesheet and script are referenced
# where they live; `../assets/` and `../` are re-pointed at `design/`.
REWRITES = [
    ('href="./styles.css"', f'href="./{SOURCE_DIR}/styles.css"'),
    ('src="./app.js"', f'src="./{SOURCE_DIR}/app.js"'),
    ('"../assets/', '"./design/assets/'),
    ('href="../concept-02/"', 'href="./design/concept-02/"'),
    ('href="../"', 'href="./"'),
]


class RefCollector(HTMLParser):
    """Collect every local href/src so the output can be link-checked."""

    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        for key in ("href", "src"):
            value = values.get(key)
            if not value or value.startswith(
                ("http:", "https:", "mailto:", "#", "data:")
            ):
                continue
            self.refs.append(value.split("?", 1)[0].split("#", 1)[0])


def check(html: str) -> list[str]:
    errors = []
    if "../" in html:
        for match in set(re.findall(r'["\'](\.\./[^"\']*)', html)):
            errors.append(f"unrewritten parent reference: {match}")

    collector = RefCollector()
    collector.feed(html)
    for ref in collector.refs:
        relative = ref.lstrip("./")
        if ref.endswith("/"):
            relative = f"{relative}index.html"
        # The root page links to itself; it is about to be written.
        if relative == TARGET:
            continue
        if not os.path.exists(os.path.join(ROOT, relative.replace("/", os.sep))):
            errors.append(f"broken reference: {ref}")
    return errors


def main() -> None:
    source = os.path.join(ROOT, SOURCE)
    html = open(source, encoding="utf-8").read()

    for old, new in REWRITES:
        html = html.replace(old, new)
    html = html.replace("<!doctype html>", f"<!doctype html>\n{BANNER}", 1)

    errors = check(html)
    if errors:
        for error in errors:
            print(f"publish: {error}", file=sys.stderr)
        raise SystemExit("publish aborted: generated root would be broken")

    target = os.path.join(ROOT, TARGET)
    previous = ""
    if os.path.exists(target):
        previous = open(target, encoding="utf-8").read()
    if previous == html:
        print(f"{TARGET}: unchanged")
        return

    open(target, "w", encoding="utf-8").write(html)
    print(f"{TARGET}: published from {SOURCE_DIR}/index.html")


if __name__ == "__main__":
    main()
