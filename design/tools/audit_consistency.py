import socket, subprocess, sys, time
from playwright.sync_api import sync_playwright
import os as _os
ROOT = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")); PORT=4499
def free(p):
    with socket.socket() as s: return s.connect_ex(("127.0.0.1",p))!=0
srv=None
if free(PORT):
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1","--directory",ROOT],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(50):
        if not free(PORT): break
        time.sleep(0.1)
JS="""(pct) => {
  const p = pct / 100;
  const coup = couplingPressureFor(p);
  const m = microContactModel(coup);
  const chord = contactChordUnits(m.area);
  const s = document.querySelector('.camera-stage').getBoundingClientRect();
  const b = document.querySelector('.camera-contact').getBoundingClientRect();
  const drawnChord = Number(document.querySelector('#macro-coupling-line')
    .dataset.couplingChordWidth);
  const sect = surfaceProfile.filter(h => h >= m.sectionThreshold).length
             / surfaceProfile.length;
  return {
    area: m.area, sect,
    lawChord: chord, drawnChord,
    camFrac: b.width / s.width, expectFrac: chord / CAMERA_VIEW_SPAN,
    readout: document.querySelector('#contact-fraction')?.value
      || document.querySelector('.micro-window-label ~ *')?.textContent || ''
  };
}"""
with sync_playwright() as pw:
    b=pw.chromium.launch()
    pg=b.new_page(viewport={"width":1440,"height":1000})
    pg.goto(f"http://127.0.0.1:{PORT}/concept-03/",wait_until="networkidle")
    print(f"{'press':>6} | {'micro area':>10} {'2D sect':>8} | {'law chord':>9} {'device':>7} | {'camera':>7} {'expect':>7}")
    print("-"*72)
    ok=True
    for pct in (0,25,35,50,60,75,90,100):
        pg.locator("#signal-pressure").fill(str(pct)); pg.wait_for_timeout(280)
        d=pg.evaluate(JS,pct)
        dev_ok = abs(d['drawnChord']-d['lawChord'])<0.5 or d['lawChord']==0
        cam_ok = abs(d['camFrac']-d['expectFrac'])<0.07 or d['lawChord']==0
        sec_ok = abs(d['area']-d['sect'])<0.08
        flag = "" if (dev_ok and cam_ok and sec_ok) else "  <-- MISMATCH"
        print(f"{pct:5d}% | {d['area']*100:9.1f}% {d['sect']*100:7.1f}% | "
              f"{d['lawChord']:9.1f} {d['drawnChord']:7.1f} | "
              f"{d['camFrac']*100:6.1f}% {d['expectFrac']*100:6.1f}%{flag}")
        ok = ok and dev_ok and cam_ok and sec_ok
    print("\nALL CONSISTENT" if ok else "\nMISMATCHES FOUND")
    b.close()
if srv: srv.terminate()
