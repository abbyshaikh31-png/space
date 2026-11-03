import asyncio, aiohttp, random
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
           "Accept-Language": "en-US,en;q=0.9"}

URL = "https://www.google.com/search?q=best+python+books&num=10&hl=en"

def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    out=[]
    for g in soup.select("div.g, div.tF2Cxc"):
        h=g.select_one("h3"); a=g.select_one("a[href]")
        if h and a:
            href=a.get("href","")
            if href.startswith("/url?q="): href=href.split("/url?q=")[1].split("&")[0]
            out.append((h.get_text(strip=True)[:60], href[:80]))
    return out, len(soup.select('form[action="/images/results"]'))

async def probe(session, label, proxy=None):
    try:
        async with session.get(URL, proxy=proxy) as r:
            html = await r.text()
            res, imgs = parse(html)
            captcha = "unusual traffic" in html or "/sorry/" in html
            print(f"{label}: status={r.status} len={len(html)} parsed={len(res)} captcha={captcha}")
            for t,_ in res[:3]: print("   ", t)
            if not res and not captcha:
                import re
                txt = re.sub(r"\s+"," ",soup_text(html))
                print("   sample page text:", txt[:300])
    except Exception as e:
        print(f"{label}: EXC {type(e).__name__}: {e}")

def soup_text(h):
    return BeautifulSoup(h,"html.parser").get_text(" ")

async def main():
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout, headers=HEADERS) as s:
        await probe(s, "DIRECT(docker-hub-ok)")
        await probe(s, "DIRECT(google-direct)")
    # try some free proxies quickly
    from google_free_search import harvest, validate
    proxies = await harvest(500)
    good = proxies[:80]
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout, headers=HEADERS) as s:
        for p in good[:8]:
            await probe(s, f"proxy {p}", proxy=p)

asyncio.run(main())
