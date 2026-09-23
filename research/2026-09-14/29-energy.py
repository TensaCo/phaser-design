"""Experiment 29c: task quality vs photon budget (from 29-noise.ts features), and an explicit energy-per-input-step model
for the optical reservoir vs tuned digital reservoirs (29-digital.py). Every device number is an ASSUMPTION listed in
PARAMS with a low / nominal / high value; the output JSON carries them so every derived number can be traced.
usage: python 29-energy.py   → out/29/energy_summary.json, out/29/fig_energy.png"""
import glob, importlib.util, json, math, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('ro', os.path.join(HERE, '15-readout.py'))
ro = importlib.util.module_from_spec(spec); spec.loader.exec_module(ro)
D = os.path.join(HERE, 'out', '29')
u = np.fromfile(os.path.join(HERE, 'out', '15', 'inputs_uniform.f64')); b = np.fromfile(os.path.join(HERE, 'out', '15', 'inputs_bits.f64'))

H_NU = 6.62607015e-34 * 2.99792458e8 / 650e-9  # J per photon at 650 nm
RETAIN = 0.684
PARAMS = {  # name: (low, nominal, high, unit, note)
    'wallplug': (0.5, 0.3, 0.1, '', 'electrical→optical efficiency of source and gain pump (laser diodes 30–60 %; lower for SOA/VCSEL gain)'),
    'dac_mod_J': (0.1e-12, 1e-12, 10e-12, 'J/sample', 'DAC + modulator per analog input sample'),
    'adc_fom_J': (1e-15, 10e-15, 100e-15, 'J/conv-step', 'ADC Walden figure of merit; 8 bit ⇒ ×256 per conversion'),
    'rx_J': (0.1e-12, 1e-12, 5e-12, 'J/sample', 'photodiode + TIA front end per detector bin per readout'),
    'readout_mac_J': (0.05e-12, 0.2e-12, 1e-12, 'J/MAC', 'digital linear readout MAC incl. local SRAM (8-bit ASIC ≈ 0.05–0.2; CPU/GPU ≈ 1+)'),
    'slm_static_W': (0.0, 0.1, 1.0, 'W', 'holding a static phase + absorbing program (0 = fabricated phase/absorber plates)'),
    'thermal_W': (0.05, 0.3, 1.0, 'W', 'temperature/phase stabilisation (Exp. 23: ≤ 0.03 rad rms phase needed)'),
    'digital_mac_J': (0.05e-12, 0.2e-12, 2e-12, 'J/MAC', 'digital reservoir MAC: 8-bit ASIC (0.05–0.2) … GPU batch-1 effective (≈ 2)'),
}
P = {k: v[1] for k, v in PARAMS.items()}
ADC_BITS, BINS = 8, 256


def evaluate(Fu, Fb):
    """features in field units (Σ|E|² per bin); fixed transform log10(x+1) for every run."""
    X, Xb = np.log10(Fu + 1), np.log10(Fb + 1)
    mc = []
    for k in range(1, 61):
        y = np.roll(u, k); y[:k] = 0
        p, yt = ro.ridge_eval(X, y); mc.append(float(np.corrcoef(p, yt)[0, 1] ** 2) if np.std(p) > 0 else 0.0)
    y = ro.narma10(u); p, yt = ro.ridge_eval(X, y)
    yx = np.logical_xor(np.roll(b, 2), np.roll(b, 3)).astype(float); yx[:4] = 0
    pb, ytb = ro.ridge_eval(Xb, yx)
    return dict(memory_capacity=float(sum(mc)), narma10_nmse=float(np.mean((p - yt) ** 2) / np.var(yt)), xor_d2=float(np.mean((pb > 0.5) == (ytb > 0.5))))


def optical_energy(meta, p=P):
    """J per input step. K trips per step; loss replenished by the gain each trip; source photons as simulated (2 % input
    coupler) and with an ideal coupler (photons that actually enter)."""
    K, t_rt, Nc = meta['K'], meta['t_rt'], meta['Nc']
    step_t = K * t_rt
    pump = K * (1 - RETAIN) * Nc * H_NU / p['wallplug']
    src_sim = meta['injectedPhotonsPerStep'] * H_NU / p['wallplug']
    src_ideal = 0.02 * meta['injectedPhotonsPerStep'] * H_NU / p['wallplug']
    det = BINS * (p['rx_J'] + p['adc_fom_J'] * 2 ** ADC_BITS)
    return dict(pump=pump, source_as_simulated=src_sim, source_ideal_coupler=src_ideal, input_dac_mod=p['dac_mod_J'], detection=det,
                readout=BINS * p['readout_mac_J'], static=(p['slm_static_W'] + p['thermal_W']) * step_t, step_time_s=step_t)


def digital_energy(N, p=P):
    return dict(recurrence=N * N * p['digital_mac_J'], readout=N * p['digital_mac_J'], input_adc=p['adc_fom_J'] * 2 ** ADC_BITS)


if __name__ == '__main__':
    # 1. quality vs photon budget
    runs = []
    for jf in sorted(glob.glob(os.path.join(D, 'feat_Nc*_uniform.json'))):
        m = json.load(open(jf)); fb = jf.replace('_uniform.json', '_bits.f64')
        if not os.path.exists(fb): continue
        Fu = np.fromfile(jf.replace('.json', '.f64')).reshape(m['steps'], 256); Fb = np.fromfile(fb).reshape(m['steps'], 256)
        m['Nc'] = math.inf if m['Nc'] is None else m['Nc']
        if math.isfinite(m['Nc']):  # photoelectrons → field units, so every run gets the same feature transform
            c = m['photonsPerFieldUnit'] * m['tap'] * m['qe']; Fu, Fb = Fu / c, Fb / c
        r = evaluate(Fu, Fb); r.update(Nc=m['Nc'], meta=m); runs.append(r)
        print('Nc %-8s MC %.1f NARMA %.3f XORd2 %.3f det/step %.2e' % (m['Nc'], r['memory_capacity'], r['narma10_nmse'], r['xor_d2'], m['meanDetectedPerStep']), flush=True)
    runs.sort(key=lambda r: r['Nc'])
    clean = [r for r in runs if not math.isfinite(r['Nc'])][0]
    noisy = [r for r in runs if math.isfinite(r['Nc'])]
    # smallest budget within 10 % of the noise-free NARMA error and MC
    ok = [r for r in noisy if r['narma10_nmse'] <= 1.1 * clean['narma10_nmse'] and r['memory_capacity'] >= 0.9 * clean['memory_capacity']]
    op = ok[0] if ok else None

    # 2. digital equal-quality size
    dig = json.load(open(os.path.join(D, 'digital_esn.json')))
    best = {}
    for r in dig:
        best.setdefault(r['N'], []).append(r)
    target = clean
    match = [N for N in sorted(best) if any(r['narma10_nmse'] <= target['narma10_nmse'] and r['memory_capacity'] >= target['memory_capacity'] and r['xor_d2'] >= target['xor_d2'] - 0.02 for r in best[N])]
    match_narma = [N for N in sorted(best) if any(r['narma10_nmse'] <= target['narma10_nmse'] and r['xor_d2'] >= target['xor_d2'] - 0.02 for r in best[N])]

    out = dict(params=PARAMS, h_nu_J=H_NU, clean=dict((k, clean[k]) for k in ('memory_capacity', 'narma10_nmse', 'xor_d2')),
               sweep=[dict(Nc=r['Nc'], memory_capacity=r['memory_capacity'], narma10_nmse=r['narma10_nmse'], xor_d2=r['xor_d2'],
                           detected_per_step=r['meta']['meanDetectedPerStep'], injected_photons_per_step=r['meta']['injectedPhotonsPerStep']) for r in noisy],
               operating_point=None if op is None else dict(Nc=op['Nc'], **{k: op[k] for k in ('memory_capacity', 'narma10_nmse', 'xor_d2')}),
               digital_best_by_N={N: min(v, key=lambda r: r['narma10_nmse']) for N, v in best.items()},
               digital_min_N_matching_all=match[0] if match else None, digital_min_N_matching_narma_xor=match_narma[0] if match_narma else None)
    if op:
        cases = {}
        for lvl, idx in (('low', 0), ('nominal', 1), ('high', 2)):
            p = {k: v[idx] for k, v in PARAMS.items()}
            e = optical_energy(op['meta'], p)
            tot_ideal = sum(v for k, v in e.items() if k not in ('source_as_simulated', 'step_time_s'))
            tot_sim = tot_ideal - e['source_ideal_coupler'] + e['source_as_simulated']
            cases[lvl] = dict(optical_components=e, optical_total_ideal_coupler=tot_ideal, optical_total_as_simulated=tot_sim,
                              digital={N: sum(digital_energy(int(N), p).values()) for N in best})
        out['energy_per_step'] = cases
    json.dump(out, open(os.path.join(D, 'energy_summary.json'), 'w'), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ('clean', 'operating_point', 'digital_min_N_matching_all', 'digital_min_N_matching_narma_xor')}, indent=1))
    if op:
        for lvl, c in out['energy_per_step'].items():
            print(lvl, 'optical %.3g J (sim coupler %.3g)' % (c['optical_total_ideal_coupler'], c['optical_total_as_simulated']),
                  {k: '%.2g' % v for k, v in c['optical_components'].items()}, {N: '%.2g' % v for N, v in c['digital'].items()})

    # figure: quality vs photons, energy breakdown
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
    x = [r['Nc'] for r in noisy]
    ax[0].semilogx(x, [r['narma10_nmse'] for r in noisy], 'o-', label='NARMA10 NMSE')
    ax[0].semilogx(x, [r['memory_capacity'] / 60 for r in noisy], 's-', label='MC / 60')
    ax[0].semilogx(x, [r['xor_d2'] for r in noisy], '^-', label='XOR d=2 acc')
    ax[0].axhline(clean['narma10_nmse'], c='C0', ls=':'); ax[0].set_xlabel('photons circulating N_c'); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
    if op:
        c = out['energy_per_step']['nominal']
        comp = {k: v for k, v in c['optical_components'].items() if k not in ('step_time_s', 'source_as_simulated')}
        ax[1].barh(list(comp), list(comp.values())); ax[1].set_xscale('log'); ax[1].set_xlabel('J per input step (nominal)')
        for N, v in c['digital'].items(): ax[1].axvline(v, ls=':', c='k'); ax[1].text(v, 0, f' ESN-{N}', rotation=90, fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(D, 'fig_energy.png'), dpi=130)
