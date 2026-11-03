#!/usr/bin/env python3
"""free_search.py v2.1.0 - free, keyless, high-speed web search with hedged racing.
Survives cloud datacenter IPs via engine fleet + bing_rss + proxy egress tier.
"""
import argparse
import base64
import bisect
import concurrent.futures as cf
import dataclasses
import json
import os
import random
import re
import socket
import sqlite3
import sys
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

__version__ = "2.1.0"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
LYNX_UA = "Lynx/2.9.2 libwww-FM/2.14 SSL-MM/1.4.1 OpenSSL/3.0.13"
GOOGLE_COOKIES = {
    "CONSENT": "YES+cb.20230531-04-p0.en+FX+908",
    "SOCS": "CAISHAgBEhJnd3NfMjAyNDA1MTUtMF9SQzIaAmVuIAEaBgiAo_CmBg",
}
STOPWORDS = set("a an and are as at be by for from has have how i in is it its of on or that the to was what when where which who will with vs not you your can this these".split())


def _clean(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&\w+;|&#\d+;", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _curl_get(url: str, **kw):
    try:
        from curl_cffi import requests as creq
        return creq.get(url, impersonate="chrome124", timeout=kw.get("timeout", 12), **{k: v for k, v in kw.items() if k != "timeout"})
    except Exception:
        return None


def fetch(url: str, timeout: float = 12.0, method: str = "GET", data=None, headers=None, cookies=None, impersonate=False):
    hdrs = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        hdrs.update(headers)
    if impersonate:
        try:
            from curl_cffi import requests as creq
            r = creq.request(method, url, timeout=timeout, headers=hdrs, data=data, cookies=cookies, impersonate="chrome124")
            if getattr(r, "status_code", 0) == 200:
                return r.text
            if r.status_code == 429:
                raise RuntimeError("wall-429")
        except RuntimeError:
            raise
        except Exception:
            pass
    r = requests.request(method, url, timeout=timeout, headers=hdrs, data=data, cookies=cookies)
    if r.status_code == 429:
        raise RuntimeError("wall-429")
    r.raise_for_status()
    return r.text


JUNK_HOSTS = ("bing.com/ck/a", "google.com/url", "google.com/search", "search.yahoo.com/", "duckduckgo.com/", "r.search.yahoo.com", "www.bing.com/ck", "startpage.com", "brave.com", "news.google.com/rss", "bing.com/search", "google.com/amp", "yandex.ru/search")


def is_junk(url: str) -> bool:
    u = (url or "").lower()
    return any(j in u for j in JUNK_HOSTS)


def unwrap_bing(url: str) -> str:
    try:
        if "bing.com/ck/a" in url:
            m = re.search(r"[?&]u=a1([^&]+)", url)
            if m:
                b = m.group(1)
                b = b[:-2 * ((len(b) % 4) == 2)] + ("==" if len(b) % 4 else "")
                dec = base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)).decode("utf-8", "ignore")
                return dec
    except Exception:
        pass
    return url


def unwrap_google(url: str) -> str:
    try:
        if "google.com/url" in url:
            m = re.search(r"[?&]q=([^&]+)", url)
            if m:
                return urllib.parse.unquote(m.group(1))
        m = re.search(r"/url\?q=([^&]+)", url)
        if m:
            return urllib.parse.unquote(m.group(1).split("&sa=")[0])
    except Exception:
        pass
    return url


def unwrap_yahoo(url: str) -> str:
    try:
        m = re.search(r"/RU=([^/]+)/RK=", url)
        if m:
            return urllib.parse.unquote(m.group(1))
    except Exception:
        pass
    return url


def unwrap_ddg(url: str) -> str:
    try:
        m = re.search(r"uddg=([^&]+)", url)
        if m:
            return urllib.parse.unquote(m.group(1))
    except Exception:
        pass
    return url


def normalize(url: str) -> str:
    u = unwrap_bing(unwrap_google(unwrap_yahoo(unwrap_ddg(url or ""))))
    if not u.startswith("http"):
        return ""
    return u


def relevant(hit: Dict[str, Any], terms: List[str]) -> bool:
    text = (hit.get("title", "") + " " + hit.get("snippet", "")).lower()
    return any(t in text for t in terms)


def relevance_score(hits: List[Dict[str, Any]], query: str) -> float:
    terms = [t.lower() for t in re.findall(r"[\w-]{2,}", query) if t.lower() not in STOPWORDS]
    if not terms or not hits:
        return 0.0
    return sum(1 for h in hits if relevant(h, terms)) / len(hits)


@dataclass
class Hit:
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "url": self.url, "href": self.url, "link": self.url, "snippet": self.snippet, "source": self.source, "rank": self.rank}


@dataclass
class SearchOutcome:
    query: str
    results: List[Hit] = field(default_factory=list)
    engine: str = ""
    egress: str = "direct"
    from_cache: bool = False
    elapsed_ms: int = 0
    errors: Dict[str, str] = field(default_factory=dict)
    deferred: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"query": self.query, "results": [h.to_dict() for h in self.results], "engine": self.engine, "egress": self.egress, "from_cache": self.from_cache, "elapsed_ms": self.elapsed_ms, "errors": self.errors, "deferred": self.deferred}

# ---------- Engines ----------
def _soup(html):
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, "html.parser")
    except Exception:
        return None


def startpage_html(query: str, n: int = 10) -> List[Hit]:
    html = fetch("https://www.startpage.com/sp/search", method="POST", timers:=None,
                 data={"query": query, "cat": "web", "cmd": "process_search"})
    hits, soup = [], _soup(html)
    if not soup:
        return hits
    for a in soup.select("a.w-gl__result-title, a.result-title")[:n]:
        title = _clean(a.get_text()); url = normalize(a.get("href", ""))
        if not url or is_junk(url):
            continue
        desc = a.find_next(class_="w-gl__description") if a.parent else None
        hits.append(Hit(title=title, url=url, snippet=_clean(desc.get_text()) if desc else "", source="startpage_html"))
    return hits


def google_html(query: str, n: int = 10) -> List[Hit]:
    hits = _google_mode(query, n, gbv=False)
    if not hits:
        hits = _google_mode(query, n, gbv=True)  # gbv=1 + Lynx UA fallback
    return hits


def _google_mode(query: str, n: int, gbv: bool) -> List[Hit]:
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query) + "&udm=14&hl=en&gl=us"
    if gbv:
        url += "&gbv=1"
    hdrs = {"User-Agent": LYNX_UA} if gbv else {}
    html = fetch(url, headers=hdrs, cookies=GOOGLE_COOKIES, impersonate=not gbv)
    soup = _soup(html)
    if not soup:
        return []
    hits = []
    for h3 in soup.find_all("h3")[:n * 2]:
        a = h3.find_parent("a")
        if not a:
            continue
        u = normalize(a.get("href", ""))
        if not u or is_junk(u):
            continue
        hits.append(Hit(title=_clean(h3.get_text()), url=u, snippet=_clean(a.parent.get_text(" "))[:300], source="google_html"))
        if len(hits) >= n:
            break
    return hits


def bing_html(query: str, n: int = 10) -> List[Hit]:
    html = fetch("https://www.bing.com/search?q=" + urllib.parse.quote(query) + "&count=" + str(n))
    soup = _soup(html)
    if not soup:
        return []
    hits = []
    for li in soup.select("li.b_algo")[:n]:
        a = li.find("a"); h2 = li.find("h2")
        if not a:
            continue
        u = normalize(a.get("href", ""))
        if not u or is_junk(u):
            continue
        p = li.find("p") or li.find(class_="b_caption")
        hits.append(Hit(title=_clean(h2.get_text()) if h2 else _clean(a.get_text()), url=u, snippet=_clean(p.get_text()) if p else "", source="bing_html"))
    return hits


def bing_rss(query: str, n: int = 10) -> List[Hit]:
    xml_text = fetch("https://www.bing.com/search?q=" + urllib.parse.quote(query) + "&format=rss&count=" + str(n))
    hits = []
    try:
        root = ET.fromstring(xml_text.encode("utf-8", "ignore") if isinstance(xml_text, str) else xml_text)
        for item in root.iter("item")[:n]:
            t = item.findtext("title") or ""; lk = item.findtext("link") or ""; d = item.findtext("description") or ""
            u = normalize(lk)
            if not u or is_junk(u):
                continue
            hits.append(Hit(title=_clean(t), url=u, snippet=_clean(d), source="bing_rss"))
    except Exception:
        pass
    return hits


def yahoo_html(query: str, n: int = 10) -> List[Hit]:
    html = fetch("https://search.yahoo.com/search?p=" + urllib.parse.quote(query) + "&b=1")
    soup = _soup(html)
    if not soup:
        return []
    hits = []
    for div in soup.select("div.algo, div.dd.algo")[:n]:
        a = div.find("a"); h3 = div.find("h3") or div.find("h2")
        if not a:
            continue
        u = normalize(a.get("href", ""))
        if not u or is_junk(u):
            continue
        p = div.find("p")
        hits.append(Hit(title=_clean(h3.get_text()) if h3 else _clean(a.get_text()), url=u, snippet=_clean(p.get_text()) if p else "", source="yahoo_html"))
    return hits


def brave_html(query: str, n: int = 10) -> List[Hit]:
    html = fetch("https://search.brave.com/search?q=" + urllib.parse.quote(query), impersonate=True)
    soup = _soup(html)
    if not soup:
        return []
    hits = []
    for a in soup.select("a[href^='https'] :is(h1,h2,h3), div.result a"):
        pass
    for sn in soup.select("div#results div.result")[:n]:
        a = sn.find("a"); d = sn.find("div", class_="snippet-description") or sn.find("p")
        if not a:
            continue
        u = normalize(a.get("href", ""))
        if not u or is_junk(u):
            continue
        hits.append(Hit(title=_clean(a.get_text()), url=u, snippet=_clean(d.get_text()) if d else "", source="brave_html"))
    return hits


def google_news_rss(query: str, n: int = 10) -> List[Hit]:
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-US&gl=US&ceid=US:en"
    xml_text = fetch(url)
    hits = []
    try:
        root = ET.fromstring(xml_text.encode("utf-8", "ignore") if isinstance(xml_text, str) else xml_text)
        for item in root.iter("item")[:n]:
            t = _clean(item.findtext("title") or ""); lk = normalize(item.findtext("link") or "")
            if not lk:
                continue
            hits.append(Hit(title=t, url=lk, snippet=_clean(item.findtext("description") or "")[:300], source="google_news_rss"))
    except Exception:
        pass
    return hits


def _ddgs_engine(backend: str):
    def engine(query: str, n: int = 10) -> List[Hit]:
        from ddgs import DDGS
        hits = []
        try:
            rows = DDGS().text(query, max_results=n, backend=backend) or []
        except Exception:
            return hits
        for r in rows[:n]:
            u = normalize(r.get("href", "") or r.get("url", ""))
            if not u or is_junk(u):
                continue
            hits.append(Hit(title=_clean(r.get("title", "")), url=u, snippet=_clean(r.get("body", "") or ""), source="ddgs:" + backend))
        return hits
    return engine


ENGINES = {
    "google_html": google_html,
    "bing_html": bing_html,
    "bing_rss": bing_rss,
    "startpage_html": startpage_html,
    "yahoo_html": yahoo_html,
    "brave_html": brave_html,
    "google_news_rss": google_news_rss,
}
for _b in ("google", "brave", "bing", "yahoo", "duckduckgo"):
    ENGINES["ddgs:" + _b] = _ddgs_engine(_b)

NEWS_ENGINES = {"google_news_rss": google_news_rss, "ddgs:google": ENGINES["ddgs:google"]}

# ---------- Cache ----------
CACHE_PATH = os.environ.get("SEARCH_CACHE_PATH") or os.path.expanduser("~/.free_search_cache.sqlite3")
CACHE_TTL = 7 * 86400
_tls = threading.local()


def _conn():
    if getattr(_tls, "conn", None) is None:
        try:
            c = sqlite3.connect(CACHE_PATH, timeout=10)
            try:
                c.execute("PRAGMA journal_mode=WAL")
            except sqlite3.OperationalError:
                c.execute("PRAGMA journal_mode=MEMORY")
        except sqlite3.OperationalError:
            tmp = os.path.join("/tmp", "free_search_cache.sqlite3")
            c = sqlite3.connect(tmp, timeout=10)
            try:
                c.execute("PRAGMA journal_mode=WAL")
            except sqlite3.OperationalError:
                c.execute("PRAGMA journal_mode=MEMORY")
        c.execute("CREATE TABLE IF NOT EXISTS results (k TEXT PRIMARY KEY, js TEXT, ts REAL)")
        c.commit()
        _tls.conn = c
    return _tls.conn


def cache_enabled():
    return os.environ.get("SEARCH_CACHE_ENABLED", "1") not in ("0", "false", "no") and not os.environ.get("SEARCH_NO_CACHE")


def cache_key(query, engine, n, egress):
    return hashlib_sha(f"{query}|{engine}|{n}|{egress}")


def hashlib_sha(s):
    import hashlib
    return hashlib.sha1(s.encode()).hexdigest()


def cache_get(k):
    if not cache_enabled():
        return None
    try:
        row = _conn().execute("SELECT js, ts FROM results WHERE k=?", (k,)).fetchone()
        if row and time.time() - row[1] < CACHE_TTL:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def cache_put(k, js):
    if not cache_enabled():
        return
    try:
        _conn().execute("INSERT OR REPLACE INTO results (k, js, ts) VALUES (?,?,?)", (k, json.dumps(js), time.time()))
        _conn().commit()
    except Exception:
        pass


# ---------- ProxyPool ----------
class ProxyPool:
    SOURCES = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=4000",
    ]

    def __init__(self):
        self.proxies: List[str] = []
        self._idx = 0
        self._lock = threading.Lock()

    def refresh(self, limit=240, want=20, threads=100, timeout=3.5):
        cands = []
        for src in self.SOURCES:
            try:
                txt = fetch(src, timeout=8)
                cands += [l.strip() for l in txt.splitlines() if l.strip() and re.match(r"\d+\.\d+\.\d+\.\d+:\d+", l.strip())]
            except Exception:
                pass
        random.shuffle(cands)
        cands = cands[:limit]
        alive: List[str] = []

        def probe(p):
            if len(alive) >= want:
                return
            try:
                r = requests.get("https://www.bing.com/search?q=test&format=rss",
                                 proxies={"http": "http://" + p, "https": "http://" + p}, timeout=timeout)
                if r.status_code == 200 and "<item>" in r.text:
                    alive.append(p)
            except Exception:
                pass

        with cf.ThreadPoolExecutor(threads) as ex:
            for _ in ex.map(probe, cands):
                if len(alive) >= want:
                    break
        with self._lock:
            self.proxies = list(dict.fromkeys(alive))
            self._idx = 0
        return len(self.proxies)

    def get(self):
        with self._lock:
            if not self.proxies:
                return None
            p = self.proxies[self._idx % len(self.proxies)]
            self._idx += 1
            return "http://" + p

    def mark_dead(self, p):
        if not p:
            return
        with self._lock:
            self.proxies = [x for x in self.proxies if x != p]

    def __len__(self):
        return len(self.proxies)


POOL = ProxyPool()


# ---------- FreeSearch ----------
ORDER = ["bing_rss", "ddgs:google", "google_html", "bing_html", "ddgs:duckduckgo", "startpage_html", "yahoo_html", "ddgs:brave", "brave_html", "ddgs:bing", "ddgs:yahoo"]


class FreeSearch:
    def __init__(self, order=None, pool=None):
        self.order = order or list(ORDER)
        self.health: Dict[str, str] = {}
        self.counters: Dict[str, int] = {}
        self.pool = pool or POOL

    def _run_engine(self, name, query, n, egress="direct"):
        fn = ENGINES.get(name)
        if not fn:
            return []
        if egress == "proxy" and self.pool is not None:
            p = self.pool.get()
            if not p:
                raise RuntimeError("no-proxy")
            old = requests.get
            try:
                def patched(url, *a, **kw):
                    kw["proxies"] = {"http": p, "https": p}
                    return old(url, *a, **kw)
                requests.get = patched
                hits = fn(query, n)
            finally:
                requests.get = old
        else:
            hits = fn(query, n)
        return hits

    def _try(self, name, query, n, egress, min_rel, terms):
        t0 = time.time()
        try:
            hits = self._run_engine(name, query, n, egress)
        except Exception as e:
            self.health[name] = "wall" if "wall" in str(e) else "down"
            return None, {name: str(e)[:80]}, egress
        hits = [h for h in hits if h.url and not is_junk(h.url)]
        dicts = [h.to_dict() for h in hits[:n]]
        elapsed = int((time.time() - t0) * 1000)
        if not dicts:
            self.health[name] = self.health.get(name, "nores")
            return None, {name: "no-results"}, egress
        rel = relevance_score(dicts, query)
        if rel < min_rel and not terms.get("allow_low"):
            return None, {name: f"low-rel-{rel:.2f}"}, egress
        self.health[name] = "ok"
        for i, h in enumerate(dicts, 1):
            h["rank"] = i
            h["source"] = name
        self.counters[name] = self.counters.get(name, 0) + 1
        return dicts, None, elapsed

    def search_outcome(self, query, n=10, engine=None, egress_hint=None, allow_low=False, use_cache=True, waves=None):
        t0 = time.time()
        ck = cache_key(query, engine or "auto", n, egress_hint or "auto")
        if use_cache:
            cached = cache_get(ck)
            if cached:
                out = SearchOutcome(query=query)
                out.results = [Hit(**{k: v for k, v in r.items() if k in ("title", "url", "snippet", "source", "rank")}) for r in cached.get("results", [])]
                out.engine = cached.get("engine", ""); out.from_cache = True
                out.elapsed_ms = int((time.time() - t0) * 1000)
                return out
        errors: Dict[str, str] = {}
        deferred = []
        cand = [engine] if engine else list(self.order)
        backoff = None
        best = None
        waves = waves or [4, 4, 3, 1]
        start = 0
        done = False
        egress = "direct"
        for wnum, wsize in enumerate(waves):
            if start >= len(cand):
                break
            wave = cand[start:start + wsize]; start += wsize
            if wnum >= 2 and self.pool and self.pool.__len__() > 0:
                egress = "proxy"
                if backoff:
                    time.sleep(backoff);
                backoff = 1.5 * (wnum - 1)
            with cf.ThreadPoolExecutor(min(len(wave), 6)) as ex:
                futs = {ex.submit(self._try, name, query, n, egress, 0.25 if wnum < 2 else 0.0, {"allow_low": wnum >= 2}): name for name in wave}
                for f in cf.as_completed(futs):
                    dicts, err, el = f.result()
                    if err:
                        errors.update(err)
                        continue
                    out = SearchOutcome(query=query, engine=futs[f], egress=egress, errors=errors, elapsed_ms=int((time.time() - t0) * 1000))
                    out.results = [Hit(**{k: v for k, v in d.items() if k in ("title", "url", "snippet", "source", "rank")}) for d in dicts]
                    out.elapsed_ms = int((time.time() - t0) * 1000)
                    if use_cache:
                        cache_put(ck, {"engine": out.engine, "results": dicts})
                    return out
            deferred = cand[start:]
        if not best:
            for name in cand:
                dicts, err, el = self._try(name, query, n, "direct", 0.0, {"allow_low": True})
                if dicts:
                    out = SearchOutcome(query=query, engine=name, egress="direct", errors=errors, deferred=deferred)
                    out.results = [Hit(**{k: v for k, v in d.items() if k in ("title", "url", "snippet", "source", "rank")}) for d in dicts]
                    out.elapsed_ms = int((time.time() - t0) * 1000)
                    if use_cache:
                        cache_put(ck, {"engine": name, "results": dicts})
                    return out
                errors.update(err or {})
        out = SearchOutcome(query=query, errors=errors, deferred=deferred)
        out.elapsed_ms = int((time.time() - t0) * 1000)
        return out

    def search(self, query, n=10, **kw):
        return self.search_outcome(query, n=n, **kw).results

    def news(self, query, n=10):
        t0 = time.time()
        for name, fn in NEWS_ENGINES.items():
            try:
                hits = fn(query, n)
                if hits:
                    out = SearchOutcome(query=query, engine=name)
                    out.results = hits
                    out.elapsed_ms = int((time.time() - t0) * 1000)
                    return out
            except Exception as e:
                pass
        return SearchOutcome(query=query, elapsed_ms=int((time.time() - t0) * 1000))


CLIENT = FreeSearch()


def search(query, n=10, **kw):
    return CLIENT.search(query, n=n, **kw)


def google_search(query, n=10, **kw):
    return CLIENT.search_outcome(query, n=n, engine="google_html", **kw).results


def search_outcome(query, n=10, **kw):
    return CLIENT.search_outcome(query, n=n, **kw)


def news(query, n=10):
    return CLIENT.news(query, n=n)


# ---------- CLI ----------
def main(argv=None):
    ap = argparse.ArgumentParser(prog="free_search", description="Free keyless web search v" + __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ps = sub.add_parser("search"); ps.add_argument("query", nargs="+"); ps.add_argument("-n", type=int, default=10); ps.add_argument("--google", action="store_true"); ps.add_argument("--engine"); ps.add_argument("--no-cache", action="store_true"); ps.add_argument("--json", action="store_true"); ps.add_argument("-o", "--out")
    pb = sub.add_parser("batch"); pb.add_argument("file"); pb.add_argument("-j", type=int, default=3); pb.add_argument("-n", type=int, default=10); pb.add_argument("--json", dest="json_out")
    pn = sub.add_parser("news"); pn.add_argument("query", nargs="+"); pn.add_argument("-n", type=int, default=10); pn.add_argument("--json", action="store_true")
    sub.add_parser("selftest")
    pp = sub.add_parser("proxies"); pp.add_argument("--refresh", action="store_true"); pp.add_argument("--google", action="store_true")
    sub.add_parser("serve");
    sub.add_parser("stats")
    args = ap.parse_args(argv)
    if args.cmd == "search":
        q = " ".join(args.query)
        egress = None
        if args.no_cache:
            os.environ["SEARCH_CACHE_ENABLED"] = "0"
        out = CLIENT.search_outcome(q, n=args.n, engine=(args.engine or ("google_html" if args.google else None)), use_cache=not args.no_cache)
        if args.json or args.out:
            js = json.dumps(out.to_dict(), indent=2)
            if args.out:
                open(args.out, "w").write(js)
            else:
                print(js)
        else:
            print(f"engine={out.engine} egress={out.egress} cache={out.from_cache} elapsed_ms={out.elapsed_ms} count={len(out.results)}")
            for h in out.results:
                print(f"  {h.rank}. {h.title[:90]}\n     {h.url}")
        if not out.results:
            print("errors:", out.errors, file=sys.stderr)
    elif args.cmd == "batch":
        qs = [l.strip() for l in open(args.file) if l.strip() and not l.startswith("#")]
        res = []
        with cf.ThreadPoolExecutor(args.j) as ex:
            outs = list(ex.map(lambda q: CLIENT.search_outcome(q, n=args.n), qs))
        for q, o in zip(qs, outs):
            o.query = q
            res.append(o.to_dict())
            print(f"{len(o.results)}/{o.engine or 'NONE'} {o.elapsed_ms}ms  {q}")
        if args.json_out:
            json.dump(res, open(args.json_out, "w"), indent=2)
            print("wrote", args.json_out)
        served = sum(1 for o in outs if o.results)
        print(f"served {served}/{len(qs)}")
    elif args.cmd == "news":
        q = " ".join(args.query)
        out = CLIENT.news(q, n=args.n)
        print(f"engine={out.engine} elapsed_ms={out.elapsed_ms} count={len(out.results)}")
        for h in out.results:
            print(f"  - {h.title[:100]}\n    {h.url}")
    elif args.cmd == "selftest":
        names = ["bing_rss", "google_html", "bing_html", "startpage_html", "yahoo_html", "brave_html", "ddgs:google", "ddgs:duckduckgo", "ddgs:brave", "ddgs:bing", "ddgs:yahoo"]
        egresses = ["direct", "proxy"]
        print(f"{'engine':<18}" + "".join(f"{e:>12}" for e in egresses))
        for name in names:
            row = f"{name:<18}"
            for eg in egresses:
                cand = [eg] if eg == "direct" else ["proxy"]
                try:
                    hits = CLIENT._run_engine(name, "python programming", 5, eg if eg == "proxy" else "direct")
                    if not hits:
                        row += f"{'NORES':>12}"
                    else:
                        row += f"{('OK:' + str(len(hits))):>12}"
                except Exception as e:
                    msg = str(e)
                    st = "WALL" if "wall" in msg else ("NOPROXY" if "no-proxy" in msg else "DOWN")
                    row += f"{st:>12}"
            print(row)
    elif args.cmd == "proxies":
        if args.refresh or not len(POOL):
            print("refreshing pool...")
            n_ok = POOL.refresh()
            print(f"alive proxies: {n_ok}")
        else:
            print(f"pool: {len(POOL)} proxies")
        if args.google:
            n_ok = POOL.refresh()
            hits = CLIENT._run_engine("google_html", "openai", 5, "proxy") if n_ok else []
            print(f"google via proxy: {len(hits)} hits")
        for p in POOL.proxies:
            print(" ", p)
    elif args.cmd == "stats":
        print(json.dumps({"health": CLIENT.health, "counters": CLIENT.counters, "proxies": len(POOL)}, indent=2))
    elif args.cmd == "serve":
        from http.server import HTTPServer, BaseHTTPRequestHandler
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                u = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(u.query)
                q = params.get("q", [""])[0]
                if u.path == "/search" and q:
                    o = CLIENT.search_outcome(q, n=10)
                    body = json.dumps(o.to_dict()).encode()
                else:
                    body = b'{"error":"use /search?q=..."}'
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        HTTPServer(("0.0.0.0", 8080), H).serve_forever()


if __name__ == "__main__":
    main()
