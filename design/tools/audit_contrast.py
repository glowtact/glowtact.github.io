"""Round 2: contrast + colour-token audit across all routes."""
import os
import socket
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

import os as _os
ROOT = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
PORT = 4431
ROUTES = ["/", "/concept-01/", "/concept-02/", "/concept-03/"]

JS = r"""
(() => {
  const lum = (c) => {
    const f = c.map((v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
  };
  const parse = (s) => {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map((x) => parseFloat(x));
    return { rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1 };
  };
  const over = (fg, bg) => fg.rgb.map((c, i) => c * fg.a + bg[i] * (1 - fg.a));
  const ratio = (a, b) => {
    const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
  };
  const bgOf = (el) => {
    let n = el;
    while (n && n !== document.documentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0.85) return c.rgb;
      n = n.parentElement;
    }
    const r = parse(getComputedStyle(document.body).backgroundColor);
    return r ? r.rgb : [255, 255, 255];
  };

  const fails = [];
  const colours = {};
  document.querySelectorAll('body *').forEach((el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const txt = (el.textContent || '').trim();
    if (!txt || el.children.length) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    const fg = parse(cs.color);
    if (!fg) return;
    const bg = bgOf(el);
    const eff = over(fg, bg);
    const cr = ratio(eff, bg);
    const px = parseFloat(cs.fontSize);
    const bold = parseInt(cs.fontWeight, 10) >= 700;
    const large = px >= 24 || (px >= 18.66 && bold);
    const need = large ? 3.0 : 4.5;
    const key = cs.color;
    colours[key] = (colours[key] || 0) + 1;
    if (cr < need) {
      fails.push({
        cr: +cr.toFixed(2), need, px: +px.toFixed(1),
        color: cs.color,
        text: txt.slice(0, 40),
        sel: el.tagName.toLowerCase() +
             (typeof el.className === 'string' && el.className
               ? '.' + el.className.trim().split(/\s+/)[0] : '')
      });
    }
  });
  return { fails, colours };
})()
"""


def free(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


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

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for route in ROUTES:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"http://127.0.0.1:{PORT}{route}", wait_until="networkidle")
        page.wait_for_timeout(350)
        data = page.evaluate(JS)
        print(f"\n===== {route} =====")
        seen = {}
        for f in data["fails"]:
            k = (f["color"], f["sel"])
            if k in seen:
                continue
            seen[k] = f
        print(f"  contrast failures: {len(data['fails'])} nodes, "
              f"{len(seen)} distinct colour/selector pairs")
        for (col, sel), f in sorted(seen.items(), key=lambda kv: kv[1]["cr"])[:8]:
            print(f"    {f['cr']:5.2f} (need {f['need']}) {f['px']:>5}px "
                  f"{sel:<26} {col:<22} {f['text']!r}")
        print(f"  distinct text colours: {len(data['colours'])}")
        page.close()
    browser.close()

if srv:
    srv.terminate()
