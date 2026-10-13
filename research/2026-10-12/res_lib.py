"""Exps. 43–45 (2026-10-12): GPU readout and scoring for reservoir features, same protocol as 2026-09-14/30-lib.py
(ridge on standardised features, transform and λ chosen per target on a validation split, test split untouched; same
targets and metrics), but in torch so 16k–65k features are practical. Primal (F×F) or dual (n×n) eigendecomposition,
whichever is smaller; every λ then costs one matrix product.

Also the OPTICAL readout of Exp. 44: one amplitude mask per output in front of a pair of bucket detectors (positive and
negative weights), so the electronics no longer scale with the modes."""
import importlib.util, json, math, os
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location('L30', os.path.join(HERE, '..', '2026-09-14', '30-lib.py'))
L30 = importlib.util.module_from_spec(_s); _s.loader.exec_module(L30)
OUT = os.path.join(HERE, 'out')
DEV = 'cuda' if torch.cuda.is_available() else 'cpu'
WASH = L30.WASH
LAMS = L30.LAMS


def transforms_t(F, which=('log1', 'lin', 'sqrt', 'log0.01', 'log0.1', 'log1n')):
    """torch version of 30-lib transforms (yields one at a time to bound memory)"""
    m = F[WASH:].mean()
    for t in which:
        if t == 'raw': yield t, F
        elif t == 'log1': yield t, torch.log10(F + 1)
        elif t == 'lin': yield t, F / m
        elif t == 'sqrt': yield t, torch.sqrt(torch.clamp(F, min=0) / m)
        elif t.startswith('log') and t.endswith('n'): yield t, torch.log10(F / m + float(t[3:-1]))
        elif t.startswith('log'): yield t, torch.log10(F / m + float(t[3:]))


def _eigh(A):
    """symmetric eigendecomposition; a tiny diagonal shift (1e-12 of the mean eigenvalue) and a CPU fallback for the GPU
    solver's convergence failures on rank-deficient Gram matrices (constant feature columns)"""
    A = A + (1e-12 * A.diagonal().mean()) * torch.eye(A.shape[0], dtype=A.dtype, device=A.device)
    try:
        return torch.linalg.eigh(A)
    except torch._C._LinAlgError:
        e, V = torch.linalg.eigh(A.cpu())
        return e.to(A.device), V.to(A.device)


class _Solver:
    """ridge solutions for many λ from one eigendecomposition (primal or dual)"""
    def __init__(self, Z, Y):
        n, F = Z.shape
        self.dual = F > n
        if self.dual:
            e, U = _eigh(Z @ Z.T)
            self.e, self.U, self.Z = e.clamp_min(0), U, Z
            self.UtY = U.T @ Y
        else:
            e, V = _eigh(Z.T @ Z)
            self.e, self.V = e.clamp_min(0), V
            self.VtZtY = V.T @ (Z.T @ Y)

    def W(self, lam, cols=None):
        if self.dual:
            A = self.UtY if cols is None else self.UtY[:, cols]
            return self.Z.T @ (self.U @ (A / (self.e + lam)[:, None]))
        A = self.VtZtY if cols is None else self.VtZtY[:, cols]
        return self.V @ (A / (self.e + lam)[:, None])


def ridge_select(F, Y, which=None, lams=LAMS, dtype=torch.float64):
    """F: (steps, feats) torch (any device); Y: (steps, T). Returns test predictions and test targets (numpy)."""
    steps = F.shape[0]
    a, b = L30.splits(steps); cut = a + int((b - a) * 0.8)
    Y = torch.as_tensor(Y, dtype=dtype, device=DEV)
    best = torch.full((Y.shape[1],), float('inf'), dtype=dtype, device=DEV)
    pred = torch.zeros(steps - b, Y.shape[1], dtype=dtype, device=DEV)
    kw = {} if which is None else dict(which=which)
    for name, X in transforms_t(F.to(DEV, dtype), **kw):
        mu, sd = X[a:b].mean(0), X[a:b].std(0) + 1e-12
        Z = torch.cat([(X - mu) / sd, torch.ones(steps, 1, dtype=dtype, device=DEV)], 1)
        del X
        Str, Sfull = _Solver(Z[a:cut], Y[a:cut]), _Solver(Z[a:b], Y[a:b])
        for lam in lams:
            err = ((Z[cut:b] @ Str.W(lam) - Y[cut:b]) ** 2).mean(0)
            better = err < best
            if better.any():
                cols = better.nonzero().flatten()
                pred[:, cols] = Z[b:] @ Sfull.W(lam, cols)
                best = torch.where(better, err, best)
        del Z, Str, Sfull
        torch.cuda.empty_cache()
    return pred.cpu().numpy(), Y[b:].cpu().numpy()


def capacity_score(Fu, Fb, u, bb, which=None, thr=0.01, lin_max=300, quad_max=20):
    """30-lib.capacity_score with the GPU ridge"""
    Yl, Yq = L30.capacity_targets(u, lin_max, quad_max)
    Y = np.hstack([Yl, Yq, L30.narma(u, 10)[:, None], L30.narma(u, 20)[:, None]])
    p, y = ridge_select(Fu, Y, which)
    ok = np.std(p, 0) > 0
    r2 = np.nan_to_num(np.array([np.corrcoef(p[:, k], y[:, k])[0, 1] ** 2 if ok[k] else 0 for k in range(Y.shape[1])]))
    nl, nq = Yl.shape[1], Yq.shape[1]
    cap = lambda a: float(np.sum(a[a > thr]))
    nm = lambda k: float(np.mean((p[:, k] - y[:, k]) ** 2) / np.var(y[:, k]))
    res = dict(cap_linear=cap(r2[:nl]), cap_quadratic=cap(r2[nl:nl + nq]), narma10_nmse=nm(nl + nq), narma20_nmse=nm(nl + nq + 1),
               mc_1_60=float(np.sum(r2[1:61])))
    res['cap_total'] = res['cap_linear'] + res['cap_quadratic']
    if Fb is not None:
        pb, yb = ridge_select(Fb, L30.targets_bits(bb)[:, :1], which)
        res['xor_d2'] = float(np.mean((pb[:, 0] > 0.5) == (yb[:, 0] > 0.5)))
    return res


def binf(F, b):
    """sum b×b blocks of a square B×B feature image (torch or numpy, steps × B²)"""
    if b == 1: return F
    S = F.shape[0]; B = int(round(math.sqrt(F.shape[1])))
    return F.reshape(S, B // b, b, B // b, b).sum((2, 4)).reshape(S, -1)


def load(tag, stream, d='43'):
    meta = json.load(open(os.path.join(OUT, d, f'{tag}_{stream}.json')))
    F = np.fromfile(os.path.join(OUT, d, f'{tag}_{stream}.f32'), dtype=np.float32).reshape(meta['steps'], -1)
    return torch.from_numpy(F), meta


# ── digital ESN on the GPU (30-lib.esn_features, same recipe; the spectral radius is normalised by power iteration) ──
@torch.no_grad()
def esn_features(N, rho, ins, leak, act, s, seed=0):
    g = torch.Generator(device='cpu').manual_seed(seed)
    W = (torch.randn(N, N, generator=g, dtype=torch.float64) / math.sqrt(N)).to(DEV)
    if N <= 4096:
        ev = torch.linalg.eigvals(W).abs().max().real
    else:  # circular law: spectral radius → 1 (30-lib uses 1.0 above 2048 as well)
        ev = torch.tensor(1.0, dtype=torch.float64, device=DEV)
    W = (W * rho / ev).float()
    Win = torch.randn(N, generator=g).float().to(DEV); bias = (0.2 * torch.randn(N, generator=g)).float().to(DEV)
    s = torch.as_tensor(s, dtype=torch.float32, device=DEV)
    h = torch.zeros(N, device=DEV); H = torch.empty(len(s), N, device=DEV)
    for t in range(len(s)):
        z = W @ h + Win * ((s[t] - 0.25) * 4 * ins) + (bias if act == 'tanh' else 0)
        h = (1 - leak) * h + leak * (torch.tanh(z) if act == 'tanh' else z); H[t] = h
    return H
