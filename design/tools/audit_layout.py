"""Whole-site design audit: layout, typography, colour, media, across viewports."""
import json
import os
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

import os as _os
ROOT = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
PORT = int(os.environ.get("AUDIT_PORT", "4411"))
OUT = "C:/tmp/glowtact-audit"
ROUTES = ["/", "/concept-01/", "/concept-02/", "/concept-03/"]
VIEWPORTS = {
    "m375": {"width": 375, "height": 812},
    "t768": {"width": 768, "height": 1024},
    "d1280": {"width": 1280, "height": 800},
    "w1920": {"width": 1920, "height": 1080},
}

AUDIT = """
(() => {
  const out = { overflow: [], tiny: [], touch: [], families: {}, sizes: {},
                media: [], contrast: [] };
  const vw = document.documentElement.clientWidth;

  document.querySelectorAll('body *').forEach((el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;

    // Horizontal overflow past the viewport.
    if (r.right > vw + 1 || r.left < -1) {
      out.overflow.push({
        sel: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
             (typeof el.className === 'string' && el.className
               ? '.' + el.className.trim().split(/\\s+/).join('.') : ''),
        left: Math.round(r.left), right: Math.round(r.right)
      });
    }

    const txt = (el.textContent || '').trim();
    const leaf = el.children.length === 0 && txt.length > 0;
    if (leaf) {
      const px = parseFloat(cs.fontSize);
      out.sizes[px.toFixed(1)] = (out.sizes[px.toFixed(1)] || 0) + 1;
      const fam = cs.fontFamily.split(',')[0].replace(/["']/g, '');
      out.families[fam] = (out.families[fam] || 0) + 1;
      if (px < 9) {
        out.tiny.push({ px: +px.toFixed(1), text: txt.slice(0, 40) });
      }
    }

    // Touch target size for interactive elements.
    if (['A', 'BUTTON', 'INPUT', 'SELECT'].includes(el.tagName)) {
      if (r.height > 0 && (r.height < 40 || r.width < 40)) {
        out.touch.push({
          tag: el.tagName, id: el.id || '',
          w: Math.round(r.width), h: Math.round(r.height),
          text: txt.slice(0, 24)
        });
      }
    }
  });

  document.querySelectorAll('video, canvas, svg, img').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0) return;
    out.media.push({
      tag: el.tagName.toLowerCase(),
      id: el.id || el.className?.baseVal || el.className || '',
      w: Math.round(r.width), h: Math.round(r.height),
      ratio: +(r.width / Math.max(r.height, 1)).toFixed(2)
    });
  });

  return out;
})()
"""


def free(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


os.makedirs(OUT, exist_ok=True)
srv = None
if free(PORT):
    srv = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT),
         "--bind", "127.0.0.1", "--directory", ROOT],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        if not free(PORT):
            break
        time.sleep(0.1)

report = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for route in ROUTES:
        for vname, vp in VIEWPORTS.items():
            page = browser.new_page(viewport=vp)
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.goto(f"http://127.0.0.1:{PORT}{route}", wait_until="networkidle")
            page.wait_for_timeout(350)
            data = page.evaluate(AUDIT)
            data["errors"] = errs
            key = f"{route}|{vname}"
            report[key] = data
            page.close()
    browser.close()

if srv:
    srv.terminate()

json.dump(report, open(f"{OUT}/audit.json", "w"), indent=1)

print("=== HORIZONTAL OVERFLOW ===")
for k, v in report.items():
    if v["overflow"]:
        uniq = {o["sel"]: o for o in v["overflow"]}
        print(f"  {k}: {len(uniq)} elements")
        for sel, o in list(uniq.items())[:4]:
            print(f"      {sel[:70]}  L{o['left']} R{o['right']}")

print("\n=== TEXT UNDER 9px ===")
for k, v in report.items():
    if v["tiny"]:
        sizes = sorted({t["px"] for t in v["tiny"]})
        print(f"  {k}: {len(v['tiny'])} nodes at {sizes}")
        for t in v["tiny"][:3]:
            print(f"      {t['px']}px  {t['text']!r}")

print("\n=== TOUCH TARGETS < 40px ===")
for k, v in report.items():
    if v["touch"] and k.split("|")[1] in ("m375", "t768"):
        print(f"  {k}: {len(v['touch'])}")
        for t in v["touch"][:5]:
            print(f"      {t['tag']}#{t['id']} {t['w']}x{t['h']} {t['text']!r}")

print("\n=== DISTINCT FONT SIZES PER PAGE (desktop) ===")
for k, v in report.items():
    if k.endswith("d1280"):
        sizes = sorted(float(s) for s in v["sizes"])
        print(f"  {k}: {len(sizes)} distinct -> {sizes}")
        print(f"      families: {v['families']}")

print("\n=== MEDIA BOXES (m375) ===")
for k, v in report.items():
    if k.endswith("m375"):
        for m in v["media"]:
            if m["w"] > 100:
                print(f"  {k}: {m['tag']}[{str(m['id'])[:26]}] {m['w']}x{m['h']} r={m['ratio']}")

print("\n=== JS ERRORS ===")
for k, v in report.items():
    if v["errors"]:
        print(f"  {k}: {v['errors']}")
