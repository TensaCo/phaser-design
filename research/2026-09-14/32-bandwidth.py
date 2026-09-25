"""Experiment 32 (analytic part, ESTIMATED, not simulated): how many time slots (pulses) M fit in one round trip, and what
detection bandwidth they need. The CW simulator has no temporal dimension; these are closed-form estimates.
 - slot Δ = t_rt / M; Gaussian pulses of FWHM τ_p; intensity overlap into the neighbouring slot = erfc(Δ/2 /(σ√2)) (σ = τ_p/2.355)
 - dispersion per round trip φ2 (fs²) summed over the glass actually in the route (GVD at 650 nm: N-BK7 ≈ 61 fs²/mm,
   fused silica ≈ 50 fs²/mm, YLF ≈ 50 fs²/mm (est.), air ≈ 0.02 fs²/mm); broadening after N trips of a transform-limited
   Gaussian: τ(N) = τ_p √(1 + (4 ln2 · N φ2 / τ_p²)²)
 - gain narrowing: a Gaussian gain line of FWHM Δν_g with log power gain lnG per pass (loss-compensated at line centre)
   filters the power spectrum by exp(−4 ln2 · lnG · δν²/Δν_g²) every trip, so after N trips 1/Δν_N² = 1/Δν_0² + N·lnG/Δν_g²
 - detector: single-pole response; residual of the previous slot after Δ is exp(−2πBΔ) ⇒ B = ln(1/ε)/(2πΔ)
usage: python 32-bandwidth.py → out/32/bandwidth.json"""
import json, math, os
from scipy.special import erfc
HERE = os.path.dirname(os.path.abspath(__file__))
C0, LAM = 2.99792458e8, 650e-9
GVD = dict(bk7=61.0, fs=50.0, ylf=50.0, air=0.02)  # fs²/mm
ROUTES = {  # glass per round trip (mm) for each configuration (Exp. 33 budgets)
    'ring (0.733 ns)': dict(t_rt=0.733e-9, glass=dict(bk7=2 * 4 + 2 * 1.0, ylf=5, air=200)),        # 2 lenses 4 mm, LCOS cover 1 mm ×2 passes
    'stack, 4 plates (0.255 ns)': dict(t_rt=0.255e-9, glass=dict(fs=4 * 1 * 2, ylf=10, air=50)),  # plates 1 mm ×2 passes, gain host ×2
    'stack, 4 LC panels (0.273 ns)': dict(t_rt=0.273e-9, glass=dict(bk7=4 * 1.4 * 2, ylf=10, air=50)),
}
GAIN = {'semiconductor (AlGaInP), Δλ ≈ 10 nm (est.)': 10e-9, 'Pr:YLF 640 nm line, Δλ ≈ 0.19 nm (lasing-line FWHM)': 0.19e-9}
dnu = lambda dl: C0 * dl / LAM ** 2
out = dict(routes={}, notes=__doc__)
for rname, r in ROUTES.items():
    phi2 = sum(GVD[k] * v for k, v in r['glass'].items()) * 1e-30  # s² per trip
    rows = []
    for M in (1, 4, 8, 13, 16, 32, 64, 80, 128):
        slot = r['t_rt'] / M
        tp = slot / 3  # pulse FWHM a third of the slot
        sig = tp / 2.355
        overlap = float(erfc(slot / 2 / (sig * math.sqrt(2))))
        row = dict(M=M, slot_ps=slot * 1e12, pulse_ps=tp * 1e12, bandwidth_GHz=0.441 / tp / 1e9, dlambda_nm=0.441 / tp * LAM ** 2 / C0 * 1e9, overlap=overlap)
        for N in (20, 100, 400, 1000):  # trips the information must survive (K=2: memory ≈ 90 trips; K=10: ≈ 400)
            b = math.sqrt(1 + (4 * math.log(2) * N * phi2 / tp ** 2) ** 2)
            row[f'dispersion_broadening_N{N}'] = b
            for gname, dl in GAIN.items():
                d0 = 0.441 / tp; lnG = math.log(1 / 0.7)  # gain replaces ≈ 30 % loss per trip
                dN = 1 / math.sqrt(1 / d0 ** 2 + N * lnG / dnu(dl) ** 2)
                row[f'gain_narrowed_pulse_ps_N{N}[{gname.split()[0]}]'] = 0.441 / dN * 1e12
        for eps in (1e-2, 1e-3):
            row[f'detector_B_GHz_isi{eps}'] = math.log(1 / eps) / (2 * math.pi * slot) / 1e9
        rows.append(row)
    out['routes'][rname] = dict(phi2_fs2_per_trip=phi2 * 1e30, rows=rows)
    print(rname, 'φ2 = %.0f fs²/trip' % (phi2 * 1e30))
    for row in rows:
        print('  M %3d slot %6.1f ps pulse %5.1f ps (%5.2f nm) overlap %.1e | disp N400 ×%.3f | SC N400 %.1f ps, Pr:YLF N100 %.0f ps N400 %.0f ps | det B %.1f GHz (ISI 1e-2)' % (
            row['M'], row['slot_ps'], row['pulse_ps'], row['dlambda_nm'], row['overlap'], row['dispersion_broadening_N400'],
            row['gain_narrowed_pulse_ps_N400[semiconductor]'], row['gain_narrowed_pulse_ps_N100[Pr:YLF]'], row['gain_narrowed_pulse_ps_N400[Pr:YLF]'], row['detector_B_GHz_isi0.01']))
json.dump(out, open(os.path.join(HERE, 'out', '32', 'bandwidth.json'), 'w'), indent=1)
