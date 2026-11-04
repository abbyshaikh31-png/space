#!/usr/bin/env python3
import subprocess, json, time, concurrent.futures

QUERIES = [
 # News 20
 "monsoon withdrawal India latest IMD update","ISRO Gaganyaan test flight status","Telangana Rythu Bharosa payout news","RBI repo rate latest decision","Delhi air quality index this week","Cyclone Bay of Bengal track update","India vs England series schedule","Jio vs Airtel 5G tariff hike news","Nifty Sensex yesterday close","Hyderabad metro phase 2 approval","Uttarakhand avalanche rescue latest","Apple factory Foxconn Tamil Nadu news","Supreme Court electoral bonds verdict update","Indian Railways Vande Bharat new routes","US visa H1B rule change for Indians","Gold price India today 24 karat","Pradhan Mantri Awas Yojana beneficiaries update","GDP quarterly growth India 2026","ISRO NGLV development status","Telangana intermediate syllabus change 2026",
 # Tech 20
 "Claude vs ChatGPT coding benchmark 2026","AMD Ryzen 9 9950X price India","best noise cancelling headphones 2026","Llama latest open model release","Google Pixel 11a leaks","Windows 12 release date rumors","Nvidia N1X ARM laptop chip news","Postgres logical replication tutorial","best budget mirrorless camera 2026","Zinode vs Caddy web server benchmark","WhatsApp multi account feature update","codeium vs GitHub Copilot comparison","Go 1.25 generics changes","WireGuard vs OpenVPN speed test","cheapest EV battery recycling company","Apple M6 chip rumors","SSD vs NVMe controller firmware guide","Python 3.14 free threading performance","Starlink India launch price","Kali Linux top tools 2026",
 # GK 20
 "height of Mount Everest meters","inventor of the world wide web","national animal of Bhutan","speed of sound in air m/s","first Indian in space","chemical symbol for gold","monsoon onset date Kerala average","how many states in India 2026","number of bones in human ear","longest coastline country world","unit of electrical resistance","Telugu literary comrade Gurajada Apparao work","Bhagat Singh execution year","water freezing point celsius"," Función of chloroplast in cell","hottest planet in solar system","number of time zones Russia","Hibiscus flower botanical family","tallest statue in the world","largest desert in the world",
 # Site lookups 15
 "IRCTC tatkal booking hours","Aarogya Setu app download link","Digilocker official government portal","Telangana State Board of Intermediate official website","AP EAPCET official site link","BHU entrance exam portal","Jio customer care toll free number","Flipkart big billion days official page","Pradhan Mantri Jan Arogya Yojana portal","PAN card apply NSDL official","Chandigarh housing board site","Biodiversity board India official website","Ministry of Education India official site","Indian Institute of Science admission portal","EPFO member passbook login",
 # Fun/shopping 15
 "boAt Airdopes 141 price India","Redmi Note 15 Pro specs price","HP Pavilion laptop under 60000 review","JBL Flip 7 vs Sony ULT Field","best Kindle alternative India","Rummy vs Teen Patti legal India apps","Asus ROG Ally 2 price","iPhone SE 5 release date India","Airtel Fiber 1 Gbps plan price","best kids coding apps free 2026","RAL color chart online free","Fat Bear Week 2026 winner","UK snap election poll latest","FA Cup draw round 3 2027","Nobel Peace Prize 2026 winner",
]

def run_q(i, q):
    t0 = time.time()
    try:
        p = subprocess.run(["python3","free_search.py","search",q,"--count","3","--deadline","20"],
                           capture_output=True, text=True, timeout=90)
        out = p.stdout
        n = out.count("http")
        low = "low_quality" in out or "off-topic" in out.lower()
        ok = n >= 2 and not low
        return {"i":i,"q":q,"ok":ok,"urls":n,"low":low,"secs":round(time.time()-t0,1)}
    except Exception as e:
        return {"i":i,"q":q,"ok":False,"urls":0,"low":False,"secs":round(time.time()-t0,1),"err":str(e)[:80]}

# first 10 in-process to sanity check, save checkpoint
res = []
for i,q in enumerate(QUERIES[:10]):
    r = run_q(i,q); res.append(r)
    print(r["i"], "OK " if r["ok"] else "FAIL", r["urls"], r["secs"], "s", r["q"][:55], flush=True)
json.dump(res, open("batch_ck.json","w"))
print("SMOKE DONE", sum(r['ok'] for r in res), "/10")
