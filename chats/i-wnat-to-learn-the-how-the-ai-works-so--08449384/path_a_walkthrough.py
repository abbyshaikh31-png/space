import json, math
import numpy as np

np.set_printoptions(precision=3, suppress=True)

rng = np.random.default_rng(7)
B, N, D, dk, dv = 1, 3, 8, 4, 4

X = np.round(rng.normal(0, 1, (N, D)), 2)
WQ = np.round(rng.normal(0, 0.6, (D, dk)), 2)
WK = np.round(rng.normal(0, 0.6, (D, dk)), 2)
WV = np.round(rng.normal(0, 0.6, (D, dv)), 2)

PE = np.array([
    [math.sin(p / 10000 ** (2 * i / D)) for i in range(D // 2)] for p in range(N)
], dtype=float)

Xin = X + np.hstack([PE, PE])  # (N, D)

Q = Xin @ WQ
K = Xin @ WK
V = Xin @ WV

S = Q @ K.T
Sn = S / math.sqrt(dk)


def softmax(v):
    e = np.exp(v - v.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


A = softmax(Sn)
Z = A @ V

mask = -1e9 * np.triu(np.ones((N, N)), 1)
Am = softmax(Sn + mask)
Zm = Am @ V

out = dict(X=X, PE=PE, Xin=Xin, Q=Q, K=K, V=V,
           S=S, Sn=Sn, A=A, Z=Z, Am=Am, Zm=Zm)
with open("path_a_numbers.json", "w") as f:
    json.dump({k: v.tolist() for k, v in out.items()}, f, indent=1)

print("shapes", {k: list(v.shape) for k, v in out.items()})
print("A=\n", np.round(A, 4))
print("row sums", np.round(A.sum(axis=1), 6))
print("Am=\n", np.round(Am, 4))
print("Z row1=", np.round(Z[0], 4))
print("Zm row2=", np.round(Zm[2], 4))