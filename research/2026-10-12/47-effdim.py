"""Experiment 47b (2026-10-12): how many independent dimensions does the optical state actually use, as the mode count grows?

Eigen-spectrum of the feature covariance (features centred, one global scale) over the steps after washout, for the Exp. 43
rings (one input channel, uniform stream) and for tuned digital ESNs on the same input. Reported: participation ratio
(Σλ)²/Σλ², and the number of eigenvalues above 10⁻³, 10⁻⁵, 10⁻⁷ of the largest (10⁻⁵ ≈ what survives shot noise at
~10⁸–10¹⁰ detected photons per step). If the state were as rich as the mode count, these would grow ∝ modes.
usage: python 47-effdim.py <tag> [tag …]   (out/43 tags; 'esnN' computes an ESN of N units) → out/47/effdim.json
"""
import json, os, sys
import numpy as np
import torch
import res_lib as RL

D = os.path.join(RL.OUT, '47'); os.makedirs(D, exist_ok=True)
p = os.path.join(D, 'effdim.json')
res = json.load(open(p)) if os.path.exists(p) else {}
for tag in sys.argv[1:]:
    if tag.startswith('esn'):
        N = int(tag[3:])
        u, _ = RL.L30.streams(16000)
        F = RL.esn_features(N, 0.9, 0.1, 1.0, 'tanh', u).double()
        meta = dict(N=N)
    else:
        F, meta = RL.load(tag, 'uniform'); F = F.to(RL.DEV, torch.float64)
    X = F[RL.WASH:]
    X = (X - X.mean(0)) / X.abs().mean()
    C = (X.T @ X) if X.shape[1] <= X.shape[0] else (X @ X.T)
    ev = torch.linalg.eigvalsh(C).flip(0).clamp_min(0).cpu().numpy()
    ev = ev / ev[0]
    r = dict(features=int(F.shape[1]), modes=meta.get('modes'), N=meta.get('N'), participation_ratio=float(ev.sum() ** 2 / (ev ** 2).sum()),
             n_above_1e3=int((ev > 1e-3).sum()), n_above_1e5=int((ev > 1e-5).sum()), n_above_1e7=int((ev > 1e-7).sum()),
             spectrum_head=[float(x) for x in ev[:64]])
    res[tag] = r
    json.dump(res, open(p, 'w'), indent=1)
    print(tag, {k: v for k, v in r.items() if k != 'spectrum_head'}, flush=True)
    del F, X, C; torch.cuda.empty_cache()
