"""Experiment 29d: which noise limits the optical reservoir? Post-hoc on the noise-free features (29-noise.ts Nc=inf):
(a) detector shot noise only, at the detected-photon level implied by N_c; (b) ADC quantisation only (per-bin full scale
from the training split). Compare with 29a (ASE + shot + read noise, in-loop)."""
import importlib.util, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'out', '29')
spec = importlib.util.spec_from_file_location('en', os.path.join(HERE, '29-energy.py')); en = importlib.util.module_from_spec(spec); spec.loader.exec_module(en)
m = json.load(open(os.path.join(D, 'feat_Ncinf_uniform.json')))
Fu = np.fromfile(os.path.join(D, 'feat_Ncinf_uniform.f64')).reshape(-1, 256); Fb = np.fromfile(os.path.join(D, 'feat_Ncinf_bits.f64')).reshape(-1, 256)
rng = np.random.default_rng(0); res = dict(shot_only=[], adc_only=[])
for Nc in [1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11]:
    s = Nc / m['meanP_fieldUnits'] * 0.05 * 0.8
    r = en.evaluate(rng.poisson(Fu * s) / s, rng.poisson(Fb * s) / s); r['Nc'] = Nc; res['shot_only'].append(r); print('shot', Nc, r, flush=True)
def q(F, bits):
    lo, hi = F[200:2200].min(0), F[200:2200].max(0)
    k = np.round(np.clip((F - lo) / (hi - lo + 1e-30), 0, 1) * (2 ** bits - 1))
    return lo + k / (2 ** bits - 1) * (hi - lo)  # dequantised, field units
for bits in [6, 8, 10, 12, 14, 16]:
    X, Xb = q(Fu, bits), q(Fb, bits)
    r = en.evaluate(X, Xb); r['bits'] = bits; res['adc_only'].append(r); print('adc', bits, r, flush=True)
json.dump(res, open(os.path.join(D, 'decompose.json'), 'w'), indent=1)
