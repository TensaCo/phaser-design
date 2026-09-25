"""Experiment 34: energy per input step and per equivalent multiply, revisited with the Exp. 30 tuning, the Exp. 33 loss
budgets (incl. glass), the Exp. 32 multiplexing and the Exp. 31 scaling test, against fairly tuned digital baselines (30b).

Photon accounting (per input step, per stream). The detector integrates the output tap T over the K trips of a step, so the
detected photoelectrons are D = K·T·QE·N_c. The gain replaces the whole round-trip loss L = 1 − R (tap included) every trip:
    E_pump = K·L·N_c·hν/η = D·hν·(L/T)/(QE·η)        (independent of K at fixed D)
so the tap should be large compared with the parasitic loss (L/T → 1). Every other term is electronic or static:
    E_src = n_in·D·hν/η_src (n_in = photons entering per detected photon, from the run), E_dac, E_det = bins·(E_rx + E_adc(f_s)),
    E_readout = bins·E_mac, E_static = (P_slm + P_thermal)·K·t_rt/M
f_s = per-bin sample rate = M/(K·t_rt) (integrate-and-dump over the K trips of each slot).
Digital: MACs/step × J/MAC for the cheapest tuned baseline meeting the same quality target (single ESN, two-ESN, NG-RC).
All device numbers: PARAMS (low / nominal / high) with sources in research/notes/energy-per-multiply.md.
usage: python 34-energy.py → out/34/energy.json"""
import importlib.util, json, math, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('L', os.path.join(HERE, '30-lib.py')); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
OUT = os.path.join(L.OUT, '34'); os.makedirs(OUT, exist_ok=True)
H_NU = L.H_NU
QE = 0.8

def adc_J(fs, lvl):
    """8-bit ADC energy per sample vs sample rate (Murmann ADC survey, SNDR 40–56 dB: best ≈ 2.2–2.6 pJ/sample at 1–10 GS/s,
    5.5 pJ at 72 GS/s; medians ≈ 20 pJ (0.5–2 GS/s) and 33 pJ (≥ 10 GS/s)). Below 1 GS/s SAR ADCs reach ≈ 1–5 fJ/conv-step."""
    if lvl == 'low': return 0.3e-12 if fs < 1e9 else (2.2e-12 if fs <= 20e9 else 5.5e-12)
    if lvl == 'nominal': return 2.6e-12 if fs < 1e9 else (5e-12 if fs <= 20e9 else 10e-12)
    return 20e-12 if fs < 1e9 else 33e-12

PARAMS = {  # name: (low, nominal, high)
    'eta_pump': (0.45, 0.27, 0.1),    # electrical → circulating-signal efficiency (red LD 45 %; blue pump 48 % × quantum defect 0.69 × overlap 0.8)
    'eta_src': (0.45, 0.3, 0.1),      # input source laser wall-plug
    'rx_J': (0.1e-12, 1e-12, 5e-12),  # photodiode + TIA per sample (0.08–1.4 pJ/bit class receivers)
    'dac_J': (0.1e-12, 1e-12, 10e-12),  # DAC + modulator per input sample (TFLN ~1 fJ/bit; 10 GS/s DAC ~10 pJ/sample)
    'mac_readout_J': (0.05e-12, 0.2e-12, 1e-12),
    'slm_W': (0.0, 0.1, 1.0), 'thermal_W': (0.05, 0.3, 1.0),
    'mac_digital_J': (0.05e-12, 0.2e-12, 1.0e-12),  # dense 8-bit ASIC incl. local SRAM: 5 nm (~0.02–0.05) … 45 nm + SRAM (~1)
}
GPU_J_PER_MAC = (0.71e-12, 1.24e-12, 2e-12)  # chip-level, batched: H100 INT8 dense at TDP; TPU v4 mean; H100 BF16 measured ≈ 2 pJ/MAC

def p(lvl): return {k: v[['low', 'nominal', 'high'].index(lvl)] for k, v in PARAMS.items()}

def optical(sc, lvl='nominal'):
    q = p(lvl); M = sc.get('M', 1); K = sc['K']; t_rt = sc['t_rt']; bins = sc.get('bins', 256)
    fs = M / (K * t_rt)
    D = sc['D']; LT = sc['loss'] / sc['tap']
    e = dict(pump=D * H_NU * LT / (QE * q['eta_pump']),
             source=sc['n_in'] * D * H_NU / q['eta_src'],
             dac=q['dac_J'],
             detection=bins * (q['rx_J'] + adc_J(fs, lvl)),
             readout=bins * q['mac_readout_J'],
             static=((0.0 if sc.get('plate') else q['slm_W']) + q['thermal_W']) * K * t_rt / M)
    e['total'] = sum(e.values())
    return dict(components=e, steps_per_s=M / (K * t_rt), per_bin_sample_rate=fs, power_W=e['total'] * M / (K * t_rt))

def load_json(*a):
    f = os.path.join(L.OUT, *a)
    return json.load(open(f)) if os.path.exists(f) else None

if __name__ == '__main__':
    A = load_json('30', 'analysis_b16.json') or {}
    A8 = load_json('30', 'analysis_b8.json') or {}
    LB = {r['name']: r for r in (load_json('33', 'loss_budget.json') or {'results': []})['results']}
    dig = load_json('30', 'digital.json') or []
    TGT = dict(bundle29=L.BUNDLE29, short=dict(narma5_nmse=0.07, mc5=4.35, xor_d0=0.99))
    def cheapest(t, kinds):
        ok = [r for r in dig if r['kind'] in kinds and L.meets(r, TGT[t])]
        return min(ok, key=lambda r: r['macs_per_step']) if ok else None
    digital = {t: {k: cheapest(t, ks) for k, ks in (('single ESN', ('esn',)), ('two ESNs', ('esn2',)), ('NG-RC', ('ngrc',)))} for t in TGT}

    def n_in(r, T):  # photons entering per detected photon, from the run (ring: 2 % input coupler; stack: 5 %; 5 % tap as
        # simulated). The input is a fixed fraction of the circulating power, and N_c = D/(K·T·QE), so it scales as 0.05/T.
        cin = 0.02 if r['cfg']['arch'] == 'ring' else 0.05
        return cin * r['injected'] / (r['meanP'] * r['K'] * 0.05 * QE) * (0.05 / T)
    scen = {}
    def add(name, run, target, lb=None, tap=None, M=1, bins=256, plate=False, analysis=None, note=''):
        r = (analysis or A).get(run)
        if r is None or r.get(f'D_req_{target}') is None: return
        # K = 1 runs have no trip without injection, so no retention measurement: use the same geometry at K = 2
        fb = A['base']['retention'] if r['cfg']['arch'] == 'ring' else (A.get(run.replace('_K1_', '_K2_'), {}).get('retention') or A['stackP_K2_G1.35']['retention'])
        loss_run = 1 - (r['retention'] or fb)
        if lb:  # swap in an Exp. 33 budget: parasitic loss from the budget, tap chosen here
            par = LB[lb]['loss'] - LB[lb]['tap']; T = tap or LB[lb]['tap']; loss = 1 - (1 - par) * (1 - T); t_rt = LB[lb]['t_rt']
        else:
            T = 0.05; loss = loss_run; t_rt = r['t_rt']
        sc = dict(run=run, target=target, D=r[f'D_req_{target}'], K=r['K'], t_rt=t_rt, loss=loss, tap=T, n_in=n_in(r, T), M=M, bins=bins, plate=plate, note=note, budget=lb)
        sc['energy'] = {lvl: optical(sc, lvl) for lvl in ('low', 'nominal', 'high')}
        scen[name] = sc
    for t in TGT:
        add(f'{t}: Exp. 29 point (K=10, as modelled)', 'base', t)
        ring = [k for k in A if A[k].get(f'D_req_{t}') and A[k]['cfg']['arch'] == 'ring']
        for k in ring: add(f'_{t}_{k}', k, t)  # every tuned ring configuration as modelled; the best by nominal energy is kept
        best = min(ring, key=lambda k: scen[f'_{t}_{k}']['energy']['nominal']['components']['total'], default=None)
        if best:
            add(f'{t}: tuned ({best})', best, t)
            add(f'{t}: tuned + dielectric LCOS, IBS AR, tap 5 %', best, t, lb='ring: dielectric LCOS + IBS AR')
            add(f'{t}: tuned + dielectric LCOS, tap 30 %', best, t, lb='ring: dielectric LCOS + IBS AR', tap=0.3)
            add(f'{t}: tuned + static plate, tap 30 %', best, t, lb='ring: static reflective plate + IBS', tap=0.3, plate=True)
            for M in (13, 32, 80):
                add(f'{t}: tuned + plate + tap 30 % + M={M} slots', best, t, lb='ring: static reflective plate + IBS', tap=0.3, plate=True, M=M)
            if best in A8 and A8[best].get(f'D_req_{t}'):
                add(f'{t}: tuned, 8×8 bins + plate + tap 30 % + M=13', best, t, lb='ring: static reflective plate + IBS', tap=0.3, plate=True, M=13, bins=64, analysis=A8)
        st = [k for k in A if A[k].get(f'D_req_{t}') and A[k]['cfg']['arch'] == 'stack']
        for k in st: add(f'_{t}_{k}', k, t)
        bs = min(st, key=lambda k: scen[f'_{t}_{k}']['energy']['nominal']['components']['total'], default=None)
        if bs:
            add(f'{t}: stack ({bs}), plates, tap 30 %', bs, t, lb='stack: fabricated plates (IBS AR)', tap=0.3, plate=True)
            add(f'{t}: stack ({bs}), plates, tap 30 %, M=13', bs, t, lb='stack: fabricated plates (IBS AR)', tap=0.3, plate=True, M=13)
    # digital energies
    dig_e = {}
    for t, d in digital.items():
        dig_e[t] = {}
        for k, r in d.items():
            if r is None: continue
            dig_e[t][k] = dict(macs=r['macs_per_step'], cfg={x: r.get(x) for x in ('N', 'N1', 'N2', 'L', 'q', 'rho', 'ins', 'leak', 'act')},
                               J={lvl: r['macs_per_step'] * p(lvl)['mac_digital_J'] for lvl in ('low', 'nominal', 'high')},
                               J_gpu_batched=[r['macs_per_step'] * j for j in GPU_J_PER_MAC])
    # Exp. 29 as reported: in-loop criterion D = 4.04e9 (the half-decade grid above rounds it up to 1e10)
    b = dict(scen['bundle29: Exp. 29 point (K=10, as modelled)']); b['D'] = 4.04e9
    b['energy'] = {lvl: optical(b, lvl) for lvl in ('low', 'nominal', 'high')}; scen['bundle29: Exp. 29 point, in-loop D = 4.0e9'] = b

    # ── scaling (MODELED from the 64² operating points + Exp. 31 equivalence; NOT simulated beyond 256²) ──────────────
    # optical per step at `modes`: detector bins = modes/16 (Exp. 31: equivalence needs bins ∝ modes), photons per mode as
    # at the 64² tuned point, static fixed; digital dense ESN of N_eq = modes/r units (r = modes per unit, Exp. 31: ≈ 16–64).
    sc0 = scen.get('bundle29: tuned + static plate, tap 30 %')
    scaling = {}
    if sc0:
        for lvl in ('low', 'nominal', 'high'):
            q = p(lvl); rows = []
            for modes in [4096 * 4 ** k for k in range(0, 10)]:
                sc = dict(sc0); sc['D'] = sc0['D'] * modes / 4096; sc['bins'] = modes / 16
                e = optical(sc, lvl)['components']['total']
                row = dict(modes=modes, optical_J=e)
                for r in (16, 40, 64):
                    N = modes / r; macs = N * N + N
                    row[f'r{r}'] = dict(N_eq=N, dense_asic_J=macs * q['mac_digital_J'], ratio=macs * q['mac_digital_J'] / e, optical_J_per_equiv_MAC=e / macs)
                rows.append(row)
            scaling[lvl] = rows
    out = dict(params=PARAMS, gpu_J_per_mac=GPU_J_PER_MAC, scenarios=scen, digital=dig_e, scaling=scaling)
    json.dump(out, open(os.path.join(OUT, 'energy.json'), 'w'), indent=1, default=float)
    for name, sc in scen.items():
        if name.startswith('_'): continue
        e = sc['energy']
        t = sc['target']; ds = dig_e[t].get('single ESN'); d2 = dig_e[t].get('two ESNs'); dn = dig_e[t].get('NG-RC')
        c = e['nominal']['components']
        print(f"{name:62s} D {sc['D']:.1e}  {e['low']['components']['total']*1e9:8.3f} / {c['total']*1e9:8.3f} / {e['high']['components']['total']*1e9:8.3f} nJ  "
              f"[pump {c['pump']*1e9:.3f} det {c['detection']*1e9:.3f} static {c['static']*1e9:.3f}]  {e['nominal']['steps_per_s']:.2e} steps/s  {e['nominal']['power_W']:.2f} W")
    for t, d in dig_e.items():
        for k, v in d.items(): print(t, k, v['macs'], v['cfg'], ' '.join('%.3g nJ' % (x * 1e9) for x in v['J'].values()))
    for lvl, rows in scaling.items():
        for row in rows:
            print(lvl, 'modes %.1e optical %.3g J' % (row['modes'], row['optical_J']), ' '.join('r%d: N %.0f ratio %.3g, %.2g J/eqMAC' % (r, row[f'r{r}']['N_eq'], row[f'r{r}']['ratio'], row[f'r{r}']['optical_J_per_equiv_MAC']) for r in (16, 40, 64)))
