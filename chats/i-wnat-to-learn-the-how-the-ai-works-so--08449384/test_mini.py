from mini_transformer import forward
import numpy as np
ok=True
for n in range(1,17):
    ids=list(range(n))
    lg,A=forward(ids)
    assert lg.shape==(1,n,32), lg.shape
    assert A.shape==(1,4,n,n), A.shape
    rs=np.round(A.sum(-1).ravel(),6)
    if not np.allclose(rs,1.0): ok=False; print("bad rowsum",n)
    # causality: upper triangle must be exactly 0
    fut=A[0].copy()
    for h in range(4):
        fut[h]=np.triu(fut[h],1)
    assert np.allclose(fut,0.0), ("future leak",n)
print("ALL PASS", ok, "| lengths 1..16 checked")
