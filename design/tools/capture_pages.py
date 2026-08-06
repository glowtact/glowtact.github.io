import os, socket, subprocess, sys, time
from playwright.sync_api import sync_playwright
import os as _os
ROOT = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
PORT = int(os.environ.get("P","4421")); OUT = os.environ.get("O","C:/tmp/gt-r1")
def free(p):
    with socket.socket() as s: return s.connect_ex(("127.0.0.1", p)) != 0
os.makedirs(OUT, exist_ok=True)
srv = None
if free(PORT):
    srv = subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1","--directory",ROOT],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        if not free(PORT): break
        time.sleep(0.1)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for route, name in [("/","root"),("/concept-01/","c01"),("/concept-02/","c02"),("/concept-03/","c03")]:
        for vn, vp in [("m375",{"width":375,"height":812}),("d1280",{"width":1280,"height":800})]:
            pg = b.new_page(viewport=vp)
            pg.goto(f"http://127.0.0.1:{PORT}{route}", wait_until="networkidle")
            pg.wait_for_timeout(400)
            pg.screenshot(path=f"{OUT}/{name}-{vn}.png", full_page=True)
            pg.close()
    b.close()
if srv: srv.terminate()
print("saved", OUT)
