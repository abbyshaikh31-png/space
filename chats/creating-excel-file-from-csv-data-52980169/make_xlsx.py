import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

with open('chats/creating-excel-file-from-csv-data-52980169/addresses.csv', newline='', encoding='utf-8') as f:
    rows = list(csv.reader(f))

wb = Workbook()
ws = wb.active
ws.title = "Addresses"
for row in rows:
    ws.append(row)

# Style header
header_fill = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
for cell in ws[1]:
    cell.font = Font(bold=True, color='FFFFFF')
    cell.fill = header_fill

# Freeze header row, auto-fit columns
ws.freeze_panes = 'A2'
for col in ws.columns:
    width = max(len(str(c.value)) if c.value else 0 for c in col)
    ws.column_dimensions[get_column_letter(col[0].column)].width = min(width + 2, 60)

wb.save('chats/creating-excel-file-from-csv-data-52980169/addresses.xlsx')
print('OK data rows:', len(rows) - 1)
