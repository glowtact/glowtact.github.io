"""Assert every marked number in the markup matches design/data/results.json.

One claim, one source. A number edited in the page without editing the data
file -- or the reverse -- fails the build instead of shipping a stale claim.

Mark a claim by putting the dotted path on the element that holds the value:

    <strong data-metric="force.macro_mae_glowtact">0.106</strong> N

A number shown in another unit names the factor, and the page must equal the
data value times that factor (0.12 N shown in mN):

    <strong data-metric="sensitivity.min_detectable_force_median_glowtact"
            data-metric-scale="1000">120</strong> mN

The unit printed right after the number (inside the element or just after
it) must be the data's unit, re-prefixed by the scale: a factor of 1000 turns
N into mN. So "0.12 mN" with the scale forgotten fails, and so does a scale of
0 or -1000, which would match any value.

Run directly, or via design/verify.py which gates on it.
"""
from __future__ import annotations

import json
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "design" / "data" / "results.json"
ROUTES = [
    ROOT / "design" / "concept-03" / "index.html",
    ROOT / "design" / "concept-04" / "index.html",
]
NUMERIC = re.compile(r"-?\d+(?:\.\d+)?")
# SI prefixes a scaled metric may move between, by power of ten.
PREFIXES = {"k": 3, "": 0, "m": -3, "\u00b5": -6}
SI_BASES = {"N", "g", "m", "s"}


def scaled_unit(unit: str, factor: float) -> str | None:
    """The unit a value carries after multiplying by `factor` (N x 1000 -> mN).

    None when the factor is not a power of ten or the unit has no SI prefix
    ladder (a percentage cannot be shown "x 1000").
    """
    if factor == 1:
        return unit
    shift = math.log10(factor)
    if abs(shift - round(shift)) > 1e-9:
        return None
    prefix, base = "", unit
    for candidate in ("k", "m", "\u00b5"):
        if unit.startswith(candidate) and unit[len(candidate):] in SI_BASES:
            prefix, base = candidate, unit[len(candidate):]
            break
    if base not in SI_BASES:
        return None
    target = PREFIXES[prefix] - round(shift)
    for candidate, exponent in PREFIXES.items():
        if exponent == target:
            return candidate + base
    return None


class MetricCollector(HTMLParser):
    """Collect data-metric elements and embedded application/json blocks.

    Data a script reads out of the page is a published number too. Checking
    only the visible spans would leave a chart free to draw one value while
    the table beside it printed another.
    """

    def __init__(self) -> None:
        super().__init__()
        # (path, text inside the element, scale, text right after it)
        self.found: list[tuple[str, str, str | None, str]] = []
        self._after: int | None = None
        self.blocks: list[tuple[str, str]] = []
        self._path: str | None = None
        self._scale: str | None = None
        self._text: list[str] = []
        self._depth = 0
        self._json_id: str | None = None
        self._json_text: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if self._after is not None:
            # A tag before any text: nothing follows the number directly.
            self._close_after("")
        if tag == "script" and values.get("type") == "application/json":
            self._json_id = values.get("id") or "<unnamed>"
            self._json_text = []
        path = values.get("data-metric")
        if path and self._path is None:
            self._path, self._text, self._depth = path, [], 0
            self._scale = values.get("data-metric-scale")
        elif self._path is not None:
            self._depth += 1

    def _close_after(self, text: str) -> None:
        index = self._after
        if index is None:
            return
        path, inside, scale, _ = self.found[index]
        self.found[index] = (path, inside, scale, text)
        self._after = None

    def handle_data(self, data: str) -> None:
        if self._after is not None and self._path is None:
            self._close_after(data)
        if self._json_id is not None:
            self._json_text.append(data)
        if self._path is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_id is not None:
            self.blocks.append((self._json_id, "".join(self._json_text)))
            self._json_id = None
        if self._path is None:
            return
        if self._depth:
            self._depth -= 1
            return
        self.found.append((self._path, "".join(self._text).strip(), self._scale, ""))
        self._after = len(self.found) - 1
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

    def walk_block(node, where: str) -> None:
        """Any {"value": x, "metric": "a.b"} pair anywhere in the JSON."""
        nonlocal total
        if isinstance(node, dict):
            if "metric" in node and "value" in node:
                total += 1
                leaf = resolve(data, node["metric"])
                if leaf is None:
                    failures.append(f"{where}: unknown metric path {node['metric']}")
                elif normalize(str(node["value"])) != normalize(str(leaf["value"])):
                    failures.append(
                        f"{where}: {node['metric']} embeds {node['value']}, "
                        f"data says {leaf['value']}"
                    )
            for value in node.values():
                walk_block(value, where)
        elif isinstance(node, list):
            for value in node:
                walk_block(value, where)

    for route in ROUTES:
        collector = MetricCollector()
        collector.feed(route.read_text(encoding="utf-8"))
        total += len(collector.found)
        for block_id, raw in collector.blocks:
            try:
                walk_block(json.loads(raw), f"{route.name}#{block_id}")
            except json.JSONDecodeError as error:
                failures.append(f"{route.name}#{block_id}: invalid JSON ({error})")
        for path, text, scale, after in collector.found:
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
            expected = leaf["value"]
            unit = leaf.get("unit", "")
            factor = 1.0
            if scale is not None:
                try:
                    factor = float(scale)
                except ValueError:
                    failures.append(f"{route.name}: {path} has a non-numeric scale {scale!r}")
                    continue
                if not math.isfinite(factor) or factor <= 0:
                    failures.append(f"{route.name}: {path} scale {scale!r} must be a positive finite number")
                    continue
                # Round away float noise: 0.12 * 1000 is 120.00000000000001.
                expected = round(float(expected) * factor, 9)
            if unit:
                want = scaled_unit(unit, factor)
                if want is None:
                    failures.append(
                        f"{route.name}: {path} scale {scale!r} does not map {unit!r} to an SI prefix"
                    )
                    continue
                shown_unit = (text[shown.end():].strip() or after).strip(" \u00a0\t\r\n(")
                if not re.match(re.escape(want) + r"(?![A-Za-z\u00b5])", shown_unit):
                    failures.append(
                        f"{route.name}: {path} is in {want!r} but the page prints "
                        f"{(shown_unit.split() or [''])[0]!r} after {shown.group(0)}"
                    )
                    continue
            if normalize(shown.group(0)) != normalize(str(expected)):
                failures.append(
                    f"{route.name}: {path} shows {shown.group(0)}, "
                    f"data says {leaf['value']}"
                    + (f" x {scale} = {expected:g}" if scale is not None else "")
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
