import csv, io, os, re, shutil

HDR = ["Record_ID","Customer_Name","Contact_Info","Date_Standardized","Source_Channel",
       "Primary_Category","Secondary_Category","Sentiment","Urgency_Level","Action_Required"]

CATS = {"Billing","Bug","Feature_Request","Account_Auth","Logistics","Cancellation",
        "Praise","General_Query","None"}
CH = {"Email","Chat","Phone","Social","SMS","Form"}
SENT = {"Positive","Neutral","Negative","Mixed"}
URG = {"Critical","High","Medium","Low"}

rows = []
seen = set()
for fn in ["rows.txt","rows2.txt","rows3.txt"]:
    with open(fn, encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n").rstrip("\r")
            if not ln.strip():
                continue
            parts = ln.split("|")
            if parts[0].strip() == "Record_ID":
                continue
            if len(parts) != 10:
                print("SKIP malformed (%d fields): %r" % (len(parts), ln[:60]))
                continue
            rec = [p.strip() for p in parts]
            if rec[1].upper() == "REMOVE" or rec[0].upper() == "REMOVE":
                print("DROPPED removal marker:", rec[0])
                continue
            if rec[0] in seen:
                print("DROPPED duplicate ID:", rec[0])
                continue
            seen.add(rec[0])
            rows.append(rec)

print("unique records after dedupe:", len(rows))

# re-sequence IDs REC-1001..
for i, r in enumerate(rows):
    r[0] = "REC-%d" % (1001 + i)

# validation
errs = []
for r in rows:
    rid = r[0]
    if not re.fullmatch(r"REC-\d{4}", rid):
        errs.append((rid, "bad id"))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", r[3]):
        errs.append((rid, "bad date %r" % r[3]))
    if r[4] not in CH: errs.append((rid, "channel %r" % r[4]))
    if r[5] not in CATS: errs.append((rid, "primary %r" % r[5]))
    if r[6] not in CATS: errs.append((rid, "secondary %r" % r[6]))
    if r[7] not in SENT: errs.append((rid, "sentiment %r" % r[7]))
    if r[8] not in URG: errs.append((rid, "urgency %r" % r[8]))
    if not (3 <= len(r[9].split()) <= 6): errs.append((rid, "action word count %r" % r[9]))
    if r[1] == "": errs.append((rid, "empty name"))
    if r[2] == "": errs.append((rid, "empty contact"))

buf = io.StringIO()
w = csv.writer(buf, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
w.writerow(HDR)
w.writerows(rows)
data = buf.getvalue()

with open("rows_combined.csv", "w", encoding="utf-8", newline="") as f:
    f.write(data)
shutil.copyfile("rows_combined.csv", "customers.csv")

print("=== VALIDATION ERRORS:", len(errs))
for e in errs: print("  ", e)

# read back with csv reader
with open("rows_combined.csv", encoding="utf-8", newline="") as f:
    back = list(csv.reader(f))
print("header ok:", back[0] == HDR)
print("data rows:", len(back) - 1)
ids = [r[0] for r in back[1:]]
print("ids sequential:", ids == ["REC-%d" % (1001 + i) for i in range(len(ids))])
print("unique ids:", len(set(ids)) == len(ids))
print("all 10 cols:", all(len(r) == 10 for r in back))
with open("rows_combined.csv", encoding="utf-8") as f:
    raw = f.read().splitlines()
q = [l for l in raw if '"' in l]
print("lines requiring quotes (contain commas):", len(q))
for l in q[:6]: print("   ", l)
print("LF-only endings:", open("rows_combined.csv","rb").read().count(b"\r") == 0)
print("bytes:", os.path.getsize("rows_combined.csv"))