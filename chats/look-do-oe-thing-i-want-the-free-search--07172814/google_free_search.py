#!/usr/bin/env python3
"""
google_free_search.py — free, keyless Google search with rotating free proxies.
Usage:
    python google_free_search.py "your query" -n 10
    python google_free_search.py "best python books" -n 20 --max-proxies 800
Outputs: google_results.json + google_results.csv (in the script's folder)
"""
import asyncio, aiohttp, random, argparse, csv, json, re, sys, time, os
from pathlib import Path
from bs4 import BeautifulSoup

BASE = Path(os.path.dirname(os.path.abspath(__file__)))

# ---------- tunables ----------
VALIDATE_CONCURRENCY = 400
VALIDATE_TIMEOUT = 8
SEARCH_TIMEOUT = 12
MAX_ATTEMPTS = 40
RESULTS_WANTED = 10

HARVEST_URLS = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=6000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://api.openproxylist.xyz/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}


def raw_url(text):
    for line in text.splitlines():
        line = line.strip()
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}:\d{2,5}$", line):
            yield "http://" + line


# ---------- 1. harvest ----------
async def harvest(limit=3000):
    proxies = set()
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async def fetch(url):
            try:
                async with s.get(url) as r:
                    if r.status == 200:
                        text = await r.text()
                        proxies.update(raw_url(text))
            except Exception:
                pass
        await asyncio.gather(*(fetch(u) for u in HARVEST_URLS))
    sample = list(proxies)[:limit]
    print(f"[harvest] {len(sample)} raw proxies collected")
    return sample

# ---------- 2. validate ----------
async def validate(proxies, target="https://www.google.com/generate_204"):
    good = []
    sem = asyncio.Semaphore(VALIDATE_CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=VALIDATE_CONCURRENCY, ssl=False)
    timeout = aiohttp.ClientTimeout(total=VALIDATE_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as s:
        async def check(p):
            async with sem:
                try:
                    async with s.get(target, proxy=p) as r:
                        if r.status == 204:
                            good.append(p)
                except Exception:
                    pass
        await asyncio.gather(*(check(p) for p in proxies))
    print(f"[validate] {len(good)} working Google proxies")
    return good


# ---------- 3. parse results ----------
def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for g in soup.select("div.g, div.tF2Cxc"):
        h = g.select_one("h3")
        a = g.select_one("a[href^='/url'], a[href^='http']")
        if not h or not a:
            continue
        href = a.get("href", "")
        if href.startswith("/url?q="):
            href = href.split("/url?q=")[1].split("&")[0]
        sn = g.select_one("div.VwiC3b, span.aCOpRe")
        out.append({"title": h.get_text(" ", strip=True),
                    "link": href,
                    "snippet": sn.get_text(" ", strip=True) if sn else ""})
    if not out:  # fallback simple pattern
        for a in soup.select("a[href^='/url?q=']:")[:RESULTS_WANTED]:
            pass
    return out


# ---------- 4. search with rotation ----------
async def search(query, proxies, want=RESULTS_WANTED):
    q = query.replace(" ", "+")
    url = f"https://www.google.com/search?q={q}&num={want}&hl=en"
    random.shuffle(proxies)
    attempts = min(MAX_ATTEMPTS, len(proxies))
    timeout = aiohttp.ClientTimeout(total=SEARCH_TIMEOUT)
    for i in range(attempts):
        p = proxies[i % len(proxies)]
        try:
            async with aiohttp.ClientSession(timeout=timeout, headers=HEADERS) as s:
                async with s.get(url, proxy=p) as r:
                    if r.status != 200:
                        continue
                    html = await r.text()
                    if "detected unusual traffic" in html or "capt" in html.lower():
                        continue
                    res = parse_html(html)
                    if res:
                        print(f"[search] success via {p} (attempt {i+1})")
                        return res[:want]
        except Exception:
            continue
    return []


# ---------- 5. save ----------
def save(results):
    jf, cf = BASE / "google_results.json", BASE / "google_results.csv"
    jf.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(cf, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "link", "snippet"])
        w.writeheader()
        w.writerows(results)
    print(f"[save] {len(results)} results -> {jf.name}, {cf.name}")


# ---------- main ----------
async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-n", "--num", type=int, default=RESULTS_WANTED)
    ap.add_argument("--max-proxies", type=int, default=3000)
    args = ap.parse_args()
    t0 = time.time()
    raw = await harvest(args.max_proxies)
    if not raw:
        sys.exit("no proxies harvested")
    good = await validate(raw)
    if not good:
        sys.exit("no validated proxies")
    res = await search(args.query, good, args.num)
    save(res)
    print(f"[done] {time.time()-t0:.1f}s total")
    for r in res[:5]:
        print("-", r["title"], "->", r["link"])


if __name__ == "__main__":
    asyncio.run(main())
