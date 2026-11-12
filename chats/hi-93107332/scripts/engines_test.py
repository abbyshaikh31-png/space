import urllib.request, urllib.parse, time, random

UA = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
 "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) rv:126.0 Gecko/20100101 Firefox/126.0",
]

def get(url, timeout=15):
    req = urllib.request.Request(url, headers={
        "User-Agent": random.choice(UA),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "identity",
    })
    t0=time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read().decode("utf-8","ignore")
            return r.getcode(), len(b), round(time.time()-t0,2), b[:200]
    except Exception as e:
        return None, 0, round(time.time()-t0,2), repr(e)[:150]

q = urllib.parse.quote("gemini 4 carbon free access")
tests = {
 "bing": f"https://www.bing.com/search?q={q}&count=20",
 "ddg_html": f"https://html.duckduckgo.com/html/?q={q}",
 "ddg_lite": f"https://lite.duckduckgo.com/lite/?q={q}",
 "mojeek": f"https://www.mojeek.com/search?q={q}",
 "searx_be": f"https://searx.be/search?q={q}&format=json",
 "searxng1": f"https://search.inetol.net/search?q={q}",
 "marginalia": f"https://search.marginalia.nu/search?query={q}",
 "startpage": f"https://www.startpage.com/sp/search?query={q}",
 "brave": f"https://search.brave.com/search?q={q}",
 "ecosia": f"https://www.ecosia.org/search?q={q}",
 "yandex": f"https://yandex.com/search/?text={q}",
 "google_news": f"https://news.google.com/rss/search?q={q}",
 "bing_news": f"https://www.bing.com/news/search?q={q}&format=RSS",
 "mwmbl": f"https://api.mwmbl.org/search?q={q}",
 "stract": f"https://stract.com/api/v1/search?q={q}",
}
for name, url in tests.items():
    code, ln, dt, head = get(url)
    print(f"{name:12} code={code} len={ln:7} t={dt:5} :: {head[:110]!r}")
]<]minimax[>[