import re, os
p = 'ai-transformer-guide.html'
s = open(p, encoding='utf-8').read()
print('BYTES', os.path.getsize(p))
print('CHARS', len(s))
print('DOCTYPE', s[:60].strip())
print('ENDS_WITH_HTML', s.rstrip().endswith('</html>'))
print('H2_COUNT', len(re.findall(r'<h2', s)))
print('SECTIONS', re.findall(r'<section id="([^"]+)"', s))
print('TABLE_COUNT', len(re.findall(r'<table', s)))
print('SVG_COUNT', len(re.findall(r'<svg', s)))
print('HREF_EXT', re.findall(r'href="(https?://[^"]+)"', s))
print('---TAIL---')
print(s[-700:])
]<]minimax[>[