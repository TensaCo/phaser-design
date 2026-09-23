"""Experiment 29b: tuned digital reservoirs (ESN) of size N on the Exp. 15 tasks, to find the smallest digital reservoir that
matches the optical Apre_lin K=10 result, and so a fair digital cost per input step. Hyper-parameters are chosen on the
TEST split (favours the digital baseline; conservative for the optical comparison)."""
import importlib.util, itertools, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('ro', os.path.join(HERE, '15-readout.py'))
ro = importlib.util.module_from_spec(spec); spec.loader.exec_module(ro)
D15 = os.path.join(HERE, 'out', '15'); OUT = os.path.join(HERE, 'out', '29'); os.makedirs(OUT, exist_ok=True)
u = np.fromfile(os.path.join(D15, 'inputs_uniform.f64')); b = np.fromfile(os.path.join(D15, 'inputs_bits.f64'))


def esn(N, rho, ins, leak, act, seed=0):
    rng = np.random.default_rng(seed)
    W = rng.normal(size=(N, N)) / np.sqrt(N); W *= rho / np.max(np.abs(np.linalg.eigvals(W)))
    Win = rng.normal(size=N); bias = 0.2 * rng.normal(size=N)
    f = np.tanh if act == 'tanh' else (lambda z: z)

    def F(s):
        h = np.zeros(N); H = np.empty((len(s), N))
        for t, x in enumerate(s):
            h = (1 - leak) * h + leak * f(W @ h + Win * (x - 0.25) * 4 * ins + (bias if act == 'tanh' else 0)); H[t] = h
        return H
    return F


def score(F):
    Fu, Fb = F(u), F(b * 0.5)
    mc = []
    for k in range(1, 61):
        y = np.roll(u, k); y[:k] = 0
        p, yt = ro.ridge_eval(Fu, y); mc.append(float(np.corrcoef(p, yt)[0, 1] ** 2) if np.std(p) > 0 else 0.0)
    y = ro.narma10(u); p, yt = ro.ridge_eval(Fu, y)
    nmse = float(np.mean((p - yt) ** 2) / np.var(yt))
    yx = np.logical_xor(np.roll(b, 2), np.roll(b, 3)).astype(float); yx[:4] = 0
    p, yt = ro.ridge_eval(Fb, yx)
    return dict(memory_capacity=float(sum(mc)), narma10_nmse=nmse, xor_d2=float(np.mean((p > 0.5) == (yt > 0.5))))


grid = list(itertools.product([0.9, 0.99], [0.1, 0.5, 1.0], [1.0, 0.3], ['tanh', 'linear']))
rows = []
sizes = [int(x) for x in sys.argv[1:]] or [64, 128, 256, 512, 1024, 2048]
for N in sizes:
    cand = grid if N <= 256 else [g for g in grid if g[3] == 'tanh' and g[1] in (0.1, 0.5)]
    for rho, ins, leak, act in cand:
        r = score(esn(N, rho, ins, leak, act)); r.update(N=N, rho=rho, ins=ins, leak=leak, act=act); rows.append(r)
        print(json.dumps(r), flush=True)
    json.dump(rows, open(os.path.join(OUT, 'digital_esn.json'), 'w'), indent=1)
