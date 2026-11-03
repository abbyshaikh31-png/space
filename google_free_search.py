#!/usr/bin/env python3
"""google_free_search.py — free, keyless Google search from any datacentre IP.

Pipeline:
  1) HARVEST  : pull thousands of free proxies from public GitHub lists.
  2) VALIDATE : async concurrency-300 filter — only proxies that return a real
                Google 2xx response (not CAPTCHA/429) survive.
  3) SEARCH   : send the query through rotating validated proxies, re-trying
                on 429/captcha until results are parsed.

Usage:
    python google_free_search.py "your query" [--num 10] [--json out.json]
    python google_free_search.py --revalidate          # refresh proxy cache only

Deps: aiohttp  (pip install --user aiohttp)
"""
import argparse, asyncio, json, html, re, sys, time
from pathlib import Path

try:
    import aiohttp
except ImportError:
    sys.exit("aiohttp missing. Run:  pip install --user aiohttp")

CACHE = Path("proxy_cache.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
]

# ---------------------------------------------------------------- harvest --
def harvest(max_n=9000):
    import urllib.request
    pool = []
    seen = set()
    for src in PROXY_SOURCES:
        try:
            req = urllib.request.Request(src, headers={"User-Agent": UA})
            data = urllib.request.urlopen(req, timeout=30).read().decode(errors="ignore")
            for line in data.splitlines():
                m = re.search(r"\b(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})\b", line)
                if m and m.group(1) not in seen:
                    seen.add(m.group(1))
                    pool.append(f"{m.group(1)}:{m.group(2)}")
            print(f"[harvest] {src.rsplit('/', 1)[-1]}\t total unique so far: {len(pool)}")
        except Exception as e:
            print(f"[harvest] {src} FAILED: {e}")
    print(f"[harvest] unique proxies: {len(pool)}")
    return pool[:max_n]

# --------------------------------------------------------------- validate --
async def check_proxy(session, proxy, sem, good, timeout=6):
    url = "https://www.google.com/generate_204"
    try:
        async with sem:
            async with session.get(url, proxy=f"http://{proxy}", timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                if r.status == 204:
                    good[proxy] = {"ok": 0, "fail": 0}
    except Exception:
        pass

async def validate(proxies, concurrency=400):
    good = {}
    sem = asyncio.Semaphore(concurrency)
    conn = aiohttp.TCPConnector(limit=concurrency * 2, ssl=False)
    async with aiohttp.ClientSession(connector=conn, headers={"User-Agent": UA}) as s:
        tasks = [check_proxy(s, p, sem, good) for p in proxies]
        await asyncio.gather(*tasks)
    return list(good)

# ----------------------------------------------------------------- search --
GOOGLE = "https://www.google.com/search?q={}&num={}&hl=en"

def parse_google(html_text, num):
    results = []
    blocks = re.findall(r'<div class="(?:tF2Cxc|g|H92pTy)[^"]*">(.*?)</div>\s*</div>', html_text, re.S)
    for b in blocks[:num * 2]:
        m_t = re.search(r'<h3[^>]*>(.*?)</h3>', b, re.S)
        m_u = re.search(r'href="(https?://[^"&]+)', b)
        if not (m_t and m_u):
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", m_t.group(1))).strip()
        url = html.unescape(m_u.group(1))
        if title and url and not url.startswith("https://www.google"):
            snip = re.search(r'<div class="VwiC3b[^"]*"[^>]*>(.*?)</div>', b, re.S)
            snip_text = html.unescape(re.sub(r"<[^>]+>", "", snip.group(1))).strip() if snip else ""
            results.append({"title": title, "url": url, "snippet": snip_text[:220]})
        if len(results) >= num:
            break
    return results

async def google_search(session, query, num, pool, max_rounds=None):
    """Rotate through the validated proxy pool until one returns clean SERP HTML."""
    import random
    url = GOOGLE.format(query.replace(" ", "+"), num)
    tried = list(pool)
    random.shuffle(tried)
    if max_rounds is None:
        max_rounds = min(len(tried), 500)
    for i, proxy in enumerate(tried[:max_rounds]):
        try:
            async with session.get(url, proxy=f"http://{proxy}",
                                   timeout=aiohttp.ClientTimeout(total=8),
                                   headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}) as r:
                text = await r.text()
                if r.status == 200 and "captcha" not in text.lower() and "unusual traffic" not in text.lower():
                    res = parse_google(text, num)
                    if res:
                        print(f"[search] SUCCESS via {proxy} (attempt {i+1}, {r.status}, {len(res)} results)")
                        return res
                    print(f"[search] {proxy}: 200 but no results parsed, next...")
                else:
                    print(f"[search] {proxy}: status={r.status} blocked, rotating")
        except Exception as e:
            if i % 50 == 0:
                print(f"[search] {proxy}: {type(e).__name__}")
    return []

# ------------------------------------------------------------------- main --
async def main():
    ap = argparse.ArgumentParser(description="Free proxy-rotated Google search")
    ap.add_argument("query", nargs="*", default=[])
    ap.add_argument("--revalidate", action="store_true", help="harvest + validate, then exit")
    ap.add_argument("--num", type=int, default=10)
    ap.add_argument("--json", default="search_results.json")
    args = ap.parse_args()

    if args.revalidate or not CACHE.exists():
        proxies = harvest()
        if not proxies:
            sys.exit("[!] No proxies harvested — network may be blocked.")
        t0 = time.time()
        good = await validate(proxies)
        print(f"[validate] {len(good)}/{len(proxies)} passed Google check in {time.time()-t0:.1f}s")
        if not good:
            sys.exit("[!] Zero working proxies — try again later.")
        CACHE.write_text(json.dumps(good, indent=1))
        if args.revalidate:
            return

    if not args.query:
        sys.exit("[!] Give a query:  python google_free_search.py \"your search\"")

    pool = list(json.loads(CACHE.read_text()).keys())
    print(f"[cache] {len(pool)} known-good proxies")
    conn = aiohttp.TCPConnector(limit=20, ssl=False)
    async with aiohttp.ClientSession(connector=conn, headers={"User-Agent": UA}) as s:
        results = await google_search(s, " ".join(args.query), args.num, pool)

    if results:
        Path(args.json).write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\n=== {len(results)} results (saved to {args.json}) ===")
        for r in results:
            print(f"  {r['title']}\n    {r['url']}\n    {r['snippet'][:120]}")
    else:
        print("[!] All proxies hit CAPTCHA/block — rerun with --revalidate to crop a fresh pool.")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
