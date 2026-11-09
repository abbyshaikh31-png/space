import csv
from openpyxl import Workbook
from openpyxl.styles import Font

# Page 1: names, qty and prices as read in the vision transcriptions (page total 22,350).
# Flags: c = check predicted name/qty, u = unclear, o = reasonably clear
P1 = """1|12pis Soup Plate|12|1700|Soup Plate Set (12)|c
2|12pis Sweet Bowl|12|1100|Mithai Katori Set (12)|c
3|12pis Sweet Plate|12|1080|Mithai Plate Set (12)|c
4|12p Tea SponE|12|280|Chai Chammach Set (12)|c
5|2p RICE Dish|2|1100|Chawal Katori (2)|c
6|2p RICE Spone|2|180|Chawal Chammach (2)|c
7|1p Fild Bowl|1|550|Dal Katori|c
8|6n/0|6|480|Unclear (6 No)|u
9|5n/0|5|440|Unclear (5 No)|u
10|Spone|1|680|Chammach|c
11|Tea Glass|12|900|Chai Gilas Set (12)|c
12|Water Glass|12|1100|Paani Gilas Set (12)|c
13|Tea Cup|12|1300|Chai Pyala Set (12)|c
14|Soup Box|1|180|Shorba Dabba|c
15|Akka|1|550|Unclear|u
16|Puri Darrba Sato|1|380|Poori Darba Satto|c
17|Clip tin Box|1|750|Clip Tin Dabba|c
18|9No Latha|9|300|Latha (9 No)|o
19|11No Latha|11|480|Latha (11 No)|o
20|12No Latha|12|750|Latha (12 No)|o
21|Hot Ring|1|200|Garam Ring|o
22|4pis W Jug|4|2200|Paani Jug (4 pcs)|c
23|1p HKA Priyapol|1|790|Unclear|u
24|1p Tankutti|1|1100|Tankki|c
25|GHADA STAND|1|760|Ghada Stand|o
26|Souspan|1|480|Sauspan|o
27|Juse Chani|1|760|Juice Chhanni|o
28|3No Tray|3|480|Tray (3 No)|o
29|4No Tray|4|550|Tray (4 No)|o
30|Steel Trat|1|750|Steel Thaat|o"""

wb = Workbook()
ws = wb.active
ws.title = "Items"
ws.append(["Page", "Row", "Item as written", "Qty", "Price (Rs)", "Predicted name", "Flag"])
for c in ws[1]:
    c.font = Font(bold=True)

tot = {}
for line in P1.splitlines():
    r, n, q, p, pred, f = line.split("|")
    ws.append([1, int(r), n, int(q), int(p), pred, f])
    tot[1] = tot.get(1, 0) + int(p)

# Pages 2-4 from the transcription file already written to the workspace
with open("dowry_pages_2_4.csv", encoding="utf-8") as fh:
    for d in csv.DictReader(fh):
        pg = int(d["page"])
        price = int(d["price_as_written"])
        ws.append([pg, int(d["row"]), d["item_as_written"], d["qty_as_written"], price, "pending", "pending"])
        tot[pg] = tot.get(pg, 0) + price

written = {1: 22350, 2: 11390, 3: 58440, 4: 62030}
rc = wb.create_sheet("Reconciliation")
rc.append(["Page", "Sum of rows (Rs)", "Written page total (Rs)", "Match"])
for pg in sorted(written):
    rc.append([pg, tot[pg], written[pg], "yes" if tot[pg] == written[pg] else "no"])
grand = sum(tot.values())
rc.append(["Grand", grand, 154210, "yes" if grand == 154210 else "no"])

nt = wb.create_sheet("Notes")
for line in [
    "Flags: c = check predicted name or quantity; u = unclear; o = reasonably clear; pending = not yet predicted.",
    "Predicted Hyderabad-style names are interpretations, not confirmed against the source photos.",
    "Page 4 row 5 (34980) is kept as read; it is consistent with the written page total of 62,030.",
    "Page 2 total is 11,390 (not 11,290); the row sum confirms it.",
    "Pages 2-4 predicted names are pending a separate pass.",
]:
    nt.append([line])

wb.save("dowry_items.xlsx")
print("rows:", ws.max_row - 1)
print("page sums:", tot, "grand:", grand)