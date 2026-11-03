import aiohttp, asyncio
from bs4 import BeautifulSoup

def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    out=[]
    for g in soup.select("div.g, div.tF2Cxc"):
        h=g.select_one("h3"); a=g.select_one("a[href]")
        if h and a:
            href=a.get("href","")
            if href.startswith("/url?q="): href=href.split("/url?q=")[1].split("&")[0]
            out.append((h.get_text(strip=True)[:60], href[:60]))
    return out

async def try_url(s, label, url, hdrs):
    try:
        async with s.get(url, headers=hdrs) as r:
            html = await r.text()
            res = parse(html)
            cap = "unusual traffic" in html or "/sorry/" in html
            js = "not redirected" in html
            print(f"{label}: {r.status} len={len(html)} parsed={len(res)} cap={cap} jsredirect={js}")
            for t,_ in res[:3]: print("   ", t)
    except Exception as e:
        print(f"{label}: EXC {type(e).__name__}: {e}")

UAC = {
 "chrome":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
 "curl":"curl/8.1.1",
 "firefox":"Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0",
}

async def main():
    for ua in UAC:
        h={"User-Agent":UAC[ua],"Accept-Language":"en-US,en;q=0.9","Accept":"text/html,application/xhtml+xml"}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15), cookie_jar=aiohttp.CookieJar(unsafe=True)) as s:
            # warm-up to get NID cookies
            for pre in [None, "https://www.google.com/?hl=en"]:
                base="https://www.google.com/search?q=best+python+books&hl=en"
                url=base+("&gbv=1" if pre is None else "")
                pass
            await try_url(s, f"{ua}-gbv1", "https://www.google.com/search?q=best+python+books&hl=en&gbv=1", h)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15), cookie_jar=aiohttp.CookieJar(unsafe=True)) as s:
            try:
                async with s.get("https://www.google.com/?hl=en", headers=h): pass
            except Exception: pass
            await try_url(s, f"{ua}-cookie-warm", "https://www.google.com/search?q=best+python+books&hl=en&gbv=1", h)

asyncio.run(main())
