"""Focused screenshots of the concept-03 mechanism across compression."""
import os
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("SHOTS_PORT", "4322"))
OUT = os.environ.get("SHOTS_OUT", os.path.join("C:\\", "tmp", "glowtact-shots"))


def port_free(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


os.makedirs(OUT, exist_ok=True)

server = None
if port_free(PORT):
    server = subprocess.Popen(
        [
            sys.executable, "-m", "http.server", str(PORT),
            "--bind", "127.0.0.1", "--directory", ROOT,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        if not port_free(PORT):
            break
        time.sleep(0.1)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page(
        viewport={"width": 1440, "height": 960}, device_scale_factor=2
    )
    page.goto(f"http://127.0.0.1:{PORT}/concept-03/", wait_until="networkidle")
    page.wait_for_timeout(400)

    page.locator(".signal-hero").screenshot(path=os.path.join(OUT, "hero.png"))

    for view in ("2d", "3d"):
        page.locator(f"#micro-tab-{view}").click()
        page.wait_for_timeout(250)
        for value in (0, 35, 60, 100):
            page.locator("#signal-pressure").fill(str(value))
            page.wait_for_timeout(300)
            page.locator("#mechanism").screenshot(
                path=os.path.join(OUT, f"mech-{view}-{value}.png")
            )

    page.locator("#signal-pressure").fill("100")
    page.wait_for_timeout(300)
    page.locator(".macro-stage").screenshot(path=os.path.join(OUT, "macro-100.png"))

    browser.close()

if server:
    server.terminate()

print("screenshots:", OUT)
