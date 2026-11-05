"""Path B: sweep attention across input lengths (NumPy only).
Outputs: path_b_attention.json (Q/K/V/S/A per length), path_b_summary.csv
"""
import json, math
import numpy as np

rng = np.random.default_rng(11)
D, H, VOCAB = 16, 4, 64
d_h = D // H

def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)

E = rng.normal(0, 0.1, (VOCAB, D))
Wq = rng.normal(0, 0.1, (D, D))
Wk = rng.normal(0, 0.1, (D, D))
Wv = rng.normal(0, 0.1, (D, D))

def run(n):
    ids = rng.integers(0, VOCAB, n)
    X = E[ids]
    Q = X @ Wq
    K = X @ Wk
    V = X @ Wv
    r = lambda t: t.reshape(n, H, d_h).transpose(1, 0, 2)
    Qh, Kh, Vh = r(Q), r(K), r(V)
    S = Qh @ Kh.transpose(0, 2, 1) / math.sqrt(d_h)
    A = softmax(S)
    C = (A @ Vh).transpose(1, 0, 2).reshape(n, D)
    ent = float(-(A * np.log(A + 1e-12)).sum(-1).mean())
    return {"ids": ids.tolist(), "Q": Q.tolist(), "K": K.tolist(),
            "V": V.tolist(), "S": S.tolist(), "A": A.tolist(),
            "C": C.tolist(), "entropy": ent, "max_w": float(A.max())}

lengths = [2, 4, 6, 8, 12, 16]
res = {str(n): run(n) for n in lengths}
with open("path_b_attention.json", "w") as f:
    json.dump(res, f, indent=1)

rows = ["seq_len,heads,head_dims,attn_rows,rowsum_mean,entropy_mean,max_weight"]
for n in lengths:
    d = res[str(n)]
    A = np.array(d["A"])
    rows.append("%d,%d,%d,%d,%.6f,%.6f,%.6f" % (n, H, d_h, A.shape[1],
                  A.sum(-1).mean(), d["entropy"], d["max_w"]))
with open("path_b_summary.csv", "w") as f:
    f.write("\n".join(rows) + "\n")

print("swept lengths:", lengths)
for n in lengths:
    print(n, "A shape", np.array(res[str(n)]["A"]).shape,
          "rowsum mean %.4f" % np.array(res[str(n)]["A"]).sum(-1).mean())