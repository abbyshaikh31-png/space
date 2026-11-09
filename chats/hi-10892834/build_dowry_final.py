import re
import openpyxl
from openpyxl.styles import Font

src = open('build_dowry_all.py', encoding='utf-8').read()
raw = src.split('RAW = """', 1)[1].split('"""', 1)[0]
# Repair lines glued together during the chunked append (e.g. "880#P3")
raw = re.sub(r'(?<=\S)#(P\d)', r'\n#\1', raw)

pages = {}
cur = None
for line in raw.splitlines():
    line = line.strip()
    if not line:
        continue
    if line.startswith('#P'):
        cur = line[1:]
        pages[cur] = []
        continue
    if line.startswith('#') or cur is None:
        continue  # skip struck-through heading comments
    parts = [p.strip() for p in line.split('|')]
    if len(parts) == 3:  # pages 1-2: as-written, qty, price
        parts = [parts[0], parts[0], parts[1], parts[2]]
    if len(parts) != 4:
        print('SKIPPED malformed line:', line)
        continue
    pages[cur].append(tuple(parts))

wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Dowry List'
headers = ['Page', 'Row', 'Item (as written)', 'Predicted English name',
           'Qty', 'Price (Rs)', 'Uncertain price?']
ws.append(headers)
for c in ws[1]:
    c.font = Font(bold=True)

grand = 0
for page_key, items in pages.items():
    page_no = page_key[1:]
    subtotal = 0
    for i, (written, english, qty, price) in enumerate(items, 1):
        unc = '?' in price
        digits = re.sub(r'\D', '', price)
        num = int(digits) if digits else None
        if num is not None:
            subtotal += num
        ws.append([int(page_no), i, written, english, qty, num,
                   'Yes' if unc else 'No'])
    ws.append([int(page_no), '', f'Page {page_no} subtotal (computed)',
               '', '', subtotal, ''])
    grand += subtotal
    print(f'Page {page_no}: {len(items)} rows, computed subtotal {subtotal}')

ws.append(['', '', 'GRAND TOTAL (computed)', '', '', grand, ''])
for col, width in zip('ABCDEFG', [7, 6, 36, 36, 9, 12, 16]):
    ws.column_dimensions[col].width = width
wb.save('dowry_list_all_pages.xlsx')
print('saved dowry_list_all_pages.xlsx, grand total', grand)