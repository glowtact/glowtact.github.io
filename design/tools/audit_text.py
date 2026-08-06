import socket, subprocess, sys, time
from playwright.sync_api import sync_playwright
import os as _os
ROOT = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")); PORT=4507
def free(p):
    with socket.socket() as s: return s.connect_ex(("127.0.0.1",p))!=0
srv=None
if free(PORT):
    srv=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1","--directory",ROOT],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(50):
        if not free(PORT): break
        time.sleep(0.1)
JS="""() => {
  const out=[];
  document.querySelectorAll('section, header.instrument-header, footer').forEach((sec)=>{
    const id=sec.id||sec.getAttribute('aria-labelledby')||sec.className.split(' ')[0]||sec.tagName;
    const text=(sec.innerText||'').trim();
    const words=text.split(/\s+/).filter(Boolean).length;
    const paras=[...sec.querySelectorAll('p')].map(p=>{
      const t=(p.innerText||'').trim();
      return {words:t.split(/\s+/).filter(Boolean).length, text:t.slice(0,90)};
    }).filter(p=>p.words>18);
    out.push({id, words, longParas:paras});
  });
  return out;
}"""
with sync_playwright() as pw:
    b=pw.chromium.launch()
    for route in ["/","/concept-01/","/concept-02/","/concept-03/"]:
        pg=b.new_page(viewport={"width":1440,"height":1000})
        pg.goto(f"http://127.0.0.1:{PORT}{route}",wait_until="networkidle")
        d=pg.evaluate(JS)
        total=sum(x['words'] for x in d)
        print(f"\n===== {route}  total ~{total} words =====")
        for x in d:
            flag=" **" if x['words']>150 else ""
            print(f"  {x['id'][:36]:38s} {x['words']:>4}w{flag}")
            for p in x['longParas'][:3]:
                print(f"      {p['words']:>3}w  {p['text']!r}")
        pg.close()
    b.close()
if srv: srv.terminate()
