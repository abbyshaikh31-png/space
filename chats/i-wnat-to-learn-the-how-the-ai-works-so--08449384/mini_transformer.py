"""Path B - runnable mini Transformer (NumPy only).
Shapes: MAXLEN=16 positions, D=32, H=4 heads, d_head=8, vocab=32.
Causal self-attention + residual + LayerNorm + FFN + tied-embedding LM head.
Run: python3 mini_transformer.py
"""
import numpy as np

rng = np.random.default_rng(0)
MAXLEN, D, H, VOCAB = 16, 32, 4, 32
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

E = rng.normal(0, 0.05, (VOCAB, D))
P = rng.normal(0, 0.05, (MAXLEN, D))
Wqkv = rng.normal(0, 0.1, (D, 3 * D))
Wo = rng.normal(0, 0.1, (D, D))
W1 = rng.normal(0, 0.1, (D, 4 * D))
W2 = rng.normal(0, 0.1, (4 * D, D))

def forward(ids):
    """ids: list of token ids, length n <= MAXLEN. Returns (logits, attention)."""
    n = len(ids)
    assert n <= MAXLEN, "context exceeds MAXLEN"
    xt = E[np.asarray(ids)] + P[:n]
    qkv = xt @ Wqkv
    q, k, v = np.split(qkv, 3, axis=-1)
    r = lambda t: t.reshape(1, n, H, d_h).transpose(0, 2, 1, 3)
    Qh, Kh, Vh = r(q), r(k), r(v)
    S = Qh @ Kh.transpose(0, 1, 3, 2) / np.sqrt(d_h)
    A = softmax(np.where(np.tril(np.ones((n, n), bool)), S, -1e9))
    C = (A @ Vh).transpose(0, 2, 1, 3).reshape(1, n, D)
    h = norm(xt + C @ Wo)
    h = norm(h + gelu(h @ W1) @ W2)
    return h @ E.T, A

if __name__ == "__main__":
    tok = [3, 7, 11, 2, 19]
    logits, A = forward(tok)
    print("logits", logits.shape, "argmax", logits[0].argmax(-1))
    print("A rowsums", np.round(A.sum(-1), 6).ravel())
    ctx = list(tok)
    for _ in range(4):
        lg, _a = forward(ctx)
        p = softmax(lg[0, -1])
        nxt = int(p.argmax())
        ctx.append(nxt)
        if len(ctx) > MAXLEN:
            ctx = ctx[-MAXLEN:]
    print("generated ids:", ctx)
    print("OK")