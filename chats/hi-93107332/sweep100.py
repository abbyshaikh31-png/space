import json, re, time, threading, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
LOG = []
LOCK = threading.Lock()

TOPICS = [
 "Gemini 4 Carbon free access",
 "Gemini 4 Carbon API pricing per million tokens",
 "Gemini 4 Carbon model card",
 "Gemini 4 Carbon vs Claude Opus 5.5 benchmarks",
 "Gemini 4 Carbon OpenRouter",
 "Gemini 4 Carbon Google AI Studio",
 "Gemini 4 Carbon Gemini for business",
 "Google AI Ultra Gemini 4 Carbon",
 "Gemini 4 Argon vs Carbon",
 "Gemini CLI Antigravity CLI free tier",
 "Puter.js user pays model Gemini free allowance",
 "OpenRouter free models free tier limits 2026",
 "Gemini API free tier rate limits 2026",
 "Vertex AI Gemini free trial credits",
 "Atlas Cloud Gemini 4 Carbon free",
]
MODS = [
 "",
 " how to get free access 2026",
 " free tier limits quota",
 " tutorial step by step",
 " alternative platforms",
]

def eng_bing(q, n=1):
    url = "https://www.bing.com/search?q=" + urllib.parse.quote(q) + ("&first=%d" % (1 + (n-1)*10) if n > 1 else "")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
    links = re.findall(r'href="(https?://[^"]+)"', html)
    out = []
    for l in links:
        if any(b in l for b in ("bing.com", "microsoft.com", "msn.com", "go.microsoft", "msn.cn")):
            continue
        out.append(l)
    return out

def eng_startpage(q):
    url = "https://www.startpage.com/sp/search?query=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")
    links = re.findall(r'href="(https?://[^"]+)"', html)
    return [l for l in links if "startpage.com" not in l]

def run(q, idx):
    ts = datetime.now(timezone.utc).isoformat()
    res, engine, err = [], None, None
    for name, fn in (("bing", lambda: eng_bing(q)), ("startpage", lambda: eng_startpage(q))):
        try:
            res = fn()
            if res:
                engine = name
                break
        except Exception as e:
            err = str(e)[:120]
    with LOCK:
        LOG.append({"id": idx, "query": q, "engine": engine, "timestamp": ts,
                    "error": err, "results": res[:25], "n_results": len(res)})
    print(idx, engine, len(res), q[:52], flush=True)

if __name__ == "__main__":
    queries = []
    for t in TOPICS:
        for m in MODS:
            queries.append((t + m).strip())
    queries = list(dict.fromkeys(queries))[:100]
    ths = [threading.Thread(target=run, args=(q, i + 1)) for i, q in enumerate(queries)]
    for t in ths: t.start()
    for t in ths: t.join()
    with open("research_log.json", "w") as f:
        json.dump(LOG, f, indent=1)
    uniq = set()
    for e in LOG:
        for r in e["results"]:
            uniq.add(r)
    print("QUERIES:", len(LOG), "UNIQUE_URLS:", len(uniq),
          "OK_ENGINES:", sum(1 for e in LOG if e["engine"]))
]<]minimax[>[