import aiohttp, asyncio, re
from bs4 import BeautifulSoup

UAC={"chrome":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

async def main():
    h={"User-Agent":UAC["chrome"],"Accept-Language":"en-US,en;q=0.9"}
    jar=aiohttp.CookieJar(unsafe=True)
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15), cookie_jar=jar) as s:
        async with s.get("https://www.google.com/search?q=best+books&hl=en&gbv=1", headers=h) as r:
            html=await r.text()
            print("status", r.status, "len", len(html))
            # print all meta refresh + all anchor hrefs
            for m in re.findall(r'<meta[^>]+refresh[^>]*>', html, re.I): print("META:", m)
            soup=BeautifulSoup(html,"html.parser")
            for a in soup.find_all("a", href=True)[:15]:
                print("A:", a.get_text(strip=True)[:40], "|", a["href"][:120])
            # scripts with location.replace
            for m in re.findall(r'location\.replace\(["\']([^"\']+)', html): print("LOC:", m)
            for m in re.findall(r'window\.location\s*=\s*["\']?([^"\';]+)', html): print("WIN:", m)
            # cookie set via js?
            for m in re.findall(r'document\.cookie[^;]{0,120}', html): print("CK:", m)
            # form actions
            for f in soup.find_all("form")[:5]: print("FORM:", f.get("action",""), [i.get("name") for i in f.find_all("input")])
asyncio.run(main())
