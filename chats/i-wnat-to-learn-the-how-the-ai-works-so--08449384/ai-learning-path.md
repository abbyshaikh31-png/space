# AI Learning Path: From Math to a Working Mini-Transformer

This plan turns the conceptual guide (`ai-transformer-guide.html` / `.pdf`) into a hands-on
track. Two paths run in parallel; you can pick one, but Path B is far more effective if
Path A is done concurrently.

## Path A — Attention Equations Walkthrough (Understanding)

Goal: derive every tensor shape in the Transformer by hand on a 3-token example, so that
reading a real implementation becomes mechanical rather than mysterious.

### A1. Shapes ledger (the single most useful table)

| Symbol | Meaning | Shape (batch B, seq N, model D) | Concrete toy numbers |
|---|---|---|---|
| X | input embeddings | (B, N, D) | (1, 3, 8) |
| W_Q | query projection | (D, D_k) | (8, 4) |
| W_K | key projection | (D, D_k) | (8, 4) |
| W_V | value projection | (D, D_v) | (8, 4) |
| Q, K | queries, keys | (B, N, D_k) | (1, 3, 4) |
| V | values | (B, N, D_v) | (1, 3, 4) |
| S = QK^T | raw scores | (B, N, N) | (1, 3, 3) |
| A = softmax(S/√d_k) | attention weights | (B, N, N) | (1, 3, 3) |
| Z = AV | context vectors | (B, N, D_v) | (1, 3, 4) |
| MHA | multi-head output | (B, N, D) | (1, 3, 8) |

### A2. Steps

1. **Tokenize a 3-token sentence** by hand. Write the integer IDs.
2. **Look up embeddings** from a toy table you invent. Confirm `X` shape.
3. **Add positional encoding** as a sinusoid: `PE(pos,2i)=sin(pos/10000^(2i/D))`.
4. **Project** to Q, K, V with the toy matrices. Write out full numbers.
5. **Score** every query–key pair (9 numbers for N=3). Divide by `√d_k = 2`.
6. **Softmax** row-wise. Verify each row sums to 1.0.
7. **Weight values** to obtain `Z`. Note that row i is a convex combination of rows of V.
8. **Mask** the future (decoder) with `-inf` before the softmax. Redo step 6 and observe
   that the masked columns receive exactly zero weight.
9. **Multi-head**: repeat with `H=2`, `D_k=2`, `D_v=4`, concatenate, apply `W_O`.
10. **Add residuals and LayerNorm**, then apply the FFN and LayerNorm again.

Deliverable: a single-page PDF containing the 9-number score matrix, three softmax rows,
and the resulting context vectors, with each line annotated by shape.## Path B — Build a Mini-Transformer From Scratch (Implementation)

Goal: implement a ~120-line character-level decoder-only Transformer in plain PyTorch that
trains on a tiny corpus, generates text, and prints attention maps.

### B1. Project layout

```
mini_transformer/
  tokenizer.py        # byte/char-level vocab, encode/decode
  model.py            # MultiHeadAttention, Block, MiniGPT
  train.py            # dataset, loop, checkpointing
  inspect.py          # attention heatmap + generation samples
  tests/test_shapes.py
```

### B2. Implementation order (each step ends with a runnable check)

1. **Tokenizer.** Map bytes to IDs (`len(vocab)=256`). Check: `decode(encode(s)) == s`.
2. **Embedding + position.** `nn.Embedding(V, D)` plus learned positions. Check shape `(B,N,D)`.
3. **Causal mask.** `mask[i,j] = 0 if j<=i else -inf`. Check: `softmax(scores+mask)` has
   zero above the diagonal and rows sum to 1.
4. **Scaled dot-product attention.** Implement manually (no `nn.MultiheadAttention`) so
   every line matches Path A. Assert `scores.shape == (B,H,N,N)`.
5. **Multi-head.** Split `D` into `H` heads of `D/H`, concatenate, project with `W_O`.
   Check: output shape `(B,N,D)`; a random-init model must not crash on long inputs.
6. **Feed-forward + residual + LayerNorm.** Pre-norm layout:
   `x = x + MHA(LN(x))` then `x = x + FFN(LN(x))`, `FFN` width `4D`, GELU.
7. **Block stack.** `N_layers` blocks, final LayerNorm.
8. **LM head.** `Linear(D, V)` producing logits `(B,N,V)`; cross-entropy against shifted
   targets with `ignore_index`.
9. **Training loop.** AdamW, lr 3e-4, cosine schedule, gradient clip 1.0, batch 32,
   block size 64. Log loss every 50 steps; must drop below ~1.7 nats/char quickly on a
   tiny corpus.
10. **Generation.** Temperature + top-k sampling, KV-cache optional (stretch). Seed for
    reproducibility.
11. **Inspection.** Print per-head attention matrices as text heatmaps and export one PNG.

### B3. Hyperparameters that matter

| Knob | Tiny setting | Typical GPT-3-class | Effect |
|---|---|---|---|
| layers | 4 | 96 | depth |
| d_model | 128 | 4096 | width |
| heads | 4 | 96 | head_dim fixed at 64 |
| context | 64 | 2048+ | attention is O(N^2) |
| dropout | 0.0 | 0.1 | regularization |
| optimizer | AdamW, clip 1.0 | AdamW, warmup | stability |

### B4. Deliberate failure drills (do these on purpose)

- Remove the `1/sqrt(d_k)` scaling and watch loss blow up with high logits.
- Remove the causal mask and watch the model copy the plaintext answer.
- Swap pre-norm and post-norm and observe training stability differences.
- Set `V` projection to identity and inspect how the attention maps change.
- Freeze embeddings and observe slower loss convergence on rare characters.

Deliverable: `mini_transformer/` repository that trains to a visibly coherent sample and
renders one attention heatmap, plus a README explaining each line against Path A.## Path B — Build a Mini-Transformer From Scratch (Doing)

Goal: implement a decoder-only Transformer in PyTorch, train it on a tiny corpus, and
generate text. Every layer you write should map to a row in the Path A shapes ledger.

### B0. Project layout

```
mini_transformer/
  tokenizer.py   # char/byte-level BPE-lite encoder + decoder
  model.py       # attention, block, full model
  train.py       # data pipeline, loop, checkpointing
  sample.py      # autoregressive generation
  viz.py         # attention heatmaps
tests/
  test_shapes.py # assert every intermediate tensor shape
```

### B1. Tokenizer

Write a byte-level tokenizer first. It has no vocabulary file, no merge table, and no
trainable parts — which makes it the fastest way to get end-to-end signal. Replace it
later with a learned BPE.

```python
# tokenizer.py
class ByteTokenizer:
    def __init__(self, limit=256):
        self.vocab_size = limit
        self.idx = {c: i for i, c in enumerate(range(limit))}

    def encode(self, text):
        return list(text.encode("utf-8"))

    def decode(self, ids):
        return bytes(ids).decode("utf-8", errors="replace")
```

Check: `decode(encode(s)) == s` for ASCII, and that `len(ids) == len(s.encode())`.

### B2. Model skeleton and shape asserts

Write the model so every intermediate asserts its shape. If an assert fires, the shape
ledger in Path A is your debugging map.

```python
# model.py
import math, torch, torch.nn as nn, torch.nn.functional as F

class CausalSelfAttention(nn.Module):
    def __init__(self, d_model=64, n_head=4, max_len=128):
        super().__init__()
        assert d_model % n_head == 0
        self.h, self.dh = n_head, d_model // n_head
        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.proj = nn.Linear(d_model, d_model)
        self.register_buffer("mask", torch.tril(torch.ones(max_len, max_len)).bool())

    def forward(self, x):
        B, N, D = x.shape
        q, k, v = self.qkv(x).split(D, dim=2)
        q = q.view(B, N, self.h, self.dh).transpose(1, 2)
        k = k.view(B, N, self.h, self.dh).transpose(1, 2)
        v = v.view(B, N, self.h, self.dh).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.dh)
        att = att.masked_fill(~self.mask[:N, :N], float("-inf"))
        att = att.softmax(dim=-1)
        y = (att @ v).transpose(1, 2).contiguous().view(B, N, D)
        return self.proj(y), att
```

Note the causal mask: `torch.tril` keeps the lower triangle (past + current), so a token
never attends to a future token — the same `-inf` trick from Path A step 8.