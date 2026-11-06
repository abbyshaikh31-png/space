import re, hashlib, os, subprocess

p = 'ai-transformer-guide.html'
html = open(p, encoding='utf-8').read()

print('BYTES', len(html.encode('utf-8')))
print('SHA256', hashlib.sha256(html.encode('utf-8')).hexdigest())
print('DOCTYPE', html.lstrip()[:15].lower().startswith('<!doctype html'))
print('CLOSES_HTML', html.rstrip().endswith('</html>'))

# tag balance
void = set(['meta','link','br','hr','img','input','path','rect','circle','line','text','polygon','polyline','ellipse','use','stop','tspan','marker','g','defs','symbol','area','source','col','colgroup'])
tags = re.findall(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>', html)
stack = []
errs = 0
for close, name, selfclose in tags:
    n = name.lower()
    if n in void or selfclose == '/':
        continue
    if close:
        if stack and stack[-1] == n:
            stack.pop()
        else:
            errs += 1
            print('MISMATCH close', n, 'expected', stack[-1] if stack else None)
    else:
        stack.append(n)
print('UNCLOSED', stack)
print('TAG_ERRORS', errs)

ids = re.findall(r'\sid="([^"]+)"', html)
print('IDS', len(ids), ids)
h2 = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.S)
print('H2_COUNT', len(h2))
for h in h2:
    print('  -', re.sub(r'<[^>]+>', '', h).strip()[:90])
print('SVG_COUNT', html.count('<svg'))
print('TABLE_COUNT', html.count('<table'))
print('MATH_EQU', html.count('class="eq"'))
links = sorted(set(re.findall(r'href="(https?://[^"]+)"', html)))
print('EXT_LINKS', len(links))
for l in links:
    print('  *', l)
anchors = set(re.findall(r'href="#([^"]+)"', html))
print('ANCHOR_LINKS', len(anchors), 'BROKEN', sorted(a for a in anchors if a not in ids))
for key in ['Attention Is All You Need', 'Illustrated Transformer', 'Annotated Transformer']:
    print('CITE', key, key in html)
pdf = 'ai-transformer-guide.pdf'
if os.path.exists(pdf):
    data = open(pdf, 'rb').read()
    print('PDF_BYTES', len(data))
    print('PDF_SHA256', hashlib.sha256(data).hexdigest())
    print('PDF_PAGES', data.count(b'/Type /Page') - data.count(b'/Type /Pages'))
    print('PDF_HEADER', data[:8])
]<]minimax[>[