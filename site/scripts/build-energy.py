"""Copies the Experiment 29 energy results (research/2026-09-14/out/29) into site/src/data/exp29.json.
usage (repo root): python3 site/scripts/build-energy.py"""
import json
R = 'research/2026-09-14/out/29/'
sc = json.load(open(R + 'scaling.json'))
es = json.load(open(R + 'energy_summary.json'))
ep = es['energy_per_step']
mac = {k: es['params']['digital_mac_J'][i] for i, k in enumerate(('low', 'nominal', 'high'))}
out = {
    'N': sc['N_equiv_digital_units'],
    'series': sc['series'],
    'per_mode_J': sc['per_mode_J'], 'per_bin_J': sc['per_bin_J'], 'static_J': sc['static_J'],
    'photons_per_mode': sc['photons_per_mode'],
    'crossover_vs_dense_asic': sc['crossover_vs_dense_asic'],
    'N_for_ratio': sc['N_for_ratio'],
    'vs_sparse_asic_max_ratio': sc['vs_sparse_asic_max_ratio'],
    'optical_total': {k: ep[k]['optical_total_ideal_coupler'] for k in ep},
    'components': {k: ep[k]['optical_components'] for k in ep},
    'esn128': {k: ep[k]['digital']['128'] for k in ep},
    'esn1024': {k: 1024 ** 2 * mac[k] for k in mac},
    'step_time_s': ep['nominal']['optical_components']['step_time_s'],
    'sweep': [{k: s[k] for k in ('Nc', 'memory_capacity', 'narma10_nmse', 'xor_d2', 'detected_per_step')} for s in es['sweep']],
    'clean': es['clean'],
    'operating_point': es['operating_point'],
    'digital_best_by_N': es['digital_best_by_N'],
    'h_nu_J': es['h_nu_J'],
    'params': {k: v for k, v in es['params'].items()},
}
json.dump(out, open('site/src/data/exp29.json', 'w'), indent=0)
print('wrote site/src/data/exp29.json', len(out['N']), 'points')
