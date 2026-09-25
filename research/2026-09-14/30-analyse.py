"""Experiment 30 analysis: for every run in out/<dir>/ (30-run.ts features), the noise-free task scores and the detected
photons per input step D_req needed to reach
  - BUNDLE29: the Exp. 29 operating point (NARMA10 ≤ 0.127, MC ≥ 33.7, XOR d2 ≥ 0.989), and
  - SHORT: a short-memory bundle (NARMA5 ≤ 0.07, MC5 ≥ 4.35, XOR d0 ≥ 0.99) — within 10 % of the noise-free base on
    NARMA5 / MC5.
Readout: transform and λ per task on validation (30-lib.py). usage: python 30-analyse.py [dir] [bins …] [--tags a,b]
→ out/<dir>/analysis_b{bins}.json (merged over calls)"""
import glob, importlib.util, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('L', os.path.join(HERE, '30-lib.py')); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
SHORT = dict(narma5_nmse=0.07, mc5=4.35, xor_d0=0.99)

args = [a for a in sys.argv[1:] if not a.startswith('--')]
d = args[0] if args else '30'
bins = [int(x) for x in args[1:]] or [16]
tags = None
for a in sys.argv[1:]:
    if a.startswith('--tags='): tags = a.split('=', 1)[1].split(',')
slot = 0
for a in sys.argv[1:]:
    if a.startswith('--slot='): slot = int(a.split('=')[1])

for nb in bins:
    path = os.path.join(L.OUT, d, f'analysis_b{nb}{"_s%d" % slot if slot else ""}.json')
    res = json.load(open(path)) if os.path.exists(path) else {}
    for jf in sorted(glob.glob(os.path.join(L.OUT, d, '*_uniform.json'))):
        tag = os.path.basename(jf)[:-len('_uniform.json')]
        if tags and tag not in tags: continue
        if tag in res or not os.path.exists(jf.replace('_uniform', '_bits')): continue
        Fu, m = L.load(tag, 'uniform', slot, d); Fb, mb = L.load(tag, 'bits', slot, d)
        B = int(round(np.sqrt(Fu.shape[1]))); b = B // nb
        if b < 1 or B % nb: continue
        Fu, Fb = L.binf(Fu, b), L.binf(Fb, b)
        u, _ = L.streams(m['steps'], slot); _, bb = L.streams(m['steps'], slot)
        clean = L.score(Fu, Fb, u, bb); clean.pop('mc_curve')
        fixed = L.score(Fu, Fb, u, bb, which=('log1',)); fixed.pop('mc_curve')
        D29, sw29 = L.d_required(Fu, Fb, u, bb, L.BUNDLE29)
        Ds, sws = L.d_required(Fu, Fb, u, bb, SHORT)
        c = m['cfg']
        res[tag] = dict(cfg=c, K=m['K'], t_rt=m['t_rt'], step_time=m['K'] * m['t_rt'], retention=m['passiveRetention'], gain=m['meanGain'],
                        lam2=m['lam2_passive'], meanP=m['meanP_fieldUnits'], injected=m['injectedFieldUnitsPerStep'], bins=nb * nb,
                        clean=clean, clean_fixed_log1=fixed, D_req_bundle29=D29, D_req_short=Ds, sweep_bundle29=sw29, sweep_short=sws)
        f = lambda x: '%.1e' % x if x else '  none '
        print(f"{tag:22s} b{nb:<3d} MC {clean['memory_capacity']:5.1f} NARMA10 {clean['narma10_nmse']:.3f} XORd2 {clean['xor_d2']:.3f} | NARMA5 {clean['narma5_nmse']:.3f} MC5 {clean['mc5']:.2f} XORd0 {clean['xor_d0']:.3f} | D29 {f(D29)} Dshort {f(Ds)} | ret {m['passiveRetention']:.3f}", flush=True)
        json.dump(res, open(path, 'w'), indent=1)
