"""Experiment 51 (2026-10-13): the fair digital baseline for Exp. 50 — a recurrent network trained END TO END with the same
objective (held-out error of a closed-form ridge readout on windows of the KS training split), then scored with the Exp. 45
protocol. h ← act(W h + Win x + b), N units; W, Win, b trained by Adam from the tuned-ESN initialisation (rho 0.7, input 0.01).
act: tanh, or 'quad' = linear recurrence with features [h, h²] (the digital twin of a linear ring + square-law detection).
usage: python 51-train-rnn.py <N> <tanh|quad> <iters> [B=384] [seed=0] → out/45/results.json (kind 'rnn-trained')
"""
import importlib.util, json, math, os, sys, time
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location('KS45', os.path.join(HERE, '45-ks.py'))
_argv, sys.argv = sys.argv, ['45-ks.py', 'none']
KS = importlib.util.module_from_spec(_s); _s.loader.exec_module(KS)
sys.argv = _argv
N, act, iters = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
B = int(sys.argv[4]) if len(sys.argv) > 4 else 384
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
dev = KS.DEV; Q = KS.Q
torch.manual_seed(seed)
W = (torch.randn(N, N, device=dev) / math.sqrt(N) * 0.7).requires_grad_(True)
Win = (torch.randn(N, Q, device=dev) * (0.01 if act == 'tanh' else 1.0) / math.sqrt(Q)).requires_grad_(True)
bias = (0.2 * torch.randn(N, device=dev)).requires_grad_(True)
loglam = torch.tensor(-2.0, device=dev, requires_grad=True)


def features(Xw, keep_from=0):
    h = torch.zeros(Xw.shape[0], N, device=dev); out = []
    for t in range(Xw.shape[1]):
        z = h @ W.T + Xw[:, t] @ Win.T + bias
        h = torch.tanh(z) if act == 'tanh' else z
        if t >= keep_from: out.append(h if act == 'tanh' else torch.cat([h, h * h], 1))
    return torch.stack(out, 1)


X = torch.as_tensor(KS.X, dtype=torch.float32, device=dev); Y = torch.as_tensor(KS.Y, dtype=torch.float32, device=dev)
a, b = KS.a, KS.b
WASH, S = 12, 16; T = WASH + S
opt = torch.optim.Adam([dict(params=[W, Win, bias], lr=1e-3), dict(params=[loglam], lr=0.05)])
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, max(iters, 1), eta_min=1e-4)
t0 = time.time()
for it in range(iters):
    st = torch.randint(a, b - T - max(KS.H), (B,), device=dev)
    idx = st[:, None] + torch.arange(T, device=dev)[None]
    F = features(X[idx], WASH).double()
    xs, ys = X[idx[:, WASH:]].double(), Y[idx[:, WASH:]].double()
    h = B // 2
    mu, sd = F[:h].mean((0, 1)), F[:h].std((0, 1)) + 1e-9 * F[:h].std()
    Z = torch.cat([(F - mu) / sd, xs, torch.ones(B, S, 1, dtype=torch.float64, device=dev)], 2)
    Zf, Yf, Ze, Ye = Z[:h].reshape(h * S, -1), ys[:h].reshape(h * S, -1), Z[h:].reshape((B - h) * S, -1), ys[h:].reshape((B - h) * S, -1)
    lam = torch.exp(loglam.double() * math.log(10)) * Zf.shape[0]
    Wr = torch.linalg.solve(Zf.T @ Zf + lam * torch.eye(Zf.shape[1], dtype=torch.float64, device=dev), Zf.T @ Yf)
    err = ((Ze @ Wr - Ye) ** 2).mean(0) / Ye.var(0)
    loss = torch.log(err).mean()
    opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    if it % 100 == 0 or it == iters - 1:
        e = err.detach().reshape(len(KS.H), Q).mean(1).tolist()
        print(f'it {it} loss {float(loss):.3f} nmse h1/h4/h16 {e[0]:.2e} {e[1]:.2e} {e[2]:.3f} loglam {float(loglam):.2f} {time.time() - t0:.0f}s', flush=True)
with torch.no_grad():
    Fall = features(X[None], 0)[0].cpu().numpy()
del X, Y; torch.cuda.empty_cache()
KS.score(Fall, ('raw',) if act == 'tanh' else None, f'RNN-trained N={N} {act}', dict(kind='rnn-trained', N=N, act=act, iters=iters, B=B, seed=seed, train_secs=time.time() - t0))
