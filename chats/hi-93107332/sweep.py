import json, re, ssl, sys, time, urllib.parse, urllib.request, hashlib, os, threading
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
LOCK = threading.Lock()
LOG = "research_log.jsonl"
os.makedirs("sources", exist_ok=True)

BLACK = ("startpage.com","bing.com","microsoft.com","searx","duckduckgo","mojeek","marginalia",
         "ecosia","google.com/search","youtube.com/redirect","go.microsoft")

def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
          "Accept-Language": "en-US,en;q=0.9", "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read().decode("utf-8", "ignore")

def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()

def bing(q):
    st, html = fetch("https://www.bing.com/search?q=" + urllib.parse.quote_plus(q) + "&count=25&setlang=en")
    out = []
    for m in re.finditer(r'<h2><a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a></h2>', html, re.S):
        out.append((clean(m.group(2)), m.group(1)))
    return st, out

def startpage(q):
    st, html = fetch("https://www.startpage.com/sp/search?query=" + urllib.parse.quote_plus(q))
    out = []
    for m in re.finditer(r'<a[^>]+class="[^"]*result-link[^"]*"[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S):
        out.append((clean(m.group(2)), m.group(1)))
    if not out:
        for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S):
            u = m.group(1)
            if not any(b in u for b in BLACK):
                out.append((clean(m.group(2)), u))
    return st, out

def norm(u):
    p = urllib.parse.urlsplit(u)
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith("utm") and k.lower() not in ("ref","source","fbclid")]
    path = p.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), path, urllib.parse.urlencode(q), ""))

BASES = ["gemini 4 carbon", "gemini-4-carbon", "Gemini 4 Carbon model", "Gemini 4 Carbon API",
         "Gemini 4 Carbon Google", "Gemini 4 Carbon developer", "Gemini 4 Carbon pricing",
         "Gemini 4 Carbon free", "Gemini 4 Carbon vs Claude", "Gemini 4 Carbon Argon"]
MODS = ["pricing per million tokens", "free tier", "free access", "AI Studio", "OpenRouter",
        "Puter.js", "rate limits", "release date", "benchmark", "documentation"]
QUERIES = []
for b in BASES:
    for m in MODS:
        q = (b + " " + m).replace('"', "").replace("'", "")
        if q not in QUERIES:
            QUERIES.append(q)
print("queries:", len(QUERIES), flush=True)