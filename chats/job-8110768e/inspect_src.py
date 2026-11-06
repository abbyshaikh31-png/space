import re, os
src = "../job-a5e4e15c/ai-transformer-guide.html"
h = open(src, encoding="utf-8").read()
print("bytes", len(h))
print("doctype", h.strip().startswith("<!DOCTYPE html>"))
ids = re.findall(r'<section id="([^"]+)"', h)
print("sections", len(ids), ids)
print("h2", len(re.findall(r"<h2", h)))
print("tables", len(re.findall(r"<table", h)))
print("svg", len(re.findall(r"<svg", h)))
print("links", re.findall(r'href="(http[^"]+)"', h))
print("head:", h[:120])
print("tail:", h[-120:])
for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', h, re.S):
    print("H2:", re.sub(r"<[^>]+>", "", m.group(1))[:70])
]<]minimax[>[