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
    if 'class="build-stamp"' in src:
        out, n = re.subn(
            r'<span class="build-stamp" aria-hidden="true">[^<]*</span>',
            marker, src,
        )
    else:
        out, n = re.subn(r"(</footer>)", f"  {marker}\n    \\1", src, count=1)
    if n != 1:
        raise SystemExit(f"{rel}: expected exactly one stamp point, found {n}")
    open(path, "w", encoding="utf-8").write(out)
    print(f"{rel}: {stamp}")
