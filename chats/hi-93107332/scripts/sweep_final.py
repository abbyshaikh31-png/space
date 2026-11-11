import json,os,re,itertools,threading
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import requests

UA=["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
"Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0"]

SKIP=re.compile(r'(bing|microsoft|startpage|duckduckgo|mojeek|marginalia|brave|ecosia|searx|google\.|gstatic|youtube|facebook|twitter|x\.com|pinterest|instagram|linkedin|wikipedia\.org|youtube\.com|amazon|reddit)',re.I)

def ts(): return datetime.now(timezone.utc).isoformat()

def urls_from(html,host):
    out=[]
    for m in re.finditer(r'href="(https?://[^"]+)"',html):
        u=m.group(1).replace('&amp;','&')
        mm=re.match(r'https?://([^/]+)',u)
        if not mm: continue
        h=mm.group(1).lower()
        if host in h: continue
        if SKIP.search(h): continue
        if u not in out: out.append(u)
    return out[:15]

def fetch(t):
    key,engine,i=t
    cfg={'bing':("https://www.bing.com/search?q=%s&count=20","bing.com"),
         'startpage':("https://www.startpage.com/sp/search?query=%s","startpage.com"),
         'marginalia':("https://search.marginalia.nu/search?query=%s","marginalia.nu"),
         'searx_be':("https://searx.be/search?q=%s&format=json","searx.be")}[engine]
    url=cfg[0]%requests.utils.quote(key)
    rec={"id":i,"query":key,"engine":engine,"timestamp":ts(),"http_status":None,
         "n_results":0,"urls":[],"error":None}
    try:
        r=requests.get(url,headers={"User-Agent":UA[i%len(UA)],"Accept-Language":"en-US,en;q=0.9"},
                       timeout=12,allow_redirects=True)
        rec["http_status"]=r.status_code
        if engine=='searx_be' and r.text.strip().startswith('{'):
            j=r.json(); rec["urls"]=[x.get("url") for x in j.get("results",[])[:15] if x.get("url")]
        if not rec["urls"]:
            rec["urls"]=urls_from(r.text,cfg[1])
        rec["n_results"]=len(rec["urls"])
    except Exception as e:
        rec["error"]=str(e)[:180]
    return rec
]<]minimax[>[