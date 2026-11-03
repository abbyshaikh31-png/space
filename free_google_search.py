#!/usr/bin/env python3
"""free_google_search.py - Fast, free Google SERP scraper for cloud datacenter IPs.
Uses curl_cffi Chrome TLS impersonation + optional free-proxy rotation.
Requires: pip install curl_cffi beautifulsoup4 free-proxy
Usage: python3 free_google_search.py "query" -n 10 [--proxy-country IN] [--json]
"""
import argparse, json, random, re, sys, time, urllib.parse
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from curl_cffi import requests as creq
from bs4 import BeautifulSoup

@dataclass
class SearchResult:
    position: int
    title: str
    url: str
    snippet: str = ""

@dataclass
class ProxyPool:
    proxies: List[str] = field(default_factory=list)
    idx: int = 0
    def next(self):
        if not self.proxies: return None
        p = self.proxies[self.idx % len(self.proxies)]; self.idx += 1; return p
    def ban(self, proxy):
        if proxy and proxy in self.proxies and len(self.proxies) > 1:
            self.proxies.remove(proxy)

def fetch_free_proxies(country=None, limit=30):
    try:
        from fp import FreeProxy
    except ImportError:
        print("free-proxy not installed; direct mode", file=sys.stderr); return []
    try:
        p = FreeProxy(country_id=country, https=True, timeout=3)
        raw = p.get_proxy_list()
        return [x for x in raw if x.strip()][:limit]
    except Exception as e:
        print(f"proxy fetch failed: {e}", file=sys.stderr); return []

UAS = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
 "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

def parse_google(html):
    soup = BeautifulSoup(html, "lxml")
    results, seen = [], set()
    for h3 in soup.find_all("h3"):
        a = h3.find_parent("a")
        if not a: continue
        href = a.get("href", "")
        m = re.search(r"/url\?q=([^&]+)", href)
        url = urllib.parse.unquote(m.group(1)) if m else href
        if not url.startswith("http") or "google." in url or url in seen: continue
        seen.add(url)
        snippet = ""
        block = h3.find_parent("div")
        if block:
            txt = block.get_text(" ", strip=True)
            t = h3.get_text(strip=True)
            snippet = txt.replace(t, "", 1).strip()[:280]
        results.append(SearchResult(len(results)+1, h3.get_text(strip=True), url, snippet))
        if len(results) >= 50: break
    return results

def google_search(query, num=10, pool=None, max_retries=6, timeout=12, debug=False):
    session = creq.Session(impersonate="chrome131")
    for attempt in range(max_retries):
        proxy = pool.next() if pool else None
        proxies = {"http": proxy, "https": proxy} if proxy else None
        host = random.choice(["www.google.com", "www.google.co.in", "www.google.ca"])
        params = {"q": query, "num": str(min(num, 20)), "hl": "en"}
        headers = {"User-Agent": random.choice(UAS), "Accept-Language": "en-US,en;q=0.9"}
        try:
            r = session.get(f"https://{host}/search", params=params, headers=headers, proxies=proxies, timeout=timeout)
            if r.status_code == 200:
                res = parse_google(r.text)
                if res: return res[:num]
                if debug: print("200 but 0 parsed (CAPTCHA?)", file=sys.stderr)
            elif debug:
                print(f"attempt {attempt+1}: {r.status_code} proxy={proxy}", file=sys.stderr)
        except Exception as e:
            if debug: print(f"attempt {attempt+1}: {type(e).__name__}: {e}", file=sys.stderr)
        if proxy: pool.ban(proxy)
        time.sleep(random.uniform(1.0, 2.5))
    return []

def main():
    ap = argparse.ArgumentParser(description="Free Google SERP scraper")
    ap.add_argument("query"); ap.add_argument("-n", "--num", type=int, default=10)
    ap.add_argument("--proxy-country"); ap.add_argument("--no-proxy", action="store_true")
    ap.add_argument("--json", action="store_true"); ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    pool = None
    if not args.no_proxy:
        plist = fetch_free_proxies(args.proxy_country)
        if plist:
            print(f"[*] got {len(plist)} free proxies", file=sys.stderr)
            pool = ProxyPool(plist)
    t0 = time.time()
    results = google_search(args.query, args.num, pool, debug=args.debug)
    print(f"[*] {len(results)} results in {time.time()-t0:.2f}s", file=sys.stderr)
    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(f"{r.position:>3}. {r.title}\n     {r.url}\n     {r.snippet[:150]}\n")
    sys.exit(0 if results else 1)

if __name__ == "__main__":
    main()
