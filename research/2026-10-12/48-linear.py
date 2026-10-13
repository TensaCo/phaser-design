"""Experiment 48b (2026-10-12): the reservoir ring run as a LINEAR feedback system — below lasing threshold, gain constant
(no saturation: a slow gain medium or a pump servo holding the operating point), with a constant coherent carrier injected
next to the signal — on the Exp. 45 KS task.

Exp. 48a: the Apre_lin ring sits just above threshold (√G0·|λ_1| = 1.037) with ~100 modes within 1 % of the lasing mode, so
the fast global gain clamps the effective spectral radius to 1: memory far longer than the task wants. Here the per-trip
amplitude factor is ρ_trip = √G0·|λ_1| < 1, set by G0 (ρ_step = ρ_trip^K), and the gain no longer depends on the light.
Detection |E|² of a linear field gives quadratic forms of the input history; a constant carrier c·P_c (a fixed reference
field, here a fixed random-sign sum of the input patterns) adds the linear terms 2c·Re(P_c* s) — homodyne detection.
Shot noise (env DGRID, e.g. "1e8,1e10,1e12"): Poisson + 2 e⁻ read noise per detector bin at D detected photons per step in
total over all bins — the carrier's photons count, so a strong carrier buys linear terms at the price of its shot noise.
DREF=signal instead fixes the SIGNAL photons (D = detected photons per step of the carrier-0 run, which must be first in the
list) and adds the carrier's light on top at the same photon scale: the homodyne accounting, where the reference is extra laser
power whose own shot noise is included.
usage: python 48-linear.py <n> <bin> <K> <G0> <carrier/signal> [carrier …]   (RES_SUFFIX for the export variant)
→ out/45/results.json (kind 'optical-linear')
"""
import importlib.util, json, math, os, sys, time
import numpy as np
import torch
from res_gpu import Reservoir

_s = importlib.util.spec_from_file_location('KS45', os.path.join(os.path.dirname(os.path.abspath(__file__)), '45-ks.py'))
sys_argv, sys.argv = sys.argv, ['45-ks.py', 'none']  # load 45-ks.py's data and score() without running a mode
KS = importlib.util.module_from_spec(_s); _s.loader.exec_module(KS)
sys.argv = sys_argv

n, bin_, K, G0 = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
carriers = [float(v) for v in sys.argv[5:]]
SUF = os.environ.get('RES_SUFFIX', '')
R = Reservoir(n, d_in=KS.Q, suffix=SUF)
P = R.patterns[:KS.Q]
g = torch.Generator().manual_seed(7)
sgn = (torch.randint(0, 2, (KS.Q,), generator=g) * 2 - 1).to(R.dev, R.cdt)
Pc = torch.einsum('d,dxy->xy', sgn, P) / math.sqrt(KS.Q)  # fixed reference field with the same overall scale as the signal
U = torch.as_tensor(KS.X / math.sqrt(KS.Q), dtype=R.cdt, device=R.dev)
B, S, nb = len(carriers), KS.STEPS, n // bin_
c = torch.as_tensor(carriers, dtype=R.cdt, device=R.dev).reshape(-1, 1, 1)
E = torch.zeros(B, n, n, dtype=R.cdt, device=R.dev)
F = np.empty((B, S, nb * nb), np.float32)
t = time.time()
with torch.no_grad():
    for s in range(S):
        inj = torch.einsum('d,dxy->xy', U[s], P)[None] + c * Pc
        acc = None
        for k in range(K):
            E = R.trip(E, inj if k == 0 else None, G0, 1e300)  # Is → ∞: constant gain G0
            I = E.real ** 2 + E.imag ** 2
            acc = I if acc is None else acc + I
        if bin_ > 1:
            acc = acc.reshape(B, nb, bin_, nb, bin_).sum((2, 4))
        F[:, s] = acc.reshape(B, -1).float().cpu().numpy()
sim = time.time() - t
DG = [float(v) for v in os.environ['DGRID'].split(',')] if os.environ.get('DGRID') else [None]
rng = np.random.default_rng(0)
for i, cr in enumerate(carriers):
    for D in DG:
        if D is None:
            Fi = F[i]
        elif os.environ.get('DREF') == 'signal':
            assert carriers[0] == 0
            sc = D / F[0].astype(np.float64).sum(1).mean()  # photons per field unit, set by the signal-only run
            lam = np.maximum(F[i].astype(np.float64), 0) * sc
            Fi = ((lam + np.sqrt(lam) * rng.normal(size=lam.shape) + 2.0 * rng.normal(size=lam.shape)) / sc).astype(np.float32)
        else:
            Fi = KS.RL.L30.shot(F[i].astype(np.float64), D, rng).astype(np.float32)
        KS.score(Fi, None, f'optical-linear n={n}{SUF}', dict(kind='optical-linear', n=n, modes=n * n, bin=bin_, K=K, G0=G0,
                                                            carrier=cr, D=D, dref=os.environ.get('DREF', 'total'), sim_secs=sim, variant=SUF))
