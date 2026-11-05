"""Path B - runnable mini Transformer (NumPy only).
Shapes: B=1, N=MAXLEN tokens, D=32, H=4 heads, d_head=8, vocab=32.
Causal self-attention + residuals + LayerNorm + FFN + tied-embedding LM head.
Run:  python3 mini_transformer.py
"""
import numpy as np

rng = np.random.default_rng(0)
B, MAXLEN, D, H, VOCAB = 1, 16, 32, 4, 32
d_h = D // H
assert D % H == 0

def norm(x, eps=1e-5):
    m = x.mean(-1, keepdims=True)
    v = x.var(-1, keepdims=True)
    return (x - m) / np.sqrt(v + eps)

def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)

def gelu(x):
    return 0.5 * x * (1 + np.tanh(0.7978845608 * (x + 0.044715 * x ** 3)))

print("--- Path B mini Transformer ---")
tok = np.array([3, 7, 11, 2, 19])
E = rng.normal(0, 0.05, (VOCAB, D))
P = rng.normal(0, 0.05, (MAXLEN, D))   # MAXLEN positions only
Wqkv = rng.normal(0, 0.1, (D, 3 * D))
Wo = rng.normal(0, 0.1, (D, D))
W1 = rng.normal(0, 0.1, (D, 4 * D)); W2 = rng.normal(0, 0.1, (4 * D, D))

def attn_heads(t, n):
    return t.reshape(1, n, H, d_h).transpose(0, 2, 1, 3)

def forward(ids):
    """Position-safe forward: n = len(ids) <= MAXLEN."""
    n = len(ids)
    assert n <= MAXLEN, f"context {n} exceeds MAXLEN {MAXLEN}"
    xt = E[np.asarray(ids)] + P[:n]          # <-- matched length, no broadcast error
    qkv = xt @ Wqkv
    q, k, v = np.split(qkv, 3, axis=-1)
    Qh, Kh, Vh = attn_heads(q, n), attn_heads(k, n), attn_heads(v, n)
    mask = np.tril(np.ones((n, n), bool))
    S = Qh @ Kh.transpose(0, 1, 3, 2) / np.sqrt(d_h)
    A = softmax(np.where(mask, S, -1e9))
    C = (A @ Vh).transpose(0, 2, 1, 3).reshape(1, n, D)
    h = norm(xt + C @ Wo)
    h = norm(h + gelu(h @ W1) @ W2)
    logits = h @ E.T
    return logits, Aprint("logits", logits.shape)
print("attn row sums", np.round(A.sum(-1), 6).ravel())
print("argmax per pos", logits[0].argmax(-1))

# 8. Greedy generation loop
ctx = tok.tolist()
for step in range(3):
    lg, _ = forward(ctx)
    p = softmax(lg[0, -1] / np.sqrt(D))
    nxt = int(p.argmax())
    ctx.append(nxt)
    print(f"step {step}: next id {nxt}  p={p.max():.4f}  ctx={ctx}")

print("generated ids:", ctx)
print("(random init => text is noise; the point is that every shape is correct)")

# 9. Shape ledger
print("--- shape ledger ---")
for name, t in [("X", X), ("logits", logits), ("A", A)]:
    print(name, t.shape)# --- shape ledger ---
logits, A = forward(tok.tolist())
print("logits", logits.shape, "argmax", logits[0].argmax(-1))
print("A", A.shape, "row sums", np.round(A.sum(-1), 6).ravel())

# --- greedy generation (random weights => junk tokens; shapes are the point) ---
ctx = tok.tolist()
for step in range(4):
    logits, _ = forward(ctx)
    p = softmax(logits[0, -1])
    nxt = int(p.argmax())
    ctx.append(nxt)
    print(f"step {step}: next={nxt} p={p.max():.3f} ctx_len={len(ctx)}")
print("generated ids:", ctx)