"""Write the current commit stamp into every page footer.

Solves the "which version am I looking at" problem: reviews kept flagging
already-fixed issues because the browser was serving a cached page. Run
before committing (the stamp then names the PARENT commit's successor; the
date alone is usually enough to disambiguate) or wire into a release step.
"""
import os
import re
import subprocess
from datetime import date

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PAGES = [
    "index.html",
    "concept-01/index.html",
    "concept-02/index.html",
    "concept-03/index.html",
]

short = subprocess.run(
    ["git", "rev-parse", "--short", "HEAD"],
    capture_output=True, text=True, cwd=ROOT,
).stdout.strip() or "dev"
stamp = f"{date.today().isoformat()} · {short}"

for rel in PAGES:
    path = os.path.join(ROOT, rel)
    src = open(path, encoding="utf-8").read()
    marker = f'<span class="build-stamp" aria-hidden="true">{stamp}</span>'
    # Strip any existing stamp first, then insert before the LAST </footer>.
    # Matching the first one once planted the stamp inside concept-03's
    # in-panel readout footer instead of the page footer.
    src = re.sub(
        r'\s*<span class="build-stamp" aria-hidden="true">[^<]*</span>',
        "", src,
    )
    anchor = src.rfind("</footer>")
    if anchor == -1:
        raise SystemExit(f"{rel}: no </footer> found")
    out = src[:anchor] + f"  {marker}\n    " + src[anchor:]
    open(path, "w", encoding="utf-8").write(out)
    print(f"{rel}: {stamp}")
