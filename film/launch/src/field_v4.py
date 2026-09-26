"""The explainer's field: the input light, one etched plate, and free-space propagation to the next plate, computed with
angular-spectrum propagation on the site's own plate program and input pattern (gen/v4/sim.json, exported from
phaser-sim.ts). Writes per-frame amplitude and phase (float32) for harness/field.ts, plus the frame script.
The plate's phase is drawn 3x deeper than it is so the twist is visible; nothing else is exaggerated."""
import json, os
import numpy as np
from scipy.ndimage import zoom
d = json.load(open('gen/v4/sim.json'))
N, DX, LAM = d['N'], d['DX'], d['LAMBDA']
U = 2  # upsample for a smoother surface
E0 = (np.array(d['inRe']) + 1j * np.array(d['inIm'])).reshape(N, N)
PH = [np.array(p).reshape(N, N) for p in d['phases']]
k = 2 * np.pi / LAM
fx = np.fft.fftfreq(N, DX); FX, FY = np.meshgrid(fx, fx)
kz = np.sqrt(np.maximum(0, k ** 2 - (2 * np.pi * FX) ** 2 - (2 * np.pi * FY) ** 2)).astype(np.complex128)
prop = lambda E, z: np.fft.ifft2(np.fft.fft2(E) * np.exp(1j * kz * z))
up = lambda A: zoom(A, U, order=1)
FPS = 24
frames, script = [], []
def add(E, cycle, **kw):
    """one frame: amplitude and phase (the phase rotated by 'cycle' radians to show the wave oscillating)"""
    Eu = up(E.real) + 1j * up(E.imag)
    frames.append(np.stack([np.abs(Eu), np.angle(Eu * np.exp(-1j * cycle))]).astype(np.float32)); script.append(kw)
E = E0 / np.abs(E0).max()
t = 0
# A: the light as it arrives (8 s): brightness and phase, the phase cycling
for i in range(int(8 * FPS)):
    add(E, 2 * np.pi * 0.6 * i / FPS, part='A', plate=0.0)
# B: the plate rises beneath and the wave passes through it (9.5 s): the phase twists pixel by pixel
Eafter = E * np.exp(1j * PH[0])
for i in range(int(9.5 * FPS)):
    s = min(1, max(0, (i / FPS - 2.0) / 4.5))  # sweep the plate's effect across the field, left to right
    mask = (np.arange(N)[None, :] / N) < s
    add(np.where(mask, Eafter, E), 2 * np.pi * 0.6 * (8 + i / FPS), part='B', plate=min(1, i / FPS / 1.5), sweep=s)
# C: downstream, the twisted waves meet (11.5 s): free-space propagation over the 5 mm gap
for i in range(int(11.5 * FPS)):
    z = 5e-3 * (min(1, (i / FPS) / 9.0) ** 1.4)
    add(prop(Eafter, z), 2 * np.pi * 0.6 * (17.5 + i / FPS), part='C', plate=max(0, 1 - i / FPS / 1.2), z=z)
# D: four plates and back, fast (4 s)
Ez = prop(Eafter, 5e-3)
for i in range(int(4 * FPS)):
    u = i / (4 * FPS) * 3  # through plates 2, 3, 4
    kk = min(2, int(u)); f = u - kk
    Ek = Ez
    for j in range(1, kk + 1): Ek = prop(Ek * np.exp(1j * PH[j]), 5e-3)
    add(prop(Ek * np.exp(1j * PH[kk + 1]), 5e-3 * f), 2 * np.pi * 0.6 * (29 + i / FPS), part='D', plate=0.0)
os.makedirs('gen/v4/field', exist_ok=True)
A = np.stack(frames)
A[:, 0] /= np.percentile(A[:, 0], 99.5)  # amplitude to ~0..1
A.astype(np.float32).tofile('gen/v4/field/frames.bin')
json.dump(dict(n=len(frames), size=N * U, script=script, plate=(np.array(PH[0]) * 3).round(4).tolist()), open('gen/v4/field/meta.json', 'w'))
print(A.shape, round(A.nbytes / 1e6), 'MB')
