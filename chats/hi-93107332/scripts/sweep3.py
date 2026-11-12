#!/usr/bin/env python3
"""Multi-engine web sweep for Gemini 4 Carbon free-access research.
Atomic, resumable, per-query logging to research_log.json.
"""
import json, os, re, time, random, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG = os.path.join(ROOT, "research_log.json")
QUERIES_FILE = os.path.join(HERE, "queries.json")
CANON = os.path.join(ROOT, "sources", "canonical.json")
REPORT = os.path.join(ROOT, "sources", "dedup_report.txt")

UAS = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
 "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

def now():
    return datetime.now(timezone.utc).isoformat()

def load_log():
    if os.path.exists(LOG):
        try:
            d = json.load(open(LOG))
            if isinstance(d, list):
                return d
            if isinstance(d, dict):
                r = d.get("results")
                return r if isinstance(r, list) else []
        except Exception:
            pass
    return []

def save_log(items):
    tmp = LOG + ".tmp"
    with open(tmp, "w") as f:
        json.dump(items, f, indent=1)
    os.replace(tmp, LOG)