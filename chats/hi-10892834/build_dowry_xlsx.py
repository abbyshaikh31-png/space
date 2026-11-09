from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

rows = [
(1,"Soup Plate","12pcs","1700"),
(2,"Sweet Bowl","12pcs","1100"),
(3,"Sweet Plate","12pcs","1080"),
(4,"Tea Spoon","12p","280"),
(5,"Rice Dish","2p","1100"),
(6,"Rice Spoon","2p","180"),
(7,"Half Bowl","1p","450?"),
(8,"6 no ...","2p?","440"),
(9,"5 no ...","1p?","680"),
(10,"Spoon","1p?","900"),
(11,"Tea Glass","12p","1100"),
(12,"Water Glass","12p","1300"),
(13,"Tea Cup","12p","180"),
(14,"Soup Box","1p","550"),
(15,"Aicka","1p","380"),
(16,"Puri Dabba","1p","750"),
(17,"Clip Tiffin Box","1p","300"),
(18,"9 no Lotha","1p","480"),
(19,"1 no Lotha","1p","750"),
(20,"12 no Lotha","2p","200"),
(21,"Hot Pring?","2p?","200"),
(22,"4pcs Jug","4pcs","2200"),
(23,"4KA Priyapot?","1p","790?"),
(24,"Pankutti?","1p","1100"),
(25,"Chhada Stand?","2p","740?"),
(26,"Soupan","1p","480"),
(27,"Juse Chani?","2p","760"),
(28,"3no Tray","1p","480"),
(29,"4no Tray","1p","550"),
(30,"Steel Tray?","1p","750?"),
]

wb = Workbook()
ws = wb.active
ws.title = "Page 1"
ws.append(["BIHAR / MAINS - Dowry Item List, Page 1 (date 03/11/26, partly obscured)"])
ws.append([])
ws.append(["Row","Item (as written)","Quantity","Price (as written)","Price (number)","Uncertain"])
for c in ws[3]:
    c.font = Font(bold=True)
    c.fill = PatternFill("solid", fgColor="DDDDDD")
for r, item, qty, price in rows:
    num = int(price.replace("?", ""))
    unsure = "Yes" if "?" in item + qty + price else "No"
    ws.append([r, item, qty, price, num, unsure])
ws.append([])
ws.append(["", "Total (as legible on page)", "", "", 22350, "Verify"])
ws.column_dimensions["B"].width = 26
ws.column_dimensions["D"].width = 18
ws.column_dimensions["F"].width = 12
ws["A1"].font = Font(bold=True, size=12)
wb.save("dowry_list_page1.xlsx")
print("saved dowry_list_page1.xlsx with", len(rows), "rows")