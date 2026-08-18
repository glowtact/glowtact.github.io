"""Assert every marked number in the markup matches design/data/results.json.

One claim, one source. A number edited in the page without editing the data
file -- or the reverse -- fails the build instead of shipping a stale claim.

Mark a claim by putting the dotted path on the element that holds the value:

    <strong data-metric="force.macro_mae_glowtact">0.106</strong> N

Run directly, or via design/verify.py which gates on it.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "design" / "data" / "results.json"
ROUTES = [ROOT / "design" / "concept-03" / "index.html"]
NUMERIC = re.compile(r"-?\d+(?:\.\d+)?")


class MetricCollector(HTMLParser):
    """Collect (path, rendered text) for every element carrying data-metric."""

    def __init__(self) -> None:
        super().__init__()
        self.found: list[tuple[str, str]] = []
        self._path: str | None = None
        self._text: list[str] = []
        self._depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        path = dict(attrs).get("data-metric")
        if path and self._path is None:
            self._path, self._text, self._depth = path, [], 0
        elif self._path is not None:
            self._depth += 1

    def handle_data(self, data: str) -> None:
        if self._path is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._path is None:
            return
        if self._depth:
            self._depth -= 1
            return
        self.found.append((self._path, "".join(self._text).strip()))
        self._path = None


def resolve(data: dict, path: str):
    node = data
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def normalize(number: str) -> str:
    """0.120 and 0.12 are the same claim; 20.0 and 20 are not different data."""
    return f"{float(number):g}"


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    failures: list[str] = []
    total = 0

    for route in ROUTES:
        collector = MetricCollector()
        collector.feed(route.read_text(encoding="utf-8"))
        total += len(collector.found)
        for path, text in collector.found:
            leaf = resolve(data, path)
            if leaf is None:
                failures.append(f"{route.name}: unknown metric path {path}")
                continue
            if not isinstance(leaf, dict) or "value" not in leaf:
                failures.append(f"{route.name}: {path} is not a metric leaf")
                continue
            shown = NUMERIC.search(text)
            if not shown:
                failures.append(f"{route.name}: {path} renders no number ({text!r})")
                continue
            if normalize(shown.group(0)) != normalize(str(leaf["value"])):
                failures.append(
                    f"{route.name}: {path} shows {shown.group(0)}, "
                    f"data says {leaf['value']}"
                )

    # Guard the guard: a markup change must never let this pass vacuously.
    if total == 0:
        failures.append(
            "no data-metric spans found; the checker matched nothing and "
            "would have passed on any content"
        )

    if failures:
        print("\n".join(f"FAIL metrics: {item}" for item in failures))
        return 1
    print(f"PASS: {total} metrics match {DATA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
