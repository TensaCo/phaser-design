"""Kuramoto–Sivashinsky data for Exp. 45: u_t = −u u_x − u_xx − u_xxxx on a periodic domain of length L, Q grid points,
ETDRK4 (Kassam & Trefethen 2005) with internal step h, sampled every dt. The standard high-dimensional chaotic benchmark
for reservoir forecasting (Pathak et al. 2018): bigger reservoirs keep forecasting further.
usage: python ks.py <L> <Q> <steps> [dt=0.25] → out/45/ks_L{L}_Q{Q}.f64 (steps × Q, every 2nd point of a 2Q-point
simulation), after a 2000-time-unit transient"""
import os, sys
import numpy as np


def ks(L, Q, steps, dt=0.25, h=0.025, seed=0, transient=2000.0):
    x = L * np.arange(Q) / Q
    rng = np.random.default_rng(seed)
    u = 0.1 * np.cos(2 * np.pi * x / L) * (1 + np.sin(2 * np.pi * x / L)) + 0.01 * rng.normal(size=Q)
    v = np.fft.fft(u)
    k = 2 * np.pi / L * np.fft.fftfreq(Q, 1 / Q)
    Lk = k ** 2 - k ** 4
    E, E2 = np.exp(h * Lk), np.exp(h * Lk / 2)
    M = 32
    r = np.exp(1j * np.pi * (np.arange(1, M + 1) - 0.5) / M)
    LR = h * Lk[:, None] + r[None, :]
    Qc = h * np.real(np.mean((np.exp(LR / 2) - 1) / LR, 1))
    f1 = h * np.real(np.mean((-4 - LR + np.exp(LR) * (4 - 3 * LR + LR ** 2)) / LR ** 3, 1))
    f2 = h * np.real(np.mean((2 + LR + np.exp(LR) * (-2 + LR)) / LR ** 3, 1))
    f3 = h * np.real(np.mean((-4 - 3 * LR - LR ** 2 + np.exp(LR) * (4 - LR)) / LR ** 3, 1))
    kg = k.copy(); kg[Q // 2] = 0  # no odd-derivative at Nyquist (keeps u real; Kassam & Trefethen do the same)
    g = -0.5j * kg
    N = lambda v: g * np.fft.fft(np.real(np.fft.ifft(v)) ** 2)
    sub = int(round(dt / h))
    nt = int(round(transient / h))
    out = np.empty((steps, Q))
    for it in range(nt + steps * sub):
        Nv = N(v); a = E2 * v + Qc * Nv; Na = N(a); b = E2 * v + Qc * Na; Nb = N(b); c = E2 * a + Qc * (2 * Nb - Nv); Nc = N(c)
        v = E * v + Nv * f1 + 2 * (Na + Nb) * f2 + Nc * f3
        v = np.fft.fft(np.real(np.fft.ifft(v)))  # keep u real: round-off's imaginary part would grow at the unstable k
        j = it - nt + 1
        if j > 0 and j % sub == 0:
            out[j // sub - 1] = np.real(np.fft.ifft(v))
    return out


if __name__ == '__main__':
    L, Q, steps = float(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    dt = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', '45')
    os.makedirs(d, exist_ok=True)
    U = ks(L, 2 * Q, steps, dt)[:, ::2]  # simulate on 2Q points (resolved; explicit nonlinear step needs h·k_max·|u| ≲ 1), keep Q channels
    U.tofile(os.path.join(d, f'ks_L{int(L)}_Q{Q}.f64'))
    print(f'KS L={L} Q={Q}: {steps} samples, std {U.std():.3f}, range [{U.min():.2f}, {U.max():.2f}]')
