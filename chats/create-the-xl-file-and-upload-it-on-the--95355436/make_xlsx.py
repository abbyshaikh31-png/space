import openpyxl, random, requests
from openpyxl.styles import Font
wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Student Data'
headers = ['Student ID','Name','Gender','Age','Grade','Class','Math','Science','English','Attendance %','Email']
ws.append(headers)
for c in range(1,12):
    ws.cell(1,c).font = Font(bold=True)
first=['James','Mary','John','Patricia','Robert','Jennifer','Michael','Linda','David','Elizabeth','William','Susan','Richard','Jessica','Joseph','Sarah','Thomas','Karen','Charles','Nancy']
last=['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez','Anderson','Taylor','Thomas','Moore','Jackson','Martin','Lee','Clark','Lewis','Walker']
for i in range(1,101):
    name=f"{random.choice(first)} {random.choice(last)}"
    row=[f'STU{i:04d}',name,random.choice(['Male','Female']),random.randint(14,18),random.choice([9,10,11,12]),random.choice(['A','B','C']),random.randint(35,100),random.randint(35,100),random.randint(35,100),round(random.uniform(70,100),1),name.split()[0].lower()+f'.{i}@school.edu']
    ws.append(row)
wb.save('student_data.xlsx')
print('saved')
r=requests.post('https://tmpfiles.org/api/v1/upload',files={'file':open('student_data.xlsx','rb')},timeout=60)
print('tmpfiles:',r.status_code,r.text[:300])
r2=requests.post('https://file.io/?expires=1w',files={'file':('student_data.xlsx',open('student_data.xlsx','rb'),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')},timeout=60)
print('file.io:',r2.status_code,r2.text[:300])