#!/usr/bin/env python3
"""Haalt server-side (vanaf de box) per kantoor favicon/apple-touch-icon/og:image op, verkleint naar 64px PNG
en schrijft data-URI's naar private/logos.json (gitignored). Wordt in de versleutelde payload opgenomen."""
import json,re,io,base64,os,sys,urllib.request,urllib.parse,shutil,subprocess
from PIL import Image
OUT='private/logos.json'; UA={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36'}
cache=json.load(open(OUT)) if os.path.exists(OUT) else {}
def get(u,n=2_000_000):
    r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=12); return r.read(n),r.geturl(),r.headers.get('Content-Type','')
def dom(w):
    if not w or ' ' in w.strip() or '.' not in w: return None
    if '://' not in w: w='https://'+w
    h=urllib.parse.urlparse(w).hostname or ''; return h.lower().removeprefix('www.') or None
def to_png(b,ct,u):
    if b'<svg' in b[:500] or 'svg' in ct or u.endswith('.svg'):
        if not shutil.which('rsvg-convert'): return None
        b=subprocess.run(['rsvg-convert','-w','128','-h','128','--keep-aspect-ratio'],input=b,capture_output=True).stdout
    im=Image.open(io.BytesIO(b))
    if getattr(im,'n_frames',1)>1 and im.format=='ICO': im.size=max(im.info.get('sizes',[im.size]))
    im=im.convert('RGBA'); 
    if im.width<16: return None
    im.thumbnail((64,64),Image.LANCZOS); c=Image.new('RGBA',(64,64),(0,0,0,0)); c.paste(im,((64-im.width)//2,(64-im.height)//2))
    o=io.BytesIO(); c.save(o,'PNG',optimize=True); return 'data:image/png;base64,'+base64.b64encode(o.getvalue()).decode()
def logo(d):
    base='https://'+d+'/'; cands=[]
    try:
        html,fin,_=get(base,600_000); html=html.decode('utf-8','ignore')
        for tag in re.findall(r'<link[^>]+>',html,re.I):
            rel=(re.search(r'rel=["\']([^"\']+)',tag,re.I) or [None,''])[1].lower(); href=re.search(r'href=["\']([^"\']+)',tag,re.I)
            if href and 'icon' in rel:
                sz=re.search(r'sizes=["\'](\d+)',tag); score=(3 if 'apple' in rel else 1)+(int(sz[1])/100 if sz else 0)
                cands.append((score,urllib.parse.urljoin(fin,href[1])))
        m=re.search(r'<meta[^>]+property=["\']og:logo["\'][^>]+content=["\']([^"\']+)',html,re.I)
        if m: cands.append((2.5,urllib.parse.urljoin(fin,m[1])))
    except Exception as e: print('  html fout',d,e,file=sys.stderr)
    cands.sort(reverse=True); cands+= [(0,base+'apple-touch-icon.png'),(0,base+'favicon.ico')]
    for _,u in cands:
        try:
            b,fu,ct=get(u); p=to_png(b,ct,fu)
            if p: return p
        except Exception: pass
    return None
rows=json.load(open('private/prospects.json')); rows=rows.get('results',rows) if isinstance(rows,dict) else rows
for r in rows:
    d=dom(r.get('Website'))
    if not d or d in cache: continue
    cache[d]=logo(d); print(('✓ ' if cache[d] else '– ')+d)
json.dump(cache,open(OUT,'w'))
