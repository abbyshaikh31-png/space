import json, os, re, sys, time, random, urllib.parse
import requests
from datetime import datetime, timezone

ROOT = os.getcwd()
SRC = os.path.join(ROOT, "sources")
os.makedirs(SRC, exist_ok=True)
LOG = os.path.join(SRC, "research_log.json")
QFILE = os.path.join(SRC, "queries.txt")

UAS = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
 "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

ENGINES = {
 "startpage": "https://www.startpage.com/sp/search?query={q}",
 "bing": "https://www.bing.com/search?q={q}&count=20",
 "marginalia": "https://search.marginalia.nu/search?query={q}",
}

JUNK = ("startpage.com","bing.com","microsoft.com","marginalia.nu","duckduckgo.com",
        "google.com/search","w3.org","schema.org","creativecommons.org","mozilla.org")

def load():
    if not os.path.exists(LOG):
        return []
    try:
        d = json.load(open(LOG, "r", encoding="utf-8"))
    except Exception:
        return []
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        r = d.get("results")
        return r if isinstance(r, list) else []
    return []

def save(entries):
    tmp = LOG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=1, ensure_ascii=False)
    os.replace(tmp, LOG)

def extract_urls(html):
    out, seen = [], set()
    for m in re.finditer(r'href="(https?://[^"\\]+)"', html):
        u = m.group(1).replace("&amp;", "&")
        host = urllib.parse.urlparse(u).netloc.lower()
        if any(j in host for j in JUNK):
            continue
        base = u.split("#")[0]
        if base in seen:
            continue
        seen.add(base)
        out.append(base)
        if len(out) >= 20:
            break
    return out

def fetch(engine, query, timeout=12):
    url = ENGINES[engine].format(q=urllib.parse.quote_plus(query))
    hdr = {"User-Agent": random.choice(UAS),
           "Accept": "text/html,application/xhtml+xml",
           "Accept-Language": "en-US,en;q=0.9"}
    t0 = time.time()
    try:
        r = requests.get(url, headers=hdr, timeout=timeout)
        dt = round(time.time() - t0, 2)
        return r.status_code, dt, extract_urls(r.text)
    except Exception as e:
        return "ERR", round(time.time() - t0, 2), [str(e)[:120]]