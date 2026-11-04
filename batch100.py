#!/usr/bin/env python3
"""Batch-run 20 diverse queries through free_search.py and score result quality."""
import json, subprocess, time

QUERIES = [
 "India cricket team latest match result",
 "ISRO latest rocket launch 2026",
 "Telangana government latest scheme 2026",
 "Union budget India key highlights",
 "petrol price India today Mumbai",
 "Python 3.14 new features",
 "Nvidia RTX 5090 price India",
 "best laptop under 50000 rupees 2026",
 "Kubernetes latest version changelog",
 "Jio 5G plans price list",
 "capital of Australia",
 "who invented the telephone",
 "speed of light exact value",
 "Taj Mahal built by whom which year",
 "largest planet in solar system",
 "official website Rotten Tomatoes",
 "IRCTC official website",
 "CBSE board result portal",
 "best 5G phone under 15000",
 "Ather 450X range specs",
]

results = []
start = time.time()
for i, q in enumerate(QUERIES):
    t0 = time.time()
    try:
        p = subprocess.run([
            "python3", "free_search.py", "search", q,
            "--count", "3", "--deadline", "15"
        ], capture_output=True, text=True, timeout=90)
        out = p.stdout.strip()
        n_urls = out.count("http")
        low = ("low_quality" in out) or ("off-topic" in out.lower())
        ok = n_urls >= 1 and not low
    except Exception as e:
        out, n_urls, low, ok = str(e), 0, False, False
    elapsed = round(time.time() - t0, 1)
    results.append({"q": q, "ok": ok, "urls": n_urls, "s": elapsed, "low": low})
    print(f"{i:>3} {'OK ' if ok else 'FAIL'} urls={n_urls:>2} {elapsed:>5}s  {q[:55]}", flush=True)

with open("batch100_results.json", "w") as f:
    json.dump(results, f, indent=1)

ok_n = sum(1 for r in results if r["ok"])
low_n = sum(1 for r in results if r["low"])
avg_urls = sum(r["urls"] for r in results) / len(results)
avg_s = sum(r["s"] for r in results) / len(results)
print(f"\nSUMMARY: {ok_n}/{len(results)} ok ({ok_n*100//len(results)}%), "
      f"low_quality={low_n}, avg urls={avg_urls:.1f}, avg {avg_s:.1f}s, "
      f"total {time.time()-start:.0f}s")
