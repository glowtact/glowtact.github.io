"""Generate the published site root from the selected concept.

GitHub Pages serves this repository from `main:/`, but every page lives
under `design/`, so the bare domain used to 404. This writes a root
`index.html` that IS the selected concept, with its relative references
rewritten to resolve from the repository root.

Only `index.html` is generated. The concept's CSS and JS are referenced in
place under the concept's folder (`design/concept-04/`), and images/video in place under
`design/assets/`, so nothing is duplicated and the published page can never
drift from the reviewed one.

Run after `stamp.py` so the published page carries the same build stamp:

    python design/tools/publish.py

`release.py` wires this in automatically.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
# The default publishes concept-04 to the root (since 2026-10-07; concept-03
# before). Any concept can still go to a subsite with --source and --target.
DEFAULT_SOURCE_DIR = "design/concept-04"
DEFAULT_TARGET = "index.html"


def banner(source_dir: str) -> str:
    return (
        "<!--\n"
        "  GENERATED FILE - DO NOT EDIT.\n"
        f"  Produced from {source_dir}/index.html by design/tools/publish.py.\n"
        "  Edit the concept, then re-run the tool (or design/tools/release.py).\n"
        "-->"
    )


def rewrites(source_dir: str, prefix: str) -> list[tuple[str, str]]:
    """Applied in order. The concept's own stylesheet and script are referenced
    where they live; `../assets/` and `../` are re-pointed at `design/`.
    `prefix` leads from the target's directory to the repository root."""
    return [
        ('href="./styles.css"', f'href="{prefix}{source_dir}/styles.css"'),
        ('src="./app.js"', f'src="{prefix}{source_dir}/app.js"'),
        ('"../assets/', f'"{prefix}design/assets/'),
        ('href="../concept-02/"', f'href="{prefix}design/concept-02/"'),
        # The local PDF lives at the repository root (public URL
        # https://glowtact.github.io/GlowTact.pdf); the Paper links go to arXiv
        # 2609.32471 and the research record links this copy.
        ('href="../../GlowTact.pdf"', f'href="{prefix}GlowTact.pdf"'),
        ('href="../"', f'href="{prefix}"'),
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


def check_runtime_paths(source_dir: str) -> list[str]:
    """Reject asset paths built at runtime by the concept's script.

    The rewrites below are textual, so they can only fix references that
    exist in the HTML. A path assembled in JavaScript -- `"../assets/" + name`
    -- survives untouched and resolves against the ROOT page's directory,
    which is one level up from the concept's. That failure is invisible
    locally, where the concept route is the one being served, and shows up
    only on the published site, only after an interaction.
    """
    script = os.path.join(ROOT, source_dir, "app.js")
    if not os.path.exists(script):
        return [f"cannot audit runtime paths: {source_dir}/app.js is missing"]
    text = open(script, encoding="utf-8").read()
    # Strip comments first: prose about this very rule would otherwise match.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    hits = sorted(set(re.findall(r'["\'`](\.\./assets/[^"\'`$]*)', text)))
    return [
        f"runtime asset path in app.js: {hit!r} -- derive the directory from "
        "the markup instead, so the published root resolves it too"
        for hit in hits
    ]


def check(html: str, target: str) -> list[str]:
    """Resolve every local reference from the target's own directory.

    A reference left in its concept-relative form either escapes the site or
    lands on a missing file, so this also catches an unrewritten `../`.
    """
    errors = []
    target_dir = os.path.dirname(target)
    collector = RefCollector()
    collector.feed(html)
    for ref in collector.refs:
        relative = os.path.normpath(os.path.join(target_dir, ref))
        if ref.endswith("/") or ref in {".", ".."}:
            relative = os.path.join(relative, "index.html")
        # A page may link to itself; it is about to be written.
        if os.path.normpath(relative) == os.path.normpath(target):
            continue
        if relative.startswith(".."):
            errors.append(f"reference escapes the site: {ref}")
        elif not os.path.exists(os.path.join(ROOT, relative)):
            errors.append(f"broken reference: {ref}")
    return errors


def publish(source_dir: str, target: str) -> None:
    source_dir = source_dir.strip("/").replace(os.sep, "/")
    target = target.replace(os.sep, "/")
    depth = target.count("/")
    prefix = "../" * depth if depth else "./"

    source = os.path.join(ROOT, source_dir, "index.html")
    html = open(source, encoding="utf-8").read()

    for old, new in rewrites(source_dir, prefix):
        html = html.replace(old, new)
    html = html.replace("<!doctype html>", f"<!doctype html>\n{banner(source_dir)}", 1)

    errors = check(html, target) + check_runtime_paths(source_dir)
    if errors:
        for error in errors:
            print(f"publish: {error}", file=sys.stderr)
        raise SystemExit(f"publish aborted: generated {target} would be broken")

    path = os.path.join(ROOT, target)
    previous = ""
    if os.path.exists(path):
        previous = open(path, encoding="utf-8").read()
    if previous == html:
        print(f"{target}: unchanged")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(html)
    print(f"{target}: published from {source_dir}/index.html")


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a concept to a site path.")
    parser.add_argument("--source", default=DEFAULT_SOURCE_DIR,
                        help="concept directory (default: %(default)s)")
    parser.add_argument("--target", default=DEFAULT_TARGET,
                        help="output path from the repository root (default: %(default)s)")
    args = parser.parse_args()
    publish(args.source, args.target)


if __name__ == "__main__":
    main()
