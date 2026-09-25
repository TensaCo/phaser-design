"""Experiment 32 analysis: task quality per time slot vs the number of slots M, the gain recovery time τ, in-cavity
leakage ε_cav, and (post hoc) detector crosstalk between neighbouring slots:
  - incoherent inter-symbol interference (finite detector/ADC bandwidth): F'_m = F_m + ε_d F_{m−1}
  - coherent pulse-tail overlap at the detector (amplitude a): |E_m + a E_{m−1}|² = F_m + 2a Re(E_m E*_{m−1}) + a² F_{m−1}
16×16 bins, readout as 30-analyse.py. usage: python 32-analyse.py → out/32/analysis.json"""
import glob, importlib.util, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('L', os.path.join(HERE, '30-lib.py')); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
D = '32'; path = os.path.join(L.OUT, D, 'analysis.json')
res = json.load(open(path)) if os.path.exists(path) else {}
KEYS = ('memory_capacity', 'narma10_nmse', 'xor_d2', 'narma5_nmse', 'mc5', 'xor_d0')
for jf in sorted(glob.glob(os.path.join(L.OUT, D, '*_uniform.json'))):
    tag = os.path.basename(jf)[:-len('_uniform.json')]
    if tag in res or not os.path.exists(jf.replace('_uniform', '_bits')): continue
    mu = json.load(open(jf)); S = mu['saveSlots']; steps = mu['steps']
    if not (mu['meanP_fieldUnits'] < 1e100):  # diverged (e.g. in-cavity leakage adds net gain to a fixed-gain loop)
        res[tag] = dict(cfg=mu['cfg'], M=mu['M'], diverged=True, meanP=str(mu['meanP_fieldUnits'])); print(tag, 'DIVERGED'); json.dump(res, open(path, 'w'), indent=1); continue
    out = dict(cfg=mu['cfg'], M=mu['M'], t_rt=mu['t_rt'], retention=mu['passiveRetention'], gain=mu['meanGain'], slots={})
    F = {}
    for s in range(S):
        Fu, _ = L.load(tag, 'uniform', s, D); Fb, _ = L.load(tag, 'bits', s, D)
        F[s] = (L.binf(Fu, 4), L.binf(Fb, 4))
        u, bb = L.streams(steps, s)
        r = L.score(*F[s], u, bb); r.pop('mc_curve'); out['slots'][s] = {k: r[k] for k in KEYS}
    u0, b0 = L.streams(steps, 0)
    D29, _ = L.d_required(*F[0], u0, b0, L.BUNDLE29); out['D_req_bundle29_slot0'] = D29
    if S >= 2 and mu['M'] > 1:
        u1, b1 = L.streams(steps, 1)
        Xu, _ = L.load(tag, 'uniform', 1, D, xterm=True); Xb, _ = L.load(tag, 'bits', 1, D, xterm=True)
        Xu, Xb = L.binf(Xu, 4), L.binf(Xb, 4)
        det = {}
        for e in (1e-3, 1e-2, 3e-2, 0.1, 0.3):
            r = L.score(F[1][0] + e * F[0][0], F[1][1] + e * F[0][1], u1, b1); det[f'isi_{e}'] = {k: r[k] for k in KEYS}
        for a in (1e-2, 3e-2, 0.1, 0.3):
            r = L.score(F[1][0] + 2 * a * Xu + a * a * F[0][0], F[1][1] + 2 * a * Xb + a * a * F[0][1], u1, b1); det[f'coherent_{a}'] = {k: r[k] for k in KEYS}
        out['detector_crosstalk_slot1'] = det
    res[tag] = out
    s0 = out['slots'][0]
    print(f"{tag:22s} M {mu['M']:3d} slot0 MC {s0['memory_capacity']:.1f} NARMA10 {s0['narma10_nmse']:.3f} XORd2 {s0['xor_d2']:.3f} | slots " +
          ' '.join('%.3f' % out['slots'][s]['narma10_nmse'] for s in out['slots']) + f" | D29 {D29} | gain {mu['meanGain']:.3f}", flush=True)
    json.dump(res, open(path, 'w'), indent=1)
