import aiohttp, asyncio, re, json
from bs4 import BeautifulSoup

CANDS = [
 ("rss","https://news.google.com/rss/search?q=best+books&hl=en-US&gl=US&ceid=US:en"),
 ("whoogle-sdf","https://whoogle.sdf.org/search?q=best+books"),
 ("searx-be","https://searx.be/search?q=best+books"),
 ("searx-garuda","https://search.garudalinux.org/search?q=best+books"),
 ("searx-tiekoetter","https://searx.tiekoetter.com/search?q=best+books"),
 ("searx-opnxng","https://opnxng.com/search?q=best+books"),
 ("searx-paulgo","https://sv.paulgo.io/search?q=best+books"),
 ("priv-au","https://priv.au/search?q=best+books"),
 ("lite-ddg","https://lite.duckduckgo.com/lite/?q=best+books"),
 ("g-nested","https://www.google.com/search?q=best+books&udm=14&hl=en"),
 ("g-news-rss-json","https://news.google.com/rss/search?q=%22best+books%22"),
 ("g-books-ndl","https://www.googleapis.com/books/v1/volumes?q=best+books"),
]
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36","Accept-Language":"en-US,en;q=0.9"}

async def main():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15), headers=UA) as s:
        async def go(name,url):
            try:
                async with s.get(url) as r:
                    body=await r.text()
                    info={}
                    if name.startswith("rss"):
                        t=re.findall(r"<title>(.*?)</title>",body)
                        info={"titles":t[1:5]}
                    elif "books" in name:
                        j=json.loads(body)
                        info={"n":j.get("totalItems"),"first":[i["volumeInfo"]["title"] for i in j.get("items",[])[:3]]}
                    else:
                        soup=BeautifulSoup(body,"html.parser")
                        res=soup.select("a.result-link, a.result, article h3 a, h3 a, a[href^='http']")
                        links=[a["href"] for a in res if a.get("href","").startswith("http")][:5]
                        titles=[a.get_text(strip=True)[:60] for a in res][:5]
                        info={"status":r.status,"ntitles":len(titles),"titles":titles[:3],"links":links[:3]}
                    print(name, "OK", info)
            except Exception as e:
                print(name, "ERR", type(e).__name__, str(e)[:100])
        await asyncio.gather(*(go(n,u) for n,u in CANDS))
asyncio.run(main())
