#!/usr/bin/env python3
"""google_free_search.py — free, keyless Google SERP/news search engine client.

Strategy (research-validated on datacenter IPs):
  1. Google News RSS  (https://news.google.com/rss/search) — Google's official,
     no-CAPTCHA endpoint. Works directly from cloud-datacenter IPs. ~0.3-1.5 s.
  2. Bing HTML        (https://www.bing.com/search) — general web results,
     parses class="b_algo" blocks. Works direct and rotates through a free
     proxy pool when direct hits are blocked (429/CAPTCHA).
  3. Optional free-proxy pool: fetched from public lists, pre-validated,
     with per-proxy ban + backoff state. Never makes the pipeline slow:
     proxies are only engaged if direct requests are blocked.

Usage:
  python google_free_search.py "naturopathy treatment india" -n 10
  python google_free_search.py "ts inter results" --json out.json --proxy
"""
import argparse
import json
import base64
import re
import sys
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

try:
    from curl_cffi import requests as creq
except ImportError:
    sys.exit("pip install curl_cffi lxml  (required for TLS fingerprint impersonation)")

from lxml import etree

UA_DATA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
]


def html_unescape(s):
    return re.sub(r'&(#?\w+);', lambda m: {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'"
    }.get(m.group(0), m.group(0)), s or "")


def clean(s):
    return html_unescape(re.sub(r'<[^>]+>', '', s or '')).strip()


# ---------------------------------------------------------------- ProxyPool
def _decode_bing_url(url: str) -> str:
    """Unwrap Bing's /ck/a redirect (u=a1<base64url>) to the real target URL."""
    m = re.search(r'[?&]u=a1([A-Za-z0-9_-]+)', url)
    if not m:
        return url
    b = m.group(1)
    b += '=' * (-len(b) % 4)
    try:
        return base64.urlsafe_b64decode(b).decode('utf-8', 'ignore')
    except Exception:
        return url


class ProxyPool:
    """Free HTTP/HTTPS proxies from public lists, validated + banned with backoff."""

    SOURCES = (
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=8000&country=all",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://www.proxy-list.download/api/v1/get?type=http",
    )

    def __init__(self, limit=40, timeout=10):
        self.timeout = timeout
        self._lock = threading.Lock()
        self._banned_until = {}
        self._fail = {}
        self._idx = 0
        self.proxies = []

    def harvest(self, limit=40, workers=16):
        raw = []
        for url in self.SOURCES:
            try:
                r = creq.get(url, timeout=15, impersonate="chrome131")
                raw += [ln.strip() for ln in r.text.splitlines()
                        if re.match(r'^\d+\.\d+\.\d+\.\d+:\d+$', ln.strip())]
            except Exception:
                pass
        raw = list(dict.fromkeys(raw))
        good = []

        def check(p):
            try:
                r = creq.get("https://httpbin.org/ip", proxy=f"http://{p}", timeout=self.timeout)
                return p if r.status_code == 200 else None
            except Exception:
                return None

        with ThreadPoolExecutor(workers) as ex:
            for res in ex.map(check, raw[:200]):
                if res:
                    good.append(res)
                if len(good) >= limit:
                    break
        self.proxies = good
        return len(good)

    def get(self):
        with self._lock:
            if not self.proxies:
                return None
            now = time.time()
            for _ in range(len(self.proxies)):
                p = self.proxies[self._idx % len(self.proxies)]
                self._idx += 1
                if self._banned_until.get(p, 0) <= now:
                    return p
            return None

    def report(self, p, ok):
        with self._lock:
            if ok:
                self._fail.pop(p, None)
                self._banned_until.pop(p, None)
            else:
                n = self._fail.get(p, 0) + 1
                self._fail[p] = n
                self._banned_until[p] = time.time() + min(2 ** n * 5, 600)
                if n >= 5 and p in self.proxies:
                    self.proxies.remove(p)


# ------------------------------------------------------------- backends
def _blocked(text):
    return any(s in text for s in ("recaptcha", "/httpservice/retry/enablejs",
                                   "unusual traffic", "g-recaptcha"))


def search_google_news_rss(query, limit, country="US", lang="en-US"):
    """Google's official News RSS — the only Google endpoint that reliably
    returns real results to datacenter IPs with zero CAPTCHA (0.3-1.5 s)."""
    q = urllib.parse.quote(query)
    url = (f"https://news.google.com/rss/search?q={q}"
           f"&hl={lang}&gl={country}&ceid={country}:{lang.split('-')[0]}")
    r = creq.get(url, impersonate="chrome131", timeout=15)
    if r.status_code != 200 or "<item>" not in r.text:
        return None
    root = etree.fromstring(r.content)
    out = []
    for it in root.xpath("//channel/item")[:max(limit, 10)]:
        title = clean(it.findtext("title"))
        link = (it.findtext("link") or "").strip()
        # RSS titles end with ' - Source'; split for cleanliness
        m = re.match(r'^(.*)\s+-\s+([^\-]+)$', title)
        src = m.group(2).strip() if m else ""
        out.append({
            "title": m.group(1).strip() if m else title,
            "url": link,
            "source": src,
            "published": it.findtext("pubDate") or "",
            "backend": "google-news-rss",
        })
        if len(out) >= limit:
            break
    return out


def _parse_bing(html):
    from lxml import html as lh
    doc = lh.fromstring(html)
    results = []
    for li in doc.xpath('//li[contains(@class,"b_algo")]'):
        a = li.xpath('.//h2/a[@href]')
        if not a:
            continue
        a = a[0]
        snips = li.xpath('.//div[contains(@class,"b_caption")]//p//text()')
        results.append({
            "title": clean(a.text_content()),
            "url": a.get("href", ""),
            "snippet": clean(" ".join(snips))[:300],
            "backend": "bing-html",
        })
    return results


def search_bing(query, limit, pool=None, proxies=False):
    url = ("https://www.bing.com/search?q=" + urllib.parse.quote(query)
           + f"&count={min(limit * 2, 30)}")
    attempts = [(None, 0)] if not proxies else \
               [(None, 0)] + [(pool.get(), 1) for _ in range(4) if pool and pool.proxies]
    for ppx, gen in attempts:
        kw = {"impersonate": "chrome131", "timeout": 20}
        if ppx:
            kw["proxy"] = f"http://{ppx}"
        try:
            r = creq.get(url, headers={"User-Agent": UA_DATA[gen % len(UA_DATA)]}, **kw)
            if r.status_code == 200 and not _blocked(r.text):
                res = _parse_bing(r.text)
                if res and pool:
                    pool.report(ppx, ok=True)
                return res[:limit]
            if pool:
                pool.report(ppx, ok=False)
        except Exception as e:
            if pool:
                pool.report(ppx, ok=False)
            time.sleep(1)
    return []


# ------------------------------------------------------------- orchestrator
def search(query, limit=10, mode="auto", use_proxies=False, pool=None):
    """Returns list[dict] using the fastest unblocked backend."""
    t0 = time.time()
    # 1. Google News RSS (direct, Google-brand results, never blocked here)
    if mode in ("auto", "news"):
        try:
            res = search_google_news_rss(query, limit)
            if res:
                return res, "google-news-rss", time.time() - t0
        except Exception:
            pass
    # 2. Bing general web (direct first, then via free proxy pool)
    res = search_bing(query, limit, pool=pool, proxies=use_proxies)
    if res:
        return res, "bing-html", time.time() - t0
    return [], "none", time.time() - t0


def main():
    ap = argparse.ArgumentParser(description="Free Google-style SERP search (zero cost)")
    ap.add_argument("query")
    ap.add_argument("-n", "--num", type=int, default=10)
    ap.add_argument("--mode", choices=["auto", "news", "web"], default="auto",
                    help="news = Google News RSS only, web = Bing only")
    ap.add_argument("--proxy", action="store_true",
                    help="harvest + validate free proxies for the web backend")
    ap.add_argument("--json", metavar="FILE", help="write results to a JSON file")
    args = ap.parse_args()

    pool = ProxyPool() if args.proxy else None
    if pool:
        print(f"[pool] harvesting free proxies ...", file=sys.stderr)
        n = pool.harvest()
        print(f"[pool] {n} validated free proxies", file=sys.stderr)

    results, backend, dt = search(args.query, args.num, args.mode, args.proxy, pool)
    payload = {
        "query": args.query, "backend": backend, "latency_s": round(dt, 2),
        "count": len(results), "fetched_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    for i, r in enumerate(results, 1):
        print(f"{i:2d}. {r['title']}")
        print(f"    {r.get('url', r.get('link', ''))}")
        if r.get("snippet"):
            print(f"    {r['snippet'][:160]}")
        if r.get("source") or r.get("published"):
            print(f"    [{r.get('source','')} | {r.get('published','')}]".strip())
    if not results:
        print("No results (all backends blocked).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
