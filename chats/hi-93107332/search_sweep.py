import json, re, time, urllib.parse, hashlib, os, sys
import requests

OUT = "corpus"
os.makedirs(OUT, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

QUERIES = [
 "gemini 4 carbon price",
 "gemini 4 carbon free tier",
 "gemini 4 carbon api pricing per million tokens",
 "gemini 4 carbon release date",
 "gemini 4 carbon benchmarks",
 "gemini 4 carbon vs claude opus 5.5",
 "gemini 4 carbon vs gpt-6 astra",
 "gemini 4 carbon openrouter",
 "gemini 4 carbon puter free",
 "gemini 4 carbon ai studio",
 "gemini 4 carbon google ai ultra",
 "gemini 4 carbon gemini for business",
 "gemini 4 carbon free access no api key",
 "gemini 4 carbon tutorial free use",
 "gemini 4 carbon student discount",
 "gemini 4 carbon vertex ai",
 "gemini 4 carbon context window 1M",
 "gemini 4 carbon batch api discount",
 "gemini 4 carbon flex pricing",
 "gemini 4 carbon priority tier",
 "gemini 4 carbon grounding google search price",
 "gemini 4 carbon context caching price",
 "gemini 4 argon price",
 "gemini 4 carbon review",
 "gemini 4 carbon hands on test",
 "gemini 4 carbon cursorbench",
 "gemini 4 carbon wandr benchmark perplexity",
 "gemini 4 carbon automationbench zapier",
 "gemini 4 carbon artificial analysis intelligence index",
 "gemini 4 carbon MKA benchmark multimodal knowledge agent",
 "gemini 4 carbon codex cli cursor",
 "gemini 4 carbon antigravity swarm",
 "gemini 4 carbon github copilot",
 "gemini 4 carbon gemini cli",
 "gemini 4 carbon code assist",
 "gemini 4 carbon colab kaggle notebook free",
 "gemini 4 carbon cloud credits trial",
 "gemini 4 carbon google cloud new user credits",
 "gemini 4 carbon free tier limits rpm rpd",
 "gemini 4 carbon rate limits paid tier",
 "gemini 4 carbon terms of service",
 "gemini 4 carbon data used to improve products",
 "gemini 4 carbon api model id gemini-4-carbon",
 "gemini 4 carbon docs models page",
 "gemini 4 carbon whats new",
 "gemini 4 carbon enterprise agent platform",
 "gemini 4 carbon security cyber defense fairwind",
 "fairwind program google deepmind eligibility",
 "gemini 4 carbon scientists program free",
 "gemini 4 carbon developer program free credits",
 "gemini 4 carbon google for education free",
 "gemini 4 carbon workspace gemini app free plan",
 "gemini 4 carbon vs openai free tier",
 "gemini 4 carbon cheap alternatives",
 "best free gemini models api 2026",
 "openrouter free models list",
 "openrouter free tier limits 50 requests per day",
 "google ai studio free tier available models list",
 "gemini api free tier models gemini 3.8 flash",
 "gemini 4 carbon poe perplexity labs access",
 "gemini 4 carbon lmarena arena vote",
 "gemini 4 carbon huggingface inference",
 "gemini 4 carbon groq cloudflare workers ai",
 "gemini 4 carbon vercel ai gateway",
 "gemini 4 carbon together fireworks replicate",
 "gemini 4 carbon you.com chat",
 "gemini 4 carbon duckduckgo chat",
 "gemini 4 carbon local llm alternative",
 "gemini 4 carbon gpt-oss local reasoning",
 "gemini 4 carbon cheapest api provider",
 "gemini 4 carbon prompt caching discount 95 percent",
 "gemini 4 carbon thinking tokens billing",
 "gemini 4 carbon long decode 1M output",
 "gemini 4 carbon software engineering terminal bench",
 "gemini 4 carbon exploitgym cwe-bench",
 "gemini 4 carbon swe-bench verified",
 "gemini 4 carbon 3d modeling blender",
 "gemini 4 carbon coding leaderboard 2026",
 "best frontier model 2026 carbon astra fable",
 "gemini 4 carbon pricing change december 1 2026",
 "gemini 4 carbon introductory pricing november 30",
 "gemini 4 carbon api migration guide",
 "gemini 4 carbon token count billable grounding",
 "gemini 4 carbon enterprise pricing discount",
 "gemini 4 carbon startup credits program",
 "gemini 4 carbon google cloud credits eligible",
 "gemini 4 carbon researchers free access program",
 "gemini 4 carbon availability by country region",
 "gemini 4 carbon app rollout google antigravity",
 "gemini 4 carbon ai mode in search",
 "gemini 4 carbon model card deepmind",
 "gemini 4 carbon safety evaluation report",
 "gemini 4 carbon hallucination rate benchmark",
 "gemini 4 carbon price comparison openrouter cheapest",
 "gemini 4 carbon api key free no signup",
 "free llm api no credit card 2026",
 "free unlimited gemini api puter user pays",
 "puter user pays model quotas monthly allowance",
 "puter rate limits and quotas docs",
 "puter terms of service ai models",
 "puter gemini 4 carbon support",
 "atlascloud gemini 4 carbon free users",
 "gemini 4 carbon free users try it yet",
 "gemini 4 carbon news november 2026",
 "gemini 4 carbon launch announcement google blog",
 "gemini 4 carbon engadget coverage",
 "gemini 4 carbon techcrunch coverage",
 "gemini 4 carbon 9to5google",
 "gemini 4 carbon lifetime access promo credit",
 "gemini 4 carbon referral promo code 2026",
 "gemini 4 carbon api bundle credits top up",
 "gemini 4 carbon google cloud console walkthrough",
 "gemini 4 curl api example request",
 "gemini 4 carbon python SDK sample code",
 "gemini 4 carbon count tokens endpoint",
 "gemini 4 carbon safety settings filters",
 "gemini 4 carbon structured output json mode",
 "gemini 4 carbon function calling parallel",
 "gemini 4 carbon gemini app limits messages per day",
 "gemini 4 carbon ultra quota heavy requests",
 "gemini 4 carbon pro plan model picker",
 "gemini 4 carbon upgrade badge in gemini app",
 "gemini 4 carbon price cheap use via api only",
 "gemini 4 carbon cheapest way to try free",
]

LOG = os.path.join(OUT, "search_log.jsonl")
seen_urls = set()
recs = []
qfile = os.path.join(OUT, "queries.txt")
with open(qfile, "w") as f:
    f.write("\n".join(QUERIES))


def clean(u):
    if not u:
        return None
    if u.startswith("//duckduckgo.com/l/?uddg="):
        q = urllib.parse.parse_qs(urllib.parse.urlparse("https:" + u).query)
        return q.get("uddg", [None])[0]
    if u.startswith("http"):
        return u
    return None


def search_engine(q, engine):
    try:
        if engine == "ddg":
            r = requests.post("https://html.duckduckgo.com/html/", data={"q": q}, headers=HEADERS, timeout=25)
            r.raise_for_status()
            links = re.findall(r'class="result__a"[^>]*href="([^"]+)"', r.text)
            titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', r.text, re.S)
        else:
            r = requests.get("https://lite.duckduckgo.com/lite/", params={"q": q}, headers=HEADERS, timeout=25)
            r.raise_for_status()
            links = re.findall(r'href="(//duckduckgo.com/l\?uddg=[^"]+)"', r.text)
            titles = re.findall(r'class="result-link"[^>]*>(.*?)</a>', r.text, re.S)
        out = []
        for i, l in enumerate(links):
            c = clean(l)
            if c:
                t = re.sub(r"<[^>]+>", "", titles[i]) if i < len(titles) else ""
                out.append((c, t.strip()))
        return out
    except Exception as e:
        return []


def bing(q):
    try:
        r = requests.get("https://www.bing.com/search", params={"q": q}, headers=HEADERS, timeout=25)
        r.raise_for_status()
        links = re.findall(r'<h2><a href="(http[^"]+)"', r.text)
        titles = re.findall(r'<h2><a href="http[^"]+"[^>]*>(.*?)</a>', r.text, re.S)
        out = []
        for i, l in enumerate(links):
            t = re.sub(r"<[^>]+>", "", titles[i]) if i < len(titles) else ""
            out.append((l, t.strip()))
        return out
    except Exception:
        return []


def brave(q):
    try:
        r = requests.get("https://search.marcia.cc/search", params={"q": q}, timeout=20, headers=HEADERS)
        return []
    except Exception:
        return []


log = open(LOG, "a")
n = 0
for qi, q in enumerate(QUERIES):
    res = search_engine(q, "ddg")
    if len(res) < 3:
        res = (res or []) + bing(q)
    engine = "ddg+bing"
    for url, title in res:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        rec = {"q_index": qi, "query": q, "engine": engine, "url": url, "title": title,
               "key": hashlib.md5(url.encode()).hexdigest()[:10]}
        recs.append(rec)
        log.write(json.dumps(rec) + "\n")
        log.flush()
    n += 1
    if qi % 10 == 0:
        print(f"progress {qi}/{len(QUERIES)} queries, {len(recs)} urls", flush=True)
    time.sleep(0.7)

log.close()
json.dump(recs, open(os.path.join(OUT, "sources.json"), "w"), indent=1)
print("DONE queries=", n, "unique_urls=", len(recs))