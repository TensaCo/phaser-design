"""Experiment 46 (2026-10-12): techno-economic model — at what scale, for which workloads, would a built PHASER be an
economically viable alternative to GPUs? Every input is a stated assumption with a low/high range (prototype and volume
pricing are separate columns); results are reported as ranges. MODELED, not measured: no hardware exists.

The capability side comes from the simulations: modes per equivalent dense-ESN unit r (Exp. 31: 16–44 to 65k modes; Exps. 43
and 45 extend it), step time (Exp. 30: ring K = 2 → 1.33 ns; plate stack K = 1 → 0.17 ns), and the readout architecture
(Exp. 44: optical readout = 2 detectors per output instead of one per 16 modes).

Digital reference: a dense ESN of the equivalent size N_eq = modes / r, run on GPUs. Two regimes:
  * batched (many independent streams): throughput-bound, N² MAC per step per stream at an effective GPU MAC rate;
  * single stream: latency-bound, each step needs the whole N² weight matrix read once (memory bandwidth) and at least one
    kernel launch, so the step rate is capped no matter how many GPUs are bought.
A dense ESN is not the cheapest digital model for most tasks: a 'digital efficiency' factor (1 = dense ESN, 100 = a model
100× cheaper per step at the same quality) is swept to show how much of the advantage survives smarter digital algorithms.

usage: python 46-econ.py [results jsons are read if present] → out/46/econ.json + printed tables
"""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', '46')
os.makedirs(OUT, exist_ok=True)

# ── assumptions (low, high); USD and W ──────────────────────────────────────────────────────────────────────────────
A = dict(
    # GPU (H100-class SXM, 2025–26): price incl. share of server; effective dense FP8 MAC/s on large batched GEMV/GEMM;
    # HBM bandwidth; power incl. server overhead
    gpu_price=(25e3, 40e3), gpu_mac_s=(0.5e15, 1.0e15), gpu_bw=(3.35e12, 3.35e12), gpu_W=(700 * 1.3, 700 * 1.5),
    gpu_step_floor_s=(5e-6, 10e-6),  # kernel launch + sync per sequential step (CUDA graphs ~5 µs)
    # PHASER bill of materials, prototype (lab parts) and volume (≥ 1k units) — per system
    optics_proto=(3e3, 8e3), optics_vol=(200, 800),                # relay lenses, coupler, mounts / moulded optics
    program_proto=(8e3, 20e3), program_vol=(100, 1000),            # LCOS phase SLM / fabricated phase plate (+NRE amortised)
    gain_proto=(3e3, 15e3), gain_vol=(300, 2e3),                    # gain chip + pump diode + driver
    input_mod_proto=(2e3, 5e3), input_mod_vol=(30, 200),            # per input channel: EOM / Si-photonic modulator + driver
    ro_mask_proto=(3e3, 15e3), ro_mask_vol=(50, 300),              # readout amplitude mask (SLM / fixed mask)
    det_ch_proto=(200, 1000), det_ch_vol=(5, 30),                   # per GHz detector channel: photodiode + TIA + ADC share
    ctrl_proto=(2e3, 10e3), ctrl_vol=(200, 1000),                   # FPGA / control electronics
    # power
    det_ch_W=(0.05, 0.5),            # per GHz-rate detection channel (ASIC ADC ~50 mW … discrete ~0.5 W)
    pump_W=(2, 20), ctrl_W=(10, 50), input_W=(0.2, 1.0),  # input: per channel modulator driver
    # light: detected photons per step per output for the target quality (Exp. 44, optical readout, 128² ring:
    # NARMA10 ≈ 0.03 at 1e8 for one output; 64 outputs at 1e10 total ≈ 1.6e8 each), the fraction of circulating light
    # tapped and detected, and laser/gain wall-plug efficiency
    photons_per_output=(1e8, 3e8), tap_and_QE=(0.3, 0.1), wallplug=(0.3, 0.1),
)
H_NU = 6.62607015e-34 * 2.99792458e8 / 650e-9


def lohi(k):
    return A[k]


def phaser(modes, outputs, inputs, readout='optical', volume=False, modes_per_bin=16, step_rate=7.5e8):
    """BOM cost and power ranges of one PHASER system (optical power from the photon budget at step_rate)"""
    s = 'vol' if volume else 'proto'
    ch = 2 * outputs if readout == 'optical' else modes / modes_per_bin
    cost = [A[f'optics_{s}'][i] + A[f'program_{s}'][i] + A[f'gain_{s}'][i] + inputs * A[f'input_mod_{s}'][i]
            + (A[f'ro_mask_{s}'][i] if readout == 'optical' else 0) + ch * A[f'det_ch_{s}'][i] + A[f'ctrl_{s}'][i] for i in (0, 1)]
    light = [outputs * A['photons_per_output'][i] * H_NU * step_rate / A['tap_and_QE'][i] / A['wallplug'][i] for i in (0, 1)]
    W = [A['pump_W'][i] + A['ctrl_W'][i] + inputs * A['input_W'][i] + ch * A['det_ch_W'][i] + light[i] for i in (0, 1)]
    return dict(cost=cost, W=W, channels=ch, light_W=light)


def gpu_equiv(N, step_rate, streams, eff=1.0):
    """GPUs needed for `streams` independent streams of a dense N-unit ESN at step_rate each (eff: digital efficiency).
    Returns (gpus low, high) and whether a single stream is feasible at that rate at all."""
    mac = N * N / eff
    need = mac * step_rate * streams
    gpus = [need / A['gpu_mac_s'][1], need / A['gpu_mac_s'][0]]
    t_step = max(mac / (A['gpu_bw'][0] / 1.0), A['gpu_step_floor_s'][0])  # 1 byte per weight (FP8), best case
    max_rate_single = 1 / t_step
    return dict(gpus=gpus, max_single_stream_rate=max_rate_single, feasible_single=step_rate <= max_rate_single)


def table(r_modes_per_unit, step_rates, out_counts=(1, 64), inputs=(1, 64), effs=(1, 10, 100)):
    rows = []
    for modes in (65536, 262144, 1048576, 4194304):
        N = modes / r_modes_per_unit
        for f in step_rates:
            for M in out_counts:
                for d in inputs:
                    for vol in (False, True):
                        for ro in ('optical', 'electronic'):
                            p = phaser(modes, M, d, ro, vol, step_rate=f)
                            for eff in effs:
                                g = gpu_equiv(N, f, 1, eff)
                                gcost = [g['gpus'][0] * A['gpu_price'][0], g['gpus'][1] * A['gpu_price'][1]]
                                gW = [g['gpus'][0] * A['gpu_W'][0], g['gpus'][1] * A['gpu_W'][1]]
                                rows.append(dict(modes=modes, N_eq=N, step_rate=f, outputs=M, inputs=d, volume=vol, readout=ro, digital_eff=eff,
                                                 phaser_cost=p['cost'], phaser_W=p['W'], det_channels=p['channels'],
                                                 gpu_count_for_same_MACs=g['gpus'], gpu_cost=gcost, gpu_W=gW,
                                                 gpu_single_stream_max_rate=g['max_single_stream_rate'], gpu_single_stream_feasible=g['feasible_single'],
                                                 cost_ratio=[gcost[0] / p['cost'][1], gcost[1] / p['cost'][0]], power_ratio=[gW[0] / p['W'][1], gW[1] / p['W'][0]]))
    return rows


if __name__ == '__main__':
    # capability inputs; overridden by the measured values of Exps. 43/45 when the analysis below is filled in
    R = dict(modes_per_unit=(16, 44))
    rates = (1 / 1.33e-9, 1 / 0.17e-9 / 4)  # ring K=2 (0.75 G steps/s); plate stack K1 detected at 1.5 GS/s (detector-limited)
    res = dict(assumptions=A, capability=R, rows=[])
    for r in R['modes_per_unit']:
        for row in table(r, rates):
            row['modes_per_unit'] = r
            res['rows'].append(row)
    json.dump(res, open(os.path.join(OUT, 'econ.json'), 'w'), indent=1)
    f = lambda x: f'{x[0]:.3g}–{x[1]:.3g}'
    print('modes  r   N_eq     rate     out in vol  readout     eff  PHASER $        PHASER W      GPUs(MAC-equal)   GPU single-stream max   $ ratio')
    for row in res['rows']:
        if row['inputs'] != 1 or row['digital_eff'] not in (1, 100) or row['step_rate'] < 1e9 and False:
            continue
        print(f"{row['modes']:>8} {row['modes_per_unit']:>3} {row['N_eq']:>8.0f} {row['step_rate']:.2e} {row['outputs']:>3} {row['inputs']:>2} {str(row['volume'])[0]} "
              f"{row['readout']:>10} {row['digital_eff']:>4} {f(row['phaser_cost']):>16} {f(row['phaser_W']):>14} {f(row['gpu_count_for_same_MACs']):>18} "
              f"{row['gpu_single_stream_max_rate']:>10.3g}/s {f(row['cost_ratio']):>14}")
