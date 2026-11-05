import re
src = open("mini_transformer.py").read()
src = src.replace(
    "P = rng.normal(0, 0.05, (N, D))",
    "MAXLEN = 16\nP = rng.normal(0, 0.05, (MAXLEN, D))")
src = src.replace(
    "X = E[tok][None] + P[None]",
    "X = E[tok][None] + P[:N][None]")
i = src.index("# 8. Greedy next-token loop")
tail = '''# 8. Greedy next-token loop (shared forward pass, position-safe)
def forward(ids):
    n = len(ids)
    xt = E[np.array(ids)] + P[:n]
    qkv = xt @ Wqkv
    q, k, v = np.split(qkv, 3, axis=-1)
    Q = q.reshape(1, n, H, d_h).transpose(0, 2, 1, 3)
    K = k.reshape(1, n, H, d_h).transpose(0, 2, 1, 3)
    Vv = v.reshape(1, n, H, d_h).transpose(0, 2, 1, 3)
    S = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(d_h)
    A = softmax(np.where(np.tril(np.ones((n, n), bool)), S, -1e9))
    C = (A @ Vv).transpose(0, 2, 1, 3).reshape(1, n, D)
    h = norm(xt + C @ Wo)
    h = norm(h + gelu(h @ W1) @ W2)
    return h

ctx = tok.tolist()
for step in range(3):
    h = forward(ctx)
    p = softmax((h[0, -1] @ E.T) / np.sqrt(D))
    nxt = int(p.argmax())
    ctx.append(nxt)
    print("step", step + 1, "-> next id", nxt, "p=%.4f" % p.max(), "ctx len", len(ctx))
print("generated ids:", ctx, "(random init => output is noise; shapes are the point)")
'''
open("mini_transformer.py", "w").write(src[:i] + tail)
print("patched, lines:", len((src[:i] + tail).splitlines()))