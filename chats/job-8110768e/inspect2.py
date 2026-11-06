import re
p = 'ai-transformer-guide.html'
s = open(p, encoding='utf-8').read()
print('LEN', len(s))
print('--- SECTIONS ---')
for m in re.finditer(r'<section id="([^"]+)"', s):
    print(m.group(1))
print('--- TAIL ---')
print(s[-1500:])
print('--- STYLE TAIL + BODY START ---')
i = s.find('</style>')
print(s[i:i+2600])
]<]minimax[>[