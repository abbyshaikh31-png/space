import json, os, re, time, random, hashlib
import urllib.parse, urllib.request
from datetime import datetime, timezone

LOG = "research_log.json"
UA = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
 "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if os.path.exists(LOG):
        try:
            d = json.load(open(LOG))
            if isinstance(d, list):
                return d
            if isinstance(d, dict):
                return d.get("results", []) or []
        except Exception:
            pass
    return []

def save(items):
    tmp = LOG + ".tmp"
    with open(tmp, "w") as f:
        json.dump(items, f, indent=1)
    os.replace(tmp, LOG)

def fetch(url, timeout=14):
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(UA),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "ignore")
        return r.getcode(), body, round(time.time() - t0, 2)

def links(html, base):
    out = []
    for m in re.finditer(r'href="(https?://[^"#]+)"', html):
        u = m.group(1)
        dom = urllib.parse.urlparse(base).netloc
        if urllib.parse.urlparse(u).netloc == dom:
            continue
        if any(x in u for x in ["google.com/search", "bing.com/", "duckduckgo.com", "yandex", "youtube.com", "facebook.com", "twitter.com", "instagram.com", "linkedin.com", "reddit.com/r/", "pinterest", "amazon.", "ebay."]):
            continue
        out.append(u)
    seen, res = set(), []
    for u in out:
        k = u.split("#")[0].rstrip("/")
        if k not in seen:
            seen.add(k)
            res.append(u)
    return res