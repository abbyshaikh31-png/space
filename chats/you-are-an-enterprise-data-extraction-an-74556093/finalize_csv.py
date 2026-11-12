import csv, io, os, re

HDR = ["Record_ID","Customer_Name","Contact_Info","Date_Standardized","Source_Channel",
       "Primary_Category","Secondary_Category","Sentiment","Urgency_Level","Action_Required"]
CATS = {"Billing","Bug","Feature_Request","Account_Auth","Logistics","Cancellation",
        "Praise","General_Query","None"}
CHAN = {"Email","Chat","Phone","Social","SMS","Form"}
SENT = {"Positive","Neutral","Negative","Mixed"}
URG  = {"Critical","High","Medium","Low"}

rows = {}
order = []
for f in ("rows.txt","rows2.txt","rows3.txt"):
    if not os.path.exists(f):
        continue
    for ln in io.open(f, encoding="utf-8").read().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("===") or ln.startswith("Record_ID|"):
            continue
        p = [x.strip() for x in ln.split("|")]
        if len(p) != 10:
            continue
        rid = p[0]
        if rid.endswith("REMOVE") or p[1] == "REMOVE":
            print("DROPPED marker:", rid); continue
        if rid in rows:
            print("DUP dropped:", rid); continue
        rows[rid] = p
        order.append(rid)

order.sort(key=lambda r: int(re.sub(r"\D","",r)))
recs = [rows[r] for r in order]

OVR = {
 "REC-1004": {"Action_Required":"Thank user and log dark mode"},
 "REC-1017": {"Action_Required":"Fix 2FA SMS delivery restore access"},
 "REC-1023": {"Date_Standardized":"Unknown"},
}
for i,p in enumerate(recs):
    for k,v in OVR.get(p[0],{}).items():
        p[4+HDR.index(k)] = v

for i,p in enumerate(recs):
    p[0] = "REC-%d" % (1001+i)

errs = []
seen = set()
for i,p in enumerate(recs):
    rid = p[0]
    if rid in seen: errs.append((rid,"duplicate id"))
    seen.add(rid)
    if rid != "REC-%d" % (1001+i): errs.append((rid,"not sequential"))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", p[3]) and p[3] != "Unknown":
        errs.append((rid,"bad date %r" % p[3]))
    if p[4] not in CHAN: errs.append((rid,"channel %r" % p[4]))
    if p[5] not in CATS: errs.append((rid,"primary %r" % p[5]))
    if p[6] not in CATS: errs.append((rid,"secondary %r" % p[6]))
    if p[7] not in SENT: errs.append((rid,"sentiment %r" % p[7]))
    if p[8] not in URG: errs.append((rid,"urgency %r" % p[8]))
    w = len(p[9].split())
    if w < 3 or w > 6: errs.append((rid,"action words %d: %r" % (w,p[9])))
    if not p[1]: errs.append((rid,"empty name"))
    if not p[2]: errs.append((rid,"empty contact"))

with io.open("rows_combined.csv","w",encoding="utf-8",newline="") as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    w.writerow(HDR)
    for p in recs: w.writerow(p)

raw = io.open("rows_combined.csv",encoding="utf-8").read()
print("=== RECORDS:", len(recs))
print("=== VALIDATION ERRORS:", len(errs))
for e in errs: print("  ", e)
print("header ok:", raw.splitlines()[0] == ",".join(HDR))
print("data rows:", len(raw.strip().splitlines())-1)
print("unique ids:", len(set(p[0] for p in recs)))
print("quoted lines:", sum(1 for l in raw.splitlines() if '"' in l))
print("LF-only:", "\r" not in raw)
print("bytes:", len(raw.encode()))
print("---CSV---")
print(raw)