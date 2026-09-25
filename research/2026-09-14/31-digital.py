"""Experiment 31b: tuned digital ESNs (N = 64 … 4096) on the capacity tasks at 16000 steps, the digital side of the
modes-per-unit equivalence at larger grids. Hyper-parameters picked on the TEST split per metric (favours digital).
usage: python 31-digital.py N [N …] → out/31/digital_N{N}.json"""
import importlib.util, json, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('L', os.path.join(HERE, '30-lib.py')); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
STEPS = 16000
u, b = L.streams(STEPS)
for N in [int(x) for x in sys.argv[1:]]:
    path = os.path.join(L.OUT, '31', f'digital_N{N}.json')
    if os.path.exists(path): continue
    grid = L.ESN_GRID if N <= 512 else [g for g in L.ESN_GRID if g[3] == 'tanh' and g[1] in (0.1, 0.5)] + [(0.99, 0.5, 1.0, 'linear')]
    rows = []
    for rho, ins, leak, act in grid:
        t = time.time()
        Hu = L.esn_features(N, rho, ins, leak, act, u); Hb = L.esn_features(N, rho, ins, leak, act, b * 0.5)
        r = L.capacity_score(Hu, Hb, u, b, which=('raw',)); r.update(N=N, rho=rho, ins=ins, leak=leak, act=act, secs=time.time() - t)
        rows.append(r); print(json.dumps(r), flush=True)
    json.dump(rows, open(path, 'w'), indent=1)
