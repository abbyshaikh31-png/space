#!/usr/bin/env python3
"""Multi-engine web sweep for Gemini 4 Carbon free-access research.
Logs every query with engine + timestamp, extracts URLs, dedups them.
"""
import json, time, hashlib, re, os, sys
from datetime import datetime, timezone
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
OUT = "research_log.json"
SOURCES = "sources/canonical.json"

QUERIES = [
 "Gemini 4 Carbon free access",
 "Gemini 4 Carbon pricing per 1M tokens",
 "Gemini 4 Carbon API model id",
 "Google AI Studio pricing Gemini 4",
 "Gemini API pricing tiers Standard Batch Flex Priority",
 "Gemini 4 Carbon free tier eligible",
 "Gemini 4 Carbon Google AI Ultra access",
 "Gemini 4 Carbon Gemini for business access",
 "Gemini 4 Carbon Vertex AI availability",
 "Gemini 4 Carbon release date announcement",
 "Google Gemini 4 Carbon blog launch post",
 "Gemini 4 Carbon OpenRouter price",
 "OpenRouter free models list Gemini",
 "OpenRouter Gemini 4 Carbon provider routes",
 "Puter.js free Gemini API tutorial",
 "Puter user-pays model terms",
 "Puter Gemini 4 Carbon model support",
 "Puter pricing free monthly allowance",
 "Puter AI hosting free for developers end user pays",
 "Atlas Cloud Gemini 4 Carbon free",
 "Gemini 4 Carbon free tier alternatives",
 "Gemini CLI free tier quotas 2026",
 "Gemini Code Assist free tier limits",
 "Google AI Pro plan models included",
 "Google AI Ultra price 2026 features",
 "Gemini app model picker Pro Ultra models",
 "Gemini 4 Argon vs Carbon naming",
 "Gemini 4 Argon pricing",
 "Gemini 4 model family naming map",
 "Google Cloud free trial credits 2026",
 "Vertex AI Express Mode free tier",
 "Vertex AI Gemini 4 Carbon pricing",
 "Cloud AI startup program credits Gemini",
 "Google AI research program scientists early access",
 "DeepMind Fairwind program cybersecurity defenders",
 "Gemini 4 Carbon Fairwind program terms",
 "Google Cloud new user $300 credit eligible Gemini API",
 "Google AI Studio rate limits free tier RPM RPD",
 "Gemini API free tier models listed Flash",
 "Gemini 3.8 Flash free tier availability",
 "Gemini 3.6 Flash free tier rate limits",
 "Gemini 4 Carbon context window tokens",
 "Gemini 4 Carbon context caching price",
 "Gemini 4 Carbon grounding with Google Search price",
 "Gemini 4 Carbon batch API half price",
 "Gemini 4 Carbon December 1 2026 price change",
 "Gemini 4 Carbon benchmarks artificial analysis index",
 "Gemini 4 Carbon SWE-bench terminal-bench score",
 "Gemini 4 Carbon vs Claude Opus 5.5 comparison",
 "Gemini 4 Carbon vs GPT-6 Astra benchmark",
 "Gemini 4 Carbon hallucination rate lowest",
 "Gemini 4 Carbon 3D modeling benchmark",
 "Gemini 4 Carbon coding agent leaderboard",
 "Gemini 4 Carbon safety model card",
 "Gemini 4 Carbon developers enterprises scientists consumers",
 "Gemini 4 Carbon worldwide rollout Engadget",
 "Gemini 4 Carbon free tier not available statement",
 "Gemini 4 Carbon cybersecurity exploit benchmark",
 "free Gemini 4 Carbon API key generator Reddit",
 "free Gemini 4 Carbon alternative aggregator",
 "Hugging Face Inference Providers Gemini 4 Carbon",
 "GitHub Models Gemini 4 Carbon free tier",
 "Vercel AI Gateway Gemini 4 Carbon",
 "Cloudflare Workers AI Gemini model",
 "Together AI Gemini 4 Carbon pricing",
 "Groq Gemini 4 Carbon availability",
 "Groq free tier rate limits open models",
 "Cline Roo Code Gemini 4 Carbon provider",
 "LiteLLM Gemini 4 Carbon model mapping",
 "Open WebUI Gemini 4 Carbon setup",
 "Poe Gemini 4 Carbon subscription",
 "You.com AI Gemini 4 Carbon access",
 "DuckDuckGo AI Chat Gemini model",
 "LM Arena Gemini 4 Carbon leaderboard",
 "Kaggle notebooks Gemini 4 Carbon API",
 "Colab Gemini 4 Carbon API key free",
 "Google AI credits for students Gemini",
 "Google AI Pro student offer terms",
 "free trial Gemini API credits new developers",
 "Gemini 4 Carbon API coupon promo code 2026",
 "Gemini 4 Carbon free access YouTube tutorial 2026",
 "gemini-4-carbon model identifier string",
 "gemini-4-carbon-preview API id",
 "AI Studio model list November 2026",
 "Google Cloud Next 2026 Gemini 4 Carbon announcements",
 "Gemini Enterprise Gemini 4 Carbon pricing",
 "Gemini Enterprise credits trial",
 "Google Workspace Gemini 4 Carbon add-on",
 "Agentspace Gemini 4 Carbon",
 "Antigravity Gemini 4 Carbon availability",
 "Google AI Ultra app Gemini 4 Carbon rollout",
 "Gemini 4 Carbon Gemini app Pro picker upgrade",
 "Gemini 4 Carbon availability by region",
 "Gemini 4 Carbon supported languages features",
 "Gemini 4 Carbon limits requests per minute",
 "API key Google AI Studio create billing account",
 "Gemini API paid tier upgrade billing steps",
 "Model Garden Gemini 4 Carbon",
 "Vertex AI Model Garden Gemini 4 Carbon",
 "Gemini 4 Carbon LangChain integration",
 "Gemini 4 Carbon MCP server",
 "Gemini 4 Carbon agent build pricing tool calls",
 "Gemini 4 Carbon image video input output",
 "Gemini 4 Carbon long context 1M tokens",
 "best free frontier models 2026 open weights",
 "Gemma 4 open weights free commercial use",
 "Qwen3.7 Max free tier availability",
 "DeepSeek V4 free API tier",
 "Kimi K2.6 free access platform",
 "GLM-5.2 free open weights",
 "free LLM API aggregators no signup 2026",
 "Polymo free API gateway LLMs",
 "NanoGPT free models pricing",
 "Nebius AI Studio free credits Gemini",
 "Hyperbolic free models tier",
 "SambaNova free tier developers",
 "SiliconFlow free credits Gemini",
 "AI/ML API free tier Gemini proxy",
 "302.AI free credits Gemini API",
 "CometAPI free quota Gemini",
 "OpenAI-compatible Gemini proxy free",
 "Gemini 4 Carbon usage policy restrictions",
 "Google API terms of service Gemini third party proxy prohibited",
 "reselling Gemini API access prohibited terms",
 "Gemini API key sharing free group 2026",
 "Gemini 4 Carbon prompt caching discount 95%",
 "Gemini 4 Carbon output token limits",
 "Gemini 4 Carbon structured output function calling",
 "Gemini 4 Carbon audio video understanding",
 "Gemini 4 Carbon Gemini Live API",
 "Gemini 4 Carbon release notes changelog",
 "aistudio.google.com pricing page 2026",
 "ai.google.dev gemini-api docs pricing free tier rate limits",
 "support.google.com gemini model access limits",
 "developers.googleblog.com Gemini CLI Antigravity transition",
 "Google Antigravity IDE Gemini 4 Carbon",
 "CodeMender Gemini 4 Carbon Google",
 "Gemini 4 Carbon for cybersecurity defenders free",
 "Gemini 4 Carbon nonprofit NGO program access",
 "Google for Startups Gemini API credits program",
 "Google Cloud credits research universities Gemini",
 "free access Gemini 4 Carbon without subscription 2026",
 "Gemini 4 Carbon token pricing third party table",
 "Gemini 4 Carbon price comparison providers",
 "Gemini 4 Carbon cheapest API provider",
 "AI Studio free tier Gemini 4 models excluded",
 "Gemini 4 Pro model naming confusion 2026",
 "Gemini 4 Flash pricing free tier 2026",
]

ENGINES = [
    ("ddg_lite", "https://lite.duckduckgo.com/lite/?q={q}", "ddg"),
    ("bing", "https://www.bing.com/search?q={q}&count=30", "bing"),
    ("mojeek", "https://www.mojeek.com/search?q={q}", "mojeek"),
    ("marginalia", "https://search.marginalia.nu/search?query={q}", "marginalia"),
    ("brave", "https://search.brave.com/search?q={q}", "brave"),
    ("startpage", "https://www.startpage.com/sp/search?query={q}", "startpage"),
]

URL_RE = re.compile(r'href=["\'](https?://[^"\']+)["\']')
BAD = ("duckduckgo.com", "bing.com", "mojeek.com", "brave.com", "startpage.com",
       "marginalia.nu", "microsoft.com/en-us", "go.microsoft.com", "w3.org", "google.com/search",
       "support.microsoft.com", "youtube.com/redirect", "policies.google.com")


def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(400000).decode("utf-8", "ignore")


def harvest(html, engine):
    urls = []
    for m in URL_RE.findall(html):
        u = m.replace("&amp;", "&")
        if any(b in u for b in BAD):
            continue
        if u in urls:
            continue
        urls.append(u)
    return urls


def norm(u):
    try:
        p = urllib.parse.urlsplit(u)
        host = p.netloc.lower().replace("www.", "")
        path = p.path.rstrip("/") or "/"
        q = urllib.parse.parse_qs(p.query)
        keys = {k: v[0] for k, v in q.items() if k.lower() in ("id", "q", "v", "page")}
        return f"{host}{path}" + (f"?{json.dumps(keys, sort_keys=True)}" if keys else "")
    except Exception:
        return u


def main():
    log = []
    if os.path.exists(OUT):
        try:
            log = json.load(open(OUT))
        except Exception:
            log = []
    done = {e["query"] for e in log}
    seen = set()
    for s in json.load(open(SOURCES))["sources"] if os.path.exists(SOURCES) else []:
        seen.add(s["canonical"])
    os.makedirs("sources", exist_ok=True)

    for i, q in enumerate(QUERIES):
        if q in done:
            continue
        e = {"query": q, "ts": datetime.now(timezone.utc).isoformat(),
             "engines": [], "urls": []}
        for name, tpl, host in ENGINES:
            try:
                st, html = fetch(tpl.format(q=urllib.parse.quote(q)))
                urls = harvest(html, name)[:12]
                e["engines"].append({"engine": name, "status": st, "n": len(urls)})
                for u in urls:
                    if u not in e["urls"]:
                        e["urls"].append(u)
            except Exception as ex:
                e["engines"].append({"engine": name, "status": "ERR", "err": str(ex)[:80]})
            time.sleep(0.4)
        log.append(e)
        json.dump(log, open(OUT, "w"), indent=1)
        print(f"[{i+1}/{len(QUERIES)}] {q[:52]} -> {len(e['urls'])} urls", flush=True)

    # dedup corpus
    corpus = {}
    for e in log:
        for u in e["urls"]:
            c = norm(u)
            if c not in corpus:
                corpus[c] = {"canonical": c, "url": u, "queries": [], "first_seen": e["ts"], "tier": ""}
            corpus[c]["queries"].append(e["query"])
    for k, v in corpus.items():
        h = k.split("/")[0]
        v["tier"] = "primary" if any(
            d in h for d in ("google.", "developers.google", "cloud.google.com", "ai.google.dev",
                             "blog.google", "support.google.com", "deepmind.google",
                             "openrouter.ai", "docs.puter.com", "puter.com", "github.com",
                             "githubusercontent", "huggingface.co", "cloudflare.com")) else "secondary"
        v["queries"] = sorted(set(v["queries"]))
    srcs = sorted(corpus.values(), key=lambda x: (x["tier"], x["canonical"]))
    json.dump({"generated": datetime.now(timezone.utc).isoformat(),
               "count": len(srcs),
               "searches": len(log),
               "sources": srcs}, open(SOURCES, "w"), indent=1)
    print("SEARCHES:", len(log), "UNIQUE SOURCES:", len(srcs))


if __name__ == "__main__":
    main()