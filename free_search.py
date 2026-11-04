#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
free_search.py (v5.4.0 - Honest-Quality Edition)
================================================================
WHAT'S NEW IN V5 (quality - the dumb-results fix):
- relevance() was certifying junk as PERFECT: a hit counted as
      'good' if it contained ANY ONE query word anywhere (substring
      match - 'top' matched 'toppings'). 'Best Buy' scored 1.0 for a
      movies query. It is now mean term-COVERAGE per hit with word
      boundaries + light stemming: off-topic junk scores ~0.1 and is
      rejected by the 0.25 gate; the 'relevance' field in --json is
      now a trustworthy quality signal.
- RECENCY ROUTING: queries carrying 'this week' / 'now playing' /
      'new releases' / 'just released' etc now send the news engines
      (google_news_rss, bing_news) to the FRONT of the race instead
      of answering from static encyclopedic pages.
- CONDENSED RETRY: 10+ word keyword-stuffed queries make bing answer
      with random garbage. After such a failed wave, the top engines
      refire once with a 6-salient-term version of the query (years
      first, then proper nouns, then the rest) - never a 1-2 word
      shadow. Logged in errors as 'condensed retry: ...'.

WHAT'S NEW IN V4 (datacenter-proofing; live-researched on a heavily
walled datacenter ASN where google=429, startpage=captcha, brave=429,
google_cse=403 and the whole searxng pool is rate-limited):
- RELAY EGRESS IS NOW DEFAULT: free CORS relays fetch from THEIR ip,
      which is the only way through an ASN-level wall. Two relay
      candidates also ride inside the initial race. SEARCH_USE_RELAY=0
      restores the old direct+proxy chain; SEARCH_RELAYS overrides the
      relay list. Dead relays dropped (corsproxy went key-walled 401).
- NEVER-EMPTY BY DEFAULT: SEARCH_ALLOW_LOW_QUALITY now defaults ON.
      When every engine that answers is off-topic (geo-poisoned junk
      etc), the best REAL result set is returned flagged low_quality
      instead of an empty list. Empty only when the network is dead.
- NEW ENGINE wikipedia_api: Wikimedia REST search. Live-researched:
      browser UAs get 403'd by Wikimedia robot policy; a descriptive
      UA passes in ~0.5s. CDN-backed, walls almost nobody - the
      last-resort layer that keeps informational queries non-empty.
- curl_cffi chrome TLS impersonation engages automatically when
      installed (pip install curl_cffi). Measured on this sandbox: it
      does NOT beat an ASN-level google 429, but it does fix JA3-based
      walls on many other clouds.

WHAT'S NEW IN V3 (all v2 features kept; new routing core):
- ONE full-parallel race: v2 fired engines 4 at a time and waited for
  each wave to fully fail before firing the next. Profiled live on a
  walled datacenter IP: 7.98s for a query a healthy engine answered in
  <1s (wave-1: google 429 / startpage captcha / cse 403 / yahoo miss).
  v3 races ALL healthy direct engines at once (SEARCH_PARALLEL_WIDTH,
  default 12) and returns the first that passes relevance.
- HARD PER-QUERY DEADLINE: SEARCH_DEADLINE (default 3.0s) caps every
  engine, relay, proxy and searxng call by the time left. The answer,
  or a labeled best-effort fallback, always lands under it.
  CLI: --deadline 5 ; API: FreeSearch(deadline=5) / search(deadline=...)
- Free-proxy pool preloads in the background at client construction, so
  a walled direct tier escalates to proxies with zero harvest wait.
- searxng instance discovery warms in the background instead of blocking
  the first query that touches the searxng engine.
UNMETERED, zero-key, high-speed web search (with a dedicated Google Search
fleet) built specifically to survive on Cloud Datacenter IPs (AWS, GCP, Azure,
Oracle, Hetzner, DigitalOcean, GitHub Actions, Docker/K8s) as well as local
machines.

WHY V1 FAILED ON CLOUD DATACENTER IPs (AND HOW V2 FIXES IT)
-----------------------------------------------------------
1. ZERO `ddgs` DEPENDENCY REQUIRED:
   In v1, if `ddgs` wasn't installed in the cloud container, 11 engines
   silently skipped, leaving only `bing_html` (which serves JS challenges or
   geo-poisoned SERPs to AWS/GCP datacenter IPs) and `ddg_html` (which throws
   HTTP 202/403 anomaly walls to datacenter IPs).
   -> v2 ships native, zero-dependency HTML/JSON/RSS adapters for Google,
      Startpage (Google syndication), Brave, Yahoo, Bing, DuckDuckGo, SearXNG,
      Google News RSS, and Headless Chrome/Edge CDP Google Search. Every one of
      them works with ONLY `requests` + Python stdlib!

2. DEDICATED GOOGLE SEARCH FLEET (`--google` / `google_search()`):
   Bare `requests.get("https://www.google.com/search")` from a datacenter IP
   gets hit with Google's `/sorry/index` CAPTCHA or JS shell because Google
   checks (a) TLS JA3/JA4 fingerprint, (b) `SOCS`/`CONSENT` cookies, and
   (c) datacenter ASN reputation. v2 attacks this with 6 independent free
   Google layers:
     * `google_html`     Direct Google Web Search (`udm=14` clean web filter +
                         `gbv=1` / full desktop DOM parsers + `SOCS` cookie
                         bypass + `curl_cffi` Chrome TLS impersonation if
                         installed, or rotating Google-validated proxies)
     * `startpage_html`  Startpage.com POST search -> syndicates 100% genuine
                         Google Web Search results privately and works from
                         cloud datacenter IPs without Google CAPTCHAs!
     * `google_cse`      Google Programmable Search Engine (`cse.google.com`)
                         JSONP token harvester -> queries Google's official
                         internal `cse/element/v1` API keyless!
     * `google_cdp`      Local headless Chrome/Edge/Chromium DevTools Protocol
                         (CDP) runner with stealth flags -> genuine browser TLS
                         & JS execution for Google SERPs.
     * `google_news_rss` `news.google.com/rss/search` -> never blocked on
                         datacenter IPs, decodes real article links & titles.
     * `ddgs:google`     Uses `ddgs` Google backend if installed.

3. PARALLEL HEDGED RACING (`race=True` by default, ~300-800ms latency):
   Sequential failover is slow on cloud IPs because 2 walled engines x 15s
   timeout = 30s wasted before hitting a working engine.
   -> v2 fires the top `race_width` (default 4) healthy engines CONCURRENTLY
      in a hedged thread race and returns the FIRST engine that delivers
      high-relevance results! Average latency drops from 10-30s to ~400-900ms.

4. FAST-FIRST EGRESS + GOOGLE-VALIDATED FREE PROXY POOL:
   In v1, the router tried `engine1/direct` -> `engine1/proxy` (blocking 60s+
   to harvest 70,000 dead public proxies) before trying `engine2/direct`.
   -> v2 tries ALL fast `direct` engines first, and when proxies are needed
      (e.g. for `google_html` on a blocked datacenter IP), `ProxyPool` harvests
      and validates proxies with a tight 3.0s fuse specifically against Google
      & Bing, stopping as soon as 15 fast proxies respond (~2.5s total).

5. CLOUD CONTAINER / FUSE / NFS SQLITE SAFETY:
   Automatically falls back from `PRAGMA journal_mode=WAL` to `MEMORY` or
   `/tmp` when `$HOME` is mounted on a cloud FUSE/NFS volume without POSIX
   lock support.

CLI
---
  python3 free_search.py search "openai sam altman" -n 10
  python3 free_search.py search "python asyncio" --google -n 10 --json
  python3 free_search.py selftest
  python3 free_search.py batch queries.txt -j 12 --retry --json out.json
  python3 free_search.py proxies --refresh --google
  python3 free_search.py serve --port 8078

PYTHON API
----------
  from free_search import search, google_search, search_many, FreeSearch
  hits  = google_search("kubernetes ingress controller", max_results=10)
  hits2 = search("rust vs go performance", max_results=10)
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html as htmllib
import json
import logging
import os
import random
import re
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, as_completed, wait
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import requests
except ImportError:  # pragma: no cover
    sys.stderr.write("free_search: 'requests' is required -> pip install requests\n")
    raise

try:
    from curl_cffi import requests as curl_requests  # Chrome TLS JA3/JA4 impersonation
    HAVE_CURL_CFFI = True
except Exception:
    curl_requests = None
    HAVE_CURL_CFFI = False

try:
    from ddgs import DDGS
    HAVE_DDGS = True
except Exception:
    try:
        from duckduckgo_search import DDGS
        HAVE_DDGS = True
    except Exception:
        DDGS = None
        HAVE_DDGS = False

logger = logging.getLogger("free-search")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "5.4.0"

USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
)
BROWSER_UA = USER_AGENTS[0]
LYNX_UA = "Lynx/2.9.0dev.10 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/3.7.9"

BROWSER_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Google consent bypass cookie so EU/datacenter IPs never get redirected to consent.google.com
GOOGLE_CONSENT_COOKIE = (
    "CONSENT=YES+cb.20230531-04-p0.en+FX+908; "
    "SOCS=CAISHAgBEhJnd3NfMjAyNDA1MTUtMF9SQzIaAmVuIAEaBgiAo_CmBg"
)

BING_PRIMARY = "www.bing.com"
BING_MIRRORS = (
    "www.bing.com", "ca.bing.com", "au.bing.com", "in.bing.com",
    "de.bing.com", "fr.bing.com", "jp.bing.com", "br.bing.com", "uk.bing.com",
)
BING_LOCALE_COOKIE = (
    "_EDGE_CD=m=en-us&u=en-us; "
    "SRCHHPGUSR=SRCHLANG=en&NRSLT=50&NEWWND=1&AS=1; "
    "_EDGE_S=mkt=en-us&ui=en-us"
)

WALL_CODES = (999, 429, 403, 401, 418, 503, 520, 521, 522, 530)
WALL_MARKERS = (
    "captcha", "unusual traffic", "not a robot", "are you a robot",
    "enable javascript and try again", "access denied", "just a moment",
    "checking your browser", "anomaly", "please verify you are a human",
    "system has detected unusual", "/sorry/index", "g-recaptcha",
    "detected unusual traffic from your computer network",
)

JUNK_URL_MARKERS = (
    "bing.com/ck/a", "bing.com/aclick", "bing.com/news/apiclick",
    "google.com/url?", "googleadservices", "googleusercontent.com/proxy",
    "google.com/search?", "google.com/preferences", "accounts.google.com",
    "policies.google.com", "support.google.com/websearch", "maps.google.com",
    "5xx-error-landing", "cloudflare.com/cdn-cgi", "duckduckgo.com/l/?",
    "developers.cloudflare.com/support", "cloudflarestatus.com",
    "support.cloudflare.com", "/search?q=", "javascript:void",
    "support.microsoft.com", "go.microsoft.com/fwlink",
    "microsoft.com/en-us/bing", "duckduckgo.com/y.js",
    "bing.com/AS/Suggestions", "w3.org/", "schema.org",
    "creativecommons.org", "facebook.com/sharer", "twitter.com/intent",
    "linkedin.com/shareArticle", "startpage.com/do/", "startpage.com/sp/",
    "search.yahoo.com/search", "r.search.yahoo.com", "help.yahoo.com",
)

# Public Programmable Search Engine (CSE) CX IDs configured to search the entire web
PUBLIC_GOOGLE_CSE_CX_IDS = (
    "017576662512468239146:omuauf_lfve",
    "005083051908638260058:2s12ef5353m",
    "65b6c5c28e88e4376",
    "009683796281918685199:itys5a6575a",
)

DEFAULT_PROXY_SOURCES = (
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http"
    "&timeout=4000&country=all&anonymity=elite",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/http_proxies.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/all.txt",
)

DEFAULT_RELAYS = (
    # v4: corsproxy dropped (key-walled 401 since 2026); cors.lol and
    # workers.dev are 429; jina is 401. allorigins + codetabs are the
    # surviving free tier (5-8s class - raise --deadline on fully
    # walled IPs). SEARCH_RELAYS env overrides this list.
    ("allorigins", "https://api.allorigins.win/raw?url={url}"),
    ("codetabs", "https://api.codetabs.com/v1/proxy?quest={url}"),
)

SEARX_SPACE = "https://searx.space/data/instances.json"

KEY_ENVS = {
    "tavily": "TAVILY_API_KEY",
    "brave_api": "BRAVE_API_KEY",
    "serper": "SERPER_API_KEY",
    "exa": "EXA_API_KEY",
    "bing_api": "BING_SEARCH_API_KEY",
    "jina": "JINA_API_KEY",
    "serpapi": "SERPAPI_API_KEY",
    "mojeek_api": "MOJEEK_API_KEY",
    "google_custom_api": "GOOGLE_CSE_API_KEY",
}

_PROXY_LINE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$")
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def is_junk_url(u: str) -> bool:
    if not u or not u.lower().startswith(("http://", "https://")):
        return True
    low = u.lower()
    if any(m in low for m in JUNK_URL_MARKERS):
        return True
    host = (urllib.parse.urlparse(low).netloc or "")
    if host in (
        "www.bing.com", "bing.com", "www.google.com", "google.com",
        "duckduckgo.com", "html.duckduckgo.com", "www.startpage.com",
        "startpage.com", "search.brave.com", "www.mojeek.com", "yandex.com",
        "www.qwant.com", "www.ecosia.org", "search.yahoo.com",
    ):
        return True
    return False


# ---------------------------------------------------------------------------
# Exceptions & Data Classes
# ---------------------------------------------------------------------------

class SearchError(Exception):
    """Base class."""


class BotWalled(SearchError):
    """Egress IP was blocked / throttled -> escalate egress tier."""


class EngineDown(SearchError):
    """Engine itself is broken (parse change, DNS, 5xx) -> next engine."""


class EgressRetry(SearchError):
    """This particular proxy/relay died -> retry same engine with a new proxy."""


class AllEnginesFailed(SearchError):
    """Every engine x egress combination failed for this query."""


@dataclass
class Hit:
    """One normalised search result."""
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "href": self.url,
            "link": self.url,
            "snippet": self.snippet,
            "body": self.snippet,
            "content": self.snippet,
            "source": self.source,
            "engine": self.source,
            "rank": self.rank,
            "position": self.rank,
        }


@dataclass
class SearchOutcome:
    """Result of one logical search, with full provenance for debugging."""
    query: str
    results: List[Hit] = field(default_factory=list)
    engine: str = ""
    egress: str = "direct"
    proxy: str = ""
    from_cache: bool = False
    deferred: bool = False
    relevance: float = 1.0
    low_quality: bool = False
    attempts: int = 0
    elapsed_ms: int = 0
    errors: List[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.results)

    def __bool__(self) -> bool:
        return bool(self.results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [h.to_dict() for h in self.results],
            "organic_results": [h.to_dict() for h in self.results],
            "engine": self.engine,
            "egress": self.egress,
            "proxy": self.proxy,
            "from_cache": self.from_cache,
            "deferred": self.deferred,
            "relevance": round(self.relevance, 3),
            "low_quality": self.low_quality,
            "attempts": self.attempts,
            "elapsed_ms": self.elapsed_ms,
            "errors": self.errors[-8:],
        }


# ---------------------------------------------------------------------------
# Env & Text / URL Decoding Utilities
# ---------------------------------------------------------------------------

def _env_int(name: str, default: int) -> int:
    try:
        v = os.getenv(name, "").strip()
        return int(v) if v else int(default)
    except (TypeError, ValueError):
        return int(default)


def _env_float(name: str, default: float) -> float:
    try:
        v = os.getenv(name, "").strip()
        return float(v) if v else float(default)
    except (TypeError, ValueError):
        return float(default)


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on", "y")


def _env_list(name: str, default: Sequence[str]) -> List[str]:
    v = os.getenv(name, "").strip()
    if not v:
        return list(default)
    return [x.strip() for x in re.split(r"[,\s]+", v) if x.strip()]


def strip_tags(s: str) -> str:
    s = htmllib.unescape(s or "")
    s = _TAG.sub(" ", s)
    return _WS.sub(" ", s).strip()


def decode_google_url(href: str) -> str:
    """Unwrap Google `/url?q=<real>&sa=...` or `/url?url=<real>` wrappers."""
    if not href:
        return ""
    h = htmllib.unescape(href.strip())
    if h.startswith("/url?") or "google.com/url?" in h:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(h).query)
        for k in ("q", "url", "adurl"):
            if qs.get(k):
                cand = qs[k][0].strip()
                if cand.startswith(("http://", "https://")):
                    return cand
    return h


def decode_yahoo_ru(href: str) -> str:
    """Unwrap Yahoo redirect `.../RU=<url-encoded>/RK=...` links."""
    if not href:
        return ""
    h = htmllib.unescape(href.strip())
    m = re.search(r"/RU=([^/]+)/RK=", h)
    if m:
        try:
            return urllib.parse.unquote(m.group(1))
        except Exception:
            pass
    return h


def decode_bing_ck(href: str) -> str:
    if not href:
        return href
    h = htmllib.unescape(href)
    if "/ck/a" not in h:
        return h
    m = re.search(r"[?&]u=a1([^&]+)", h)
    if not m:
        return h
    s = m.group(1).replace("-", "+").replace("_", "/")
    s += "=" * (-len(s) % 4)
    try:
        out = base64.b64decode(s).decode("utf-8", "ignore").strip()
        return out or h
    except Exception:
        return h


def decode_bing_redirect(u: str) -> str:
    if not u:
        return u
    h = htmllib.unescape(u)
    m = re.search(r"[?&]url=([^&]+)", h)
    if m:
        try:
            cand = urllib.parse.unquote(m.group(1))
            if cand.startswith("http"):
                return cand
        except Exception:
            pass
    return decode_bing_ck(h)


def decode_ddg_l(href: str) -> str:
    if not href:
        return href
    h = htmllib.unescape(href)
    if h.startswith("//"):
        h = "https:" + h
    m = re.search(r"[?&]uddg=([^&]+)", h)
    if m:
        try:
            return urllib.parse.unquote(m.group(1))
        except Exception:
            return h
    return h


def canon_url(u: str) -> str:
    if not u:
        return ""
    try:
        p = urllib.parse.urlparse(u)
        host = (p.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        path = p.path or "/"
        if path.endswith("/") and path != "/":
            path = path.rstrip("/")
        return f"{p.scheme}://{host}{path}" + (f"?{p.query}" if p.query else "")
    except Exception:
        return u.lower()


def looks_walled(status: int, body: str) -> bool:
    if status in WALL_CODES:
        return True
    low = (body or "")[:20000].lower()
    if not low:
        return False
    if "/sorry/index" in low or "detected unusual traffic" in low or "g-recaptcha" in low:
        return True
    if any(m in low for m in WALL_MARKERS):
        if not re.search(r'(class="[^"]*result|<h2|<h3|<li class="b_algo"|result__a)', low):
            return True
    return False


# ---------------------------------------------------------------------------
# Result-Quality & Lexical Relevance Gate
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset("""
a an the and or but if then than that this these those of in on at to for from
by with without within into onto over under again further once here there when
where why how all any both each few more most other some such no nor not only
own same so too very can will just should now is are was were be been being do
does did doing have has had having i you he she it we they them his her its our
their your my me him us what which who whom latest news page pages
""".split())


def query_terms(query: str) -> set:
    toks = re.findall(r"[a-z0-9][a-z0-9'\-\.]{1,}", (query or "").lower())
    out = {t for t in toks if t not in _STOPWORDS and len(t) >= 3}
    out |= {t for t in toks if len(t) <= 2 and t.isalpha() and t not in ("a", "i", "an")}
    return out


def _term_variants(t: str) -> List[str]:
    """v5: match forms of t in result blobs. Word-boundary regex keeps
    'top' from matching 'toppings'; light stemming lets 'movies' match
    'movie', 'playing' match 'play', 'critically' match 'critical'."""
    v = {t}
    if len(t) > 4 and t.endswith("ies"):
        v.add(t[:-3] + "y")
    if len(t) > 4 and t.endswith("es"):
        v.add(t[:-2])
    if len(t) > 4 and t.endswith("s"):
        v.add(t[:-1])
    if len(t) > 5 and t.endswith("ing"):
        v.add(t[:-3])
    if len(t) > 5 and t.endswith("ly"):
        v.add(t[:-2])
    v.add(t + "s")
    return [x for x in v if len(x) >= 3 and x.isalnum()]


def relevance(query: str, hits: Sequence[Hit]) -> float:
    """v5: HONEST quality score. Each hit is scored by the fraction of
    the query's significant terms it actually covers (word-boundary
    match, light stemming); the set's score is the mean. The old version
    counted a hit as 'good' when it contained ANY ONE query word -
    'Best Buy' scored 1.0 (perfect) for a movies query. Now such junk
    scores ~0.1 and is rejected by the min-relevance gate."""
    if not hits:
        return 0.0
    terms = query_terms(query)
    if not terms:
        return 1.0
    rx = {}
    for t in terms:
        rx[t] = [re.compile(r"\b%s\b" % re.escape(var)) for var in _term_variants(t)]
    total = 0.0
    for h in hits:
        blob = " ".join((h.title or "", h.url or "", h.snippet or "")).lower()
        blob = urllib.parse.unquote(blob)
        cov = sum(1 for t in terms if any(p.search(blob) for p in rx[t]))
        total += cov / len(terms)
    return total / len(hits)


# ---------------------------------------------------------------------------
# Cloud-Safe SQLite Result Cache
# ---------------------------------------------------------------------------

class ResultCache:
    """Thread-safe persistent SQLite cache with automatic cloud FUSE/NFS fallback."""

    def __init__(self, path: Optional[str] = None, ttl: Optional[int] = None):
        self.path = path if path is not None else os.getenv(
            "SEARCH_CACHE_DB",
            os.path.join(os.path.expanduser("~"), ".free_search_cache.sqlite3"),
        )
        self.ttl = ttl if ttl is not None else _env_int("SEARCH_CACHE_TTL", 7 * 86400)
        self.enabled = _env_bool("SEARCH_CACHE_ENABLED", True) and self.ttl > 0
        self._lock = threading.Lock()
        self._local = threading.local()
        self.hits = 0
        self.misses = 0
        if self.enabled:
            self._init_db()

    def _open_sqlite(self, db_path: str) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        c = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
        try:
            c.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            c.execute("PRAGMA journal_mode=MEMORY")
        c.execute("PRAGMA synchronous=NORMAL")
        return c

    def _conn(self) -> sqlite3.Connection:
        c = getattr(self._local, "conn", None)
        if c is None:
            try:
                c = self._open_sqlite(self.path)
            except sqlite3.OperationalError:
                self.path = os.path.join(tempfile.gettempdir(), ".free_search_cache.sqlite3")
                c = self._open_sqlite(self.path)
            self._local.conn = c
        return c

    def _init_db(self) -> None:
        schema = (
            "CREATE TABLE IF NOT EXISTS cache("
            "  k TEXT PRIMARY KEY, v TEXT NOT NULL, ts REAL NOT NULL,"
            "  engine TEXT, n INTEGER);"
            "CREATE INDEX IF NOT EXISTS cache_ts ON cache(ts);"
        )
        with self._lock:
            try:
                self._conn().executescript(schema)
                self._conn().commit()
            except sqlite3.OperationalError:
                self._local.conn = None
                self.path = os.path.join(tempfile.gettempdir(), ".free_search_cache.sqlite3")
                self._conn().executescript(schema)
                self._conn().commit()

    @staticmethod
    def key(query: str, engine: str, n: int, region: str, timelimit: str) -> str:
        raw = json.dumps(
            [query.strip().lower(), engine, int(n), region, timelimit or "", VERSION],
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]

    def get(self, k: str) -> Optional[List[Dict[str, Any]]]:
        if not self.enabled:
            return None
        try:
            with self._lock:
                row = self._conn().execute(
                    "SELECT v, ts FROM cache WHERE k=?", (k,)
                ).fetchone()
            if not row:
                self.misses += 1
                return None
            if (time.time() - row[1]) > self.ttl:
                self.misses += 1
                return None
            self.hits += 1
            return json.loads(row[0])
        except Exception:
            self.misses += 1
            return None

    def delete(self, k: str) -> None:
        """v5.1: drop a stale row so it is never served again."""
        if not self.enabled:
            return
        try:
            with self._lock:
                self._conn().execute("DELETE FROM cache WHERE k = ?", (k,))
        except sqlite3.Error:
            pass

    def put(self, k: str, results: List[Dict[str, Any]], engine: str) -> None:
        if not self.enabled or not results:
            return
        try:
            with self._lock:
                self._conn().execute(
                    "INSERT OR REPLACE INTO cache(k,v,ts,engine,n) VALUES(?,?,?,?,?)",
                    (k, json.dumps(results, ensure_ascii=False), time.time(), engine, len(results)),
                )
                self._conn().commit()
        except Exception:
            pass

    def prune(self) -> int:
        if not self.enabled:
            return 0
        with self._lock:
            cur = self._conn().execute(
                "DELETE FROM cache WHERE ts < ?", (time.time() - self.ttl,)
            )
            self._conn().commit()
            return cur.rowcount or 0

    def size(self) -> int:
        try:
            with self._lock:
                return self._conn().execute("SELECT COUNT(*) FROM cache").fetchone()[0]
        except Exception:
            return 0


# ---------------------------------------------------------------------------
# Egress Tier 2: Fast Bounded Proxy Pool (with Google Validation Mode)
# ---------------------------------------------------------------------------

def _daemon_map(fn, items, workers=8, max_seconds=20.0):
    """v4: run fn over items on DAEMON threads. concurrent.futures pools
    spawn NON-daemon workers, so background warm/probe/validate pools were
    joining the CLI exit for their whole timeout budget (measured +3.5-8s
    per cold run). Daemon workers die with the process instead. Returns
    {item: result}; items still pending at max_seconds are dropped."""
    import queue as _queue
    items = list(items or [])
    if not items:
        return {}
    q = _queue.Queue()
    for it in items:
        q.put(it)
    out = {}
    lock = threading.Lock()

    def _work():
        while True:
            try:
                it = q.get_nowait()
            except _queue.Empty:
                return
            try:
                r = fn(it)
            except Exception:
                r = None
            with lock:
                out[it] = r

    n = max(1, min(int(workers), len(items)))
    ts = [threading.Thread(target=_work, daemon=True) for _ in range(n)]
    t0 = time.time()
    for t in ts:
        t.start()
    dl = t0 + max(1.0, float(max_seconds))
    for t in ts:
        t.join(timeout=max(0.0, dl - time.time()))
    return out


class ProxyPool:
    """Fast public HTTP proxy pool with dual validation modes:
    - General search validation (`bing.com/search?format=rss` or `startpage.com`)
    - Google-specific validation (`www.google.com/search?q=test&gbv=1`) so
      proxies that pass Google's IP check are prioritized for `google_html`.
    """

    def __init__(self, probe_url: Optional[str] = None, google_mode: bool = False):
        default_probe = (
            "https://www.google.com/search?q=python&gbv=1&hl=en"
            if google_mode
            else "https://www.bing.com/search?q=test&format=rss"
        )
        self.probe_url = probe_url or os.getenv("PROXY_PROBE_URL", default_probe)
        self.google_mode = google_mode
        self._lock = threading.Lock()
        self._pool: List[str] = []
        self._google_pool: List[str] = []
        self._idx = 0
        self._g_idx = 0
        self._dead: set = set()
        self._builds = 0
        self._last_build = 0.0
        self._validated_at: Dict[str, float] = {}
        self.max_builds = max(1, _env_int("PROXY_MAX_BUILDS_PER_RUN", 6))
        self.pool_max = max(1, _env_int("PROXY_POOL_MAX", 20))
        self.validate_limit = _env_int("PROXY_VALIDATE_LIMIT", 240)
        self.validate_workers = _env_int("PROXY_VALIDATE_WORKERS", 100)
        self.validate_timeout = _env_float("PROXY_VALIDATE_TIMEOUT", 3.5)
        self.state_file = os.getenv(
            "PROXY_STATE_FILE",
            os.path.join(tempfile.gettempdir(), ".free_search_proxies.json"),
        )

    @staticmethod
    def parse_candidates(text: str) -> List[str]:
        out: List[str] = []
        for line in (text or "").splitlines():
            s = line.strip()
            for prefix in ("http://", "https://"):
                if s.lower().startswith(prefix):
                    s = s[len(prefix):]
                    break
            s = s.split()[0] if s else s
            if _PROXY_LINE.match(s):
                try:
                    port = int(s.rsplit(":", 1)[1])
                except ValueError:
                    continue
                if 1 <= port <= 65535:
                    out.append(s)
        return list(dict.fromkeys(out))

    def _sources(self) -> List[str]:
        return _env_list("PROXY_SOURCES", DEFAULT_PROXY_SOURCES)

    def harvest(self, per_source_timeout: int = 5) -> List[str]:
        sources = self._sources()
        found: Dict[str, str] = {}
        hdr = {"User-Agent": BROWSER_UA}

        def _grab(url: str) -> Tuple[str, List[str]]:
            try:
                r = requests.get(url, timeout=per_source_timeout, headers=hdr)
                if r.status_code == 200:
                    return url, self.parse_candidates(r.text)
            except Exception:
                pass
            return url, []

        # v4: daemon pool - a background harvest must never block CLI exit
        for src, cands in _daemon_map(_grab, sources, workers=6).values():
            for c in cands:
                found.setdefault(c, src)
        out = list(found.keys())
        random.shuffle(out)
        logger.debug("proxy candidates harvested: %d unique", len(out))
        return out

    def _try_proxy(self, candidate: str, timeout: Optional[float] = None, probe: Optional[str] = None) -> Optional[float]:
        timeout = timeout or self.validate_timeout
        target = probe or self.probe_url
        purl = f"http://{candidate}"
        try:
            t0 = time.time()
            r = requests.get(
                target,
                proxies={"http": purl, "https": purl},
                timeout=timeout,
                headers={
                    "User-Agent": BROWSER_UA,
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cookie": GOOGLE_CONSENT_COOKIE,
                },
                allow_redirects=True,
            )
            if r.status_code == 200 and (r.text or "").strip():
                if looks_walled(r.status_code, r.text):
                    return None
                return time.time() - t0
        except Exception:
            pass
        return None

    def validate(
        self,
        candidates: Sequence[str],
        limit: Optional[int] = None,
        workers: Optional[int] = None,
        google_only: bool = False,
    ) -> List[Tuple[str, float]]:
        limit = limit or self.validate_limit
        workers = workers or self.validate_workers
        cands = list(candidates)[:limit]
        if not cands:
            return []
        probe = (
            "https://www.google.com/search?q=python&gbv=1&hl=en"
            if (google_only or self.google_mode)
            else self.probe_url
        )
        # v4: daemon pool - its 100 non-daemon workers were joining the CLI
        # exit for the full 3.5s validate timeout on every cold start.
        res = _daemon_map(
            lambda c: self._try_proxy(c, self.validate_timeout, probe),
            cands, workers=min(workers, len(cands)), max_seconds=25.0,
        )
        scored = []
        for c in cands:
            lat = res.get(c)
            if lat is not None:
                if len(scored) >= self.pool_max:
                    break
                scored.append((c, lat))
        scored.sort(key=lambda t: t[1])
        return scored

    def _load_state(self) -> bool:
        max_age = _env_int("PROXY_STATE_MAX_AGE", 1800)
        try:
            with open(self.state_file, "r", encoding="utf-8") as fh:
                st = json.load(fh)
            if time.time() - float(st.get("ts", 0)) > max_age:
                return False
            pool = [p for p in st.get("pool", []) if isinstance(p, str)]
            if not pool:
                return False
            with self._lock:
                self._pool = pool
                self._google_pool = [p for p in st.get("google_pool", []) if isinstance(p, str)]
                self._idx = 0
                self._dead = set()
                self._validated_at = st.get("validated_at", {}) or {}
            return True
        except Exception:
            return False

    def _save_state(self) -> None:
        try:
            with self._lock:
                payload = {
                    "ts": time.time(),
                    "pool": list(self._alive()),
                    "google_pool": [p for p in self._google_pool if p not in self._dead],
                    "validated_at": dict(self._validated_at),
                }
            with open(self.state_file, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
        except Exception:
            pass

    def build(self, force: bool = False, google_only: bool = False) -> bool:
        with self._lock:
            if self._pool and self._alive() and not force:
                return True
            if self._builds >= self.max_builds:
                return False
            if not force and (time.time() - self._last_build) < 15 and self._alive():
                return True
            self._builds += 1
            self._last_build = time.time()
        cands = self.harvest()
        if not cands:
            return False
        scored = self.validate(cands, google_only=google_only)
        pool = [c for c, _ in scored[: self.pool_max]]
        now = time.time()
        with self._lock:
            self._pool = pool
            if google_only or self.google_mode:
                self._google_pool = list(pool)
            self._idx = 0
            self._dead = set()
            for c, _ in scored[: self.pool_max]:
                self._validated_at[c] = now
        if pool:
            self._save_state()
            return True
        return False

    def ensure(self) -> bool:
        if self._load_state():
            return True
        return self.build()

    def _alive(self) -> List[str]:
        return [p for p in self._pool if p not in self._dead]

    def next(self, prefer_google: bool = False) -> Optional[str]:
        with self._lock:
            if prefer_google and self._google_pool:
                for _ in range(len(self._google_pool)):
                    p = self._google_pool[self._g_idx % len(self._google_pool)]
                    self._g_idx += 1
                    if p not in self._dead:
                        return p
            pool = self._pool
            if not pool:
                return None
            for _ in range(len(pool)):
                p = pool[self._idx % len(pool)]
                self._idx += 1
                if p not in self._dead:
                    return p
            return None

    def mark_dead(self, proxy: str) -> None:
        with self._lock:
            self._dead.add(proxy)

    def mark_ok(self, proxy: str, google_ok: bool = False) -> None:
        with self._lock:
            self._dead.discard(proxy)
            self._validated_at[proxy] = time.time()
            if google_ok and proxy not in self._google_pool:
                self._google_pool.insert(0, proxy)

    def alive_count(self) -> int:
        with self._lock:
            return len(self._alive())

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "pool": len(self._pool),
                "alive": len(self._alive()),
                "google_alive": len([p for p in self._google_pool if p not in self._dead]),
                "dead": len(self._dead),
                "builds": self._builds,
            }


# ---------------------------------------------------------------------------
# Engine Health + AIMD Rate Pacing
# ---------------------------------------------------------------------------

@dataclass
class EngineHealth:
    name: str
    ok: int = 0
    fail: int = 0
    walls: int = 0
    results: int = 0
    consecutive_fail: int = 0
    cooldown_until: float = 0.0
    strikes: int = 0
    last_error: str = ""
    total_ms: float = 0.0
    rate: float = 0.0
    base_rate: float = 0.0
    rate_min: float = 0.05
    rate_max: float = 8.0
    rate_inc: float = 0.05
    _bucket: float = field(default=0.0, repr=False)
    _last: float = field(default=0.0, repr=False)

    def __post_init__(self):
        if self.rate and not self.base_rate:
            self.base_rate = self.rate
        self.rate_max = max(self.rate_max, self.base_rate * 4)

    def ready(self) -> bool:
        return time.time() >= self.cooldown_until

    def trip(self, err: str, wall: bool = False) -> None:
        self.fail += 1
        self.consecutive_fail += 1
        self.last_error = err[:200]
        if wall:
            self.walls += 1
        if self.rate > 0:
            self.rate = max(self.rate_min, self.rate * (0.4 if wall else 0.65))
        trip_after = max(1, _env_int("ENGINE_TRIP_AFTER", 3))
        if self.consecutive_fail >= trip_after:
            self.strikes += 1
            base = _env_float("ENGINE_COOLDOWN", 45.0)
            cool = min(base * (2 ** (self.strikes - 1)), _env_float("ENGINE_COOLDOWN_MAX", 1200.0))
            self.cooldown_until = time.time() + cool
            self.consecutive_fail = 0

    def note_ok(self, n: int, ms: float) -> None:
        self.ok += 1
        self.results += n
        self.total_ms += ms
        self.consecutive_fail = 0
        if self.strikes and self.ok % 4 == 0:
            self.strikes = max(0, self.strikes - 1)
            self.cooldown_until = min(self.cooldown_until, time.time())
        if self.rate > 0:
            self.rate = min(self.rate_max, self.rate + self.rate_inc)

    def acquire(self) -> float:
        if self.rate <= 0:
            return 0.0
        now = time.time()
        if self._last == 0.0:
            self._bucket = 1.0
            self._last = now
        self._bucket = min(2.0, self._bucket + (now - self._last) * self.rate)
        self._last = now
        if self._bucket >= 1.0:
            self._bucket -= 1.0
            return 0.0
        wait_s = (1.0 - self._bucket) / self.rate
        time.sleep(wait_s)
        self._bucket = 0.0
        self._last = time.time()
        return wait_s


# ---------------------------------------------------------------------------
# Transport Helpers & Headless Browser CDP Runner
# ---------------------------------------------------------------------------

def _mk_session(
    proxy: Optional[str] = None,
    ua: str = BROWSER_UA,
) -> requests.Session:
    s = requests.Session()
    s.trust_env = False
    if proxy:
        purl = f"http://{proxy}" if "://" not in proxy else proxy
        s.proxies = {"http": purl, "https": purl}
    s.headers.update(BROWSER_HEADERS)
    s.headers["User-Agent"] = ua
    return s


def _apply_relay(url: str, relay: Optional[Tuple[str, str]]) -> str:
    if not relay:
        return url
    return relay[1].format(url=urllib.parse.quote(url, safe=""))


RELAY_ERROR_MARKERS = (
    "5xx-error-landing", "cdn-cgi/challenge-platform",
    "developers.cloudflare.com/support/troubleshooting",
    "attention required! | cloudflare", "just a moment...",
)


def _get(
    url: str,
    sess: requests.Session,
    timeout: float = 10.0,
    relay: Optional[Tuple[str, str]] = None,
    proxy: Optional[str] = None,
    use_curl_cffi: bool = False,
    **kw,
) -> requests.Response:
    final = _apply_relay(url, relay)
    # v4: an ABSOLUTE read deadline. The old formula made the read timeout
    # equal the whole budget (and None meant 'no deadline at all'), so a
    # stalled socket blocked its worker forever (reproduced in selftest:
    # eng_google_html stuck 20s in a socket read). Read is now capped at
    # 5s, or half the budget when that is lower; None becomes 8s.
    if not isinstance(timeout, (int, float)) or timeout is None or timeout <= 0:
        timeout = 8.0
    _read = min(5.0, timeout)
    _conn = min(4.5, timeout * 0.5)
    req_timeout = (_conn, _read)

    # Use curl_cffi with Chrome TLS impersonation if available (critical for Google/Brave on cloud IPs)
    if use_curl_cffi and HAVE_CURL_CFFI and curl_requests is not None and not relay:
        try:
            px = None
            if proxy:
                purl = f"http://{proxy}" if "://" not in proxy else proxy
                px = {"http": purl, "https": purl}
            r_cffi = curl_requests.get(
                final,
                impersonate="chrome124",
                timeout=(_conn, _read),
                proxies=px,
                headers=kw.get("headers") or dict(sess.headers),
                allow_redirects=True,
            )
            if r_cffi.status_code in WALL_CODES or looks_walled(r_cffi.status_code, r_cffi.text):
                raise BotWalled(f"cffi:http:{r_cffi.status_code}")
            return r_cffi  # type: ignore
        except BotWalled:
            raise
        except Exception as e:
            if proxy:
                raise EgressRetry(f"cffi-proxy:{type(e).__name__}") from e

    try:
        r = sess.get(final, timeout=req_timeout, **kw)
    except requests.RequestException as e:
        msg = str(e).lower()
        if proxy and any(k in msg for k in ("proxy", "tunnel", "connect", "timed out", "timeout", "reset")):
            raise EgressRetry(f"proxy-dead:{type(e).__name__}") from e
        if "proxy" in msg or "tunnel" in msg:
            raise BotWalled(f"transport:{type(e).__name__}") from e
        raise EngineDown(f"transport:{type(e).__name__}:{str(e)[:80]}") from e

    if r.status_code in WALL_CODES:
        raise BotWalled(f"http:{r.status_code}")
    if looks_walled(r.status_code, r.text):
        raise BotWalled("softwall:marker")
    if relay:
        low = (r.text or "")[:12000].lower()
        if any(m in low for m in RELAY_ERROR_MARKERS):
            raise BotWalled(f"relay:{relay[0]}:cdn-error-page")
    return r


def _find_chromium_binary() -> Optional[str]:
    env_bin = os.getenv("SEARCH_BROWSER_BIN", "").strip()
    if env_bin and os.path.isfile(env_bin):
        return env_bin
    for name in (
        "chrome", "google-chrome", "google-chrome-stable",
        "msedge", "microsoft-edge", "microsoft-edge-stable",
        "chromium", "chromium-browser", "brave", "brave-browser",
    ):
        p = shutil.which(name)
        if p:
            return p
    if sys.platform.startswith("win"):
        roots = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        for root in roots:
            if not root:
                continue
            for rel in (
                r"Google\Chrome\Application\chrome.exe",
                r"Microsoft\Edge\Application\msedge.exe",
                r"BraveSoftware\Brave-Browser\Application\brave.exe",
            ):
                cand = os.path.join(root, rel)
                if os.path.isfile(cand):
                    return cand
    if sys.platform == "darwin":
        for cand in (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ):
            if os.path.isfile(cand):
                return cand
    return None


# ---------------------------------------------------------------------------
# THE GOOGLE SEARCH FLEET (6 Independent Free Google Adapters)
# ---------------------------------------------------------------------------

def _parse_google_serp_html(body: str, source_name: str, max_n: int) -> List[Hit]:
    """Universal Google SERP HTML parser supporting:
    1. Modern desktop Google DOM (`<div class="g">`, `<div class="MjjYud">`, `<h3>`)
    2. Google Basic / Lite HTML (`gbv=1` / `/url?q=...` blocks)
    """
    hits: List[Hit] = []
    seen: set = set()

    # Pattern 1: Modern desktop Google <a href="https://...">...<h3...>...</h3></a>
    for m in re.finditer(
        r'<a[^>]+href=["\']((?:https?://|/url\?q=https?://)[^"\']+)["\'][^>]*>'
        r'(?:(?!</a>).)*?<h3[^>]*>(.*?)</h3>',
        body,
        re.I | re.S,
    ):
        u = decode_google_url(m.group(1))
        if is_junk_url(u):
            continue
        c = canon_url(u)
        if c in seen:
            continue
        title = strip_tags(m.group(2))
        if not title or len(title) < 3:
            continue
        seen.add(c)
        # Look ahead up to 2200 chars for the snippet container (VwiC3b, yXK7lf, BNeawe, etc.)
        tail = body[m.end() : m.end() + 2400]
        snip = ""
        sm = re.search(
            r'class=["\'][^"\']*(?:VwiC3b|yXK7lf|ITZIwc|s3v9rd|BNeawe\s+s3v9rd)[^"\']*["\'][^>]*>(.*?)</(?:div|span)>',
            tail,
            re.I | re.S,
        )
        if sm:
            snip = strip_tags(sm.group(1))
        else:
            # Fallback: strip tags from the next non-heading div
            em = re.search(r"<div[^>]*>((?:(?!</div).){40,500})</div>", tail, re.I | re.S)
            if em:
                cand_s = strip_tags(em.group(1))
                if cand_s and cand_s != title and "http" not in cand_s[:20]:
                    snip = cand_s
        hits.append(
            Hit(
                title=title[:300],
                url=u,
                snippet=snip[:600],
                source=source_name,
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= max_n:
            return hits

    # Pattern 2: Google Basic (`gbv=1`) `<a href="/url?q=...">` blocks
    for m in re.finditer(
        r'<a[^>]+href=["\'](/url\?(?:q|url)=https?://[^"\']+)["\'][^>]*>(.*?)</a>',
        body,
        re.I | re.S,
    ):
        u = decode_google_url(m.group(1))
        if is_junk_url(u):
            continue
        c = canon_url(u)
        if c in seen:
            continue
        title = strip_tags(m.group(2))
        if not title or len(title) < 4 or title.lower().startswith(("cached", "similar", "translate")):
            continue
        seen.add(c)
        tail = body[m.end() : m.end() + 1500]
        snip = ""
        sm = re.search(r'<div[^>]+class=["\'][^"\']*BNeawe\s+s3v9rd[^"\']*["\'][^>]*>(.*?)</div>', tail, re.I | re.S)
        if sm:
            snip = strip_tags(sm.group(1))
        hits.append(
            Hit(
                title=title[:300],
                url=u,
                snippet=snip[:600],
                source=source_name,
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= max_n:
            return hits

    return hits


# ---- 1. `google_html` (Direct Google Web Search + udm=14 + gbv=1) ---------

GOOGLE_DOMAINS = (
    "www.google.com",
    "www.google.co.uk",
    "www.google.ca",
    "www.google.com.au",
    "www.google.co.in",
)


def eng_google_html(
    query: str,
    n: int,
    page: int,
    region: str,
    timelimit: str,
    sess: requests.Session,
    timeout: float = 10.0,
    relay: Optional[Tuple[str, str]] = None,
    proxy: Optional[str] = None,
    try_index: int = 0,
) -> List[Hit]:
    """Direct Google Web Search (`udm=14` clean web tab + `SOCS` consent bypass
    + `gbv=1` fallback). Uses `curl_cffi` Chrome TLS impersonation if installed
    or rotating proxies when direct datacenter IP is CAPTCHA'd."""
    domain = GOOGLE_DOMAINS[try_index % len(GOOGLE_DOMAINS)]
    hl = (region or "us-en").split("-")[-1].lower()
    gl = (region or "us-en").split("-")[0].lower()
    start = max(0, (int(page) - 1) * max(10, int(n)))

    # Try desktop udm=14 (Web-only filter) first, then gbv=1 (Google Basic HTML)
    modes = [
        (
            {"q": query, "num": max(10, min(30, int(n) + 4)), "start": start, "hl": hl, "gl": gl, "udm": "14", "nfpr": "1"},
            USER_AGENTS[try_index % len(USER_AGENTS)],
        ),
        (
            {"q": query, "num": max(10, min(30, int(n) + 4)), "start": start, "hl": hl, "gl": gl, "gbv": "1"},
            LYNX_UA if try_index % 2 == 1 else USER_AGENTS[0],
        ),
    ]

    last_wall: Optional[Exception] = None
    for params, ua in modes:
        if timelimit:
            params["tbs"] = f"qdr:{timelimit[0].lower()}"
        url = f"https://{domain}/search?" + urllib.parse.urlencode(params)
        try:
            r = _get(
                url,
                sess,
                timeout=timeout,
                relay=relay,
                proxy=proxy,
                use_curl_cffi=True,
                headers={
                    "User-Agent": ua,
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cookie": GOOGLE_CONSENT_COOKIE,
                    "Referer": f"https://{domain}/",
                },
            )
            hits = _parse_google_serp_html(r.text or "", "google_html", int(n))
            if hits:
                return hits
        except BotWalled as e:
            last_wall = e
            continue
        except Exception:
            continue

    if last_wall:
        raise last_wall
    raise BotWalled("google_html:js-shell-or-captcha")


# ---- 2. `startpage_html` (Google Search Syndication - Datacenter Friendly!)

_STARTPAGE_BLOCKS = re.compile(
    r'<div[^>]+class=["\'][^"\']*\bw-gl__result\b[^"\']*["\'][^>]*>(.*?)</div>\s*</div>',
    re.I | re.S,
)


def eng_startpage_html(
    query: str,
    n: int,
    page: int,
    region: str,
    timelimit: str,
    sess: requests.Session,
    timeout: float = 12.0,
    relay: Optional[Tuple[str, str]] = None,
    proxy: Optional[str] = None,
    try_index: int = 0,
) -> List[Hit]:
    """Startpage.com is an official Google Search syndication partner: its
    results ARE Google Web Search results, and its POST `/sp/search` HTML
    endpoint works from cloud datacenter IPs where google.com throws 429s."""
    url = "https://www.startpage.com/sp/search"
    data = {
        "query": query,
        "cat": "web",
        "cmd": "process_search",
        "language": "english",
        "engine0": "v1all",
        "abp": "-1",
        "page": str(max(1, int(page))),
    }
    if timelimit:
        data["with_date"] = {"d": "d", "w": "w", "m": "m", "y": "y"}.get(timelimit, "")

    try:
        r = sess.post(
            _apply_relay(url, relay),
            data=data,
            timeout=(min(5.0, timeout * 0.5), timeout),
            headers={
                "User-Agent": USER_AGENTS[try_index % len(USER_AGENTS)],
                "Referer": "https://www.startpage.com/",
                "Origin": "https://www.startpage.com",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
    except requests.RequestException as e:
        if proxy:
            raise EgressRetry(f"startpage:proxy-dead:{type(e).__name__}") from e
        raise EngineDown(f"startpage:transport:{type(e).__name__}") from e

    if r.status_code in WALL_CODES:
        raise BotWalled(f"startpage:http:{r.status_code}")
    body = r.text or ""
    if "captcha" in body[:8000].lower():
        raise BotWalled("startpage:captcha")

    hits: List[Hit] = []
    seen: set = set()

    # Primary Startpage parser: result-title / result-link anchors
    for m in re.finditer(
        r'<a[^>]+class=["\'][^"\']*(?:result-title|result-link|w-gl__result-title)[^"\']*["\'][^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>'
        r'|<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]+class=["\'][^"\']*(?:result-title|result-link|w-gl__result-title)[^"\']*["\'][^>]*>(.*?)</a>',
        body,
        re.I | re.S,
    ):
        u = (m.group(1) or m.group(3) or "").strip()
        raw_t = m.group(2) or m.group(4) or ""
        if is_junk_url(u):
            continue
        c = canon_url(u)
        if c in seen:
            continue
        title = strip_tags(raw_t)
        if not title or len(title) < 3:
            continue
        seen.add(c)
        tail = body[m.end() : m.end() + 2000]
        sm = re.search(
            r'<p[^>]+class=["\'][^"\']*(?:w-gl__description|result-description)[^"\']*["\'][^>]*>(.*?)</p>',
            tail,
            re.I | re.S,
        )
        snip = strip_tags(sm.group(1)) if sm else ""
        hits.append(
            Hit(
                title=title[:300],
                url=u,
                snippet=snip[:600],
                source="startpage_google",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break

    if not hits:
        raise BotWalled("startpage:no-results-or-js-gate")
    return hits


# ---- 3. `google_cse` (Google Programmable Search JSONP Token Harvester) ---

_CSE_TOKEN_CACHE: Dict[str, Tuple[str, str, float]] = {}
_CSE_LOCK = threading.Lock()


def _get_google_cse_tokens(cx: str, sess: requests.Session, timeout: float = 8.0) -> Tuple[str, str]:
    """Fetch `cse_token` and `cselibv` from `cse.google.com/cse.js?cx=<cx>`."""
    with _CSE_LOCK:
        cached = _CSE_TOKEN_CACHE.get(cx)
        if cached and (time.time() - cached[2]) < 1800:
            return cached[0], cached[1]

    js_url = f"https://cse.google.com/cse.js?cx={urllib.parse.quote(cx)}"
    r = sess.get(js_url, timeout=timeout, headers={"Referer": "https://cse.google.com/"})
    if r.status_code != 200:
        raise EngineDown(f"google_cse:cse_js_http_{r.status_code}")
    text = r.text or ""
    m_tok = re.search(r'"cse_token"\s*:\s*"([^"]+)"', text)
    m_lib = re.search(r'"cselibVersion"\s*:\s*"([^"]+)"', text)
    if not m_tok:
        raise EngineDown("google_cse:no-cse-token")
    tok = m_tok.group(1)
    libv = m_lib.group(1) if m_lib else "701841450209238b"
    with _CSE_LOCK:
        _CSE_TOKEN_CACHE[cx] = (tok, libv, time.time())
    return tok, libv


def eng_google_cse(
    query: str,
    n: int,
    page: int,
    region: str,
    timelimit: str,
    sess: requests.Session,
    timeout: float = 10.0,
    relay: Optional[Tuple[str, str]] = None,
    proxy: Optional[str] = None,
    try_index: int = 0,
) -> List[Hit]:
    """Query Google's internal Programmable Search Engine (`cse/element/v1`)
    JSONP API using dynamically harvested `cse_token` credentials."""
    cx_list = _env_list("GOOGLE_CSE_CX_LIST", PUBLIC_GOOGLE_CSE_CX_IDS)
    cx = cx_list[try_index % len(cx_list)]
    tok, libv = _get_google_cse_tokens(cx, sess, timeout=min(6.0, timeout))

    start = max(0, (int(page) - 1) * min(10, int(n)))
    params = {
        "rsz": "filtered_cse",
        "num": str(max(1, min(10, int(n)))),
        "hl": "en",
        "source": "gcsc",
        "gss": ".com",
        "cselibv": libv,
        "cx": cx,
        "q": query,
        "safe": "off",
        "cse_tok": tok,
        "exp": "cc,apo",
        "callback": "google.search.cse.api1",
    }
    if start > 0:
        params["start"] = str(start)
    url = "https://cse.google.com/cse/element/v1?" + urllib.parse.urlencode(params)
    r = _get(
        url,
        sess,
        timeout=timeout,
        relay=relay,
        proxy=proxy,
        headers={"Referer": f"https://cse.google.com/cse?cx={cx}"},
    )
    body = r.text or ""
    idx1 = body.find("{")
    idx2 = body.rfind("}")
    if idx1 < 0 or idx2 <= idx1:
        raise EngineDown("google_cse:invalid-jsonp")
    data = json.loads(body[idx1 : idx2 + 1])
    results = data.get("results") or []
    hits: List[Hit] = []
    for row in results:
        if not isinstance(row, dict):
            continue
        u = str(row.get("unescapedUrl") or row.get("url") or "").strip()
        u = decode_google_url(u)
        if is_junk_url(u):
            continue
        hits.append(
            Hit(
                title=strip_tags(str(row.get("titleNoFormatting") or row.get("title") or ""))[:300],
                url=u,
                snippet=strip_tags(str(row.get("contentNoFormatting") or row.get("content") or ""))[:600],
                source="google_cse",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        raise EngineDown("google_cse:empty")
    return hits


# ---- 4. `google_cdp` (Headless Chrome/Edge DevTools Protocol Google SERP) -

def eng_google_cdp(
    query: str,
    n: int,
    page: int,
    region: str,
    timelimit: str,
    sess: requests.Session,
    timeout: float = 15.0,
    relay: Optional[Tuple[str, str]] = None,
    proxy: Optional[str] = None,
    try_index: int = 0,
) -> List[Hit]:
    """Use local headless Chrome/Edge (`--headless=new` + stealth flags) to
    execute Google's JS/TLS checks and dump the live SERP DOM."""
    binary = _find_chromium_binary()
    if not binary:
        raise EngineDown("google_cdp:no-browser-binary")

    start = max(0, (int(page) - 1) * max(10, int(n)))
    params = {"q": query, "num": max(10, min(25, int(n) + 3)), "start": start, "hl": "en", "udm": "14"}
    target_url = "https://www.google.com/search?" + urllib.parse.urlencode(params)

    user_dir = tempfile.mkdtemp(prefix="fs_gcdp_")
    env = os.environ.copy()
    if not os.access(env.get("HOME", "/"), os.W_OK) or env.get("HOME", "").startswith("/working_dir"):
        env["HOME"] = tempfile.gettempdir()

    cmd = [
        binary,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--blink-settings=imagesEnabled=false",
        f"--user-agent={BROWSER_UA}",
        f"--user-data-dir={user_dir}",
        "--dump-dom",
    ]
    if proxy:
        px = proxy if "://" in proxy else f"http://{proxy}"
        cmd.append(f"--proxy-server={px}")
    cmd.append(target_url)

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=max(8.0, timeout),
            env=env,
            check=False,
        )
        raw_html = proc.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        raise EngineDown(f"google_cdp:{type(e).__name__}") from e
    finally:
        shutil.rmtree(user_dir, ignore_errors=True)

    if looks_walled(200, raw_html):
        raise BotWalled("google_cdp:captcha-wall")

    hits = _parse_google_serp_html(raw_html, "google_cdp", int(n))
    if not hits:
        raise EngineDown("google_cdp:no-hits")
    return hits


# ---- 5. `google_news_rss` (Google News Syndication - Never Walled on DC IPs!)

_RSS_ITEM = re.compile(r"<item>(.*?)</item>", re.S)


def _rss_field(tag: str, block: str) -> str:
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.S)
    return m.group(1) if m else ""


def eng_google_news_rss(
    query: str,
    n: int,
    page: int,
    region: str,
    timelimit: str,
    sess: requests.Session,
    timeout: float = 10.0,
    relay: Optional[Tuple[str, str]] = None,
    proxy: Optional[str] = None,
    try_index: int = 0,
) -> List[Hit]:
    """`news.google.com/rss/search` is Google's official RSS syndication feed.
    It answers reliably from AWS/GCP/Azure datacenter IPs with zero CAPTCHAs."""
    q = query
    if timelimit:
        q += " " + {"d": "when:1d", "w": "when:7d", "m": "when:30d", "y": "when:1y"}.get(timelimit, "")
    params = {"q": q, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)
    r = _get(url, sess, timeout=timeout, relay=relay, proxy=proxy)
    hits: List[Hit] = []
    for m in _RSS_ITEM.finditer(r.text or ""):
        blk = m.group(1)
        u = htmllib.unescape(_rss_field("link", blk).strip())
        if not u.startswith("http"):
            continue
        title = strip_tags(_rss_field("title", blk))
        desc = strip_tags(_rss_field("description", blk))
        src_name = strip_tags(_rss_field("source", blk))
        src_url_m = re.search(r'<source[^>]+url=["\'](https?://[^"\']+)["\']', blk, re.I)
        pub_date = strip_tags(_rss_field("pubDate", blk))
        snip_parts = [p for p in (src_name, pub_date, desc if desc != title else "") if p]
        hits.append(
            Hit(
                title=title[:300],
                url=u,
                snippet=" • ".join(snip_parts)[:600] + (f" ({src_url_m.group(1)})" if src_url_m else ""),
                source="google_news_rss",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        raise EngineDown("google_news_rss:no-items")
    return hits


# ---------------------------------------------------------------------------
# Direct Zero-Dep HTML Engines (Brave, Yahoo, Bing, DuckDuckGo, SearXNG)
# ---------------------------------------------------------------------------

def eng_wikipedia_api(
    query, n, page, region, timelimit, sess, timeout=10.0, relay=None, proxy=None, try_index=0
):
    """Wikipedia REST search (v4). Live-researched on a walled datacenter
    ASN: browser UAs get 403'd by Wikimedia robot policy; a descriptive UA
    passes in ~0.5s. CDN-backed, walls almost nobody - the last-resort
    layer that keeps informational queries non-empty on any IP."""
    lang = "en"
    for cand in ((region or "us-en").replace("_", "-").split("-") + ["en"]):
        if cand.lower() in ("en", "de", "fr", "es", "it", "pt", "ru",
                            "ja", "zh", "hi", "ar", "ko", "nl", "pl", "tr"):
            lang = cand.lower()
            break
    off = (max(1, int(page)) - 1) * max(1, int(n))
    url = f"https://{lang}.wikipedia.org/w/rest.php/v1/search/page?" + urllib.parse.urlencode(
        {"q": query, "limit": min(100, off + max(1, int(n)) * 2)}
    )
    headers = {
        # Wikimedia policy requires a descriptive UA; browser UAs are 403'd.
        "User-Agent": "free-search/4.0 (+https://github.com/free-search; python-requests)",
        "Accept": "application/json",
    }
    r = _get(url, sess, timeout, relay=relay, proxy=proxy, headers=headers)
    if r.status_code != 200:
        raise BotWalled("http:%d" % r.status_code)
    try:
        pages = (r.json() or {}).get("pages") or []
    except Exception:
        raise EngineDown("wikipedia_api:bad-json")
    hits = []
    for p in pages[off:]:
        u = str(p.get("url") or "").strip()
        if not u.startswith("http"):
            key = str(p.get("key") or p.get("title") or "").strip()
            u = "https://%s.wikipedia.org/wiki/%s" % (lang, urllib.parse.quote(key.replace(" ", "_")))
        if is_junk_url(u):
            continue
        hits.append(
            Hit(
                title=strip_tags(str(p.get("title") or ""))[:300],
                url=u,
                snippet=strip_tags(str(p.get("excerpt") or ""))[:600],
                source="wikipedia_api",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        raise EngineDown("wikipedia_api:no-pages")
    return hits[:n]


def eng_brave_html(
    query: str,
    n: int,
    page: int,
    region: str,
    timelimit: str,
    sess: requests.Session,
    timeout: float = 10.0,
    relay: Optional[Tuple[str, str]] = None,
    proxy: Optional[str] = None,
    try_index: int = 0,
) -> List[Hit]:
    """Direct Brave Search HTML scraper (zero `ddgs` dependency required)."""
    params: Dict[str, Any] = {"q": query, "source": "web"}
    if int(page) > 1:
        params["offset"] = str(int(page) - 1)
    if timelimit:
        params["tf"] = {"d": "pd", "w": "pw", "m": "pm", "y": "py"}.get(timelimit, "")
    url = "https://search.brave.com/search?" + urllib.parse.urlencode(params)
    r = _get(
        url,
        sess,
        timeout=timeout,
        relay=relay,
        proxy=proxy,
        use_curl_cffi=True,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": "useLocation=0",
        },
    )
    body = r.text or ""
    hits: List[Hit] = []
    seen: set = set()
    # Brave result snippets have data-type="web" or class="snippet"
    for m in re.finditer(
        r'<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]*class=["\'][^"\']*(?:result-header|heading-serpresult|l1)[^"\']*["\'][^>]*>(.*?)</a>'
        r'|<div[^>]+data-type=["\']web["\'][^>]*>.*?<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>',
        body,
        re.I | re.S,
    ):
        u = (m.group(1) or m.group(3) or "").strip()
        raw_t = m.group(2) or m.group(4) or ""
        if is_junk_url(u):
            continue
        c = canon_url(u)
        if c in seen:
            continue
        title = strip_tags(raw_t)
        if not title or len(title) < 3:
            continue
        seen.add(c)
        tail = body[m.end() : m.end() + 2000]
        sm = re.search(
            r'class=["\'][^"\']*(?:snippet-description|snippet-content|generic-snippet)[^"\']*["\'][^>]*>(.*?)</(?:div|p|span)>',
            tail,
            re.I | re.S,
        )
        snip = strip_tags(sm.group(1)) if sm else ""
        hits.append(
            Hit(
                title=title[:300],
                url=u,
                snippet=snip[:600],
                source="brave_html",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        raise BotWalled("brave_html:no-results-or-429")
    return hits


def eng_yahoo_html(
    query: str,
    n: int,
    page: int,
    region: str,
    timelimit: str,
    sess: requests.Session,
    timeout: float = 10.0,
    relay: Optional[Tuple[str, str]] = None,
    proxy: Optional[str] = None,
    try_index: int = 0,
) -> List[Hit]:
    """Direct Yahoo Search HTML adapter - high datacenter IP tolerance."""
    b_offset = max(1, (int(page) - 1) * 10 + 1)
    params = {"p": query, "b": str(b_offset), "ei": "UTF-8", "nojs": "1"}
    if timelimit:
        params["btf"] = timelimit[0].lower()
    url = "https://search.yahoo.com/search?" + urllib.parse.urlencode(params)
    r = _get(url, sess, timeout=timeout, relay=relay, proxy=proxy)
    body = r.text or ""
    hits: List[Hit] = []
    seen: set = set()
    for m in re.finditer(
        r'<div[^>]+class=["\'][^"\']*\balgo\b[^"\']*["\'][^>]*>(.*?)</div>\s*</div>\s*</li>',
        body,
        re.I | re.S,
    ):
        blk = m.group(1)
        am = re.search(r'<a[^>]+href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', blk, re.I | re.S)
        if not am:
            continue
        u = decode_yahoo_ru(am.group(1))
        if is_junk_url(u):
            continue
        c = canon_url(u)
        if c in seen:
            continue
        title = strip_tags(am.group(2))
        # Strip trailing domain breadcrumb that Yahoo embeds inside the <a>
        title = re.sub(r"https?://\S+\s*", "", title).strip()
        if not title:
            continue
        seen.add(c)
        sm = re.search(r'class=["\'][^"\']*(?:compText|s-desc)[^"\']*["\'][^>]*>(.*?)</(?:div|p|span)>', blk, re.I | re.S)
        snip = strip_tags(sm.group(1)) if sm else ""
        hits.append(
            Hit(
                title=title[:300],
                url=u,
                snippet=snip[:600],
                source="yahoo_html",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        raise EngineDown("yahoo_html:parse-miss")
    return hits


_BING_ALGO = re.compile(
    r'<li class="b_algo".*?<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>(.*?)</li>',
    re.S,
)
_BING_CAPTION = re.compile(r"<p[^>]*>(.*?)</p>", re.S)


def eng_bing_html(
    query, n, page, region, timelimit, sess, timeout=10.0, relay=None, proxy=None, try_index=0
):
    forced = os.getenv("BING_MIRROR", "").strip()
    if forced:
        mirror = forced
    elif try_index <= 0:
        mirror = BING_PRIMARY
    else:
        mirror = BING_MIRRORS[try_index % len(BING_MIRRORS)]
    params = {
        "q": query,
        "count": max(10, min(30, int(n))),
        "first": max(1, (int(page) - 1) * max(10, int(n)) + 1),
        "mkt": region or "en-US",
        "setlang": "en",
        "cc": "US",
        "ensearch": "1",
        "form": "QBLH",
    }
    if timelimit:
        params["filters"] = {
            "d": 'ex1:"ez1"', "w": 'ex1:"ez2"', "m": 'ex1:"ez3"', "y": 'ex1:"ez5"'
        }.get(timelimit, "")
    url = f"https://{mirror}/search?" + urllib.parse.urlencode(params)
    r = _get(
        url,
        sess,
        timeout,
        relay=relay,
        proxy=proxy,
        headers={"Accept-Language": "en-US,en;q=0.9", "Cookie": BING_LOCALE_COOKIE},
    )
    body = r.text or ""
    hits: List[Hit] = []
    for i, m in enumerate(_BING_ALGO.finditer(body), 1):
        raw_href, raw_title, tail = m.group(1), m.group(2), m.group(3)
        u = decode_bing_ck(raw_href)
        if is_junk_url(u):
            continue
        cap = _BING_CAPTION.search(tail or "")
        hits.append(
            Hit(
                title=strip_tags(raw_title)[:300],
                url=u,
                snippet=strip_tags(cap.group(1) if cap else "")[:600],
                source="bing_html",
                rank=i,
            )
        )
    if not hits:
        if "b_algo" not in body:
            if len(body) < 3000 or "js_enabled" in body.lower():
                raise BotWalled("bing:js-shell")
            raise EngineDown("bing:parse-miss")
        raise EngineDown("bing:all-junk")
    return hits[: int(n)]


def eng_bing_rss(
    query, n, page, region, timelimit, sess, timeout=10.0, relay=None, proxy=None, try_index=0
):
    mirror = BING_PRIMARY if try_index <= 0 else BING_MIRRORS[try_index % len(BING_MIRRORS)]
    params = {
        "q": query,
        "format": "rss",
        "count": max(10, min(30, int(n))),
        "first": max(1, (int(page) - 1) * 10 + 1),
        "mkt": region or "en-US",
        "setlang": "en",
    }
    url = f"https://{mirror}/search?" + urllib.parse.urlencode(params)
    r = _get(
        url,
        sess,
        timeout,
        relay=relay,
        proxy=proxy,
        headers={"Accept-Language": "en-US,en;q=0.9", "Cookie": BING_LOCALE_COOKIE},
    )
    hits: List[Hit] = []
    for m in _RSS_ITEM.finditer(r.text or ""):
        blk = m.group(1)
        u = decode_bing_redirect(_rss_field("link", blk).strip())
        if is_junk_url(u):
            continue
        hits.append(
            Hit(
                title=strip_tags(_rss_field("title", blk))[:300],
                url=u,
                snippet=strip_tags(_rss_field("description", blk))[:600],
                source="bing_rss",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        raise EngineDown("bing_rss:no-items")
    return hits


def eng_bing_news_rss(
    query, n, page, region, timelimit, sess, timeout=10.0, relay=None, proxy=None, try_index=0
):
    mirror = BING_PRIMARY if try_index <= 0 else BING_MIRRORS[try_index % len(BING_MIRRORS)]
    params = {
        "q": query,
        "format": "rss",
        "count": max(10, min(30, int(n))),
        "setlang": "en",
        "mkt": region or "en-US",
    }
    url = f"https://{mirror}/news/search?" + urllib.parse.urlencode(params)
    r = _get(
        url,
        sess,
        timeout,
        relay=relay,
        proxy=proxy,
        headers={"Accept-Language": "en-US,en;q=0.9", "Cookie": BING_LOCALE_COOKIE},
    )
    hits: List[Hit] = []
    for m in _RSS_ITEM.finditer(r.text or ""):
        blk = m.group(1)
        u = decode_bing_redirect(_rss_field("link", blk).strip())
        if is_junk_url(u):
            continue
        hits.append(
            Hit(
                title=strip_tags(_rss_field("title", blk))[:300],
                url=u,
                snippet=strip_tags(_rss_field("description", blk))[:600],
                source="bing_news",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        raise EngineDown("bing_news_rss:no-items")
    return hits


def eng_ddg_html(
    query, n, page, region, timelimit, sess, timeout=10.0, relay=None, proxy=None, try_index=0
):
    url = "https://html.duckduckgo.com/html/"
    data = {"q": query, "kl": (region or "us-en").lower(), "b": ""}
    if timelimit:
        data["df"] = timelimit
    try:
        r = sess.post(
            _apply_relay(url, relay),
            data=data,
            timeout=(min(5.0, timeout * 0.5), timeout),
            headers={
                "Referer": "https://duckduckgo.com/",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    except requests.RequestException as e:
        if proxy:
            raise EgressRetry(f"ddg:proxy-dead:{type(e).__name__}") from e
        raise EngineDown(f"ddg:transport:{type(e).__name__}") from e
    if r.status_code in WALL_CODES or r.status_code == 202:
        raise BotWalled(f"ddg:http:{r.status_code}")
    body = r.text or ""
    if "result__a" not in body:
        if "anomaly" in body.lower() or "challenge" in body.lower():
            raise BotWalled("ddg:anomaly")
        raise EngineDown("ddg:parse-miss")
    hits: List[Hit] = []
    seen = set()
    for m in re.finditer(
        r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', body, re.S
    ):
        u = decode_ddg_l(m.group(1))
        if not u.startswith("http") or u in seen or is_junk_url(u):
            continue
        seen.add(u)
        tail = body[m.end() : m.end() + 1500]
        sm = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', tail, re.S)
        hits.append(
            Hit(
                title=strip_tags(m.group(2))[:300],
                url=u,
                snippet=strip_tags(sm.group(1) if sm else "")[:600],
                source="ddg_html",
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        raise EngineDown("ddg:no-results")
    return hits


# ---- ddgs metasearch (optional) -------------------------------------------

_DDGS_CACHE: Dict[str, Any] = {}
_DDGS_CACHE_LOCK = threading.Lock()
_DDGS_REENABLED = False
_DDGS_REENABLE_LOCK = threading.Lock()


def reenable_disabled_ddgs_backends() -> List[str]:
    global _DDGS_REENABLED
    if _DDGS_REENABLED or not HAVE_DDGS:
        return []
    if not _env_bool("DDGS_ENABLE_DISABLED", True):
        _DDGS_REENABLED = True
        return []
    added: List[str] = []
    with _DDGS_REENABLE_LOCK:
        if _DDGS_REENABLED:
            return []
        try:
            import importlib
            import inspect
            import pkgutil
            from ddgs.base import BaseSearchEngine
            import ddgs.engines as pkg
            from ddgs.engines import ENGINES

            for _finder, modname, _ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
                try:
                    mod = importlib.import_module(modname)
                except Exception:
                    continue
                for _n, cls in inspect.getmembers(mod, inspect.isclass):
                    if not issubclass(cls, BaseSearchEngine) or cls is BaseSearchEngine:
                        continue
                    if cls.__name__.startswith("Base"):
                        continue
                    name = getattr(cls, "name", None)
                    cat = getattr(cls, "category", None)
                    if not (isinstance(name, str) and isinstance(cat, str)):
                        continue
                    if not getattr(cls, "disabled", False):
                        continue
                    ENGINES.setdefault(cat, {})[name] = cls
                    added.append(f"{cat}:{name}")
        except Exception:
            pass
        _DDGS_REENABLED = True
    return sorted(set(added))


def _ddgs_instance(proxy: Optional[str], timeout: int):
    if not HAVE_DDGS:
        raise EngineDown("ddgs:not-installed")
    reenable_disabled_ddgs_backends()
    key = f"{proxy or ''}|{timeout}"
    with _DDGS_CACHE_LOCK:
        inst = _DDGS_CACHE.get(key)
        if inst is None:
            try:
                inst = DDGS(proxy=proxy, timeout=timeout) if proxy else DDGS(timeout=timeout)
            except TypeError:
                inst = DDGS()
            if len(_DDGS_CACHE) > 64:
                _DDGS_CACHE.clear()
            _DDGS_CACHE[key] = inst
        return inst


def make_ddgs_engine(backend: str) -> Callable[..., List[Hit]]:
    def _eng(query, n, page, region, timelimit, sess, timeout=12.0, relay=None, proxy=None, try_index=0):
        if relay:
            raise EngineDown(f"ddgs:{backend}:no-relay-support")
        ddgs_timeout = max(5, min(int(timeout), 20))
        px = (proxy if "://" in proxy else f"http://{proxy}") if proxy else None
        inst = _ddgs_instance(px, ddgs_timeout)
        try:
            raw = inst.text(
                query,
                region=region or "us-en",
                max_results=max(1, int(n)),
                page=max(1, int(page)),
                timelimit=timelimit or None,
                backend=backend,
            )
            rows = list(raw) if raw else []
        except Exception as e:
            name = type(e).__name__
            msg = f"{name}: {str(e)[:120]}"
            low = msg.lower()
            if proxy and any(k in low for k in ("proxy", "tunnel", "connect", "timed out", "timeout")):
                raise EgressRetry(f"ddgs:{backend}:proxy-failed:{name}") from e
            if any(k in low for k in ("ratelimit", "429", "403", "blocked", "captcha", "999", "anomaly")):
                raise BotWalled(f"ddgs:{backend}:{msg}") from e
            raise EngineDown(f"ddgs:{backend}:{msg}") from e

        hits: List[Hit] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            u = str(row.get("href") or row.get("url") or row.get("link") or "").strip()
            u = decode_bing_redirect(u) if "bing.com" in u else u
            if is_junk_url(u):
                continue
            title = strip_tags(str(row.get("title") or "")) or urllib.parse.urlparse(u).netloc
            hits.append(
                Hit(
                    title=title[:300],
                    url=u,
                    snippet=strip_tags(str(row.get("body") or row.get("snippet") or row.get("content") or ""))[:600],
                    source=f"ddgs:{backend}",
                    rank=len(hits) + 1,
                )
            )
            if len(hits) >= int(n):
                break
        if not hits:
            raise EngineDown(f"ddgs:{backend}:empty")
        return hits

    _eng.__name__ = f"eng_ddgs_{backend.replace(':', '_')}"
    return _eng


# ---- SearXNG (with Google-targeted mode) ----------------------------------

class SearxRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._good: List[str] = []
        self._tried: set = set()
        self._fetched = 0.0
        self._warming = False
        self.state_file = os.getenv(
            "SEARXNG_STATE_FILE",
            os.path.join(tempfile.gettempdir(), ".free_search_searxng.json"),
        )
        self.state_max_age = _env_int("SEARXNG_STATE_MAX_AGE", 6 * 3600)
        self.extra = _env_list("SEARXNG_INSTANCES", [])
        self._load()

    def _load(self) -> None:
        try:
            with open(self.state_file, "r", encoding="utf-8") as fh:
                st = json.load(fh)
            if time.time() - float(st.get("ts", 0)) <= self.state_max_age:
                good = [u for u in st.get("good", []) if isinstance(u, str)]
                if good:
                    self._good = good
                    self._fetched = time.time()
        except Exception:
            pass

    def _save(self) -> None:
        try:
            with open(self.state_file, "w", encoding="utf-8") as fh:
                json.dump({"ts": time.time(), "good": self._good}, fh)
        except Exception:
            pass

    def _discover(self) -> List[str]:
        urls: List[str] = []
        try:
            r = requests.get(SEARX_SPACE, timeout=12, headers={"User-Agent": BROWSER_UA})
            data = r.json()
            rows = []
            for base, v in (data.get("instances") or {}).items():
                if not isinstance(v, dict) or v.get("network_type") == "onion":
                    continue
                if not base.lower().startswith("https://"):
                    continue
                t = ((v.get("timing") or {}).get("search") or {})
                pct = t.get("success_percentage") or 0
                if pct < 60:
                    continue
                rows.append((len(t.get("working_engine_names") or []), pct, base.rstrip("/")))
            rows.sort(key=lambda x: (-x[0], -x[1]))
            urls = [b for _, _, b in rows]
        except Exception:
            pass
        return list(dict.fromkeys(self.extra + urls))

    def _probe(self, base: str, timeout: float = 5.0) -> bool:
        url = base + "/search?" + urllib.parse.urlencode({"q": "test", "format": "json", "pageno": 1})
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": BROWSER_UA, "Accept": "application/json"})
            return r.status_code == 200 and bool(r.json().get("results"))
        except Exception:
            return False

    def refresh(self, max_probe: Optional[int] = None) -> List[str]:
        max_probe = max_probe or _env_int("SEARXNG_PROBE_LIMIT", 25)
        cands = self._discover()[:max_probe]
        good: List[str] = []
        if cands:
            # v4: daemon pool - background probing must never block exit
            res = _daemon_map(self._probe, cands, workers=min(10, len(cands)), max_seconds=12.0)
            good = [b for b in cands if res.get(b)]
        with self._lock:
            merged = list(dict.fromkeys(self.extra + good + self._good))
            self._good = merged[:12]
            self._tried = set()
            self._fetched = time.time()
            self._save()
        return list(self._good)

    def rotate(self) -> Optional[str]:
        with self._lock:
            if not self._good and (time.time() - self._fetched) > 300:
                pass
            pool = [u for u in self._good if u not in self._tried]
            if not pool:
                self._tried = set()
                pool = list(self._good)
            if not pool:
                return None
            pick = pool[0]
            self._tried.add(pick)
            return pick

    def mark_bad(self, base: str) -> None:
        with self._lock:
            if base in self._good:
                self._good.remove(base)
                self._save()

    def mark_good(self, base: str) -> None:
        with self._lock:
            if base not in self._good:
                self._good.insert(0, base)
                self._good = self._good[:12]
                self._save()


_SEARX = SearxRegistry()


def eng_searxng(
    query, n, page, region, timelimit, sess, timeout=10.0, relay=None, proxy=None, try_index=0
):
    if not _SEARX._good and _SEARX._fetched == 0.0:
        if not _SEARX._warming:
            _SEARX._warming = True

            def _warm():
                try:
                    _SEARX.refresh(max_probe=18)
                except Exception:
                    pass  # v3: process exiting mid-warm; stay quiet
                finally:
                    _SEARX._warming = False

            threading.Thread(target=_warm, daemon=True).start()
        raise EngineDown("searxng:pool-warming(background)")
    base = _SEARX.rotate()
    if not base:
        raise EngineDown("searxng:no-json-instances")
    params = {
        "q": query,
        "format": "json",
        "pageno": max(1, int(page)),
        "language": (region or "en-US").lower(),
        "safesearch": 0,
    }
    if timelimit:
        params["time_range"] = {"d": "day", "w": "week", "m": "month", "y": "year"}.get(timelimit, "")
    url = base + "/search?" + urllib.parse.urlencode(params)
    try:
        r = _get(url, sess, timeout, relay=relay, proxy=proxy, headers={"Accept": "application/json"})
        j = r.json()
    except Exception as e:
        _SEARX.mark_bad(base)
        raise EngineDown(f"searxng:{base}:{type(e).__name__}") from e
    rows = j.get("results") or []
    hits = []
    for row in rows:
        u = str((row or {}).get("url") or "").strip()
        if is_junk_url(u):
            continue
        hits.append(
            Hit(
                title=strip_tags(str(row.get("title") or ""))[:300],
                url=u,
                snippet=strip_tags(str(row.get("content") or ""))[:600],
                source="searxng:" + urllib.parse.urlparse(base).netloc,
                rank=len(hits) + 1,
            )
        )
        if len(hits) >= int(n):
            break
    if not hits:
        _SEARX.mark_bad(base)
        raise EngineDown("searxng:empty")
    _SEARX.mark_good(base)
    return hits


# ---- Optional KEY Backends ------------------------------------------------

def _key_hits(
    rows: Iterable[Dict[str, Any]],
    src: str,
    title_k=("title",),
    url_k=("url", "href", "link"),
    snip_k=("snippet", "content", "body", "description"),
) -> List[Hit]:
    out = []
    for i, row in enumerate(rows, 1):
        t = next((row.get(k) for k in title_k if row.get(k)), "")
        u = next((row.get(k) for k in url_k if row.get(k)), "")
        s = next((row.get(k) for k in snip_k if row.get(k)), "")
        if not u or not str(u).startswith("http"):
            continue
        out.append(
            Hit(
                title=strip_tags(str(t))[:300],
                url=str(u),
                snippet=strip_tags(str(s))[:600],
                source=src,
                rank=i,
            )
        )
    return out


def eng_google_custom_api(
    query, n, page, region, timelimit, sess, timeout=12.0, relay=None, proxy=None, try_index=0
):
    key = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
    cx = os.getenv("GOOGLE_CSE_CX", PUBLIC_GOOGLE_CSE_CX_IDS[0]).strip()
    if not key:
        raise EngineDown("google_custom_api:no-key")
    r = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        timeout=timeout,
        params={
            "key": key,
            "cx": cx,
            "q": query,
            "num": max(1, min(10, int(n))),
            "start": max(1, (int(page) - 1) * min(10, int(n)) + 1),
        },
    )
    if r.status_code in (429, 401, 403):
        raise BotWalled(f"google_custom_api:http:{r.status_code}")
    r.raise_for_status()
    hits = _key_hits(r.json().get("items", []), "google_custom_api")
    if not hits:
        raise EngineDown("google_custom_api:empty")
    return hits[: int(n)]


def eng_tavily(query, n, page, region, timelimit, sess, timeout=15.0, relay=None, proxy=None, try_index=0):
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        raise EngineDown("tavily:no-key")
    r = requests.post(
        "https://api.tavily.com/search",
        timeout=timeout,
        json={"api_key": key, "query": query, "max_results": max(1, int(n)), "search_depth": "basic"},
    )
    if r.status_code in (429, 401, 403):
        raise BotWalled(f"tavily:http:{r.status_code}")
    r.raise_for_status()
    hits = _key_hits(r.json().get("results", []), "tavily")
    if not hits:
        raise EngineDown("tavily:empty")
    return hits[: int(n)]


def eng_serper(query, n, page, region, timelimit, sess, timeout=15.0, relay=None, proxy=None, try_index=0):
    key = os.getenv("SERPER_API_KEY", "").strip()
    if not key:
        raise EngineDown("serper:no-key")
    r = requests.post(
        "https://google.serper.dev/search",
        timeout=timeout,
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        json={"q": query, "num": max(1, min(100, int(n))), "gl": "us", "hl": "en"},
    )
    if r.status_code in (429, 401, 403):
        raise BotWalled(f"serper:http:{r.status_code}")
    r.raise_for_status()
    hits = _key_hits(r.json().get("organic", []), "serper")
    if not hits:
        raise EngineDown("serper:empty")
    return hits[: int(n)]


def eng_brave_api(query, n, page, region, timelimit, sess, timeout=15.0, relay=None, proxy=None, try_index=0):
    key = os.getenv("BRAVE_API_KEY", "").strip()
    if not key:
        raise EngineDown("brave_api:no-key")
    r = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        timeout=timeout,
        headers={"X-Subscription-Token": key, "Accept": "application/json"},
        params={"q": query, "count": max(1, min(20, int(n)))},
    )
    if r.status_code in (429, 401, 403, 422):
        raise BotWalled(f"brave_api:http:{r.status_code}")
    r.raise_for_status()
    hits = _key_hits(((r.json().get("web") or {}).get("results") or []), "brave_api")
    if not hits:
        raise EngineDown("brave_api:empty")
    return hits[: int(n)]


def eng_serpapi(query, n, page, region, timelimit, sess, timeout=15.0, relay=None, proxy=None, try_index=0):
    key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not key:
        raise EngineDown("serpapi:no-key")
    r = requests.get(
        "https://serpapi.com/search.json",
        timeout=timeout,
        params={"q": query, "api_key": key, "engine": "google", "num": max(1, min(100, int(n)))},
    )
    if r.status_code in (429, 401, 403):
        raise BotWalled(f"serpapi:http:{r.status_code}")
    r.raise_for_status()
    hits = _key_hits(r.json().get("organic_results", []), "serpapi")
    if not hits:
        raise EngineDown("serpapi:empty")
    return hits[: int(n)]


KEY_ENGINES: Dict[str, Callable] = {
    "google_custom_api": eng_google_custom_api,
    "serper": eng_serper,
    "serpapi": eng_serpapi,
    "tavily": eng_tavily,
    "brave_api": eng_brave_api,
}


# ---------------------------------------------------------------------------
# Engine Registry & Priority Fleets (General + Google-First)
# ---------------------------------------------------------------------------

# (name, adapter, default_qps, needs_ddgs, supports_proxy, supports_relay)
BUILTIN_ENGINES: List[Tuple[str, Callable, float, bool, bool, bool]] = [
    # Google-indexed / Google-backed engines (work with zero ddgs!)
    ("startpage_html", eng_startpage_html, 2.5, False, True, False),
    ("google_html", eng_google_html, 2.0, False, True, True),
    ("google_cse", eng_google_cse, 2.5, False, True, False),
    ("google_cdp", eng_google_cdp, 1.0, False, True, False),
    ("google_news_rss", eng_google_news_rss, 3.0, False, True, True),
    # Direct zero-dep HTML engines (work on Cloud Datacenter IPs without ddgs!)
    ("yahoo_html", eng_yahoo_html, 2.5, False, True, True),
    ("brave_html", eng_brave_html, 2.0, False, True, True),
    ("bing_html", eng_bing_html, 2.5, False, True, True),
    ("bing_rss", eng_bing_rss, 3.0, False, True, True),
    ("ddg_html", eng_ddg_html, 1.2, False, True, True),
    ("searxng", eng_searxng, 1.5, False, True, True),
    ("bing_news", eng_bing_news_rss, 2.0, False, True, True),
    # v4: CDN-backed last-resort layer (no proxy support needed - it
    # walls almost nobody; relay support kept for the truly paranoid).
    ("wikipedia_api", eng_wikipedia_api, 1.5, False, False, True),
    # Optional ddgs-backed engines (if ddgs is installed)
    ("ddgs:google", make_ddgs_engine("google"), 1.5, True, True, False),
    ("ddgs:brave", make_ddgs_engine("brave"), 1.5, True, True, False),
    ("ddgs:yandex", make_ddgs_engine("yandex"), 1.5, True, True, False),
    ("ddgs:yahoo", make_ddgs_engine("yahoo"), 1.5, True, True, False),
    ("ddgs:duckduckgo", make_ddgs_engine("duckduckgo"), 1.0, True, True, False),
    ("ddgs:bing", make_ddgs_engine("bing"), 1.5, True, True, False),
    ("ddgs:startpage", make_ddgs_engine("startpage"), 1.5, True, True, False),
    ("ddgs:auto", make_ddgs_engine("auto"), 1.5, True, True, False),
]

# Google-First Priority Fleet (used when `--google` or `google_search()` is called,
# and also leads the default priority so Google-backed results always win first!)
GOOGLE_PRIORITY = (
    "startpage_html,google_html,google_cse,ddgs:google,ddgs:startpage,"
    "google_cdp,google_news_rss,searxng,google_custom_api,serper,serpapi"
)

DEFAULT_PRIORITY = (
    "startpage_html,google_html,google_cse,yahoo_html,brave_html,bing_html,bing_rss,"
    "ddgs:brave,ddgs:google,ddgs:yandex,ddgs:yahoo,ddgs:duckduckgo,ddg_html,"
    "google_cdp,google_news_rss,searxng,bing_news,wikipedia_api,"
    "google_custom_api,serper,serpapi,tavily,brave_api"
)

EGRESS_ORDER = ("direct", "proxy", "relay")

# v3: feed-style engines excluded from web races (news() still forces them;
# the sequential escalation path also covers them).
_NEWS_FEED_ENGINES = frozenset({"google_news_rss", "bing_news"})


_RECENCY_CUES = (
    "this week", "this month", "this year", "this weekend", "this season",
    "today", "yesterday", "right now", "now playing", "now showing",
    "currently showing", "currently playing", "just released", "just dropped",
    "new releases", "newly released", "releasing this", "released this",
    "latest", "breaking", "upcoming",
)


def _recency_cue(query: str) -> bool:
    """v5: True when the query wants FRESH results (this week's releases,
    now playing, ...). Such queries must be answered by news engines, not
    static encyclopedic pages."""
    q = (query or "").lower()
    return any(c in q for c in _RECENCY_CUES)


def _condense_query(query: str, alt: bool = False) -> Optional[str]:
    """v5.1: a 3-5 salient-term version of a keyword-stuffed query, for the
    condensed retry wave. Engines like bing answer 6+ word agent queries
    with random garbage; they handle a 5-term query normally. v5.1 lowered
    the trigger from 8 to 6 significant terms (real-world failures were
    6-7 term queries). Selection: years/numbers first, then capitalized
    tokens (proper nouns), then the rest; original order preserved.
    Always drops >= 1 term, never condenses below 3 terms."""
    _nterms = len(query_terms(query))
    if _nterms < 6:
        return None
    seen: set = set()
    ordered: List[Tuple[str, str]] = []
    for t in (query or "").split():
        tk = t.strip("'()[]{}.,;:!?-")
        tl = tk.lower()
        if not tl or tl in _STOPWORDS:
            continue
        if len(tl) < 3 and not (tl.isalpha() and len(tl) <= 2 and tl not in ("a", "i", "an")):
            continue
        if tl in seen:
            continue
        seen.add(tl)
        ordered.append((tk, tl))
    if len(ordered) < 3:
        return None

    def _rank(i: int) -> int:
        tl = ordered[i][1]
        if any(c.isdigit() for c in tl):
            return 0
        if ordered[i][0][:1].isupper():
            return 1
        return 2

    if alt:
        # v5.3 variant B: years + proper nouns + the first two remaining
        # words. Reads like a human query; unblocks engines that returned
        # nothing for variant A's collocations.
        years = [i for i in range(len(ordered)) if any(c.isdigit() for c in ordered[i][1])]
        caps = [i for i in range(len(ordered)) if ordered[i][0][:1].isupper()]
        taken = set(years) | set(caps)
        rest = [i for i in range(len(ordered)) if i not in taken]
        idx = sorted(set(years + caps + rest[:2]))[:5]
        if len(idx) < 3:
            idx = sorted(range(len(ordered)), key=_rank)[:4]
            idx.sort()
        return " ".join(ordered[i][0] for i in idx)
    keep = 5 if _nterms >= 7 else _nterms - 1
    keep = max(3, min(keep, 5))
    if keep >= _nterms:
        return None
    idx = sorted(range(len(ordered)), key=_rank)[:keep]
    idx.sort()
    return " ".join(ordered[i][0] for i in idx)


def build_engine_table() -> Dict[str, Tuple[Callable, float, bool, bool, bool]]:
    tbl: Dict[str, Tuple[Callable, float, bool, bool, bool]] = {}
    for name, fn, rate, needs_ddgs, px, rl in BUILTIN_ENGINES:
        tbl[name] = (fn, rate, needs_ddgs, px, rl)
    for name, fn in KEY_ENGINES.items():
        tbl.setdefault(name, (fn, 2.0, False, False, False))
    return tbl


# ---------------------------------------------------------------------------
# The Router: `FreeSearch` (with Parallel Hedged Racing + Fast-First Egress)
# ---------------------------------------------------------------------------

class FreeSearch:
    """Unmetered web search router with parallel hedged racing (`race=True`),
    fast-first egress routing (`direct` across all engines before `proxy`),
    and a dedicated Google Search fleet."""

    def __init__(
        self,
        priority: Optional[Sequence[str]] = None,
        google_only: bool = False,
        egress: Optional[Sequence[str]] = None,
        use_proxy: Optional[bool] = None,
        use_relay: Optional[bool] = None,
        cache: Optional[ResultCache] = None,
        proxies: Optional[ProxyPool] = None,
        timeout: Optional[float] = None,
        region: str = "us-en",
        per_domain: int = 3,
        use_cache: Optional[bool] = None,
        min_relevance: Optional[float] = None,
        allow_low_quality: Optional[bool] = None,
        race: Optional[bool] = None,
        race_width: Optional[int] = None,
        deadline: Optional[float] = None,
        parallel_width: Optional[int] = None,
        verbose: bool = False,
    ):
        self.table = build_engine_table()
        base_prio = GOOGLE_PRIORITY if google_only else DEFAULT_PRIORITY
        prio = priority if priority is not None else _env_list(
            "SEARCH_ENGINES", [p.strip() for p in base_prio.split(",")]
        )
        self.priority: List[str] = []
        for name in prio:
            if name == "*":
                self.priority.extend(sorted(self.table))
            elif name in self.table and name not in self.priority:
                self.priority.append(name)
        if not self.priority:
            self.priority = ["startpage_html", "google_html", "yahoo_html", "bing_html"]

        # v4: relay rides in the default chain. On datacenter IPs the
        # relay fetches from ITS ip - the only way through an ASN-level
        # wall. SEARCH_USE_RELAY=0 -> old direct+proxy chain; the
        # SEARCH_EGRESS env still overrides everything.
        default_egress = (
            ["direct", "proxy"] if not _env_bool("SEARCH_USE_RELAY", True)
            else ["direct", "relay", "proxy"]
        )
        order = egress if egress is not None else _env_list("SEARCH_EGRESS", default_egress)
        self.egress_order = [e for e in order if e in EGRESS_ORDER] or ["direct"]
        if use_proxy is False:
            self.egress_order = [e for e in self.egress_order if e != "proxy"] or ["direct"]
        if use_relay is False:
            self.egress_order = [e for e in self.egress_order if e != "relay"] or ["direct"]
        if use_proxy is True and "proxy" not in self.egress_order:
            self.egress_order.append("proxy")

        self.use_proxy = "proxy" in self.egress_order
        self.use_relay = "relay" in self.egress_order
        self.cache = cache if cache is not None else ResultCache()
        self.proxies = proxies if proxies is not None else ProxyPool(google_mode=google_only)
        self.timeout = timeout or _env_float("SEARCH_TIMEOUT", 10.0)
        self.proxy_timeout = _env_float("SEARCH_PROXY_TIMEOUT", 6.5)
        self.relay_timeout = _env_float("SEARCH_RELAY_TIMEOUT", 12.0)
        self.proxy_retries = max(0, _env_int("SEARCH_PROXY_RETRIES", 2))
        self.relay_retries = max(0, _env_int("SEARCH_RELAY_RETRIES", 1))
        self.region = region or "us-en"
        self.per_domain = max(1, int(per_domain))
        self.min_relevance = min(1.0, max(0.0, (
            _env_float("SEARCH_MIN_RELEVANCE", 0.25) if min_relevance is None else float(min_relevance)
        )))
        self.use_cache_default = self.cache.enabled if use_cache is None else bool(use_cache)
        self.allow_low_quality = (
            _env_bool("SEARCH_ALLOW_LOW_QUALITY", True)  # v4: never-empty
            if allow_low_quality is None
            else bool(allow_low_quality)
        )
        # Parallel hedged racing: fire top N engines concurrently for ~400ms latency!
        self.race = _env_bool("SEARCH_RACE", True) if race is None else bool(race)
        self.race_width = max(2, _env_int("SEARCH_RACE_WIDTH", 4) if race_width is None else int(race_width))
        self.verbose = verbose

        self._hlock = threading.Lock()
        self._health: Dict[str, EngineHealth] = {}
        rate_scale = _env_float("SEARCH_RATE_SCALE", 1.0)
        for name in self.table:
            rate = self.table[name][1] * rate_scale
            self._health[name] = EngineHealth(
                name=name,
                rate=rate,
                base_rate=rate,
                rate_min=max(0.02, 0.05 * rate_scale),
                rate_max=max(8.0, rate * 6) * rate_scale,
            )
        self._relay_idx = 0
        self._rl_lock = threading.Lock()
        self.counters: Dict[str, int] = defaultdict(int)
        self._started = time.time()
        self._proxy_ready = False
        self._proxy_building = False

        # ---- v3: deadline + full-parallel routing ----------------------
        self.deadline = max(0.8, float(deadline) if deadline is not None
                             else _env_float("SEARCH_DEADLINE", 3.0))
        self.parallel_width = max(2, int(parallel_width) if parallel_width is not None
                                  else _env_int("SEARCH_PARALLEL_WIDTH", 12))

        # v3: preload the free-proxy pool in the background so a walled
        # direct tier escalates to proxies without paying the ~6s harvest.
        if self.use_proxy:
            threading.Thread(target=self._bg_proxies, daemon=True).start()

    def health(self, name: str) -> EngineHealth:
        with self._hlock:
            h = self._health.get(name)
            if h is None:
                h = EngineHealth(name=name, rate=self.table.get(name, (None, 1.0, False, False, False))[1])
                self._health[name] = h
            return h

    def _next_relay(self) -> Optional[Tuple[str, str]]:
        relays = _env_list("SEARCH_RELAYS", list(DEFAULT_RELAYS))
        if not relays:
            return None
        with self._rl_lock:
            r = relays[self._relay_idx % len(relays)]
            self._relay_idx += 1
        return r

    def _bg_proxies(self) -> None:
        """v3: background preload of the free-proxy pool (never blocks
        a query thread; started from __init__ when proxy egress is on)."""
        if self._proxy_building or self._proxy_ready:
            return
        self._proxy_building = True
        try:
            ok = self.proxies.ensure()
            self._proxy_ready = ok or self.proxies.alive_count() > 0
        except Exception:
            pass  # v3: process exiting mid-build; stay quiet
        finally:
            self._proxy_building = False

    def _ensure_proxies(self) -> bool:
        if not self.use_proxy:
            return False
        floor = max(2, _env_int("PROXY_REBUILD_BELOW", 3))
        if self._proxy_ready:
            alive = self.proxies.alive_count()
            if alive >= floor:
                return True
            if alive > 0 and self.proxies.stats().get("builds", 0) >= self.proxies.max_builds:
                return True
            rebuilt = self.proxies.build(force=True)
            return rebuilt or alive > 0
        if self._proxy_building:
            # v3: a background build is running; use whatever is alive now
            # instead of blocking the deadline on a 6s harvest.
            return self.proxies.alive_count() > 0
        self._proxy_ready = self.proxies.ensure()
        return self._proxy_ready

    def _attempt(
        self,
        engine: str,
        query: str,
        n: int,
        page: int,
        region: str,
        timelimit: str,
        egress: str,
        try_index: int = 0,
        tmo_cap: Optional[float] = None,
    ) -> Tuple[List[Hit], str, str]:
        fn, _rate, needs_ddgs, supports_px, supports_rl = self.table[engine]
        if needs_ddgs and not HAVE_DDGS:
            raise EngineDown("ddgs not installed")
        if engine in KEY_ENVS and not os.getenv(KEY_ENVS[engine], "").strip():
            raise EngineDown(f"{engine}:no-key")

        proxy = None
        relay = None
        prefer_google = "google" in engine or "startpage" in engine
        if egress == "proxy":
            if not supports_px:
                raise EngineDown("engine does not support proxies")
            if not self._ensure_proxies():
                raise EngineDown("no proxy pool available")
            proxy = self.proxies.next(prefer_google=prefer_google)
            if not proxy:
                raise EngineDown("proxy pool exhausted")
        elif egress == "relay":
            if not supports_rl:
                raise EngineDown("engine does not support relays")
            relay = self._next_relay()

        h = self.health(engine)
        slept = h.acquire()
        self.counters["throttle_sleep_ms"] += int(slept * 1000)
        if tmo_cap is not None and slept > 0.75 and slept > tmo_cap * 0.5:
            # v3: this engine's rate-wait would eat the deadline; skip it
            raise EngineDown("rate-wait-skipped(deadline)")

        tmo = (
            self.proxy_timeout if egress == "proxy"
            else self.relay_timeout if egress == "relay"
            else self.timeout
        )
        if tmo_cap is not None:
            tmo = max(0.5, min(tmo, tmo_cap))
        sess = _mk_session(proxy=proxy, ua=USER_AGENTS[try_index % len(USER_AGENTS)])
        t0 = time.time()
        try:
            hits = fn(
                query, n, page, region, timelimit, sess,
                timeout=tmo, relay=relay, proxy=proxy, try_index=try_index,
            )
        except (BotWalled, EngineDown, EgressRetry):
            if proxy:
                self.proxies.mark_dead(proxy)
            raise
        except Exception as e:
            if proxy:
                self.proxies.mark_dead(proxy)
            raise EngineDown(f"{type(e).__name__}:{str(e)[:120]}") from e
        finally:
            sess.close()

        ms = (time.time() - t0) * 1000.0
        clean = [x for x in (hits or []) if not is_junk_url(x.url)]
        if proxy:
            if clean:
                self.proxies.mark_ok(proxy, google_ok=prefer_google)
            else:
                self.proxies.mark_dead(proxy)
        if not clean:
            raise EngineDown(f"{engine}:all-results-filtered-as-junk")
        h.note_ok(len(clean), ms)
        return clean, proxy or "", (relay[0] if relay else "")

    def _race_candidates(
        self,
        candidates: List[Tuple[str, str, int]],
        query: str,
        max_results: int,
        page: int,
        region: str,
        timelimit: str,
        min_rel: float,
        tmo_cap: Optional[float] = None,
        stop_at: Optional[float] = None,
    ) -> Tuple[Optional[Tuple[List[Hit], str, str, str, float]], Optional[Tuple[List[Hit], str, str, str, float]], List[str], int]:
        """Fire `candidates` [(engine, egress, try_idx), ...] concurrently and
        return the first candidate whose results pass `min_rel`. v3: every
        attempt is capped by tmo_cap and the whole race stops at stop_at."""
        errors: List[str] = []
        fallback: Optional[Tuple[List[Hit], str, str, str, float]] = None
        winner: Optional[Tuple[List[Hit], str, str, str, float]] = None
        attempts = len(candidates)
        self.counters["attempts"] += attempts

        ex = ThreadPoolExecutor(max_workers=len(candidates))
        try:
            fut_map = {
                ex.submit(
                    self._attempt, eng, query, max_results, page, region, timelimit, eg,
                    try_i, tmo_cap
                ): (eng, eg)
                for eng, eg, try_i in candidates
            }
            pending = set(fut_map.keys())
            while pending:
                _tmo = max(0.0, stop_at - time.time()) if stop_at is not None else None
                if _tmo is not None and _tmo <= 0:
                    break
                done, pending = wait(pending, timeout=_tmo, return_when=FIRST_COMPLETED)
                for fut in done:
                    eng, eg = fut_map[fut]
                    h = self.health(eng)
                    try:
                        hits, px, _rl = fut.result()
                    except EgressRetry as e:
                        self.counters["egress_retries"] += 1
                        errors.append(f"{eng}/{eg} egress retry: {e}")
                        continue
                    except BotWalled as e:
                        h.trip(str(e), wall=True)
                        self.counters["walls"] += 1
                        errors.append(f"{eng}/{eg} walled: {e}")
                        continue
                    except Exception as e:
                        h.trip(str(e), wall=False)
                        self.counters["engine_errors"] += 1
                        errors.append(f"{eng}/{eg} down: {e}")
                        continue

                    self.counters["engine_ok"] += 1
                    self.counters[f"ok:{eng}"] += 1
                    self.counters[f"ok_egress:{eg}"] += 1
                    rel = relevance(query, hits)
                    if rel < min_rel:
                        self.counters["low_quality"] += 1
                        h.trip(f"low-relevance:{rel:.2f}")
                        errors.append(f"{eng}/{eg} off-topic (rel={rel:.2f} < {min_rel:.2f})")
                        if fallback is None and hits:
                            fallback = (list(hits), eng, eg, px, rel)
                        continue

                    winner = (list(hits), eng, eg, px, rel)
                    return winner, fallback, errors, attempts
                if stop_at is not None and time.time() >= stop_at and pending:
                    errors.append("deadline reached with %d engine(s) pending" % len(pending))
                    break
        finally:
            ex.shutdown(wait=False, cancel_futures=True)

        return None, fallback, errors, attempts

    def search(
        self,
        query: str,
        max_results: int = 10,
        page: int = 1,
        region: Optional[str] = None,
        timelimit: Optional[str] = None,
        engine: Optional[str] = None,
        egress: Optional[str] = None,
        google_only: bool = False,
        use_cache: Optional[bool] = None,
        multi: bool = False,
        race: Optional[bool] = None,
        allow_low_quality: Optional[bool] = None,
        min_relevance: Optional[float] = None,
        max_attempts: Optional[int] = None,
    ) -> SearchOutcome:
        """Search with parallel hedged racing + fast-first egress failover."""
        query = (query or "").strip()
        t_start = time.time()
        region = region or self.region
        use_cache = self.use_cache_default if use_cache is None else bool(use_cache)
        max_attempts = max_attempts or _env_int("SEARCH_MAX_ATTEMPTS", 14)
        allow_lq = self.allow_low_quality if allow_low_quality is None else bool(allow_low_quality)
        min_rel = self.min_relevance if min_relevance is None else min(1.0, max(0.0, float(min_relevance)))
        do_race = (self.race if race is None else bool(race)) and not multi and not engine

        out = SearchOutcome(query=query)
        if not query:
            out.deferred = True
            out.errors.append("empty query")
            return out

        if engine:
            engines = [engine]
        elif google_only:
            engines = [e.strip() for e in GOOGLE_PRIORITY.split(",") if e.strip() in self.table]
        else:
            engines = list(self.priority)
        egresses = [egress] if egress else list(self.egress_order)

        # ---- Cache lookup ----
        cache_key = ""
        if use_cache:
            cache_tag = engine or ("google" if google_only else "auto")
            cache_key = self.cache.key(query, cache_tag, max_results, region, timelimit or "")
            cached = self.cache.get(cache_key)
            if cached:
                cand = [
                    Hit(**{k: v for k, v in h.items() if k in ("title", "url", "snippet", "source", "rank")})
                    for h in cached
                ]
                # v5.1: re-validate rows written by an OLDER version. A row
                # scored by the old (broken) relevance must not be served
                # forever; below the gate it is discarded and re-searched.
                rel_cached = relevance(query, cand)
                if rel_cached < 0.25 or not cand:
                    self.cache.delete(cache_key)
                    self.counters["cache_misses"] += 1
                    out.errors.append(
                        "cache: stale row discarded (re-scored %.2f < 0.25)" % rel_cached
                    )
                else:
                    self.counters["cache_hits"] += 1
                    out.results = cand
                    out.from_cache = True
                    out.engine = "cache"
                    out.relevance = rel_cached
                    out.low_quality = rel_cached < 0.4
                    out.elapsed_ms = int((time.time() - t_start) * 1000)
                    return out
            self.counters["cache_misses"] += 1

        merged: List[Hit] = []
        seen_urls: set = set()
        fallback: Optional[Tuple[List[Hit], str, str, str, float]] = None

        # Filter engines that are ready and have dependencies installed
        ready_engines: List[str] = []
        for eng in engines:
            if eng not in self.table:
                continue
            _fn, _rate, needs_ddgs, _px, _rl = self.table[eng]
            if needs_ddgs and not HAVE_DDGS:
                continue
            if eng in KEY_ENVS and not os.getenv(KEY_ENVS[eng], "").strip():
                continue
            h = self.health(eng)
            if not h.ready():
                out.errors.append(f"{eng}:cooldown({int(h.cooldown_until - time.time())}s)")
                continue
            ready_engines.append(eng)

        # ---- v3 Fast Path: ONE deadline-bounded full-parallel race ----------
        # v2 fired 4 engines at a time and waited for each wave to fully fail
        # before the next; on walled datacenter IPs that measured 8-30s. v3
        # races ALL healthy direct engines at once; the first engine that
        # passes min_rel wins. Every attempt is capped by the time left, so
        # the answer (or a labeled best-effort) lands under self.deadline.
        stop_at = t_start + self.deadline
        raced_direct = False
        first_rel = 0.0
        best_rel = 0.0

        def _cap(floor: float = 0.4) -> Optional[float]:
            left = stop_at - time.time()
            if left <= floor:
                return None
            # v4: tight per-attempt cap — healthy engines answer <1s; a hanging
            # engine must not outlive the answer. The 1.5s hard max bounds the
            # interpreter-exit join of the (non-daemon) race pool so the CLI
            # wall stays well under 3s even when engines hang.
            return max(0.8, min(1.5, left * 0.8))

        _fresh = _recency_cue(query)
        _q2 = _condense_query(query)
        if _fresh:
            # v5: freshness cue - news engines lead the race
            ready_engines.sort(key=lambda e: e not in _NEWS_FEED_ENGINES)
        if not merged and do_race and "direct" in egresses and len(ready_engines) >= 2:
            _web = [e for e in ready_engines if e not in _NEWS_FEED_ENGINES or _fresh]
            if len(_web) >= 2:
                wave = [(eng, "direct", 0) for eng in _web[: self.parallel_width]]
            else:  # nearly everything walled; let feed engines race too
                wave = [(eng, "direct", 0) for eng in ready_engines[: self.parallel_width]]
            # v4: relay rides IN the race for the top relay-capable engines.
            # The relay fetches from its own ip, rescuing engines that just
            # got walled direct on a datacenter ASN.
            if "relay" in egresses:
                _rl_pool = ("google_html", "yahoo_html", "brave_html", "bing_html",
                            "ddg_html", "searxng", "bing_rss")
                _in_wave = {e for e, _g, _t in wave}
                for eng in [e for e in ready_engines if e in _rl_pool and e in _in_wave][:2]:
                    wave.append((eng, "relay", 0))
            cap = _cap()
            if cap:
                winner, fb1, errs1, att1 = self._race_candidates(
                    wave, query, max_results, page, region, timelimit or "", min_rel,
                    tmo_cap=cap, stop_at=stop_at,
                )
                out.attempts += att1
                out.errors.extend(errs1)
                if fb1 and fallback is None:
                    fallback = fb1
                if winner is not None:
                    w_hits, w_eng, w_eg, w_px, _w_rel = winner
                    self._merge(merged, w_hits, seen_urls)
                    out.engine, out.egress, out.proxy = w_eng, w_eg, w_px
                    first_rel = _w_rel or 0.0
                    best_rel = first_rel
            raced_direct = True

        # ---- v5 condensed retry ------------------------------------------
        # Long keyword-stuffed queries make engines answer with garbage
        # ('Best Buy' for a movies query). If the full-query wave produced
        # nothing on-topic, refire the top engines once with the condensed
        # 6-term version. Logged transparently in errors.
        if _q2 and do_race and "direct" in egresses and len(ready_engines) >= 2 \
                and (not merged or first_rel < 0.5):
            cap2 = _cap()
            if cap2:
                _web2 = [e for e in ready_engines if e not in _NEWS_FEED_ENGINES or _fresh]
                wave2 = [(eng, "direct", 0) for eng in _web2[: self.parallel_width]]
                if "relay" in egresses:
                    _rl_pool = ("google_html", "yahoo_html", "brave_html", "bing_html",
                                "ddg_html", "searxng", "bing_rss")
                    _in2 = {e for e, _g, _t in wave2}
                    for eng in [e for e in ready_engines if e in _rl_pool and e in _in2][:2]:
                        wave2.append((eng, "relay", 0))
                out.errors.append(
                    "condensed retry: %r (%d -> %d terms; first-wave rel %.2f)" % (
                        _q2, len(query_terms(query)), len(query_terms(_q2)), first_rel
                    )
                )
                winner2, fb2, errs2, att2 = self._race_candidates(
                    wave2, _q2, max_results, page, region, timelimit or "", min_rel,
                    tmo_cap=cap2, stop_at=stop_at,
                )
                out.attempts += att2
                out.errors.extend(errs2)
                if fb2 and fallback is None:
                    fallback = fb2
                if winner2 is not None:
                    w_hits, w_eng, w_eg, w_px, _w2_race = winner2
                    # v5.4: the race score (_w2_race) is measured against the
                    # CONDENSED query the engine was asked. The replacement
                    # decision uses the ORIGINAL query's yardstick - the
                    # question the user actually asked.
                    w2_rel = relevance(query, w_hits) if w_hits else 0.0
                    if not merged or w2_rel > best_rel + 0.05:
                        merged.clear()
                        seen_urls.clear()
                        self._merge(merged, w_hits, seen_urls)
                        out.engine, out.egress, out.proxy = w_eng, w_eg, w_px
                        out.errors.append(
                            "condensed retry upgraded %.2f -> %.2f (user yardstick)"
                            % (best_rel, w2_rel)
                        )
                        best_rel = w2_rel

        # ---- v5.3 alt condensation wave -----------------------------------
        # Fires when the standing answer is still below 0.5 after wave2.
        # Variant B (years + proper nouns + first words) often unblocks
        # engines that returned nothing for variant A. Replaces the answer
        # only if strictly better (+0.05); best_rel guards across waves.
        _q3 = _condense_query(query, alt=True)
        if _q3 and _q3 != _q2 and do_race and "direct" in egresses \
                and len(ready_engines) >= 2 and (not merged or best_rel < 0.5):
            cap3 = _cap()
            if cap3:
                _web3 = [e for e in ready_engines if e not in _NEWS_FEED_ENGINES or _fresh]
                wave3 = [(eng, "direct", 0) for eng in _web3[: self.parallel_width]]
                if "relay" in egresses:
                    _rl_pool = ("google_html", "yahoo_html", "brave_html", "bing_html",
                                "ddg_html", "searxng", "bing_rss")
                    _in3 = {e for e, _g, _t in wave3}
                    for eng in [e for e in ready_engines if e in _rl_pool and e in _in3][:2]:
                        wave3.append((eng, "relay", 0))
                out.errors.append("alt condensed retry: %r" % _q3)
                winner3, fb3, errs3, att3 = self._race_candidates(
                    wave3, _q3, max_results, page, region, timelimit or "", min_rel,
                    tmo_cap=cap3, stop_at=stop_at,
                )
                out.attempts += att3
                out.errors.extend(errs3)
                if fb3 and fallback is None:
                    fallback = fb3
                if winner3 is not None:
                    w_hits, w_eng, w_eg, w_px, _w3_race = winner3
                    # v5.4: same rule as wave2 - decide on the original
                    # query's yardstick, not the condensed one.
                    w3_rel = relevance(query, w_hits) if w_hits else 0.0
                    if not merged or w3_rel > best_rel + 0.05:
                        merged.clear()
                        seen_urls.clear()
                        self._merge(merged, w_hits, seen_urls)
                        out.engine, out.egress, out.proxy = w_eng, w_eg, w_px
                        out.errors.append(
                            "alt condensed retry upgraded %.2f -> %.2f (user yardstick)"
                            % (best_rel, w3_rel)
                        )
                        best_rel = w3_rel

        # ---- v3 egress escalation (remaining direct / proxy / relay) --------
        # Entered only when the fan-out produced nothing (or multi mode). The
        # same deadline governs every attempt; tiers are skipped when the
        # budget is spent instead of stalling for tens of seconds.
        if not merged or multi:
            for eg in egresses:
                if eg == "direct" and raced_direct and not multi:
                    # v3: un-raced tail PLUS feed engines excluded from the race
                    rem_engines = ready_engines[self.parallel_width:]
                    rem_engines += [e for e in ready_engines if e in _NEWS_FEED_ENGINES]
                    rem_engines = list(dict.fromkeys(rem_engines))
                else:
                    rem_engines = ready_engines
                if not rem_engines:
                    continue
                for eng in rem_engines:
                    if out.attempts >= max_attempts:
                        break
                    if merged and not multi:
                        break
                    remaining = stop_at - time.time()
                    if remaining <= 0.4:
                        out.errors.append(
                            "%s: skipped (deadline %.1fs reached)" % (eg, self.deadline)
                        )
                        break
                    _fn, _rate, _needs_ddgs, supports_px, supports_rl = self.table[eng]
                    if eg == "proxy" and not supports_px:
                        continue
                    if eg == "relay" and not supports_rl:
                        continue

                    h = self.health(eng)
                    retries = (
                        self.proxy_retries if eg == "proxy"
                        else self.relay_retries if eg == "relay"
                        else 0
                    )
                    engine_succeeded = False
                    for attempt_i in range(retries + 1):
                        if out.attempts >= max_attempts:
                            break
                        remaining = stop_at - time.time()
                        if remaining <= 0.4:
                            break
                        out.attempts += 1
                        self.counters["attempts"] += 1
                        try:
                            hits, px, _rl = self._attempt(
                                eng, query, max_results, page, region, timelimit or "", eg,
                                try_index=attempt_i, tmo_cap=max(1.0, remaining * 0.9),
                            )
                        except EgressRetry as e:
                            self.counters["egress_retries"] += 1
                            out.errors.append("%s/%s egress retry: %s" % (eng, eg, e))
                            continue
                        except BotWalled as e:
                            h.trip(str(e), wall=True)
                            self.counters["walls"] += 1
                            out.errors.append("%s/%s walled: %s" % (eng, eg, e))
                            break
                        except EngineDown as e:
                            h.trip(str(e), wall=False)
                            self.counters["engine_errors"] += 1
                            out.errors.append("%s/%s down: %s" % (eng, eg, e))
                            break
                        except Exception as e:
                            h.trip("%s:%s" % (type(e).__name__, e))
                            self.counters["unexpected"] += 1
                            out.errors.append("%s/%s error: %s: %s" % (eng, eg, type(e).__name__, e))
                            break

                        self.counters["engine_ok"] += 1
                        self.counters["ok:%s" % eng] += 1
                        self.counters["ok_egress:%s" % eg] += 1
                        rel = relevance(query, hits)
                        if rel < min_rel:
                            self.counters["low_quality"] += 1
                            h.trip("low-relevance:%.2f" % rel)
                            out.errors.append(
                                "%s/%s off-topic (relevance %.2f < %.2f) - rejected"
                                % (eng, eg, rel, min_rel)
                            )
                            if fallback is None and hits:
                                fallback = (list(hits), eng, eg, px, rel)
                            continue

                        self._merge(merged, hits, seen_urls)
                        if not out.engine:
                            out.engine, out.egress, out.proxy = eng, eg, px
                        engine_succeeded = True
                        break

                    if engine_succeeded and not multi:
                        break
                    if engine_succeeded and len(merged) >= max_results * 2:
                        break
                if (not multi and merged) or (multi and len(merged) >= max_results):
                    break

        if not merged and fallback is not None:
            fb_hits, fb_eng, fb_eg, fb_px, fb_rel = fallback
            if allow_lq:
                merged = list(fb_hits)
                out.engine, out.egress, out.proxy = fb_eng, fb_eg, fb_px
                out.low_quality = True
                self.counters["low_quality_used"] += 1
            else:
                self.counters["low_quality_discarded"] += 1
                out.errors.append(
                    f"best available was off-topic ({fb_eng} relevance {fb_rel:.2f}) - deferred"
                )

        out.results = self._cap_domains(merged)[:max_results]
        for i, h_item in enumerate(out.results, 1):
            h_item.rank = i
        out.relevance = relevance(query, out.results) if out.results else 0.0
        out.elapsed_ms = int((time.time() - t_start) * 1000)
        if out.results:
            self.counters["queries_ok"] += 1
            self.counters["results"] += len(out.results)
            if cache_key and not out.low_quality:
                self.cache.put(
                    cache_key,
                    [
                        {
                            "title": h_item.title,
                            "url": h_item.url,
                            "snippet": h_item.snippet,
                            "source": h_item.source,
                            "rank": h_item.rank,
                        }
                        for h_item in out.results
                    ],
                    out.engine,
                )
        else:
            out.deferred = True
            self.counters["queries_deferred"] += 1
        return out

    def _merge(self, dest: List[Hit], hits: List[Hit], seen: set) -> int:
        added = 0
        for h in hits:
            c = canon_url(h.url)
            if not c or c in seen:
                continue
            seen.add(c)
            dest.append(h)
            added += 1
        return added

    def _cap_domains(self, hits: List[Hit]) -> List[Hit]:
        if self.per_domain <= 0:
            return hits
        counts: Dict[str, int] = defaultdict(int)
        out = []
        for h in hits:
            try:
                host = urllib.parse.urlparse(h.url).netloc.lower()
                if host.startswith("www."):
                    host = host[4:]
                parts = host.split(".")
                root = ".".join(parts[-2:]) if len(parts) >= 2 else host
            except Exception:
                root = h.url[:40]
            if counts[root] >= self.per_domain:
                continue
            counts[root] += 1
            out.append(h)
        return out

    def search_many(
        self,
        queries: Sequence[str],
        max_results: int = 10,
        workers: Optional[int] = None,
        page: int = 1,
        region: Optional[str] = None,
        timelimit: Optional[str] = None,
        google_only: bool = False,
        use_cache: Optional[bool] = None,
        multi: bool = False,
        allow_low_quality: Optional[bool] = None,
        min_relevance: Optional[float] = None,
        progress: bool = True,
    ) -> List[SearchOutcome]:
        queries = [q.strip() for q in queries if q and q.strip()]
        if not queries:
            return []
        workers = max(1, min(int(workers or _env_int("SEARCH_WORKERS", 8)), len(queries)))
        results: List[Optional[SearchOutcome]] = [None] * len(queries)
        done = 0
        lock = threading.Lock()
        t0 = time.time()

        def _one(i_q):
            i, q = i_q
            try:
                return i, self.search(
                    q,
                    max_results=max_results,
                    page=page,
                    region=region,
                    timelimit=timelimit,
                    google_only=google_only,
                    use_cache=use_cache,
                    multi=multi,
                    allow_low_quality=allow_low_quality,
                    min_relevance=min_relevance,
                )
            except Exception as e:
                return i, SearchOutcome(query=q, deferred=True, errors=[f"fatal:{type(e).__name__}:{e}"])

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_one, (i, q)) for i, q in enumerate(queries)]
            for fut in as_completed(futs):
                i, o = fut.result()
                results[i] = o
                with lock:
                    done += 1
                    if progress and (done % 10 == 0 or done == len(queries)):
                        el = time.time() - t0
                        logger.info(
                            "batch %d/%d  %.1fs  ok=%d deferred=%d",
                            done, len(queries), el,
                            sum(1 for r in results if r and not r.deferred),
                            sum(1 for r in results if r and r.deferred),
                        )
        return [r for r in results if r is not None]

    def search_many_with_retry(
        self,
        queries: Sequence[str],
        rounds: Optional[int] = None,
        cooldown: Optional[float] = None,
        **kw,
    ) -> List[SearchOutcome]:
        rounds = max(1, int(rounds or _env_int("SEARCH_RETRY_ROUNDS", 3)))
        cooldown = cooldown if cooldown is not None else _env_float("SEARCH_RETRY_COOLDOWN", 15.0)
        outs: Dict[str, SearchOutcome] = {}
        pending = [q.strip() for q in queries if q and q.strip()]
        for rnd in range(1, rounds + 1):
            if not pending:
                break
            got = self.search_many(pending, **kw)
            still: List[str] = []
            for o in got:
                if o.deferred:
                    still.append(o.query)
                else:
                    outs[o.query] = o
            pending = still
            if pending and rnd < rounds:
                self.reset_cooldowns(partial=True)
                time.sleep(cooldown)
        for q in pending:
            outs[q] = SearchOutcome(query=q, deferred=True, errors=[f"deferred after {rounds} round(s)"])
        order = {q: i for i, q in enumerate([x.strip() for x in queries if x and x.strip()])}
        return sorted(outs.values(), key=lambda o: order.get(o.query, 10**6))

    def reset_cooldowns(self, partial: bool = False) -> None:
        with self._hlock:
            for h in self._health.values():
                if partial:
                    left = h.cooldown_until - time.time()
                    if left <= _env_float("SEARCH_RETRY_MAX_COOLDOWN", 120.0):
                        h.cooldown_until = 0.0
                        h.consecutive_fail = 0
                        h.strikes = max(0, h.strikes - 1)
                else:
                    h.cooldown_until = 0.0
                    h.consecutive_fail = 0
                    h.strikes = 0

    def stats(self) -> Dict[str, Any]:
        with self._hlock:
            hs = {
                n: {
                    "ok": h.ok,
                    "fail": h.fail,
                    "walls": h.walls,
                    "results": h.results,
                    "strikes": h.strikes,
                    "cooldown_s": max(0, int(h.cooldown_until - time.time())),
                    "rate_qps": round(h.rate, 3),
                    "avg_ms": int(h.total_ms / h.ok) if h.ok else 0,
                    "last_error": h.last_error,
                }
                for n, h in self._health.items() if (h.ok or h.fail)
            }
        st = dict(self.counters)
        st.update({
            "uptime_s": int(time.time() - self._started),
            "cache_hits": self.cache.hits,
            "cache_misses": self.cache.misses,
            "cache_rows": self.cache.size(),
            "proxies": self.proxies.stats(),
            "engines": hs,
            "ddgs_installed": HAVE_DDGS,
            "curl_cffi_installed": HAVE_CURL_CFFI,
            "browser_cdp": _find_chromium_binary() or False,
            "egress_order": self.egress_order,
            "priority": self.priority[:14],
            "key_backends": sorted(k for k, v in KEY_ENVS.items() if os.getenv(v, "").strip()),
        })
        return st

    def selftest(
        self,
        query: str = "python requests library",
        n: int = 3,
        test_proxy: bool = False,
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        have_px = self._ensure_proxies() if test_proxy else False
        for eng in self.priority:
            fn, _rate, needs_ddgs, supports_px, supports_rl = self.table[eng]
            if needs_ddgs and not HAVE_DDGS:
                rows.append({"engine": eng, "egress": "-", "status": "skip", "detail": "ddgs not installed", "n": 0, "ms": 0})
                continue
            if eng in KEY_ENVS and not os.getenv(KEY_ENVS[eng], "").strip():
                rows.append({"engine": eng, "egress": "-", "status": "skip", "detail": f"{KEY_ENVS[eng]} not set", "n": 0, "ms": 0})
                continue
            for eg in ("direct", "proxy", "relay"):
                if eg == "proxy" and (not have_px or not supports_px):
                    continue
                if eg == "relay" and (not self.use_relay or not supports_rl):
                    continue
                t0 = time.time()
                try:
                    hits, px, _rl = self._attempt(eng, query, n, 1, self.region, "", eg, try_index=0)
                    rows.append({
                        "engine": eng,
                        "egress": eg,
                        "status": "OK",
                        "n": len(hits),
                        "ms": int((time.time() - t0) * 1000),
                        "detail": (hits[0].url[:60] if hits else ""),
                        "proxy": px,
                    })
                except BotWalled as e:
                    rows.append({
                        "engine": eng, "egress": eg, "status": "WALL",
                        "n": 0, "ms": int((time.time() - t0) * 1000), "detail": str(e)[:80],
                    })
                except Exception as e:
                    rows.append({
                        "engine": eng, "egress": eg, "status": "down",
                        "n": 0, "ms": int((time.time() - t0) * 1000),
                        "detail": f"{type(e).__name__}: {str(e)[:70]}",
                    })
                h = self.health(eng)
                h.cooldown_until = 0.0
                h.consecutive_fail = 0
                h.strikes = 0
        return rows


# ---------------------------------------------------------------------------
# Module-Level Convenience API (Drop-in)
# ---------------------------------------------------------------------------

_DEFAULT: Optional[FreeSearch] = None
_DEFAULT_LOCK = threading.Lock()


def default_client() -> FreeSearch:
    global _DEFAULT
    if _DEFAULT is None:
        with _DEFAULT_LOCK:
            if _DEFAULT is None:
                _DEFAULT = FreeSearch()
    return _DEFAULT


def search(query: str, max_results: int = 10, **kw) -> List[Dict[str, Any]]:
    o = default_client().search(query, max_results=max_results, **kw)
    return [h.to_dict() for h in o.results]


def google_search(query: str, max_results: int = 10, **kw) -> List[Dict[str, Any]]:
    """Dedicated Google-first search (Startpage Google syndication + Direct
    Google Web + Google CSE + Google CDP + Google News RSS)."""
    o = default_client().search(query, max_results=max_results, google_only=True, **kw)
    return [h.to_dict() for h in o.results]


def search_outcome(query: str, max_results: int = 10, **kw) -> SearchOutcome:
    return default_client().search(query, max_results=max_results, **kw)


def search_many(queries: Sequence[str], max_results: int = 10, **kw) -> List[SearchOutcome]:
    return default_client().search_many(queries, max_results=max_results, **kw)


def search_many_with_retry(queries: Sequence[str], max_results: int = 10, **kw) -> List[SearchOutcome]:
    return default_client().search_many_with_retry(queries, max_results=max_results, **kw)


def news(query: str, max_results: int = 10, **kw) -> List[Dict[str, Any]]:
    o = default_client().search(
        query, max_results=max_results, engine=kw.pop("engine", None) or "google_news_rss", **kw
    )
    if o.deferred:
        o = default_client().search(query, max_results=max_results, engine="bing_news", **kw)
    return [h.to_dict() for h in o.results]


# ---------------------------------------------------------------------------
# HTTP Server Mode
# ---------------------------------------------------------------------------

def serve(host: str = "127.0.0.1", port: int = 8078, client: Optional[FreeSearch] = None):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    fs = client or FreeSearch()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            logger.debug("http " + fmt, *args)

        def _send(self, code: int, obj: Any):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> Dict[str, Any]:
            try:
                length = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(length) or b"{}") if length else {}
            except Exception:
                return {}

        def do_GET(self):
            p = urllib.parse.urlparse(self.path)
            qs = {k: v[0] for k, v in urllib.parse.parse_qs(p.query).items()}
            if p.path in ("/", "/health"):
                return self._send(200, {"status": "ok", "version": VERSION, "engines": fs.priority[:14]})
            if p.path == "/stats":
                return self._send(200, fs.stats())
            if p.path in ("/search", "/search/text", "/v1/search", "/google"):
                q = qs.get("q") or qs.get("query") or ""
                n = int(qs.get("n") or qs.get("max_results") or qs.get("num") or 10)
                g_only = p.path == "/google" or qs.get("google") in ("1", "true", "yes")
                o = fs.search(
                    q,
                    max_results=min(n, 50),
                    engine=qs.get("engine") or None,
                    egress=qs.get("egress") or None,
                    google_only=g_only,
                    region=qs.get("region") or fs.region,
                    timelimit=qs.get("timelimit") or None,
                    multi=qs.get("multi") in ("1", "true", "yes"),
                )
                return self._send(200 if o.results else 202, o.to_dict())
            return self._send(404, {"error": "not found", "path": p.path})

        def do_POST(self):
            p = urllib.parse.urlparse(self.path)
            data = self._body()
            if p.path in ("/search", "/search/text", "/v1/search", "/google"):
                q = data.get("query") or data.get("q") or ""
                n = int(data.get("max_results") or data.get("n") or 10)
                g_only = p.path == "/google" or bool(data.get("google"))
                o = fs.search(
                    q,
                    max_results=min(n, 50),
                    engine=data.get("engine") or None,
                    egress=data.get("egress") or None,
                    google_only=g_only,
                    multi=bool(data.get("multi")),
                )
                return self._send(200 if o.results else 202, o.to_dict())
            if p.path in ("/batch", "/search/batch"):
                qs = data.get("queries") or []
                n = int(data.get("max_results") or 10)
                w = int(data.get("workers") or 8)
                outs = fs.search_many([str(x) for x in qs], max_results=min(n, 50), workers=w, progress=False)
                return self._send(
                    200,
                    {"results": [o.to_dict() for o in outs], "deferred": [o.query for o in outs if o.deferred]},
                )
            return self._send(404, {"error": "not found", "path": p.path})

    srv = ThreadingHTTPServer((host, port), Handler)
    logger.info("free-search API listening on http://%s:%d/search?q=...", host, port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _print_hits(o: SearchOutcome, as_json: bool, limit: int = 0):
    if as_json:
        print(json.dumps(o.to_dict(), ensure_ascii=False, indent=2))
        return
    print(
        f"\n{o.query!r}  -> {len(o.results)} results  "
        f"[engine={o.engine} egress={o.egress} "
        f"{'cache' if o.from_cache else 'live'} {o.elapsed_ms}ms]"
    )
    if o.deferred:
        print("  DEFERRED - no engine delivered; retry next run.")
        for e in o.errors[-5:]:
            print("   !", e)
    for h in (o.results[:limit] if limit else o.results):
        print(f"  {h.rank:>2}. {h.title[:90]}")
        print(f"      {h.url}")
        if h.snippet:
            print(f"      {h.snippet[:160]}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--log-level", default=os.getenv("SEARCH_LOG_LEVEL", "INFO"))

    prog_name = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "free_search.py"
    ap = argparse.ArgumentParser(
        prog=prog_name,
        parents=[common],
        description="Unmetered free web search (Cloud Datacenter & Fast Google Edition).",
    )
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("search", parents=[common], help="run one search")
    p.add_argument("query", nargs="+")
    p.add_argument("-n", "--max-results", type=int, default=10)
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--google", action="store_true", help="restrict to Google-backed engines only")
    p.add_argument("--engine", default=None, help="force one engine")
    p.add_argument("--egress", default=None, choices=list(EGRESS_ORDER) + [None])
    p.add_argument("--region", default="us-en")
    p.add_argument("--timelimit", default=None, choices=[None, "d", "w", "m", "y"])
    p.add_argument("--multi", action="store_true", help="merge several engines")
    p.add_argument("--no-race", action="store_true", help="disable parallel hedged racing")
    p.add_argument("--deadline", type=float, default=None,
                   help="per-query seconds budget (default 3.0; env SEARCH_DEADLINE)")
    p.add_argument("--width", type=int, default=None,
                   help="engines racing at once (default 12; env SEARCH_PARALLEL_WIDTH)")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--allow-low-quality", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("-o", "--out", default=None, help="write JSON to file")

    p = sub.add_parser("batch", parents=[common], help="run many searches concurrently")
    p.add_argument("file", help="text file with one query per line, or '-' for stdin")
    p.add_argument("-n", "--max-results", type=int, default=10)
    p.add_argument("-j", "--workers", type=int, default=8)
    p.add_argument("--google", action="store_true", help="restrict to Google-backed engines")
    p.add_argument("--multi", action="store_true")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--allow-low-quality", action="store_true")
    p.add_argument("--retry", action="store_true")
    p.add_argument("--json", default=None)
    p.add_argument("--csv", default=None)
    p.add_argument("--deferred", default=None)

    p = sub.add_parser("news", parents=[common], help="Google & Bing news search")
    p.add_argument("query", nargs="+")
    p.add_argument("-n", "--max-results", type=int, default=10)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("selftest", parents=[common], help="engine x egress health matrix")
    p.add_argument("-q", "--query", default="python requests library")
    p.add_argument("-n", "--max-results", type=int, default=3)
    p.add_argument("--proxy", action="store_true", help="also test proxy egress tier")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("proxies", parents=[common], help="harvest / validate the free proxy pool")
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--google", action="store_true", help="validate proxies specifically against Google Search")
    p.add_argument("--test", type=int, default=0)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("serve", parents=[common], help="run the drop-in HTTP search API")
    p.add_argument("--host", default=os.getenv("SEARCH_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.getenv("SEARCH_PORT", "8078")))

    sub.add_parser("stats", parents=[common], help="dump live stats + cache info")
    sub.add_parser("prune", parents=[common], help="delete expired cache rows")

    args = ap.parse_args(argv)
    _setup_logging(args.log_level)

    if args.cmd == "search":
        fs = FreeSearch(google_only=args.google, race=not args.no_race,
                        deadline=args.deadline, parallel_width=args.width)
        o = fs.search(
            " ".join(args.query),
            max_results=args.max_results,
            page=args.page,
            engine=args.engine,
            egress=args.egress,
            google_only=args.google,
            region=args.region,
            timelimit=args.timelimit,
            multi=args.multi,
            race=not args.no_race,
            allow_low_quality=True if args.allow_low_quality else None,
            use_cache=False if args.no_cache else None,
        )
        _print_hits(o, args.json)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(o.to_dict(), fh, ensure_ascii=False, indent=2)
            print(f"\nwrote {args.out}", file=sys.stderr)
        return 0 if o.results else 2

    if args.cmd == "batch":
        raw = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
        queries = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
        fs = FreeSearch(google_only=args.google)
        common_kw = dict(
            max_results=args.max_results,
            google_only=args.google,
            multi=args.multi,
            allow_low_quality=True if args.allow_low_quality else None,
            use_cache=False if args.no_cache else None,
        )
        runner = fs.search_many_with_retry if args.retry else fs.search_many
        outs = runner(queries, workers=args.workers, **common_kw)
        ok = [o for o in outs if not o.deferred]
        print(f"\nbatch done: {len(ok)}/{len(outs)} served, {sum(len(o.results) for o in outs)} results", file=sys.stderr)
        if args.json:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump([o.to_dict() for o in outs], fh, ensure_ascii=False, indent=2)
            print(f"wrote {args.json}", file=sys.stderr)
        if args.csv:
            with open(args.csv, "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["query", "rank", "title", "url", "snippet", "engine", "egress", "from_cache"])
                for o in outs:
                    for h in o.results:
                        w.writerow([o.query, h.rank, h.title, h.url, h.snippet, o.engine, o.egress, o.from_cache])
            print(f"wrote {args.csv}", file=sys.stderr)
        deferred = [o.query for o in outs if o.deferred]
        if args.deferred and deferred:
            with open(args.deferred, "w", encoding="utf-8") as fh:
                fh.write("\n".join(deferred) + "\n")
            print(f"wrote {len(deferred)} deferred queries to {args.deferred}", file=sys.stderr)
        return 0 if ok else 2

    if args.cmd == "news":
        res = news(" ".join(args.query), max_results=args.max_results)
        print(
            json.dumps(res, ensure_ascii=False, indent=2)
            if args.json
            else "\n".join(f"{r['rank']:>2}. {r['title']}\n    {r['url']}" for r in res)
        )
        return 0 if res else 2

    if args.cmd == "selftest":
        fs = FreeSearch()
        rows = fs.selftest(query=args.query, n=args.max_results, test_proxy=args.proxy)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'ENGINE':<20}{'EGRESS':<8}{'STATUS':<7}{'N':>4}{'MS':>7}  DETAIL")
            print("-" * 100)
            for r in rows:
                print(
                    f"{r['engine']:<20}{r['egress']:<8}{r['status']:<7}"
                    f"{r['n']:>4}{r['ms']:>7}  {r.get('detail', '')[:60]}"
                )
            oks = sum(1 for r in rows if r["status"] == "OK")
            print("-" * 100)
            print(f"{oks}/{len(rows)} engine+egress combinations delivered results")
        return 0

    if args.cmd == "proxies":
        pp = ProxyPool(google_mode=args.google)
        if args.test:
            cands = pp.harvest()[: args.test]
            scored = pp.validate(cands, limit=args.test, google_only=args.google)
            payload = {
                "tested": len(cands),
                "alive": len(scored),
                "google_validated": args.google,
                "proxies": [{"proxy": c, "latency_s": round(l, 2)} for c, l in scored[:40]],
            }
            print(
                json.dumps(payload, ensure_ascii=False, indent=2)
                if args.json
                else f"tested {len(cands)} -> {len(scored)} alive\n"
                + "\n".join(f"  {c}  {l:.2f}s" for c, l in scored[:40])
            )
            return 0
        okk = pp.build(force=args.refresh, google_only=args.google)
        st = pp.stats()
        print(
            json.dumps(st, ensure_ascii=False, indent=2)
            if args.json
            else f"proxy pool: {st['alive']}/{st['pool']} alive (google_alive={st['google_alive']}) -> {'OK' if okk else 'FAILED'}"
        )
        return 0 if okk else 1

    if args.cmd == "serve":
        serve(args.host, args.port)
        return 0

    if args.cmd == "stats":
        fs = FreeSearch()
        print(json.dumps(fs.stats(), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "prune":
        c = ResultCache()
        print(f"pruned {c.prune()} expired rows; {c.size()} remain")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    _rc = main()
    # v4: hard exit. concurrent.futures atexit joins lingering pool
    # workers for their full timeout budget after the answer is printed
    # (measured +3.5s). os._exit skips every join; caches are already
    # committed and stdout/stderr are flushed explicitly first.
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    os._exit(_rc)