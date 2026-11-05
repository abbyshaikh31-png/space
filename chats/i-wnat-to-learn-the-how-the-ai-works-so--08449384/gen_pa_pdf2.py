import json, html

d = json.load(open("path_a_numbers.json"))

def mat(title, m, note=""):
    head = "".join("<th>j%d</th>" % (j + 1) for j in range(len(m[0])))
    rows = ""
    for i, r in enumerate(m):
        cells = "".join("<td>%.3f</td>" % v for v in r)
        rows += "<tr><th>i%d</th>%s</tr>" % (i + 1, cells)
    shape = "shape [%d x %d]" % (len(m), len(m[0]))
    return ("<h3>%s  <span class=dim>%s</span></h3><p class=note>%s</p>"
            "<table><tr><th></th>%s</tr>%s</table>"
            % (html.escape(title), shape, html.escape(note), head, rows))

CSS = """<!doctype html><meta charset="utf-8"><title>Path A</title>
<style>
body{font:14px/1.6 Georgia,serif;max-width:780px;margin:24px auto;padding:0 16px}
table{border-collapse:collapse;width:100%;margin:8px 0 18px}
td{border:1px solid #999;padding:6px 8px;font-family:ui-monospace,monospace;text-align:right}
th{border:1px solid #999;padding:6px 8px;font-family:system-ui;background:#eee;text-align:center}
h1,h2,h3{font-family:system-ui}
.dim{color:#666;font-size:12px;font-weight:400}
.note{color:#555;font-size:13px;margin:4px 0 8px}
code{font-family:ui-monospace,monospace;background:#f4f4f4;padding:1px 4px}
</style><h1>Path A: Attention Computed by Hand</h1>
<p>Every number below was produced by <code>path_a_walkthrough.py</code> (NumPy only).
Toy config: N=3 tokens, D=8 model dims, d_k = d_v = 4, sqrt(d_k) = 2.</p>
"""

parts = [CSS]
parts.append("<h2>1. Input embeddings X, shape [3 x 8]</h2>" + mat("X (random init embeddings)", d["X"], "Each row is one token's vector. Random here because the model is untrained."))
parts.append("<h2>2. Positional encoding</h2>" + mat("PE (sinusoidal, 3 x 4 broadcast to D)", d["PE"], "PE(pos,2i)=sin(pos/10000^(2i/D)). Added to X so order information exists."))
parts.append("<h2>3. Projections Q, K, V</h2>")
parts.append(mat("Q = X_in @ W_Q", d["Q"], "Queries: what each token is looking for."))
parts.append(mat("K = X_in @ W_K", d["K"], "Keys: what each token offers."))
parts.append(mat("V = X_in @ W_V", d["V"], "Values: the content actually mixed."))
parts.append("<h2>4. Attention scores</h2>")
parts.append(mat("S = Q K^T", d["S"], "Raw dot products between every query and every key: 9 numbers for N=3."))
parts.append(mat("S / sqrt(d_k)", d["Sn"], "Dividing by 2 keeps dot products from blowing up as d_k grows."))
parts.append("<h2>5. Softmax over keys</h2>")
parts.append(mat("A = softmax(S / sqrt(d_k))", d["A"], "Each row is a distribution over the 3 keys."))
parts.append("<h2>6. Context vectors</h2>")
parts.append(mat("Z = A @ V", d["Z"], "Row i is a convex combination of the rows of V."))
parts.append("<h2>7. Causal masking</h2>")
parts.append(mat("A_masked (future positions = 0)", d["Am"], "Same softmax but with -inf added above the diagonal, so a token cannot read the future."))
parts.append(mat("Z_masked = A_masked @ V", d["Zm"], "Row 2 now mixes only tokens 1 and 2."))
parts.append("<h2>8. Read-out</h2>"
             "<p>Next-token logits are <code>logits = h @ W_vocab^T</code>, and probabilities come from a softmax over the vocabulary. "
             "At inference the model appends the chosen token to the context and runs the whole stack again. "
             "That loop is the entire generative behaviour of a language model.</p>")
parts.append("<h2>9. Multi-head</h2>"
             "<p>Repeat steps 3-6 with H heads (each with its own W_Q, W_K, W_V of width D/H), then concatenate the "
             "H context matrices and apply an output projection W_O. Different heads can specialise on different relations.</p>")
parts.append("<h2>10. Residuals, LayerNorm, FFN</h2>"
             "<p><code>x = LayerNorm(x + MHA(LayerNorm(x)))</code>, then <code>x = LayerNorm(x + FFN(LayerNorm(x)))</code>. "
             "The FFN applies the same two-layer network independently to each position.</p>")

open("path_a_walkthrough.html", "w").write("\n".join(parts))
print("wrote path_a_walkthrough.html", sum(len(x) for x in parts))
]<]minimax[>[