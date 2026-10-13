"""Experiment 48 (2026-10-12): the round-trip spectrum of the reservoir ring — is it above lasing threshold, and how many
cavity modes have useful memory?

The ring's round trip with the gain set to 1 is a linear map T on the n² field. Its eigenvalues λ_k (largest |λ| first) are the
cavity's modes and per-trip amplitude transmissions. With small-signal gain √G0 on the amplitude, the ring lases when
√G0·|λ_1| > 1; the global gain then clamps to √g = 1/|λ_1| and every other mode decays relative to the lasing one by
|λ_k/λ_1| per trip (memory τ_k = −1/ln|λ_k/λ_1| trips). Below threshold, mode k decays by √G0·|λ_k| per trip.
Also: how much of each input pattern lies in the span of the top-k modes (the input can only excite what it overlaps).
usage: python 48-spectrum.py <res dir name> [k=400]   → out/48/<name>.json
"""
import json, math, os, sys, time
import numpy as np
import torch
from scipy.sparse.linalg import LinearOperator, eigs
import res_gpu

name = sys.argv[1]; k = int(sys.argv[2]) if len(sys.argv) > 2 else 400
n = int(name.split('_n')[1].split('_')[0])
d_in = 64 if '_d64' in name else 1
suffix = name.split(f'res_n{n}' + ('_d64' if d_in == 64 else ''))[1]
R = res_gpu.Reservoir(n, 'c128', d_in=d_in, suffix=suffix)
G0 = R.meta['G0']


@torch.no_grad()
def T(x):
    E = torch.as_tensor(x, dtype=torch.complex128, device=R.dev).reshape(-1, n, n)
    E = R.trip(E, None, 1.0, 1.0)  # G0 = 1 → gain factor 1: the passive linear round trip
    return E.reshape(E.shape[0], -1).cpu().numpy()


t0 = time.time()
N = n * n
if N <= 4096:  # dense
    M = np.empty((N, N), complex)
    for j in range(0, N, 512):
        M[:, j:j + 512] = T(np.eye(N, dtype=complex)[j:j + 512]).T
    ev, V = np.linalg.eig(M)
    o = np.argsort(-np.abs(ev)); ev, V = ev[o][:k], V[:, o][:, :k]
else:
    op = LinearOperator((N, N), matvec=lambda v: T(v[None])[0], dtype=complex)
    ev, V = eigs(op, k=k, which='LM', ncv=min(N, 2 * k + 1), tol=1e-8)
    o = np.argsort(-np.abs(ev)); ev, V = ev[o], V[:, o]
a = np.abs(ev); l1 = a[0]
rel = a / l1
above = math.sqrt(G0) * l1 > 1
# input overlap: fraction of each input pattern's energy in span(top-m modes)
P = R.patterns.reshape(R.patterns.shape[0], -1).cpu().numpy()
Q, _ = np.linalg.qr(V)
ov = {}
for m in (1, 10, 50, 100, 200, k):
    if m > V.shape[1]: continue
    c = Q[:, :m].conj().T @ P.T
    ov[m] = float(np.mean(np.sum(np.abs(c) ** 2, 0) / np.sum(np.abs(P) ** 2, 1)))
res = dict(name=name, n=n, modes=N, G0=G0, lambda1=float(l1), sqrtG0_lambda1=float(math.sqrt(G0) * l1), above_threshold=bool(above),
           loss_per_trip_best_mode=float(1 - l1 ** 2),
           n_rel_above={str(t): int((rel > t).sum()) for t in (0.99, 0.95, 0.9, 0.8, 0.7, 0.5, 0.3)},
           memory_trips_mode2=float(-1 / math.log(rel[1])) if rel[1] < 1 else None,
           input_overlap_topm=ov, k=int(len(a)), abs_eigs=[float(x) for x in a], secs=time.time() - t0)
os.makedirs(os.path.join(res_gpu.HERE, 'out', '48'), exist_ok=True)
json.dump(res, open(os.path.join(res_gpu.HERE, 'out', '48', f'{name}.json'), 'w'), indent=1)
print(json.dumps({kk: v for kk, v in res.items() if kk != 'abs_eigs'}), flush=True)
