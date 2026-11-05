import re
src = open("mini_transformer.py").read()
src = src.replace(
    "P = rng.normal(0, 0.05, (N, D))",
    "MAXLEN = 16  # position table is longer than N so the generation loop can grow\nP = rng.normal(0, 0.05, (MAXLEN, D))"
)
src = src.replace(
    "    xt = E[np.array(ctx)] + P[:n]",
    "    xt = E[np.array(ctx)] + P[:n]  # P[:n] is safe: n <= MAXLEN"
)
src = src.replace(
    'print("generated ids:", ctx, "(random init => output is noise, shapes are the point)")',
    'print("generated ids:", ctx, "(random init => output is noise, shapes are the point)")\nprint("ctx length", len(ctx), "P rows", P.shape[0])'
)
open("mini_transformer.py", "w").write(src)
print("patched")