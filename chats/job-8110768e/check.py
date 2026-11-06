import re, os, hashlib

p = "ai-transformer-guide.html"
if not os.path.exists(p):
    print("MISSING")
    raise SystemExit

s = open(p, encoding="utf-8").read()
print("bytes", len(s.encode("utf-8")))
print("doctype", s.lstrip().lower().startswith("<!doctype html"))
print("closing", s.rstrip().lower().endswith("</html>"))
print("sections", len(re.findall(r'<section\b', s)), len(re.findall(r'</section>', s)))
print("h2", len(re.findall(r'<h2\b', s)))
print("h3", len(re.findall(r'<h3\b', s)))
print("svg", s.count("<svg"))
print("tables", s.count("<table"))
print("figures", s.count("<figure"))
print("eq", s.count('class="eq"'))
print("links", s.count('href="http'))
ids = re.findall(r'<section id="([^"]+)"', s)
print("ids", ids)
anchors = re.findall(r'href="#([^"]+)"', s)
print("anchors", anchors)
print("missing anchors", [a for a in anchors if a not in ids])
print("tail", repr(s[-160:]))
print("sha", hashlib.sha256(s.encode("utf-8")).hexdigest())
]<]minimax[>[