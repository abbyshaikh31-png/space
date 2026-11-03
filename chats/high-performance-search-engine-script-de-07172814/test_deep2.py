#!/usr/bin/env python3
"""Deep test harness for free_search.py v2.1.0 — runs the two sample queries
with per-engine provenance, then a batch run, then an Engine x Egress matrix."""
import json, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import free_search as fs

QUERIES = ["openai sam altman", "python asyncio tutorial"]

print("=== PHASE 1: SAMPLE SEARCHES (hedged race, direct egress) ===", flush=True)
client = fs.FreeSearch()
for q in QUERIES:
    t0 = time.time()
    o = client.search(q, max_results=8, use_cache=False)
    ms = int((time.time() - t0) * 1000)
    print(f"\n--- QUERY: {q!r} ---", flush=True)
    print(f"engine={o.engine} egress={o.egress} results={len(o.results)} "
          f"elapsed={ms}ms rel={o.relevance:.2f} attempts={o.attempts} deferred={o.deferred}", flush=True)
    for h in o.results[:8]:
        print(f"   {h.rank}. {h.title[:80]} | {h.url[:80]} | src={h.source}", flush=True)
    if o.errors:
        print("   errors:", " | ".join(o.errors[:6]), flush=True)
    # also write machine-readable output
    with open(f"out_{q.split()[0]}.json", "w") as f:
        json.dump(o.to_dict(), f, indent=2)

print("\n=== PHASE 2: GOOGLE-ONLY SEARCH ===", flush=True)
t0 = time.time()
o = client.search("sam altman", max_results=6, google_only=True, use_cache=False)
print(f"engine={o.engine} egress={o.egress} results={len(o.results)} "
      f"elapsed={int((time.time()-t0)*1000)}ms", flush=True)
for h in o.results[:6]:
    print(f"   {h.rank}. {h.title[:80]} | {h.url[:80]} | src={h.source}", flush=True)
print("   errors:", " | ".join(o.errors[:6]), flush=True)

print("\n=== PHASE 3: ENGINE x EGRESS MATRIX (selftest) ===", flush=True)
rows = client.selftest(query="python requests library", n=3, test_proxy=False)
print(json.dumps(rows, indent=1), flush=True)

print("\n=== PHASE 4: BATCH (10 queries, workers=4) ===", flush=True)
batch = [
    "docker vs kubernetes", "rust memory safety", "fastapi tutorial",
    "sqlite wal mode", "linux epoll", "python gil explained",
    "huggingface transformers", "redis persistence", "nginx reverse proxy",
    "typescript generics",
]
t0 = time.time()
outs = client.search_many(batch, max_results=4, workers=4, progress=False, use_cache=False)
el = time.time() - t0
ok = [o for o in outs if not o.deferred]
print(f"batch: {len(ok)}/{len(outs)} served in {el:.1f}s", flush=True)
eng_wins = {}
for o in outs:
    if o.results:
        eng_wins[o.engine] = eng_wins.get(o.engine, 0) + 1
print("engine wins:", eng_wins, flush=True)
for o in outs:
    status = "OK" if o.results else "DEFERRED"
    print(f"  [{status}] {o.query!r} -> {len(o.results)} hits via {o.engine} ({o.elapsed_ms}ms)", flush=True)

print("\n=== PHASE 5: CLIENT STATS ===", flush=True)
st = client.stats()
print(json.dumps({k: v for k, v in st.items() if k != "engines"}, indent=1), flush=True)
print("engine health:")
for name, eh in (st.get("engines") or {}).items():
    print(f"  {name:22s} ok={eh['ok']:>2} fail={eh['fail']:>2} walls={eh['walls']:>2} avg_ms={eh['avg_ms']}", flush=True)
print("\nDEEP TEST COMPLETE", flush=True)
