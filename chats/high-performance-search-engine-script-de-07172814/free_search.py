#!/usr/bin/env python3
"""free_search.py 2.1.0 — free, zero-API-key, high-speed web search fleet.
Keyless engines: Google HTML (udm=14+gbv=1, CONSENT/SOCS bypass, curl_cffi Chrome
TLS impersonation), Startpage (Google syndication, POST), Bing HTML+RSS, DuckDuckGo
HTML, Yahoo, Brave, Google News RSS. Parallel hedged racing (~0.5-2s), Google-
validated free proxy pool, cloud-safe SQLite cache, CLI + module API.

USAGE
  python3 free_search.py search "openai sam altman" -n 8
  python3 free_search.py search "python asyncio" --google -n 8 --json
  python3 free_search.py batch queries.txt -j 6
  python3 free_search.py selftest
  python3 free_search.py proxies --refresh --google
  python3 free_search.py serve --port 8078

API:  from free_search import search, google_search, news
"""
from __future__ import annotations
import argparse, base64, concurrent.futures as cf, hashlib, html as H, json, os, random, re, sqlite3, sys, tempfile, threading, time, urllib.parse, urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import requests
except ImportError:
    sys.stderr.write("free_search: pip install requests\n"); raise
try:
    from curl_cffi import requests as crq
    HAVE_CFFI = True
except Exception:
    crq, HAVE_CFFI = None, False

VERSION = "2.1.0"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36)")
HDRS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9", "Upgrade-Insecure-Requests": "1"}
GOOGLE_COOKIES = {"CONSENT": "YES+cb.20230531-04-p0.en+FX+908",
                  "SOCS": "CAISHAgBEhJnd3NfMjAyNDA1MTUtMF9SQzIaAmVuIAEaBgiAo_CmBg"}
WALL_CODES = {999, 429, 403, 401, 418, 503}
WALL_MARKERS = ("captcha", "unusual traffic", "/sorry/index", "g-recaptcha",
                "just a moment", "enable javascript", "access denied", "anomaly")
PROXY_SOURCES = (
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=4000",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
)
_STOP = frozenset("a an the and or but if then than that this these those of in on at to for from by with within into over under all any both each more most other some such no nor not only same so too very can will just should now is are was were be been being do does did doing have has had i you we they what which who how when where why".split())


class SearchError(Exception): pass
class BotWalled(SearchError): pass
class EngineDown(SearchError): pass
class EgressRetry(SearchError): pass


def strip_tags(s: str) -> str:
    s = H.unescape(s or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def looks_walled(status: int, body: str) -> bool:
    if status in WALL_CODES: return True
    low = (body or "")[:20000].lower()
    return bool(low) and any(m in low for m in WALL_MARKERS)


def decode_bing_ck(u):
    h = H.unescape(u or "")
    if "/ck/a" not in h: return h
    m = re.search(r"[?&]u=a1([^&]+)", h)
    if not m: return h
    s = m.group(1).replace("-", "+").replace("_", "/"); s += "=" * (-len(s) % 4)
    try: return base64.b64decode(s).decode("utf-8", "ignore") or h
    except Exception: return h


def decode_ddg_l(u):
    h = H.unescape(u or "")
    if h.startswith("//"): h = "https:" + h
    m = re.search(r"[?&]uddg=([^&]+)", h)
    return urllib.parse.unquote(m.group(1)) if m else h


def decode_yahoo_ru(u):
    m = re.search(r"/RU=([^/]+)/RK=", H.unescape(u or ""))
    try:
        return urllib.parse.unquote(m.group(1)) if m else u
    except Exception: return u


def canon_url(u):
    try:
        p = urllib.parse.urlparse(u); host = p.netloc.lower().removeprefix("www.")
        path = p.path.rstrip("/") or "/"
        return f"{p.scheme}://{host}{path}" + (f"?{p.query}" if p.query else "")
    except Exception: return (u or "").lower()


def is_junk(u):
    if not u or not u.startswith(("http://", "https://")): return True
    low = u.lower()
    junk = ("bing.com/ck/a", "google.com/url?", "duckduckgo.com/l/?", "r.search.yahoo.com",
            "/search?q=", "javascript:void", "campaign-redirect", "go.micro")
    return any(j in low for j in junk)


def relevance(query, hits):
    if not hits: return 0.0
    terms = {t for t in re.findall(r"[a-z0-9][a-z0-9'.-]+", query.lower())
             if t not in _STOP and len(t) >= 3}
    if not terms: return 1.0
    good = sum(1 for h in hits if any(t in (h.title + " " + h.url + " " + h.snippet).lower()
               for t in terms))
    return good / len(hits)


@dataclass
class Hit:
    title: str; url: str; snippet: str = ""; source: str = ""; rank: int = 0
    def to_dict(self):
        return {"title": self.title, "url": self.url, "href": self.url, "link": self.url,
                "snippet": self.snippet, "body": self.snippet, "content": self.snippet,
                "source": self.source, "engine": self.source, "rank": self.rank,
                "position": self.rank}


@dataclass
class SearchOutcome:
    query: str; results: List[Hit] = field(default_factory=list)
    engine: str = ""; egress: str = "direct"; proxy: str = ""
    from_cache: bool = False; deferred: bool = False; relevance: float = 1.0
    low_quality: bool = False; attempts: int = 0; elapsed_ms: int = 0
    errors: List[str] = field(default_factory=list)
    def __len__(self): return len(self.results)
    def __bool__(self): return bool(self.results)
    def to_dict(self):
        return {"query": self.query, "results": [h.to_dict() for h in self.results],
                "organic_results": [h.to_dict() for h in self.results],
                "engine": self.engine, "egress": self.egress, "proxy": self.proxy,
                "from_cache": self.from_cache, "deferred": self.deferred,
                "relevance": round(self.relevance, 3), "low_quality": self.low_quality,
                "attempts": self.attempts, "elapsed_ms": self.elapsed_ms,
                "errors": self.errors[-6:]}


def http_get(url, *, headers=None, cookies=None, timeout=9.0, impersonate="chrome124",
             proxy=None, method="GET", data=None, session=None) -> Tuple[int, str]:
    """Return (status, text). curl_cffi Chrome-TLS first; requests fallback."""
    px = {"http": proxy, "https": proxy} if proxy else None
    hdr = dict(HDRS); hdr.update(headers or {})
    if HAVE_CFFI:
        try:
            r = crq.request(method, url, headers=hdr, cookies=cookies or {}, timeout=timeout,
                            impersonate=impersonate, allow_redirects=True, proxies=px, data=data)
            return int(r.status_code), r.text or ""
        except Exception as e:
            if proxy: raise EgressRetry(f"cffi:{type(e).__name__}")
            if not session: raise BotWalled(f"cffi-direct:{type(e).__name__}:{e}")
    s = session or requests.Session()
    if hasattr(s, "trust_env"): s.trust_env = False
    if px: s.proxies = px
    try:
        r = s.request(method, url, headers=hdr, cookies=cookies or {}, timeout=(4.5, timeout),
                      allow_redirects=True, data=data)
        return int(r.status_code), r.text or ""
    except requests.RequestException as e:
        if proxy: raise EgressRetry(f"req:{type(e).__name__}")
        raise EngineDown(f"req:{type(e).__name__}:{e}")
