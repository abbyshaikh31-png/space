#!/usr/bin/env python3
"""Resumable multi-engine sweep -> research_log.json (top-level list)."""
import json, os, re, sys, time, random, urllib.request, urllib.error
from urllib.parse import quote_plus

H = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(H, "research_log.json")
QF = os.path.join(H, "queries.json")

UAS = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
 "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
 "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]
ENG = {
 "bing": "https://www.bing.com/search?q={q}&count=20",
 "ddg_html": "https://html.duckduckgo.com/html/?q={q}",
 "ddg_lite": "https://lite.duckduckgo.com/lite/?q={q}",
 "mojeek": "https://www.mojeek.com/search?q={q}",
 "startpage": "https://www.startpage.com/sp/search?query={q}",
 "marginalia": "https://search.marginalia.nu/search?query={q}",
 "brave": "https://search.brave.com/search?q={q}",
 "searx_be": "https://searx.be/search?q={q}",
 "searx_tux": "https://searx.tiekoetter.com/search?q={q}",
}
BAD = ("bing.com", "duckduckgo", "mojeek.com", "startpage", "marginalia", "brave.com",
       "searx", "microsoft.com", "javascript:", "w3.org")
LINK = re.compile(r'<a[^>]+href="(https?://[^"]+)"', re.I)

BASE = [
 "Gemini 4 Carbon", "Gemini 4 Carbon free", "Gemini 4 Carbon free access",
 "Gemini 4 Carbon API pricing", "gemini-4-carbon model id", "Gemini 4 Argon",
 "Gemini 4 Argon free tier", "Gemini 4 Carbon vs Argon",
 "Google AI Studio free tier 2026", "Google AI Studio pricing Gemini 4",
 "Gemini API free tier limits", "Gemini API pricing per 1M tokens",
 "Vertex AI Express Mode free", "Vertex AI free credits",
 "OpenRouter free models", "OpenRouter Gemini free tier", "OpenRouter pricing gemini",
 "Puter.js free Gemini API", "Puter user pays model", "Puter.js gemini-4-carbon",
 "Atlas Cloud Gemini 4 Carbon", "Atlas Cloud free credits",
 "GitHub Models free tier", "Hugging Face inference free credits",
 "Cloudflare Workers AI free tier", "Groq free tier models",
 "Google AI Pro vs Ultra plans", "Google AI Ultra price",
 "Gemini for Business pricing", "Gemini Enterprise price per seat",
 "fairwind program google deepmind", "Gemini cybersecurity defenders access",
 "gemini app free plan models", "gemini cli free tier",
 "LLM arena gemini 4", "gemini 4 benchmarks",
 "google gemini free trial credits", "google cloud free credits gemini",
 "gemini 4 carbon release date", "gemini 4 carbon announcement blog",
 "gemini 4 carbon student offer", "gemini api batch discount",
 "gemini api context caching price", "gemini api grounding pricing",
 "searxng public instances", "free llm api no credit card",
 "litellm gemini provider", "open webui gemini api",
 "gemini 4 carbon reddit", "gemini 4 carbon news",
]
MODS = ["", " reddit", " github", " tutorial", " 2026", " docs", " free tier", " pricing", " limit", " alternative"]

def build_queries():
    qs, seen = [], set()
    for b in BASE:
        for m in MODS:
            q = (b + m).strip()
            if q.lower() in seen: continue
            seen.add(q.lower()); qs.append(q)
            if len(qs) >= 120: return qs
    return qs

def load_log():
    if not os.path.exists(LOG): return []
    try: d = json.load(open(LOG, encoding="utf-8"))
    except Exception: return []
    if isinstance(d, list): return d
    if isinstance(d, dict):
        for k in ("records", "results", "log", "entries"):
            if isinstance(d.get(k), list): return d[k]
    return []

def save_log(rows):
    tmp = LOG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, LOG)

def fetch(url, timeout=8):
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/", "DNT": "1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(400000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, type(e).__name__

def main():
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 95.0
    qs = build_queries()
    json.dump(qs, open(QF, "w", encoding="utf-8"), indent=1)
    rows = load_log()
    done = {r.get("query") for r in rows if (r.get("n_results") or 0) > 0}
    engs = list(ENG)
    t0, n = time.time(), len(rows)
    fails = 0
    while time.time() - t0 < budget:
        q = next((x for x in qs if x not in done), None)
        if q is None: break
        eng = engs[n % len(engs)]
        st, body = fetch(ENG[eng].format(q=quote_plus(q)))
        links = [u for u in LINK.findall(body or "") if not any(b in u for b in BAD)]
        rows.append({"id": n + 1, "query": q, "engine": eng,
                     "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "http_status": st, "n_results": len(links),
                     "errors": "" if st == 200 else str(body)[:120],
                     "urls": links[:10]})
        if st == 200:
            fails = 0
            if links: done.add(q)
        else:
            fails += 1
        n += 1
        save_log(rows)
        time.sleep(0.15 if fails < 3 else min(2.0, 0.4 * fails))
    save_log(rows)
    print(json.dumps({"entries": len(rows),
                      "unique_queries": len({r["query"] for r in rows}),
                      "unique_urls": len({u for r in rows for u in r.get("urls", [])}),
                      "http200": sum(1 for r in rows if r.get("http_status") == 200),
                      "engines": sorted({r["engine"] for r in rows})}))

if __name__ == "__main__":
    main()