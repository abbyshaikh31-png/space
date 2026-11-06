import re, os, html

SRC = os.path.join("..", "job-a5e4e15c", "base.html")
DST = "ai-transformer-guide.html"

if not os.path.exists(SRC):
    SRC = os.path.join("..", "job-a5e4e15c", "ai-transformer-guide.html")

s = open(SRC, encoding="utf-8").read()
print("SRC", SRC, len(s))

open_tag = s.count("<section")
close_tag = s.count("</section>")
h2 = len(re.findall(r"<h2[^>]*>", s))
ids = re.findall(r'id="([^"]+)"', s)
anchors = re.findall(r'href="#([^"]+)"', s)
tables = s.count("<table")
svgs = s.count("<svg")
links = re.findall(r'href="(https?://[^"]+)"', s)
math = s.count("class=\"eq\"")
print("sections open", open_tag, "close", close_tag)
print("h2", h2)
print("ids", len(ids), ids[:25])
print("anchors", len(anchors))
print("tables", tables, "svg", svgs, "mathblocks", math)
print("ext links", len(set(links)))
for l in sorted(set(links)):
    print("  ", l)
print("has doctype", s.lstrip().lower().startswith("<!doctype html"))
print("ends with html close", s.rstrip().endswith("</html>"))
# where is the imbalance
pos = 0
depth = 0
for m in re.finditer(r"</?section[^>]*>", s):
    tag = m.group(0)
    if tag.startswith("</"):
        depth -= 1
    else:
        depth += 1
    if depth < 0:
        print("EXTRA CLOSE at", m.start())
        break
print("final depth", depth)
]<]minimax[>[