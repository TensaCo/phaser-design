"""Experiment 37a (2026-10-12): the effective lateral-inhibition kernel of each cross-gain mechanism, measured directly.

Hand-built two-cell absorbing lattice (3×3 px clear windows, everything else dark, flat SLM): cell A is written ON and held
to its steady state; a weak probe (ε) is placed in cell B, r px away along x. The probe's net round-trip power gain λ_B is
measured by linear response (two float64 runs, with and without ε, one trip), with A ON and with A OFF (A absent). Net
coupling = 1 − λ_B(A on) / λ_B(A off) (negative = A excites B: A's spill light also saturates B's absorber). Pure gain
depletion = 1 − ⟨g_on⟩_B / G0, the gain map at the gain plane with A ON, weighted by B's own intensity there (no absorber). Mechanisms: in-plane local gain (L_d 0), in-plane carrier diffusion (L_d 20–100 µm, the model
behind the Exp. 21 NAND), and a local gain sheet z mm off the image plane (go0.5 … go12 twins; no diffusion).

usage: python 37-kernel.py [G0=2.8]
"""
import json, math, os, sys
import numpy as np
import torch
from gtwin import GTwin, TAU

G0v = float(sys.argv[1]) if len(sys.argv) > 1 else 2.8
DIST = [3, 4, 5, 6, 8, 10, 12, 18]
w, cA = 3, (20, 31)  # A's corner (x0, y0); B at (x0 + r, y0)
MECH = [('in-plane local', 'A64s_amp', 0.0)] + [(f'in-plane L_d {L} µm', 'A64s_amp', L * 1e-6) for L in (20, 40, 60, 100)] + \
       [(f'sheet z = {z} mm', f'A64s_amp_go{z}', 0.0) for z in (0.5, 1, 2, 3, 5, 8, 12)]
dev = 'cuda'
rows = []
for label, twin, Ld in MECH:
    tw = GTwin(twin, 'c128')
    tw.set_media(Ig=1.0, Ld=Ld, s=-0.8, Ia=0.2, kerr=0.0)
    n = tw.n
    B = len(DIST)
    # programs per case (D axis = cases here, B = 1): clear windows at A and at B_r; flat SLM at mid-stroke (uniform phase)
    amp = torch.zeros(B, n, n, dtype=torch.float64, device=dev)
    for i, r in enumerate(DIST):
        for (x0, y0) in (cA, (cA[0] + r, cA[1])):
            amp[i, y0:y0 + w, x0:x0 + w] = 0.999 * TAU
    slm = torch.full((B, n, n), math.pi, dtype=torch.float64, device=dev)
    tr = tw.transmissions({'slm': slm, 'amp': amp})
    G0 = torch.full((B,), G0v, dtype=torch.float64, device=dev)
    winA = torch.zeros(n, n, dtype=torch.bool, device=dev); winA[cA[1]:cA[1] + w, cA[0]:cA[0] + w] = True
    winB = torch.zeros(B, n, n, dtype=torch.bool, device=dev)
    for i, r in enumerate(DIST):
        winB[i, cA[1]:cA[1] + w, cA[0] + r:cA[0] + r + w] = True
    out = {}
    for state in ('on', 'off'):
        E = torch.zeros(B, 1, n, n, dtype=torch.complex128, device=dev)
        if state == 'on':
            E[:, 0][:, winA] = math.sqrt(1.5)
        with torch.no_grad():
            for t in range(800):  # A relaxes to its steady state (B empty)
                E = tw.trip(E, tr, G0)
            IA = (E[:, 0].abs() ** 2)[:, winA].mean(1)
            eps = 1e-5
            P = torch.zeros_like(E)
            P[:, 0][winB] = eps
            E1 = tw.trip(E + P, tr, G0)
            E0 = tw.trip(E, tr, G0)
            dB = ((E1 - E0)[:, 0].abs() ** 2 * winB).sum((-2, -1)) / (eps ** 2 * w * w)
        out[state] = (dB.cpu().numpy(), IA.cpu().numpy())
    # pure cross-gain depletion at the gain plane
    gi = next(i for i, o in enumerate(tw.ops) if o['op'] == 'gain')
    with torch.no_grad():
        E = torch.zeros(B, 1, n, n, dtype=torch.complex128, device=dev)
        E[:, 0][:, winA] = math.sqrt(1.5)
        for t in range(800):
            E = tw.trip(E, tr, G0)
        Pb = torch.zeros_like(E); Pb[:, 0][winB] = 1e-5
        za, zb = E, Pb
        for o in tw.ops[:gi]:
            za = tw._op(za, o, tr, G0, None, 0.0, None)
            zb = tw._op(zb, o, tr, G0, None, 0.0, None)
        J = za.real ** 2 + za.imag ** 2
        if Ld > 0:
            J = torch.fft.ifft2(torch.fft.fft2(J) * tw.diffusion_response()).real.clamp_min(0)
        g_on = 1 + (G0v - 1) / (1 + J / 1.0)
        wB = zb.abs() ** 2
        depl = (1 - (wB * g_on).sum((-3, -2, -1)) / (wB.sum((-3, -2, -1)) * G0v)).cpu().numpy()
    lam_on, IA_on = out['on']
    lam_off, _ = out['off']
    for i, r in enumerate(DIST):
        rows.append(dict(mechanism=label, r_px=r, r_um=r * 20, lam_off=float(lam_off[i]), lam_on=float(lam_on[i]), net_coupling=float(1 - lam_on[i] / lam_off[i]), gain_depletion=float(depl[i]), I_A=float(IA_on[i])))
    print(f'{label:22s} I_A {IA_on.mean():6.2f} | net ' + ' '.join(f'{r}:{1 - lam_on[i] / lam_off[i]:+.2f}' for i, r in enumerate(DIST)) + ' | depletion ' + ' '.join(f'{r}:{depl[i]:.3f}' for i, r in enumerate(DIST)), flush=True)
os.makedirs('out/37', exist_ok=True)
json.dump(rows, open(f'out/37/kernel_G0{G0v}.json', 'w'), indent=1)
