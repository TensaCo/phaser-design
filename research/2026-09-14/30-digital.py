"""Experiment 30b: fairly tuned digital baselines on the Exp. 30 task bundles (3200 steps, same streams and splits):
  - single ESNs, N = 8 … 1024 (grid of ρ, input scale, leak, tanh/linear; ≤ 256 full grid);
  - two-reservoir ESNs (a linear ESN for memory + a tanh ESN for nonlinearity, features concatenated): cost N1² + N2²;
  - NG-RC / delay line + quadratic monomials (Gauthier et al. 2021): L linear taps, all products of the first q taps.
Hyper-parameters are picked on the TEST split (favours the digital side). Output out/30/digital.json with MACs per step.
usage: python 30-digital.py"""
import importlib.util, itertools, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('L', os.path.join(HERE, '30-lib.py')); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
STEPS = 3200
u, bb = L.streams(STEPS)
rows = []
def add(kind, macs, feats_u, feats_b, **kw):
    r = L.score(feats_u, feats_b, u, bb, which=('raw',)); r.pop('mc_curve'); r.update(kind=kind, macs_per_step=macs, n_features=feats_u.shape[1], **kw)
    rows.append(r); print(json.dumps(r), flush=True)
    json.dump(rows, open(os.path.join(L.OUT, '30', 'digital.json'), 'w'), indent=1)

cache = {}
def H(N, g, s):
    k = (N, g, s)
    if k not in cache: cache[k] = L.esn_features(N, *g, u if s == 'u' else bb * 0.5)
    return cache[k]

for N in (8, 16, 32, 64, 128, 256, 512, 1024):
    grid = L.ESN_GRID if N <= 256 else [g for g in L.ESN_GRID if g[3] == 'tanh' and g[1] in (0.1, 0.5)] + [(0.99, 0.5, 1.0, 'linear')]
    for g in grid:
        add('esn', N * N + N, H(N, g, 'u'), H(N, g, 'b'), N=N, rho=g[0], ins=g[1], leak=g[2], act=g[3])
    if N > 128: cache.clear()
cache.clear()
# two reservoirs: linear (memory) + tanh (nonlinear), small sizes
for N1, N2 in itertools.product((32, 64, 128), (32, 64, 128, 256)):
    for gl, gt in itertools.product([(0.99, 0.5, 1.0, 'linear'), (0.9, 0.5, 1.0, 'linear')], [(0.99, 0.1, 1.0, 'tanh'), (0.9, 0.1, 1.0, 'tanh'), (0.9, 0.5, 1.0, 'tanh')]):
        Fu = np.hstack([H(N1, gl, 'u'), H(N2, gt, 'u')]); Fb = np.hstack([H(N1, gl, 'b'), H(N2, gt, 'b')])
        add('esn2', N1 * N1 + N2 * N2 + N1 + N2, Fu, Fb, N1=N1, N2=N2, lin=gl, tanh=gt)
# NG-RC: delay taps + quadratic monomials of the first q taps (plus the readout)
def ngrc(s, Ld, q):
    x = 4 * (s - 0.25)
    lin = np.stack([L.shifted(x, k) for k in range(Ld)], 1)
    quad = np.stack([lin[:, i] * lin[:, j] for i in range(q) for j in range(i, q)], 1) if q else np.zeros((len(s), 0))
    return np.hstack([lin, quad])
for Ld, q in itertools.product((10, 20, 40, 60), (0, 4, 8, 12, 16)):
    if q > Ld: continue
    Fu, Fb = ngrc(u, Ld, q), ngrc(bb * 0.5, Ld, q)
    add('ngrc', q * (q + 1) // 2 + Fu.shape[1], Fu, Fb, L=Ld, q=q)
json.dump(rows, open(os.path.join(L.OUT, '30', 'digital.json'), 'w'), indent=1)
