"""Experiment 31 analysis: does the modes-per-unit equivalence hold as the optics scales (64² → 128² → 256² modes)?
For each grid: capacity metrics (linear + quadratic information-processing capacity, NARMA10/20, XOR d2) of the optical
reservoir, read out at 16 modes per detector bin (256 / 1024 / 4096 features) and at a fixed 256 features; the tuned
digital ESN curve (31-digital.py, best hyper-parameters per metric on test); and the equivalent ESN size N_eq per metric
(log-interpolated), so modes / N_eq. usage: python 31-scaling.py → out/31/scaling.json"""
import importlib.util, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('L', os.path.join(HERE, '30-lib.py')); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
D = os.path.join(L.OUT, '31')
path = os.path.join(D, 'scaling.json')
res = json.load(open(path)) if os.path.exists(path) else {'optical': {}, 'digital': {}}
METRICS = ['cap_total', 'cap_linear', 'cap_quadratic', 'narma10_nmse', 'narma20_nmse', 'mc_1_60', 'xor_d2']

# digital: best per metric per N
for f in sorted(os.listdir(D)):
    if f.startswith('digital_N') and f.endswith('.json'):
        rows = json.load(open(os.path.join(D, f))); N = rows[0]['N']
        res['digital'][str(N)] = {m: (min if m.endswith('nmse') else max)(r[m] for r in rows) for m in METRICS}

for n in (64, 128, 256):
    tag = f'g{n}'
    if not os.path.exists(os.path.join(D, f'{tag}_bits.json')): continue
    Fu, m = L.load(tag, 'uniform', 0, '31'); Fb, _ = L.load(tag, 'bits', 0, '31')
    u, bb = L.streams(m['steps'])
    B = int(round(np.sqrt(Fu.shape[1])))  # saved bins per axis (64)
    modes_per_saved = (n // B) ** 2
    for label, feats in (('16modes_per_bin', (n * n) // 16), ('256_features', 256)):
        key = f'{tag}_{label}'
        if key in res['optical']: continue
        per_axis = int(round(np.sqrt(feats))); b = B // per_axis
        r = L.capacity_score(L.binf(Fu, b), L.binf(Fb, b), u, bb)
        r.update(modes=n * n, features=feats, retention=m['passiveRetention'], t_rt=m['t_rt'])
        res['optical'][key] = r; print(key, json.dumps(r), flush=True)
        json.dump(res, open(path, 'w'), indent=1)

# equivalence: N_eq per metric by log-linear interpolation of the digital best-per-N curve
Ns = sorted(int(k) for k in res['digital'])
def n_eq(metric, val):
    ys = [res['digital'][str(N)][metric] for N in Ns]
    better = (lambda a, b: a <= b) if metric.endswith('nmse') else (lambda a, b: a >= b)
    for i, N in enumerate(Ns):
        if better(ys[i], val):
            if i == 0: return float(N), False
            y0, y1 = ys[i - 1], ys[i]
            f = 0.5 if y1 == y0 else (val - y0) / (y1 - y0)
            return float(np.exp(np.log(Ns[i - 1]) + f * (np.log(N) - np.log(Ns[i - 1])))), False
    return float(Ns[-1]), True  # optical better than the largest ESN tested: N_eq is a lower bound
eq = {}
for key, r in res['optical'].items():
    eq[key] = {}
    for mtr in METRICS:
        if mtr in r and Ns:
            N, lower = n_eq(mtr, r[mtr]); eq[key][mtr] = dict(N_eq=N, modes_per_unit=r['modes'] / N, lower_bound_on_N=lower)
res['equivalence'] = eq
json.dump(res, open(path, 'w'), indent=1)
for key, e in eq.items():
    print(key, {k: '%.0f (%.1f modes/unit)%s' % (v['N_eq'], v['modes_per_unit'], '+' if v['lower_bound_on_N'] else '') for k, v in e.items()})
