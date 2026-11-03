#!/usr/bin/env python3
"""
google_free_search.py - Free Google-powered search that works from datacentre IPs.

Strategy (validated live):
  1. Google Scholar   - full HTML, no JS wall, real titles + external links.
  2. Google News RSS  - keyless XML feed of fresh web/news results.
  3. Bing HTML        - fallback engine when Google front-ends are blocked.
Optionally routes everything through free HTTP(S) proxies (harvested from public
APIs and validated against Google) via --use-proxies.

Usage:
  python google_free_search.py "best free python libraries"
  python google_free_search.py "artificial intelligence" --max 25 --use-proxies
Outputs: google_results.json + google_results.csv in the script folder.
"""
import argparse, asyncio, csv, json, os, random, re, sys, time, warnings
import xml.etree.ElementTree as ET
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.abspath(__file__))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}

HARVEST_URLS = [
    "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=5000&country=all&ssl=all",
    "https://www.proxy-list.download/api/v1?type=http",
    "https://api.openproxylist.xyz/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]
sys.path.insert(0, BASE)

# ---------------- proxy harvesting + validation ----------------

async def harvest(session, limit=400):
    raw = set()
    async def fetch(u):
        try:
            async with session.get(u, timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status == 200:
                    text = await r.text()
                    for m in re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}", text):
                        raw.add(m)
        except Exception:
            pass
    await asyncio.gather(*(fetch(u) for u in HARVEST_URLS))
    sample = list(raw)[:limit]
    print(f"[harvest] {len(sample)} raw proxies collected")
    return sample

async def validate(session, proxy, out):
    url = "https://scholar.google.com/scholar?q=test"
    try:
        async with session.get(url, proxy=f"http://{proxy}",
                               timeout=aiohttp.ClientTimeout(total=12)) as r:
            t = await r.text()
            if r.status == 200 and "scholar" in t.lower() and "gs_rt" in t:
                out.append(proxy)
    except Exception:
        pass

async def get_working_proxies(use=True, limit=400):
    if not use:
        return []
    async with aiohttp.ClientSession() as s:
        raw = await harvest(s, limit)
    good = []
    sem = asyncio.Semaphore(150)
    async with aiohttp.ClientSession(headers=HEADERS) as s:
        async def go(p):
            async with sem:
                await validate(s, p, good)
        await asyncio.gather(*(go(p) for p in raw))
    print(f"[validate] {len(good)} working Google proxies")
    return good

# ---------------- result parsers (verified live) ----------------

def clean_abs(u):
    if u and u.startswith("/"):
        u = urllib.parse.urljoin("https://scholar.google.com", u)
    return u

# ---------------- parser: Google Scholar ----------------
def parse_scholar(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for row in soup.select("div.gs_ri"):
        h3 = row.select_one("h3.gs_rt a")
        if not h3:
            h3 = row.select_one("h3.gs_rt span")
        title = " ".join(h3.get_text(" ", strip=True).split()) if h3 else ""
        link = clean_abs(h3.get("href", "")) if h3 and h3.name == "a" else ""
        snippet = row.select_one("div.gs_rs")
        info = row.select_one("div.gs_a")
        if title:
            results.append({"title": title, "link": link,
                            "snippet": snippet.get_text(strip=True) if snippet else "",
                            "source": info.get_text(strip=True) if info else "",
                            "engine": "google_scholar"})
    return results

async def search_scholar(session, query, proxy=None, count=20):
    url = ("https://scholar.google.com/scholar?hl=en&num="
           + str(min(count, 20)) + "&q=" + urllib.parse.quote(query))
    kw = {"proxy": f"http://{proxy}"} if proxy else {}
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=25), **kw) as r:
        html = await r.text()
    return parse_scholar(html)

# ---------------- parser: Google News RSS ----------------
def parse_news_rss(xml_text):
    root = ET.fromstring(xml_text)
    results = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if title and link:
            results.append({"title": title, "link": link, "snippet": "",
                            "source": "", "engine": "google_news"})
    return results

async def search_news(session, query, proxy=None):
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(query) + "&hl=en-US&gl=US&ceid=US:en")
    kw = {"proxy": f"http://{proxy}"} if proxy else {}
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=25), **kw) as r:
        xml = await r.text()
    return parse_news_rss(xml)

# ---------------- parser: Bing HTML fallback ----------------
def parse_bing(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for li in soup.select("li.b_algo"):
        a = li.select_one("h2 a")
        sn = li.select_one("div.b_caption p, p")
        if a:
            results.append({"title": a.get_text(strip=True),
                            "link": a.get("href", ""),
                            "snippet": sn.get_text(strip=True) if sn else "",
                            "source": "", "engine": "bing_fallback"})
    return results

async def search_bing(session, query, proxy=None, count=15):
    url = "https://www.bing.com/search?count=" + str(count) + "&q=" + urllib.parse.quote(query)
    kw = {"proxy": f"http://{proxy}"} if proxy else {}
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=25), **kw) as r:
        html = await r.text()
    return parse_bing(html)

# ---------------- rotation + retry ----------------
async def rotating_search(query, proxies=(), use_proxies=False, count=20):
    results = []
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        order = list(proxies)
        random.shuffle(order)
        if not use_proxies:
            order = [None]
        for p in (order[:8] if use_proxies else [None]):
            try:
                r = await search_scholar(session, query, proxy=p, count=count)
                if r:
                    results = r
                    print(f"[scholar] {len(r)} results (proxy={p or 'direct'})")
                    break
            except Exception as e:
                print(f"[scholar] retry proxy={p}: {e}")
        if not results:
            pp = random.choice(order) if order and use_proxies else None
            try:
                r = await search_news(session, query, proxy=pp)
                if r:
                    results = r
                    print(f"[news] {len(r)} results")
            except Exception as e:
                print(f"[news] ERR {e}")
        if not results:
            pp = random.choice(order) if order and use_proxies else None
            try:
                r = await search_bing(session, query, proxy=pp, count=count)
                if r:
                    results = r
                    print(f"[bing] {len(r)} results")
            except Exception as e:
                print(f"[bing] ERR {e}")
    return results[:count]

# ---------------- save + main ----------------
def save(results, query):
    if not results:
        print("[save] NO RESULTS - files not written")
        return
    jp = os.path.join(BASE, "google_results.json")
    cp = os.path.join(BASE, "google_results.csv")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump({"query": query, "count": len(results),
                   "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "results": results}, f, ensure_ascii=False, indent=2)
    with open(cp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["title", "link", "snippet", "source", "engine"])
        w.writeheader()
        w.writerows(results)
    print(f"[save] {len(results)} results -> {jp} + {cp}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="+", help="search query text")
    ap.add_argument("--max", type=int, default=20, dest="count")
    ap.add_argument("--use-proxies", action="store_true",
                    help="route requests through validated free proxies")
    args = ap.parse_args()
    q = " ".join(args.query)
    proxies = asyncio.run(get_working_proxies(use=args.use_proxies))
    results = asyncio.run(rotating_search(q, proxies, args.use_proxies, args.count))
    save(results, q)
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. {r['title'][:70]}")
        print(f"   {r['link'][:100]}")

if __name__ == "__main__":
    main()
