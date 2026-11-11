import json, os, re, time, random, hashlib, datetime, urllib.parse, urllib.request

QUERIES = [
 "Gemini 4 Carbon release date",
 "Gemini 4 Carbon free access",
 "Gemini 4 Carbon pricing per million tokens",
 "Gemini 4 Carbon API model id",
 "Gemini 4 Carbon Google AI Studio",
 "Gemini 4 Carbon Vertex AI",
 "Gemini 4 Carbon OpenRouter",
 "Gemini 4 Carbon Puter.js",
 "Gemini 4 Carbon Atlas Cloud",
 "Gemini 4 Carbon free tier rate limits",
 "Gemini 4 Carbon Google AI Ultra",
 "Gemini 4 Carbon Google AI Pro plan",
 "Gemini 4 Carbon Gemini app",
 "Gemini 4 Carbon Gemini Enterprise",
 "Gemini 4 Carbon Fairwind program",
 "Gemini 4 Carbon benchmarks intelligence index",
 "gemini-4-carbon model name identifier",
 "gemini-4-carbon api endpoint",
 "Gemini 4 Carbon vs GPT-6 Astra",
 "Gemini 4 Carbon vs Claude Opus 5.5",
 "Gemini API free tier models list 2026",
 "Gemini API pricing free tier rate limits",
 "Google AI Studio pricing per million tokens",
 "Vertex AI Gemini pricing per million tokens",
 "Gemini Enterprise pricing developers",
 "Google AI Ultra price per month",
 "Gemini CLI free tier Antigravity",
 "Gemini Code Assist free tier limits",
 "OpenRouter free models list",
 "OpenRouter free tier rate limits requests per day",
 "Puter.js user pays model free allowance",
 "Puter.js Gemini models pricing",
 "Atlas Cloud Gemini 4 Carbon free guide",
 "GitHub Models free tier Gemini",
 "Hugging Face inference providers Gemini free credits",
 "Groq free tier Gemini models",
 "Cloudflare Workers AI Gemini models",
 "Vercel AI Gateway free tier credits",
 "Poe free Gemini models subscription",
 "Perplexity Labs free Gemini access",
 "lmarena leaderboard Gemini 4 Carbon",
 "Artificial Analysis Gemini 4 Carbon intelligence index",
 "Gemini 4 Argon model",
 "Gemini 4 Argon price per million tokens",
 "Gemini 4 Pro release",
 "Gemini 4 Flash free tier",
 "Google Cloud free trial credits Vertex AI 300 dollars",
 "Google AI startup program credits students Gemini",
 "Gemini API free tier requests per minute RPM",
 "Gemini API pricing change December 1 2026",
 "Gemini 4 Carbon batch API discount",
 "Gemini 4 Carbon context caching price",
 "Gemini 4 Carbon grounding with Google Search price",
 "Gemini 4 Carbon availability regions countries",
 "Gemini 4 Carbon announcement blog.google",
 "Gemini 4 Carbon scientists researchers program access",
 "free Gemini API no key alternatives 2026",
 "Gemini 4 Carbon not available on free tier",
 "best free Gemini API aggregator credits 2026",
 "Gemini 4 Carbon Cursor GitHub Copilot"
]

UAS = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
 "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0"
]

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(UAS),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "ignore")

def bing(q):
    url = "https://www.bing.com/search?q=" + urllib.parse.quote(q) + "&count=20&setlang=en"
    st, html = fetch(url)
    out = []
    for m in re.finditer(r'<h2>\s*<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S):
        u = m.group(1)
        t = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if "bing.com" in u or "microsofttranslator" in u:
            continue
        out.append({"url": u, "title": t})
    if not out:
        for m in re.finditer(r'<cite>(https?://[^<"]+)</cite>', html):
            out.append({"url": m.group(1), "title": ""})
    return st, out