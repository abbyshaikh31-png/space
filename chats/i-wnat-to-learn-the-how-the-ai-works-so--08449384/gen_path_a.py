import json, html

d = json.load(open("path_a_numbers.json"))
def mat(name, m):
    rows = "".join("<tr>" + "".join(f"<td>{v:.3f}</td>" for v in r) + "</tr>" for r in m)
    return f"<h4>{name} {html.escape(str([len(m), len(m[0])]))}</h4><table><tbody>{rows}</tbody></table>"

parts = []
parts.append(mat("S = QKᵀ (raw scores)", d["S"]))
parts.append(mat("S/√d_k (d_k=4, √d_k=2)", d["Sn"]))
parts.append(mat("A = softmax(S/√d_k)", d["A"]))
parts.append(mat("Z = A·V (context vectors)", d["Z"]))
parts.append(mat("A_masked (causal)", d["Am"]))
parts.append(mat("Z_masked = A_masked·V", d["Zm"]))

open("path_a_sections.html", "w").write("\n".join(parts))
print("sections written", len(parts))
print("Am rowsums:", [round(sum(r), 6) for r in d["Am"]])
print("A rowsums:", [round(sum(r), 6) for r in d["A"]])