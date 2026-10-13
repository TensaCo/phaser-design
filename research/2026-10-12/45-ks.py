"""Experiment 45 (2026-10-12): a task that keeps rewarding scale — open-loop forecasting of a high-dimensional chaotic field
(Kuramoto–Sivashinsky, Q channels). The capacity/NARMA tasks of Exp. 31 saturate at a few thousand ESN units, so they cannot
measure an equivalence at 10⁵–10⁶ modes. Here: Q-channel input x(t) (KS state, standardised), targets x(t + h) for
h = 1, 4, 16 samples (0.25, 1, 4 time units); metric NMSE per horizon (mean over channels of MSE / variance) on the test split.
Both readouts also see the current input x(t) (standard practice; a linear-in-x(t) floor is reported too).

optical: python 45-ks.py opt <n> <bin> <K> <amp> [amp …]   (the res_n{n} export needs Q patterns: res-dump.ts n Q)
digital: python 45-ks.py esn|esn2 <N> [N …];  python 45-ks.py ngrc <k> [k …]
floor:   python 45-ks.py lin
→ out/45/results.json
"""
import json, math, os, sys, time
import numpy as np
import torch
import res_lib as RL

D = os.path.join(RL.OUT, '45')
LKS, Q = 60, 64
H = (1, 4, 16)
STEPS = 32000
X = np.fromfile(os.path.join(D, f'ks_L{LKS}_Q{Q}.f64')).reshape(-1, Q)[:STEPS]
X = (X - X.mean(0)) / X.std(0)
Y = np.hstack([np.vstack([X[h:], np.zeros((h, Q))]) for h in H])  # x(t + h); the last h rows are never in the test split's scored range
a, b = RL.L30.splits(STEPS)
DEV = RL.DEV


def score(F, which, label, extra):
    """ridge (30-lib protocol) on [features, x(t)]; NMSE per horizon over the test split (excluding the last 16 rows)"""
    F = torch.as_tensor(F)
    Fx = torch.cat([F.to(torch.float64), torch.as_tensor(X, dtype=torch.float64)], 1) if F.shape[1] else torch.as_tensor(X)
    t = time.time()
    p, y = RL.ridge_select(Fx, Y, which)
    p, y = p[:-max(H)], y[:-max(H)]
    r = {f'nmse_h{h}': float(np.mean(((p[:, i * Q:(i + 1) * Q] - y[:, i * Q:(i + 1) * Q]) ** 2).mean(0) / y[:, i * Q:(i + 1) * Q].var(0)))
         for i, h in enumerate(H)}
    r.update(label=label, features=int(F.shape[1]), secs=time.time() - t, **extra)
    p_ = os.path.join(D, 'results.json')
    allr = json.load(open(p_)) if os.path.exists(p_) else []
    allr.append(r); json.dump(allr, open(p_, 'w'), indent=1)
    print(json.dumps(r), flush=True)
    return r


cmd = sys.argv[1]
if cmd == 'lin':
    score(np.zeros((STEPS, 0)), ('raw',), 'linear in x(t)', dict(kind='floor'))
elif cmd in ('esn', 'esn2'):
    # esn: the first grid; esn2: the fairness extension (smaller input scale, smaller spectral radius; leak 1, the best above)
    grid = [(r, i, l) for r in (0.9, 0.99) for i in (0.1, 0.5) for l in (1.0, 0.3)] if cmd == 'esn' else \
           [(r, i, 1.0) for r in (0.5, 0.7, 0.9) for i in (0.01, 0.03, 0.05)]
    for N in (int(v) for v in sys.argv[2:]):
        for rho, ins, leak in grid:
            if True:
                if True:
                    g = torch.Generator(device='cpu').manual_seed(0)
                    W = (torch.randn(N, N, generator=g, dtype=torch.float32) / math.sqrt(N)).to(DEV)
                    W *= rho  # circular law: spectral radius ≈ 1 before scaling
                    Win = (torch.randn(N, Q, generator=g) * ins / math.sqrt(Q)).to(DEV); bias = (0.2 * torch.randn(N, generator=g)).to(DEV)
                    Xt = torch.as_tensor(X, dtype=torch.float32, device=DEV)
                    h = torch.zeros(N, device=DEV); Hs = torch.empty(STEPS, N, device=DEV)
                    with torch.no_grad():
                        for t in range(STEPS):
                            h = (1 - leak) * h + leak * torch.tanh(W @ h + Win @ Xt[t] + bias); Hs[t] = h
                    score(Hs.cpu(), ('raw',), f'ESN N={N}', dict(kind='esn', N=N, rho=rho, ins=ins, leak=leak))
                    del W, Hs; torch.cuda.empty_cache()
elif cmd == 'ngrc':
    # next-generation RC (Gauthier et al. 2021): linear features x(t … t−k+1) and all their unique quadratic monomials
    for k in (int(v) for v in sys.argv[2:]):
        Xt = torch.as_tensor(X, dtype=torch.float32)
        lin = torch.cat([torch.cat([torch.zeros(j, Q), Xt[:STEPS - j]]) for j in range(k)], 1)
        iu = torch.triu_indices(lin.shape[1], lin.shape[1])
        quad = (lin[:, iu[0]] * lin[:, iu[1]])
        score(torch.cat([lin, quad], 1), ('raw',), f'NG-RC k={k}', dict(kind='ngrc', k=k, N=int(lin.shape[1] + quad.shape[1])))
elif cmd == 'opt':
    from res_gpu import Reservoir
    n, bin_, K = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    amps = [float(v) for v in sys.argv[5:]]
    SUF = os.environ.get('RES_SUFFIX', '')  # Exp. 47: e.g. _R0.95 (SLM reflectivity)
    R = Reservoir(n, d_in=Q, suffix=SUF)
    assert R.patterns.shape[0] >= Q, f'res_n{n} has {R.patterns.shape[0]} patterns; dump with d = {Q}'
    U = np.repeat((X / math.sqrt(Q))[None], len(amps), 0)  # per-channel scale: Σ x_i P_i has O(1) amplitude
    t = time.time()
    F = R.run(U, K, np.array(amps), bin=bin_)
    sim = time.time() - t
    for i, amp in enumerate(amps):
        score(F[i], None, f'optical n={n}{SUF}', dict(kind='optical', n=n, modes=n * n, bin=bin_, K=K, amp=amp, sim_secs=sim, variant=SUF))
