"""Headless probe of the concept-03 contact model.

Loads the real page and evaluates the model functions in page scope, so the
numbers each view derives can be compared for cross-view consistency.
"""
import os
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PROBE_PORT", "4321"))


def port_free(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


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

SWEEP = """
(() => {
  const rows = [];
  for (let i = 0; i <= 20; i += 1) {
    const p = i / 20;
    const coup = couplingPressureFor(p);
    const m = microContactModel(coup);
    const sect =
      surfaceProfile.filter((h) => h >= m.sectionThreshold).length /
      surfaceProfile.length;
    rows.push({
      p, coup,
      target: targetContactFraction(coup),
      plane: m.fieldThreshold,
      area: m.area,
      coupling: m.coupling,
      intimacy: m.intimacy,
      sect,
      state: stateFor(p, m.area).key,
    });
  }
  return rows;
})()
"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(f"http://127.0.0.1:{PORT}/concept-03/", wait_until="networkidle")
    rows = page.evaluate(SWEEP)
    browser.close()

if server:
    server.terminate()

if errors:
    print("PAGE ERRORS:", *errors, sep="\n  ")

header = (
    f"{'press':>6} {'plane':>6} {'target':>7} {'area':>7} {'sect':>7} "
    f"{'|A-S|':>7} {'camera':>7} {'intim':>7}  state"
)
print(header)
print("-" * len(header))
worst_gap = 0.0
worst_target = 0.0
for r in rows:
    gap = abs(r["area"] - r["sect"])
    worst_gap = max(worst_gap, gap)
    worst_target = max(worst_target, abs(r["area"] - r["target"]))
    print(
        f"{r['p']:6.2f} {r['plane']:6.3f} {r['target'] * 100:6.1f}% "
        f"{r['area'] * 100:6.1f}% {r['sect'] * 100:6.1f}% {gap * 100:6.1f}pp "
        f"{r['coupling'] * 100:6.1f}% {r['intimacy'] * 100:6.1f}%  {r['state']}"
    )


def monotone(key):
    vals = [r[key] for r in rows]
    drops = [
        (rows[i]["p"], vals[i - 1], vals[i])
        for i in range(1, len(vals))
        if vals[i] < vals[i - 1] - 1e-9
    ]
    return drops


last = rows[-1]
print("\n--- full compression ---")
print(f"coupled area     : {last['area'] * 100:.1f}%")
print(f"camera signal    : {last['coupling'] * 100:.1f}%")
print(f"worst area/sect  : {worst_gap * 100:.2f}pp")
print(f"worst area/target: {worst_target * 100:.2f}pp")

for key in ("area", "coupling"):
    drops = monotone(key)
    print(f"{key} monotone   : {'yes' if not drops else 'NO ' + str(drops[:3])}")
