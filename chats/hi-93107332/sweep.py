import json, os, time, random, urllib.parse, sys
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "research_log.json")

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]

def load_log():
    if os.path.exists(LOG):
        try:
            with open(LOG) as f:
                d = json.load(f)
            return d if isinstance(d, list) else d.get("results", [])
        except Exception:
            return []
    return []

def save_log(entries):
    tmp = LOG + ".tmp"
    with open(tmp, "w") as f:
        json.dump(entries, f, indent=1)
    os.replace(tmp, LOG)

def bing(q, ua):
    url = "https://www.bing.com/search?q=" + urllib.parse.quote(q) + "&count=20"
    r = requests.get(url, headers={"User-Agent": ua, "Accept-Language": "en-US,en;q=0.9"}, timeout=20)
    return r.status_code, r.text

def ddg(q, ua):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)
    r = requests.post(url, data={"q": q}, headers={"User-Agent": ua}, timeout=20)
    return r.status_code, r.text

def mojeek(q, ua):
    url = "https://www.mojeek.com/search?q=" + urllib.parse.quote(q)
    r = requests.get(url, headers={"User-Agent": ua}, timeout=20)
    return r.status_code, r.text

ENGINES = {"bing": bing, "ddg": ddg, "mojeek": mojeek}

def count_hits(html):
    return html.count("<a ") // 3

def run(queries, start_id=1):
    log = load_log()
    nid = len(log) + 1
    for q in queries:
        got = False
        for name in ["bing", "ddg", "mojeek"]:
            ua = random.choice(UAS)
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            try:
                status, html = ENGINES[name](q, ua)
                n = count_hits(html) if status == 200 else 0
                err = ""
            except Exception as e:
                status, n, err = 0, 0, type(e).__name__ + ": " + str(e)[:120]
            log.append({"id": nid, "query": q, "engine": name, "timestamp": ts,
                        "http_status": status, "n_results": n, "errors": err})
            save_log(log)
            nid += 1
            if status == 200 and n > 0:
                print(str(nid-1) + " " + name + " OK " + q[:60])
                got = True
                break
            time.sleep(0.6)
        if not got:
            print(str(nid-1) + " ALL-FAIL " + q[:60])
    save_log(log)
    print("TOTAL_LOGGED=" + str(len(log)))
    return len(log)

if __name__ == "__main__":
    qs = json.load(open(os.path.join(HERE, "queries.json")))
    run(qs)