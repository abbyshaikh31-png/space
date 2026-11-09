import re
import openpyxl
from openpyxl.styles import Font, PatternFill

text = open('dowry_data.txt', encoding='utf-8').read()
pat = re.compile(r'([1-4])\|(\d{1,2})\|([^|]*)\|([^|]*)\|([^|]*)\|(.*?)(?=[1-4]\|\d{1,2}\||\n|$)', re.S)
records = []
for m in pat.finditer(text):
    page, row, name, qty, price, notes = m.groups()
    name, qty, price, notes = name.strip(), qty.strip(), price.strip(), notes.strip()
    try:
        p = int(price.replace(',', '').replace("'", ''))
    except ValueError:
        p = None
    records.append((int(page), int(row), name, qty, p, notes))

# Hyderabad (Begum Bazaar) bartan-trade predicted spellings
fix = {'Lotha': 'Lota', 'Dechi': 'Degchi', 'Tava': 'Tawa', 'Chani': 'Chhanni',
       'Kadai': 'Kadhai', 'pis': 'pcs', 'Tiffin': 'Tiffin', 'Bucket': 'Balti',
       'Chhanni': 'Chhanni', 'Thali': 'Thali', 'Jet': 'Jug', 'Trolly': 'Trolley'}

def predict(n):
    out = n
    for k, v in fix.items():
        out = re.sub(r'\b' + re.escape(k) + r'\b', v, out, flags=re.I)
    return out

wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Items'
hdr = ['Page', 'Row', 'Name as written', 'Predicted name (Begum Bazaar)', 'Quantity', 'Price (Rs)', 'Notes']
ws.append(hdr)
for c in ws[1]:
    c.font = Font(bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='1F4E78')
for r in records:
    ws.append([r[0], r[1], r[2], predict(r[2]), r[3], r[4], r[5]])
for col, w in zip('ABCDEFG', [7, 6, 34, 34, 16, 12, 50]):
    ws.column_dimensions[col].width = w

chk = wb.create_sheet('Page Check')
chk.append(['Page', 'Rows', 'Sum of prices', 'Printed total', 'Gap'])
printed = {1: 22350, 2: 11290, 3: 58440, 4: 62030}
for i, pg in enumerate(sorted(printed), start=2):
    chk.append([pg, f'=COUNTIF(Items!A:A,{pg})', f'=SUMIF(Items!A:A,{pg},Items!F:F)',
                printed[pg], f'=D{i}-C{i}'])
chk.append(['All pages', '', '=SUM(C2:C5)', 154210, '=D6-C6'])

wb.save('dowry_items.xlsx')
print('rows parsed:', len(records))
for pg in sorted(printed):
    s = sum(r[4] or 0 for r in records if r[0] == pg)
    print('page', pg, 'sum', s, 'printed', printed[pg], 'gap', printed[pg] - s)