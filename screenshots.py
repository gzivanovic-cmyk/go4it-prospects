#!/usr/bin/env python3
"""Maakt server-side (op de box) met headless Chromium een screenshot (1280x800) van elke prospect-website,
comprimeert naar WebP (~60KB) en schrijft data-URI's naar private/shots.json (gitignored). Cache: ververst na 14 dagen.
Komt alleen versleuteld in de payload terecht, nooit als los bestand in de repo."""
import json,os,io,base64,time,urllib.parse,sys
from PIL import Image
from playwright.sync_api import sync_playwright
OUT='private/shots.json'; MAXAGE=14*86400
cache=json.load(open(OUT)) if os.path.exists(OUT) else {}
rows=json.load(open('private/prospects.json')); rows=rows.get('results',rows) if isinstance(rows,dict) else rows
def dom(w):
    if not w or ' ' in w.strip() or '.' not in w: return None
    if '://' not in w: w='https://'+w
    return (urllib.parse.urlparse(w).hostname or '').lower().removeprefix('www.') or None
todo={}
for r in rows:
    w=r.get('Website'); d=dom(w)
    if not d: continue
    c=cache.get(d)
    if c and time.time()-c.get('t',0)<MAXAGE: continue
    todo[d]=w if '://' in w else 'https://'+w
print(f'{len(todo)} screenshots te maken')
def webp(png):
    im=Image.open(io.BytesIO(png)).convert('RGB')
    for q in (70,60,50,40,30):
        o=io.BytesIO(); im.save(o,'WEBP',quality=q,method=6)
        if o.tell()<=65000: break
    return 'data:image/webp;base64,'+base64.b64encode(o.getvalue()).decode()
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--disable-dev-shm-usage'])
    ctx=b.new_context(viewport={'width':1280,'height':800},user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',ignore_https_errors=True,locale='nl-NL')
    for d,u in todo.items():
        pg=ctx.new_page()
        try:
            resp=pg.goto(u,timeout=25000,wait_until='domcontentloaded'); pg.wait_for_timeout(2500)
            ok=resp is not None and resp.status<400
            cache[d]={'t':time.time(),'img':webp(pg.screenshot()),'final':pg.url,'https':pg.url.startswith('https://'),'status':resp.status if resp else None,'ok':ok}
            print('✓',d,resp.status if resp else '-')
        except Exception as e:
            cache[d]={'t':time.time(),'img':None,'ok':False,'err':str(e)[:120]}; print('–',d,str(e)[:80],file=sys.stderr)
        finally: pg.close()
        json.dump(cache,open(OUT,'w'))
    b.close()
json.dump(cache,open(OUT,'w'))
