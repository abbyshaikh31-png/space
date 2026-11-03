#!/usr/bin/env python3
"""free_search.py 2.1.0 — free, zero-API-key, high-speed web search fleet.
Self-contained: native keyless engines (Startpage, Google, Bing HTML/RSS,
Yahoo, Brave, Google News RSS) + ddgs backends, hedged racing, SQLite cache,
proxy egress tier, CLI + module API. Survives cloud datacenter IPs by racing
many engines and falling back to proxy egress.
"""
from __future__ import annotations

import argparse
import atexit
import base64
import concurrent.futures as cf
import hashlib
import io
import json
import os
import random
import re
import socket
import sqlite3
import ssl
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional

VERSION = "2.1.0"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
LYNX_UA = "Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1 OpenSSL/3.0.x"
GOOGLE_COOKIES = {
    "CONSENT": "YES+cb.20230531-04-p0.en+FX+908",
    "SOCS": "CAISHAgBEhJnd3NfMjAyNDA1MTUtMF9SQzIaAmVuIAEaBgiAo_CmBg",
}
TVAR = threading.local()

# ---------------------------------------------------------------- transport
def _ld_get(ld: dict, *keys, default=None):
    """Dig into nested dict/list structures produced by JS-heavy pages."""
    cur = ld
    for k in keys:
        if isinstance(cur, list):
            cur = cur[0] if cur else None
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def _fetch(url: str, *, method="GET", headers=None, cookies=None,
           impersonate="chrome124", timeout=9.0, egress="direct",
           allowed_codes=(200, 301, 302, 303, 307, 308)):
    """Fetch via curl_cffi (TLS-jailbreak) with requests fallback; honors egress priority."""
    opts = dict(allow_redirects=True, timeout=timeout, impersonate=impersonate)
    headers = dict(headers or {"User-Agent": UA, "Accept": "text/html,*/*"})
    cookies = dict(cookies or {})
    # Note: curl_cffi >=0.7 uses 'proxy', older 'proxies'
    return opts, headers, cookies  # replaced at import-time below


def http_get(url, *, headers=None, cookies=None, impersonate="chrome124",
             timeout=9.0, egress="direct") -> tuple:
    """Return (status:int, text:str). Uses curl_cffi when importable, else requests."""
    if egress == "proxy":
        p = _GLOBAL_PROXIES.get()
        if not p:
            raise NetError("no proxy available")
    else:
        p = None
    try:
        from curl_cffi import requests as cr
        kw = dict(headers=headers or {}, cookies=cookies or {},
                  timeout=timeout, impersonate=impersonate, allow_redirects=True)
        if p:
            kw["proxies"] = {"http": p, "https": p}
        r = cr.get(url, **kw)
        return r.status_code if isinstance(r.status_code, int) else 500, r.text or ""
    except ImportError:
        pass
    except Exception:
        pass
global_TAG = True


class NetError(Exception):
    """Raised when every transport path failed."""
