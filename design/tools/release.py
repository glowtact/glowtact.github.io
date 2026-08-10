"""One-shot release: stamp -> verify -> full browser checks -> commit -> push.

Usage (from the repo root):

    python design/tools/release.py "commit subject line"
    python design/tools/release.py "subject" --body path/to/body.txt
    python design/tools/release.py "subject" --skip-checks   # emergencies only

The stamp is refreshed FIRST so the committed pages carry the parent
commit's id plus today's date (enough to disambiguate deployments), then
the static audit and every browser-check mode must pass before anything
is committed. A failing check aborts with the tool's own output; nothing
is left staged.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
SERVER_URL = os.environ.get("GLOWTACT_BASE_URL", "http://127.0.0.1:4173")
TRAILER = "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"


def run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    merged = {**os.environ, **(env or {})}
    result = subprocess.run(cmd, cwd=ROOT, env=merged)
    if result.returncode != 0:
        raise SystemExit(f"release aborted: {' '.join(cmd)} failed")


def ensure_server() -> subprocess.Popen | None:
    """Start a design server if nothing answers on the configured URL."""
    import urllib.request

    try:
        urllib.request.urlopen(SERVER_URL, timeout=2)
        return None
    except OSError:
        proc = subprocess.Popen(
            [sys.executable, "-m", "http.server",
             SERVER_URL.rsplit(":", 1)[-1], "--bind", "127.0.0.1",
             "--directory", os.path.join(ROOT, "design")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        import time

        time.sleep(1.5)
        return proc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", help="commit subject line")
    parser.add_argument("--body", help="file with the commit body")
    parser.add_argument("--skip-checks", action="store_true")
    args = parser.parse_args()

    run([sys.executable, os.path.join("design", "tools", "stamp.py")])
    run([sys.executable, os.path.join("design", "tools", "publish.py")])

    if not args.skip_checks:
        run([sys.executable, os.path.join("design", "verify.py")])
        server = ensure_server()
        try:
            run(
                [sys.executable, os.path.join("design", "browser_check.py")],
                env={"GLOWTACT_CHECK_MODE": "all",
                     "GLOWTACT_BASE_URL": SERVER_URL},
            )
        finally:
            if server is not None:
                server.terminate()

    run(["git", "add", "design", "index.html"])
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=ROOT
    ).returncode
    if staged == 0:
        print("release: nothing staged; skipping commit")
        return

    message = args.subject
    if args.body:
        message += "\n\n" + open(args.body, encoding="utf-8").read().strip()
    message += "\n\n" + TRAILER
    run(["git", "commit", "-m", message])

    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, cwd=ROOT,
    ).stdout.strip()
    run([sys.executable, os.path.join("design", "tools", "stamp.py")])
    run([sys.executable, os.path.join("design", "tools", "publish.py")])
    run(["git", "add", "design", "index.html"])
    run(["git", "commit", "-m", f"chore(design): stamp {head}\n\n{TRAILER}"])
    run(["git", "push", "origin", "main"])
    print(f"release: pushed {head} (+stamp)")


if __name__ == "__main__":
    main()
