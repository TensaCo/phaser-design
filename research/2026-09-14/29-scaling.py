"""Experiment 29e: energy per input step vs reservoir size, extrapolated from the one simulated operating point
(Apre_lin K=10, 4096 modes, N_c = 1e10 photons ⇒ within 10 % of noise-free quality). MODELED, not simulated:
- optical pump and source scale with modes at the measured photons/mode; detection with bins (4096 modes : 256 bins);
- equivalence: 4096 optical modes matched tuned ESNs of 128 (NARMA+XOR) … 1024 (all metrics) units ⇒ 4–32 modes/unit;
- digital: dense ESN N² MACs; sparse ESN (10 nonzeros/row) 10·N MACs.
Output: out/29/scaling.json (consumed by the site's energy.ts)."""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'out', '29')
S = json.load(open(os.path.join(D, 'energy_summary.json')))
nom = S['energy_per_step']['nominal']; c = nom['optical_components']; MODES = 4096
per_mode = (c['pump'] + c['source_ideal_coupler']) / MODES       # J per mode per step
per_bin = (c['detection'] + c['readout']) / 256
static = c['static'] + c['input_dac_mod']
h_nu = S['h_nu_J']; photons_per_mode = S['operating_point']['Nc'] / MODES
Nd = np.unique(np.round(np.logspace(np.log10(64), 9, 120))).astype(float)
def optical(Nd, r):  # r modes per equivalent digital unit
    m = Nd * r
    return m * per_mode + (m / 16) * per_bin + static
mac = 0.2e-12
series = dict(
    digital_dense_asic=(Nd ** 2 * mac).tolist(),
    digital_dense_gpu=(Nd ** 2 * 2e-12).tolist(),
    digital_sparse_asic=(Nd * 10 * mac).tolist(),
    optical_modeled_4=optical(Nd, 4).tolist(), optical_modeled_32=optical(Nd, 32).tolist(),
    optical_photon_floor_4=(Nd * 4 * photons_per_mode * 10 * (1 - 0.684) * h_nu).tolist(),  # photons only, η = 1, no electronics
)
ratio = lambda k: np.array(series['digital_dense_asic']) / np.array(series[k])
def first(mask): i = np.argmax(mask); return float(Nd[i]) if mask.any() else None
out = dict(N_equiv_digital_units=Nd.tolist(), series=series, per_mode_J=per_mode, per_bin_J=per_bin, static_J=static, photons_per_mode=photons_per_mode,
           crossover_vs_dense_asic={k: first(ratio(k) > 1) for k in ('optical_modeled_4', 'optical_modeled_32')},
           N_for_ratio={f'{x:g}': {k: first(ratio(k) >= x) for k in ('optical_modeled_4', 'optical_modeled_32', 'optical_photon_floor_4')} for x in (10, 100, 1e3, 1e6)},
           vs_sparse_asic_max_ratio=float(max(np.array(series['digital_sparse_asic']) / np.array(series['optical_modeled_4']))))
json.dump(out, open(os.path.join(D, 'scaling.json'), 'w'))
print('per mode %.3g J, per bin %.3g J, static %.3g J, photons/mode %.3g' % (per_mode, per_bin, static, photons_per_mode))
print('crossover', out['crossover_vs_dense_asic']); print('N for ratio', json.dumps(out['N_for_ratio'], indent=0)); print('best ratio vs sparse ESN', out['vs_sparse_asic_max_ratio'])
