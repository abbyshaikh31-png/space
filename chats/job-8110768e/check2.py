import re, os, hashlib, subprocess

p = "ai-transformer-guide.html"
s = open(p, encoding="utf-8").read()
print("bytes", len(s.encode("utf-8")))
print("doctype", s.lstrip().lower().startswith("<!doctype html"))
print("closing", s.rstrip().lower().endswith("</html>"))
print("sections_open", len(re.findall(r"<section\b", s)))
print("sections_close", len(re.findall(r"</section>", s)))
print("h2", len(re.findall(r"<h2\b", s)))
print("h3", len(re.findall(r"<h3\b", s)))
print("svg", s.count("<svg"))
print("tables", s.count("<table"))
print("figures", s.count("<figure"))
print("eq", s.count('class="eq"'))
print("ext_links", s.count('href="http'))
ids = re.findall(r'<section id="([^"]+)"', s)
print("ids", ids)
anchors = re.findall(r'href="#([^"]+)"', s)
print("missing_anchors", [a for a in anchors if a not in ids])
for t in ["div", "figure", "table", "ul", "ol", "pre", "svg"]:
    o = len(re.findall(r"<" + t + r"\b", s))
    c = len(re.findall(r"</" + t + r">", s))
    print("tag", t, o, c, "OK" if o == c else "MISMATCH")
print("sha256", hashlib.sha256(s.encode("utf-8")).hexdigest())
print("tail", repr(s[-200:]))
]<]minimax[>[