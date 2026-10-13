"""Experiment 44 (2026-10-12): an OPTICAL readout — can the detector electronics stop scaling with the modes?

Exp. 31: the equivalence (16–44 modes per ESN unit) holds only if detector bins grow with the modes (one channel per 16 modes),
and Exp. 34: detection electronics dominate the energy. Here the readout's linear combination is done optically: the tapped
light falls on an amplitude modulator (one pixel per mode) in front of a polarising beam splitter, so pixel p sends a fraction
T_p of its photons to detector + and 1 − T_p to detector −. The difference D+ − D− = Σ (2T_p − 1) n_p is the readout
y = Σ w_p I_p with w_p = s·(2T_p − 1) ∈ [−s, s]; the bias is added electronically. Every photon is detected, but each output's
shot noise is that of ALL the light (var = Σ λ_p), not Σ w_p² λ_p as with per-pixel detection. Two detectors per output,
whatever the number of modes. With M outputs the tap light is split M ways.

Weights are trained offline on noise-free full-resolution features (a slow calibration camera), on centred linear
intensity with one global scale (the ridge penalty acts on the physical weights; the offset goes into the bias), converted to
transmissions, quantised to q bits; λ is chosen per target on the validation split WITH the output noise; test split untouched.
Baseline: the Exp. 30/31 electronic readout (one detector per bin of 16 modes, Poisson + 2 e⁻ read noise per bin, all
transforms, ridge on noisy features).

usage: python 44-optread.py <tag of a 43-scale.py run with bin 1> → out/44/{tag}.json
"""
import json, math, os, sys, time
import numpy as np
import torch
import res_lib as RL

L30 = RL.L30
DEV = RL.DEV
tag = sys.argv[1]
D_GRID = [1e6, 1e7, 1e8, 1e9, 1e10, 1e11, 1e12, None]
QBITS = [None, 8, 6, 4]
os.makedirs(os.path.join(RL.OUT, '44'), exist_ok=True)

Fu, m = RL.load(tag, 'uniform')
Fb, _ = RL.load(tag, 'bits')
steps = m['steps']
u, bb = L30.streams(steps)
names = ['narma10', 'narma20'] + [f'mc{k}' for k in range(1, 61)]
Yu = np.hstack([L30.narma(u, 10)[:, None], L30.narma(u, 20)[:, None], np.stack([L30.shifted(u, k) for k in range(1, 61)], 1)])
Yb = L30.targets_bits(bb)[:, :1]
a, b = L30.splits(steps); cut = a + int((b - a) * 0.8)


def summarise(p, y, bits=False):
    """metrics from test predictions: NARMA10/20 NMSE, MC(1..60) = Σ r², or XOR accuracy"""
    if bits:
        return dict(xor_d2=float(np.mean((p[:, 0] > 0.5) == (y[:, 0] > 0.5))))
    nm = lambda k: float(np.mean((p[:, k] - y[:, k]) ** 2) / np.var(y[:, k]))
    r2 = [float(np.corrcoef(p[:, k], y[:, k])[0, 1] ** 2) if np.std(p[:, k]) > 0 else 0.0 for k in range(2, 62)]
    return dict(narma10_nmse=nm(0), narma20_nmse=nm(1), mc_1_60=float(np.nansum(r2)))


def optical(F, Y, Dlist, qlist, M_out=1, seed=0, bits=False):
    """optical-readout predictions for every (D, q): weights from ridge on standardised linear features (full resolution)"""
    F = F.to(DEV, torch.float64)
    Y = torch.as_tensor(Y, dtype=torch.float64, device=DEV)
    # ONE global scale, not per-pixel standardisation: the ridge penalty then acts on the physical weights (per-pixel
    # scaling hands near-dark pixels enormous weights, which set the mask's full scale and swamp quantisation and noise)
    mu, sd = F[a:b].mean(0), F[a:b].mean()
    Z = torch.cat([(F - mu) / sd, torch.ones(steps, 1, dtype=torch.float64, device=DEV)], 1)
    Str, Sfull = RL._Solver(Z[a:cut], Y[a:cut]), RL._Solver(Z[a:b], Y[a:b])
    tot = F.sum(1)  # Σ_p I_p per step (field units): the photons every output's detectors see
    meanTot = float(tot[a:].mean())
    g = torch.Generator(device=DEV).manual_seed(seed)
    noise_std = torch.randn(steps, Y.shape[1], generator=g, device=DEV, dtype=torch.float64)
    out = {}
    for D in Dlist:
        for q in qlist:
            best = torch.full((Y.shape[1],), float('inf'), dtype=torch.float64, device=DEV)
            pred = torch.zeros(steps - b, Y.shape[1], dtype=torch.float64, device=DEV)
            info = {}
            for lam in RL.LAMS:
                errs, preds = [], []
                for S, rows_fit, rows_eval in ((Str, slice(a, cut), slice(cut, b)), (Sfull, slice(a, b), slice(b, steps))):
                    W = S.W(lam)                       # (F+1, T) on standardised features
                    w = W[:-1] / sd                    # raw-intensity weights
                    s = w.abs().amax(0).clamp_min(1e-300)  # per-output scale: |w| ≤ s ⇔ T ∈ [0, 1]
                    T = 0.5 * (1 + w / s)
                    if q is not None:
                        T = torch.round(T * (2 ** q - 1)) / (2 ** q - 1)
                    wq = s * (2 * T - 1)
                    y_fit = F[rows_fit] @ wq
                    c = (Y[rows_fit] - y_fit).mean(0)  # electronic bias, fitted on the training rows
                    y = F[rows_eval] @ wq + c
                    if D is not None:
                        kappa = D / meanTot / M_out    # photons per field unit for each output
                        y = y + s * torch.sqrt(tot[rows_eval] / kappa)[:, None] * noise_std[rows_eval]
                    preds.append(y)
                err = ((preds[0] - Y[cut:b]) ** 2).mean(0)
                better = err < best
                pred[:, better] = preds[1][:, better]
                best = torch.where(better, err, best)
            out[(D, q)] = summarise(pred.cpu().numpy(), Y[b:].cpu().numpy(), bits)
    return out


def electronic(F, Y, Dlist, bin_=4, bits=False, seed=0):
    """Exp. 30/31 readout: detector bins of bin_×bin_ modes, shot + read noise on the features, all transforms"""
    Fb_ = RL.binf(F, bin_).numpy().astype(np.float64)
    rng = np.random.default_rng(seed)
    out = {}
    for D in Dlist:
        Fn = L30.shot(Fb_, D, rng) if D is not None else Fb_
        p, y = RL.ridge_select(torch.from_numpy(Fn), Y)
        out[D] = summarise(p, y, bits)
    return out


t0 = time.time()
res = dict(tag=tag, n=m['n'], K=m['K'], modes=m['modes'], steps=steps, rows=[])
LAMS_OPT = tuple(10.0 ** e for e in range(-6, 9))
RL.LAMS = LAMS_OPT  # wider λ range: noise-aware selection needs strong regularisation at low photon counts
for M_out in (1, 64):
    o_u = optical(Fu, Yu, D_GRID, QBITS, M_out)
    o_b = optical(Fb, Yb, D_GRID, QBITS, M_out, bits=True)
    for (D, q), r in o_u.items():
        res['rows'].append(dict(readout='optical', M_out=M_out, detectors=2 * M_out, D=D, qbits=q, **r, **o_b[(D, q)]))
    print(f'optical M_out={M_out} done {time.time() - t0:.0f}s', flush=True)
for bin_ in (4, 16):
    e_u = electronic(Fu, Yu, D_GRID, bin_)
    e_b = electronic(Fb, Yb, D_GRID, bin_, bits=True)
    for D, r in e_u.items():
        res['rows'].append(dict(readout='electronic', bin=bin_, detectors=(m['n'] // bin_) ** 2, D=D, **r, **e_b[D]))
    print(f'electronic bin {bin_} done {time.time() - t0:.0f}s', flush=True)
json.dump(res, open(os.path.join(RL.OUT, '44', f'{tag}.json'), 'w'), indent=1)
for r in res['rows']:
    print({k: (f'{v:.4g}' if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
