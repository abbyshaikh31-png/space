#!/usr/bin/env python3
"""free_search.py v2.1.0 - Free, fast, keyless web search fleet.

Cloud-datacenter safe: instead of scraping Google directly (CAPTCHA walls
on AWS/GCP/Azure IPs), it races multiple keyless engines in parallel and
returns the first one that delivers on-topic results:
  bing_rss     Bing XML RSS SERP (fast, parse-stable)
  bing_html    Bing HTML SERP (b_algo parser)
  ddg_lite     DuckDuckGo Lite HTML
  mojeek       Mojeek HTML (own index, no bot walls on cloud IPs)
  marginalia   Marginalia Search (indie index)
  wikipedia    Wikipedia opensearch API (entity resolution)
  google_news  news.google.com RSS (Google-backed news, never blocks DC IPs)

Features: hedged parallel racing (sub-second common case), SQLite cache,
URL redirect un-wrapping (Google/Bing/DDG), per-domain caps, batch mode,
engine health tracking, retry rounds, HTTP API server. Only deps: requests.

CLI:
  python3 free_search.py search "openai sam altman" -n 8 --json
  python3 free_search.py search "python asyncio" --google-news -n 5
  python3 free_search.py batch queries.txt -j 8 --retry --json out.json
  python3 free_search.py selftest
  python3 free_search.py serve --port 8078

PYTHON API:
  from free_search import search, search_many, SearchFleet
  hits = search("kubernetes ingress", max_results=10)
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import html as H
import json
import logging
import os
import re
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

VERSION = "2.1.0"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36)")
HEADERS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
           "Accept": "text/html,application/xhtml+xml,*/*"}
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_tags(s: str) -> str:
    return WS_RE.sub(" ", TAG_RE.sub(" ", H.unescape(s or ""))).strip()


def unwrap(href: str) -> str:
    h = H.unescape((href or "").strip())
    if h.startswith("//"):
        h = "https:" + h
    if "/url?" in h or "/l/?" in h or "/ck/a?" in h:
        for pat in (r"[?&]uddg=([^&]+)", r"[?&]q=([^&]+)", r"[?&]url=([^&]+)",
                    r"U=a1([^&]+)"):
            m = re.search(pat, h)
            if m:
                cand = m.group(1)
                if "a1" == pat[3:5] or m.group(0).startswith("U"):
                    cand = cand.replace("-", "+").replace("_", "/")
                    cand += "=" * (-len(cand) % 4)
                    import base64
                    try:
                        cand = base64.b64decode(cand).decode("utf-8", "ignore")
                    except Exception:
                        continue
                else:
                    try:
                        cand = urllib.parse.unquote(cand)
                    except Exception:
                        continue
                if cand.startswith(("http://", "https://")):
                    return cand
    if h.startswith("/http"):
        h = "https://duckduckgo.com" + h
        m = re.search(r"uddg=([^&]+)", h)
        if m:
            try:
                return urllib.parse.unquote(m.group(1))
            except Exception:
                pass
    if ".bing.com/ck/a" in h or "google.com/url" in h or "duckduckgo.com/l/" in h:
        return ""  # un-decodable ad redirect -> drop
    return h


STOP = frozenset("""a an the and or but of in on at to for from with by is are
was were be has have had it its this that these those as if not no you your his
her our their what which who how why when where all any some more most latest
news best top how-to""".split())


def q_terms(q: str) -> List[str]:
    toks = re.findall(r"[a-z0-9][a-z0-9'+.#-]*", (q or "").lower())
    return [t for t in toks if t not in STOP and len(t) >= 3][:12]


def relevance(q: str, hits: List["Hit"]) -> float:
    terms = q_terms(q)
    if not terms or not hits:
        return 1.0 if not hits else 0.0
    good = 0
    for h in hits:
        blob = " ".join((h.title, h.url, h.snippet)).lower()
        if any(t in blob for t in terms):
            good += 1
    return good / len(hits)


@dataclass
class Hit:
    title: str = ""
    url: str = ""
    snippet: str = ""
    source: str = ""
    rank: int = 0

    def d(self) -> Dict[str, Any]:
        return {"title": self.title, "url": self.url, "href": self.url,
                "snippet": self.snippet, "body": self.snippet,
                "source": self.source, "engine": self.source, "rank": self.rank}


@dataclass
class Outcome:
    query: str = ""
    results: List[Hit] = field(default_factory=list)
    engine: str = ""
    from_cache: bool = False
    relevance: float = 0.0
    elapsed_ms: int = 0
    attempts: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.results)

    def d(self) -> Dict[str, Any]:
        return {"query": self.query, "results": [h.d() for h in self.results],
                "engine": self.engine, "from_cache": self.from_cache,
                "relevance": round(self.relevance, 3),
                "elapsed_ms": self.elapsed_ms, "attempts": self.attempts,
                "errors": self.errors[-6:]}


# ------------------------------------------------------------------ engines

def _get(url: str, timeout: float = 8.0, sess: Optional[requests.Session] = None) -> str:
    s = sess or requests
    r = s.get(url, headers=HEADERS, timeout=(3.0, timeout), allow_redirects=True)
    if r.status_code != 200:
        raise RuntimeError(f"http {r.status_code}")
    return r.text


def eng_bing_rss(q: str, n: int, sess) -> List[Hit]:
    txt = _get("https://www.bing.com/search?q=" + urllib.parse.quote(q)
               + f"&format=rss&count={min(n, 30)}", sess=sess)
    out: List[Hit] = []
    root = ET.fromstring(txt.encode("utf-8", "ignore"))
    for item in root.iter("item"):
        t = strip_tags(item.findtext("title") or "")
        lnk = item.findtext("link") or ""
        u = unwrap(lnk) or (lnk if lnk.startswith("http") else "")
        sn = strip_tags(item.findtext("description") or "")[:200]
        if t and u:
            out.append(Hit(t, u, sn, "bing_rss"))
        if len(out) >= n:
            break
    return out


def eng_bing_html(q: str, n: int, sess) -> List[Hit]:
    txt = _get("https://www.bing.com/search?q=" + urllib.parse.quote(q)
               + f"&count={min(n, 30)}", sess=sess)
    out: List[Hit] = []
    for block in re.findall(r'<li class="b_algo"[^>]*>(.*?)(?=<li class="b_algo"|</ol>)',
                            txt, re.S)[:n * 2]:
        m = re.search(r'<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        u = unwrap(m.group(1))
        t = strip_tags(m.group(2))
        sm = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
        sn = strip_tags(sm.group(1))[:200] if sm else ""
        if t and u and u.startswith("http"):
            out.append(Hit(t, u, sn, "bing_html"))
        if len(out) >= n:
            break
    if "b_algo" not in txt and len(out) == 0:
        raise RuntimeError("no b_algo blocks (wall/geo)")
    return out


def eng_ddg_lite(q: str, n: int, sess) -> List[Hit]:
    r = sess.post("https://lite.duckduckgo.com/lite/",
                  data={"q": q}, headers=HEADERS, timeout=(3.0, 8.0))
    if r.status_code != 200:
        raise RuntimeError(f"http {r.status_code}")
    txt = r.text
    out: List[Hit] = []
    links = re.findall(r'<a rel="nofollow" class="result-link" href="([^"]+)"[^>]*>(.*?)</a>',
                       txt, re.S)
    snips = re.findall(r'class="result-snippet">(.*?)</td>', txt, re.S)
    for i, (href, t) in enumerate(links[:n]):
        u = unwrap(href)
        u = u if u.startswith("http") else ("https:" + u if u.startswith("//") else u)
        if not u.startswith("http"):
            continue
        sn = strip_tags(snips[i])[:200] if i < len(snips) else ""
        out.append(Hit(strip_tags(t), u, sn, "ddg_lite"))
    if not out:
        raise RuntimeError("no results parsed")
    return out


def eng_mojeek(q: str, n: int, sess) -> List[Hit]:
    txt = _get("https://www.mojeek.com/search?q=" + urllib.parse.quote(q), sess=sess)
    out: List[Hit] = []
    for m in re.finditer(r'<a[^>]+class="title"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                         txt, re.S):
        u, t = unwrap(m.group(1)), strip_tags(m.group(2))
        if u.startswith("http") and t:
            out.append(Hit(t, u, "", "mojeek"))
        if len(out) >= n:
            break
    if not out:
        raise RuntimeError("no results parsed")
    return out