"""Experiments 30–34 (2026-09-25): shared Python helpers for the post-hoc readout of 30-run.ts features.
Loaded with importlib like 29-*.py do with 15-readout.py (file names start with a digit).

- features: noise-free |E|² summed over the K trips of each step (field units), float32, steps × B²
- shot noise: Poisson at a stated number D of detected photoelectrons per input step (summed over all bins), plus 2 e⁻ read
  noise per bin (Exp. 29 detector); applied post hoc (Exp. 29d: reproduces the in-loop noise; ASE negligible)
- readout: ridge on standardised features; the feature transform (Exp. 29 fixed log10(x+1), or lin / sqrt / log(x/x̄ + c))
  and λ are chosen PER TASK on a validation split (last 20 % of the training range); the test split is never used for choices
- digital baseline: ESN with hyper-parameters chosen on the TEST split (Exp. 29 convention; favours the digital side)
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
WASH = 200
LAMS = (1e-6, 1e-4, 1e-2, 1, 1e2, 1e4)
H_NU = 6.62607015e-34 * 2.99792458e8 / 650e-9


def load(tag, stream, slot=0, d='30', xterm=False):
    meta = json.load(open(os.path.join(OUT, d, f'{tag}_{stream}.json')))
    F = np.fromfile(os.path.join(OUT, d, f'{tag}_{stream}_{"x" if xterm else "s"}{slot}.f32'), dtype=np.float32).astype(np.float64)
    return F.reshape(meta['steps'], -1), meta


def binf(F, b):
    """sum b×b blocks of a square B×B feature image (b = 1: unchanged)"""
    if b == 1: return F
    S = F.shape[0]; B = int(round(np.sqrt(F.shape[1])))
    return F.reshape(S, B // b, b, B // b, b).sum((2, 4)).reshape(S, -1)


def shot(F, D, rng, read_noise=2.0):
    """Poisson noise at D detected photoelectrons per step on average; returned in field units"""
    if D is None or not np.isfinite(D): return F
    s = D / F.sum(1).mean()
    lam = np.maximum(F, 0) * s
    N = np.where(lam < 1e7, rng.poisson(np.minimum(lam, 1e7)), lam + np.sqrt(lam) * rng.normal(size=F.shape)) + read_noise * rng.normal(size=F.shape)
    return np.maximum(N, 0) / s


def splits(steps):
    tr_end = int(round(steps * 0.6875))  # 3200 → 2200 (Exp. 15/29)
    return WASH, tr_end


def transforms(F, which=('log1', 'lin', 'sqrt', 'log0.01', 'log0.1', 'log1n')):
    m = F[WASH:].mean()
    out = {}
    for t in which:
        if t == 'raw': out[t] = F
        elif t == 'log1': out[t] = np.log10(F + 1)  # Exp. 29 fixed transform (field units)
        elif t == 'lin': out[t] = F / m
        elif t == 'sqrt': out[t] = np.sqrt(np.maximum(F, 0) / m)
        elif t.startswith('log') and t.endswith('n'): out[t] = np.log10(F / m + float(t[3:-1]))
        elif t.startswith('log'): out[t] = np.log10(F / m + float(t[3:]))
    return out


def ridge_select(Xs, Y, steps, lams=LAMS):
    """Xs: {transform: features}; Y: steps × T targets. For each target choose (transform, λ) on validation; return
    test predictions (n_test × T) and test targets."""
    a, b = splits(steps); cut = a + int((b - a) * 0.8)
    best_err = np.full(Y.shape[1], np.inf); pred = np.zeros((steps - b, Y.shape[1]))
    for X in Xs.values():
        mu, sd = X[a:b].mean(0), X[a:b].std(0) + 1e-12
        Z = np.hstack([(X - mu) / sd, np.ones((len(X), 1))])
        Ztr, Zva, Zfull, Zte = Z[a:cut], Z[cut:b], Z[a:b], Z[b:]
        A = Ztr.T @ Ztr; Af = Zfull.T @ Zfull; I = np.eye(A.shape[0])
        for lam in lams:
            W = np.linalg.solve(A + lam * I, Ztr.T @ Y[a:cut])
            err = ((Zva @ W - Y[cut:b]) ** 2).mean(0)
            better = err < best_err
            if better.any():
                Wf = np.linalg.solve(Af + lam * I, Zfull.T @ Y[a:b][:, better])
                pred[:, better] = Zte @ Wf; best_err[better] = err[better]
    return pred, Y[b:]


def narma(u, n=10):
    """NARMA-n; n ≥ 20 uses the standard tanh-bounded form (otherwise it diverges for u ∈ [0, 0.5])"""
    y = np.zeros_like(u)
    for t in range(n - 1, len(u) - 1):
        if n >= 20: y[t + 1] = np.tanh(0.3 * y[t] + 0.05 * y[t] * y[t - n + 1:t + 1].sum() + 1.5 * u[t - n + 1] * u[t] + 0.01)
        else: y[t + 1] = 0.3 * y[t] + 0.05 * y[t] * y[t - n + 1:t + 1].sum() + 1.5 * u[t - n + 1] * u[t] + 0.1
    return y


def shifted(x, k):
    y = np.roll(x, k); y[:k] = 0; return y


def targets_uniform(u, mc_max=60):
    """MC delays 1..mc_max, NARMA10, NARMA5 (short-memory)"""
    cols = [shifted(u, k) for k in range(1, mc_max + 1)] + [narma(u, 10), narma(u, 5)]
    return np.stack(cols, 1)


def targets_bits(bb):
    """bb ∈ {0,1}: XOR at d = 2 (Exp. 29) and d = 0 (short), parity-3 d = 0"""
    x2 = np.logical_xor(shifted(bb, 2), shifted(bb, 3)).astype(float); x2[:4] = 0
    x0 = np.logical_xor(bb, shifted(bb, 1)).astype(float); x0[:2] = 0
    p3 = ((bb + shifted(bb, 1) + shifted(bb, 2)) % 2).astype(float); p3[:3] = 0
    return np.stack([x2, x0, p3], 1)


def score(Fu, Fb, u, bb, mc_max=60, which=None):
    """metrics for one reservoir (features in field units). u: uniform stream (as injected, [0, 0.5]); bb: bits {0,1}"""
    steps = len(u)
    kw = {} if which is None else dict(which=which)
    res = {}
    if Fu is not None:
        Y = targets_uniform(u, mc_max)
        p, y = ridge_select(transforms(Fu, **kw), Y, steps)
        r2 = [float(np.corrcoef(p[:, k], y[:, k])[0, 1] ** 2) if np.std(p[:, k]) > 0 else 0.0 for k in range(mc_max)]
        nm = lambda k: float(np.mean((p[:, k] - y[:, k]) ** 2) / np.var(y[:, k]))
        res.update(memory_capacity=float(sum(r2)), mc5=float(sum(r2[:5])), narma10_nmse=nm(mc_max), narma5_nmse=nm(mc_max + 1), mc_curve=r2)
    if Fb is not None:
        Y = targets_bits(bb)
        p, y = ridge_select(transforms(Fb, **kw), Y, steps)
        acc = lambda k: float(np.mean((p[:, k] > 0.5) == (y[:, k] > 0.5)))
        res.update(xor_d2=acc(0), xor_d0=acc(1), parity3_d0=acc(2))
    return res


def streams(steps, slot=0):
    """same generator as 30-run.ts (mulberry32(2024 + slot)); slot 0 = Exp. 15 inputs for the first 3200 steps"""
    def mulberry32(a):
        a &= 0xFFFFFFFF
        def r():
            nonlocal a
            a = (a + 0x6D2B79F5) & 0xFFFFFFFF
            t = a
            t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
            t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
            return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
        return r
    r = mulberry32(2024 + slot); u = np.empty(steps); b = np.empty(steps)
    for s in range(steps): u[s] = 0.5 * r(); b[s] = 0.0 if r() < 0.5 else 1.0
    return u, b


# bundle targets: the Exp. 29 operating point (N_c = 1e10 on Apre_lin K = 10) — the quality every energy number refers to
BUNDLE29 = dict(narma10_nmse=0.127, memory_capacity=33.7, xor_d2=0.989)
SHORT = dict(narma5_nmse=None, mc5=None, xor_d0=None)  # filled per run from the target system


def meets(r, tgt):
    ok = True
    for k, v in tgt.items():
        if k.endswith('nmse'): ok &= r[k] <= v
        else: ok &= r[k] >= v
    return bool(ok)


def d_required(Fu, Fb, u, bb, tgt, grid=None, seed=0, **kw):
    """smallest detected photons per step (from a half-decade grid) meeting the target bundle; also the sweep"""
    grid = grid or [10 ** e for e in np.arange(5, 13.01, 0.5)]
    rng = np.random.default_rng(seed); sweep = []
    for D in grid:
        r = score(shot(Fu, D, rng) if Fu is not None else None, shot(Fb, D, rng) if Fb is not None else None, u, bb, **kw)
        r.pop('mc_curve', None); r['D'] = D; sweep.append(r)
        if meets(r, tgt): return D, sweep
    return None, sweep


# ── digital ESN (Exp. 29b generalised) ───────────────────────────────────────────────────────────
def esn_features(N, rho, ins, leak, act, s, seed=0):
    rng = np.random.default_rng(seed)
    W = rng.normal(size=(N, N)) / np.sqrt(N)
    ev = np.max(np.abs(np.linalg.eigvals(W))) if N <= 2048 else 1.0  # circular law: spectral radius → 1 for large N
    W = (W * rho / ev).astype(np.float32)
    Win = rng.normal(size=N).astype(np.float32); bias = (0.2 * rng.normal(size=N)).astype(np.float32)
    h = np.zeros(N, np.float32); H = np.empty((len(s), N), np.float32)
    for t, x in enumerate(s):
        z = W @ h + Win * np.float32((x - 0.25) * 4 * ins) + (bias if act == 'tanh' else 0)
        h = (1 - leak) * h + leak * (np.tanh(z) if act == 'tanh' else z); H[t] = h
    return H.astype(np.float64)


ESN_GRID = [(rho, ins, leak, act) for rho in (0.9, 0.99) for ins in (0.1, 0.5, 1.0) for leak in (1.0, 0.3) for act in ('tanh', 'linear')]


def esn_score(N, u, bb, grid=ESN_GRID, mc_max=60, seed=0):
    """every grid point scored (on test); caller picks the best per metric (test-split selection favours digital)"""
    rows = []
    for rho, ins, leak, act in grid:
        Hu, Hb = esn_features(N, rho, ins, leak, act, u, seed), esn_features(N, rho, ins, leak, act, bb * 0.5, seed)
        r = score(Hu, Hb, u, bb, mc_max=mc_max, which=('raw',)); r.pop('mc_curve', None)
        r.update(N=N, rho=rho, ins=ins, leak=leak, act=act); rows.append(r)
    return rows


# ── capacity metrics for the scaling test (Exp. 31): tasks that do not saturate at a few hundred units ───────────────
def capacity_targets(u, lin_max=300, quad_max=20):
    """Legendre targets on the centred input ũ = 4(u − 0.25) ∈ [−1, 1] (Dambre et al. 2012 information processing capacity):
    linear ũ(t−k), k = 0..lin_max−1; quadratic P2(ũ(t−k)) and ũ(t−i)ũ(t−j), 0 ≤ i < j < quad_max."""
    x = 4 * (u - 0.25)
    lin = [shifted(x, k) for k in range(lin_max)]
    quad = [shifted(1.5 * x ** 2 - 0.5, k) for k in range(quad_max)]
    quad += [shifted(x, i) * shifted(x, j) for i in range(quad_max) for j in range(i + 1, quad_max)]
    return np.stack(lin, 1), np.stack(quad, 1)


def capacity_score(Fu, Fb, u, bb, which=None, thr=0.01, lin_max=300, quad_max=20):
    """linear and quadratic capacity (Σ test r² above thr), NARMA10/20 NMSE, XOR d2 accuracy"""
    steps = len(u); kw = {} if which is None else dict(which=which)
    Yl, Yq = capacity_targets(u, lin_max, quad_max)
    Y = np.hstack([Yl, Yq, narma(u, 10)[:, None], narma(u, 20)[:, None]])
    Xs = transforms(Fu, **kw)
    p, y = ridge_select(Xs, Y, steps)
    ok = np.std(p, 0) > 0
    r2 = np.where(ok, [np.corrcoef(p[:, k], y[:, k])[0, 1] ** 2 if ok[k] else 0 for k in range(Y.shape[1])], 0)
    r2 = np.nan_to_num(r2)
    nl, nq = Yl.shape[1], Yq.shape[1]
    cap = lambda a: float(np.sum(a[a > thr]))
    nm = lambda k: float(np.mean((p[:, k] - y[:, k]) ** 2) / np.var(y[:, k]))
    res = dict(cap_linear=cap(r2[:nl]), cap_quadratic=cap(r2[nl:nl + nq]), narma10_nmse=nm(nl + nq), narma20_nmse=nm(nl + nq + 1),
               mc_1_60=float(np.sum(r2[1:61])))
    res['cap_total'] = res['cap_linear'] + res['cap_quadratic']
    if Fb is not None:
        pb, yb = ridge_select(transforms(Fb, **kw), targets_bits(bb)[:, :1], steps)
        res['xor_d2'] = float(np.mean((pb[:, 0] > 0.5) == (yb[:, 0] > 0.5)))
    return res
