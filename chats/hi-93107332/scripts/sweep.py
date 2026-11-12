#!/usr/bin/env python3
"""Multi-engine web sweep for Gemini 4 Carbon free-access research.
Logs every query to research_log.json atomically as a JSON list.
"""
import json, os, random, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGPATH = os.path.join(ROOT, "research_log.json")

UAS = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
 "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

ENGINES = {
 "bing":      ("https://www.bing.com/search?q={q}&count=20", "bing"),
 "ddg_html":  ("https://html.duckduckgo.com/html/?q={q}", "ddg"),
 "ddg_lite":  ("https://lite.duckduckgo.com/lite/?q={q}", "ddg"),
 "mojeek":    ("https://www.mojeek.com/search?q={q}", "mojeek"),
 "startpage": ("https://www.startpage.com/sp/search?query={q}", "startpage"),
 "searx_be":  ("https://searx.be/search?q={q}", "searx"),
 "searx_tux": ("https://searx.tiekoetter.com/search?q={q}", "searx"),
 "marginalia":("https://search.marginalia.nu/search?query={q}", "marginalia"),
}

BASE = [
 "gemini 4 carbon free access", "gemini 4 carbon pricing per million tokens",
 "gemini 4 carbon api model id", "gemini 4 carbon free tier",
 "gemini 4 carbon openrouter price", "gemini 4 carbon puter.js free",
 "gemini 4 carbon google ai studio", "gemini 4 carbon gemini app ultra",
 "gemini 4 carbon vs claude opus 5.5", "gemini 4 carbon vs gpt-6 astra",
 "google ai studio gemini api pricing free tier", "gemini api free tier rate limits 2026",
 "gemini for business pricing", "google ai ultra subscription price 2026",
 "openrouter free models list", "openrouter gemini 4 carbon provider",
 "puter.js user pays model free allowance", "puter.js gemini models pricing",
 "vertex ai express mode free credits", "google cloud free trial credit gemini",
 "gemini cli antigravity free tier", "github models free tier gemini",
 "hugging face inference providers gemini free", "lmarena leaderboard gemini 4 carbon",
 "artificial analysis gemini 4 carbon intelligence index", "gemini 4 argon model",
 "gemini 4 carbon launch date november 2026", "gemini 4 carbon blog.google available",
 "gemini api terms of service free tier data use", "gcp free trial $300 credits",
 "google one ai plus pro ultra plans comparison", "gemini app model picker pro plan",
 "atlas cloud gemini 4 carbon free", "zemith gemini 4 carbon free access",
 "apidog gemini 4 carbon free guide", "techinsights gemini 4 carbon review",
 "9to5google gemini 4 carbon gemini app", "engadget gemini 4 carbon available worldwide",
 "mindstudio gemini 4 carbon benchmarks", "deepmind fairwind program gemini",
 "gemini grounding with google search pricing", "gemini context caching pricing",
 "gemini batch api half price", "gemini flex tier pricing", "gemini api rate limits paid tier",
 "openai gpt-6 astra free tier chatgpt", "claude opus 5.5 free access anthropic",
 "perplexity labs free models", "duckduckgo ai chat free models",
 "you.com api free tier credits", "groq free tier models", "cloudflare workers ai free tier",
 "together ai free credits signup", "fireworks ai free credits", "vllm serve gemini local",
 "ollama run gemini models locally", "lm studio run gemini 4 locally",
 "gemini 4 carbon cheapest api provider", "gemini 4 carbon region availability restrictions",
 "gemini enterprise workspace pricing", "gemini code assist free quota",
 "google colab gemini api free tier", "kaggle notebooks gemini api key free",
 "gemini 4 carbon trial credit promo code", "gemini api promotional pricing december 1 2026",
 "gemini 4 carbon 4 dollar 20 dollar price increase", "gemini api standard price sheet 2026",
 "gemini 4 carbon developer tier eligibility", "gemini 4 carbon long context pricing",
 "gemini 4 carbon availability countries", "gemini 4 carbon waitlist early access",
 "gemini 4 carbon cybersecurity fairwind defenders", "gemini 4 carbon model card technical report",
 "gemini 4 carbon agent benchmarks exploitgym", "gemini 4 carbon swe-bench verified",
 "gemini 4 carbon hle score", "gemini 4 carbon mmlu pro",
 "gpt-6 astra pricing api", "claude opus 5.5 pricing api",
 "openai api free trial credit 2026", "anthropic claude free tier console",
 "puter js terms of service user pays", "puter free hosting ai models limits",
 "lm studio free models list", "ollama gemini 4 carbon gguf",
 "hugging face chat playground free models", "openrouter free variant rate limit 20 rpm",
 "google cloud startup program credits ai", "academic research program gemini free access",
 "gemini api free rate limit requests per minute", "gemini 4 carbon no key free api",
 "gemini 4 carbon scam fake api key site", "how to use gemini 4 carbon without credit card",
 "gemini 4 carbon reverse proxy share keys", "gemini 4 carbon cheapest way to run 2026",
]

def build_queries():
    q = list(BASE)
    extra = []
    for b in BASE[:40]:
        extra.append(b + " review")
    for b in BASE[:25]:
        extra.append(b + " official documentation")
    for b in BASE[:20]:
        extra.append("site:ai.google.dev " + b)
    seen, out = set(), []
    for x in q + extra:
        k = x.lower().strip()
        if k and k not in seen:
            seen.add(k); out.append(x)
    return out