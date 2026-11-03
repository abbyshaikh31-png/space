#!/usr/bin/env python3
"""Deep test harness for free_search.py v2.1.0 — runs live searches, latency
stats, engine-win report, selftest engine x egress matrix, and a batch run."""
import json
import os
import sys
import time
import urllib.request

os.environ.setdefault("SEARCH_TIMEOUT", "8")
os.environ.setdefault("SEARCH_MAX_ATTEMPTS", "10")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import free_search as fs

print("free_search", fs.VERSION)
try:
    ip = urllib.request.urlopen(
        "https://api.ipify.org", timeout=5
    ).read().decode()
    print("public_ip:", ip)
except Exception as e:
    print("public_ip: unavailable", e)
print("curl_cffi:", getattr(fs, "HAVE_CURL_CFFI", "n/a"))
print("engines:", list(fs.__dict__.get("ENGINE_TABLE", {}).keys()) or "see below")

client = fs.FreeSearch(use_cache=False)

QUERIES = ["openai sam altman", "python asyncio tutorial"]
timing = []
for q in QUERIES:
    t0 = time.time()
    out = client.search(q, max_results=5)
    ms = int((time.time() - t0) * 1000)
    timing.append({"query": q, "ms": ms, "engine": out.engine,
                   "egress": out.egress, "n": len(out.results),
                   "deferred": out.deferred})
    print(f"\n=== {q} -> {len(out.results)} results via {out.engine}/{out.egress} in {ms}ms ===")
    for h in out.results[:5]:
        print(f"  {h.rank}. {h.title[:80]}\n     {h.url}")
    if out.deferred:
        print("  DEFERRED. errors:", out.errors[-5:])

print("\n=== SELFTEST (direct egress) ===")
rows = client.selftest(query="python requests library", n=2, test_proxy=False)
for r in rows:
    print(f"  {r['engine']:<18}{r['egress']:<8}{r['status']:<6}{r['n']:>3}{r['ms']:>7}ms  {r.get('detail','')[:50]}")

print("\n=== BATCH (5 queries, workers=5) ===")
bq = ["rust vs go performance", "kubernetes ingress controller",
      "pandas dataframe merge", "telangana inter maths probability",
      "sqlite journal mode wal"]
t0 = time.time()
outs = client.search_many(bq, max_results=5, workers=5, progress=False)
bt = int((time.time() - t0) * 1000)
ok = [o for o in outs if not o.deferred]
print(f"batch {len(ok)}/{len(outs)} served in {bt}ms, {sum(len(o.results) for o in outs)} results")
for o in outs:
    print(f"  {o.query:<40}{o.engine:<18}{len(o.results):>3}  {o.elapsed_ms:>6}ms")

print("\n=== ENGINE-WIN REPORT ===")
wins = {}
lat = {}
for rec in timing + [{"engine": o.engine or "deferred", "ms": o.elapsed_ms,
                      "query": o.query} for o in outs if not o.deferred]:
    e = rec.get("engine") or "deferred"
    wins[e] = wins.get(e, 0) + 1
    lat.setdefault(e, []).append(rec.get("ms") or rec.get("elapsed_ms") or 0)
for e in wins:
    print(f"  {e:<20}wins={wins[e]:<3}avg_ms={int(sum(lat[e])/len(lat[e]))}")

print("\n=== STATS ===")
st = client.stats()
print(json.dumps({k: st[k] for k in (
    "attempts", "engine_ok", "walls", "queries_ok", "queries_deferred",
    "cache_hits", "cache_misses") if k in st}, indent=2))
for e, h in sorted((st.get("engines") or {}).items()):
    print(f"  {e:<20}ok={h.get('ok',0):<3}fail={h.get('fail',0):<4}walls={h.get('walls',0):<3}avg={h.get('avg_ms',0)}ms err={h.get('last_error','')[:40]}")
print("DONE_OK")
