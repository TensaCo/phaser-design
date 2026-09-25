"""Act 1 scientific visualization: charge moving through a lattice. Atoms are points sampled from orbital densities;
electrons try to hop to the next atom, mostly fall back; each hop shakes the lattice and the shaking is heat.
Graphite/paper palette (red is reserved for light). Writes PNG frames."""
import numpy as np, os, sys
from PIL import Image
from scipy.ndimage import gaussian_filter
W, H, FPS, SECS = 1920, 1080, 24, float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
out = sys.argv[1] if len(sys.argv) > 1 else 'gen/viz/electrons'
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(7)
# two layers: front (sharp) and back (blurred), each a jittered square lattice
def lattice(nx, ny, sp, off):
    xs, ys = np.meshgrid(np.arange(nx) * sp, np.arange(ny) * sp)
    return np.stack([xs.ravel() + off[0], ys.ravel() + off[1]], 1).astype(float)
layers = [dict(pos=lattice(13, 8, 180, (-1080 + 960, -630 + 540)), blur=0.0, gain=1.0, npts=900, r=34),
          dict(pos=lattice(17, 11, 125, (-1000 + 960, -625 + 540)), blur=5.0, gain=0.45, npts=500, r=24)]
for L in layers:
    n = len(L['pos'])
    # orbital-ish radial density: mix of 1s (exp) and a 2p lobe pair
    r = rng.gamma(2.0, L['r'] / 2.2, (n, L['npts'])); th = rng.uniform(0, 2 * np.pi, (n, L['npts']))
    lobe = rng.random((n, L['npts'])) < 0.35
    th = np.where(lobe, rng.uniform(0, np.pi, (n, 1)) + rng.choice([0, np.pi], (n, L['npts'])) + rng.normal(0, 0.35, (n, L['npts'])), th)
    r = np.where(lobe, r * 1.5, r)
    L['cloud'] = np.stack([r * np.cos(th), r * np.sin(th)], -1)
    L['heat'] = np.zeros(n); L['phase'] = rng.uniform(0, 2 * np.pi, (n, 2))
front = layers[0]; P = front['pos']; N = len(P)
nbr = [np.where((np.abs(np.linalg.norm(P - P[i], axis=1) - 180) < 1))[0] for i in range(N)]
# electrons: each sits at an atom and makes hop attempts
E = [dict(at=int(rng.integers(N)), to=-1, t=0.0, ok=False, wait=rng.uniform(0, 1)) for _ in range(26)]
def splat(img, xy, w, blur):
    x = np.clip(xy[:, 0].astype(int), 0, W - 1); y = np.clip(xy[:, 1].astype(int), 0, H - 1)
    m = (xy[:, 0] >= 0) & (xy[:, 0] < W) & (xy[:, 1] >= 0) & (xy[:, 1] < H)
    np.add.at(img, (y[m], x[m]), w)
nf = int(SECS * FPS)
for f in range(nf):
    t = f / FPS; dt = 1 / FPS
    zoom = 1.0 + 0.06 * (f / nf)  # slow push-in
    acc = np.zeros((H, W)); accb = np.zeros((H, W)); heatmap = np.zeros((H // 4, W // 4)); el = np.zeros((H, W))
    for e in E:
        if e['to'] < 0:
            e['wait'] -= dt
            if e['wait'] <= 0:
                e['to'] = int(rng.choice(nbr[e['at']])); e['t'] = 0; e['ok'] = rng.random() < 0.25
        else:
            e['t'] += dt / 0.55
            if e['ok'] and e['t'] >= 1:
                front['heat'][e['to']] += 0.9; front['heat'][e['at']] += 0.4
                e['at'], e['to'], e['wait'] = e['to'], -1, rng.uniform(0.1, 0.5)
            elif not e['ok'] and e['t'] >= 1:
                front['heat'][e['at']] += 0.25; e['to'], e['wait'] = -1, rng.uniform(0.05, 0.3)
    for L, img in ((layers[1], accb), (layers[0], acc)):
        L['heat'] *= 0.992
        amp = 2.0 + 9.0 * np.tanh(L['heat'] / 3)
        jit = amp[:, None] * np.stack([np.sin(t * 23 + L['phase'][:, 0]), np.cos(t * 19 + L['phase'][:, 1])], 1)
        centre = (L['pos'] + jit - 960) * zoom + 960
        centre[:, 1] = (L['pos'][:, 1] + jit[:, 1] - 540) * zoom + 540
        pts = (centre[:, None, :] + L['cloud'] * zoom).reshape(-1, 2)
        splat(img, pts, L['gain'], L['blur'])
        if L is front:
            hc = centre / 4
            for i in np.where(L['heat'] > 0.05)[0]:
                x, y = int(hc[i, 0]), int(hc[i, 1])
                if 0 <= x < W // 4 and 0 <= y < H // 4: heatmap[y, x] += L['heat'][i]
    for e in E:
        a = (P[e['at']] - 960) * zoom + 960
        if e['to'] >= 0:
            b = (P[e['to']] - 960) * zoom + 960
            s = e['t'] if e['ok'] else 0.42 * np.sin(np.pi * min(1, e['t']))  # failures turn back halfway
            p = a + (b - a) * s
        else: p = a + rng.normal(0, 6, 2)
        tail = p[None, :] + rng.normal(0, 4.0, (120, 2))
        splat(el, tail, 1.0, 0)
    acc = gaussian_filter(acc, 0.6); accb = gaussian_filter(accb, 5.0); el = gaussian_filter(el, 2.2)
    heat = np.kron(gaussian_filter(heatmap, 14), np.ones((4, 4)))[:H, :W]
    base = np.clip(acc * 0.85 + accb * 1.6, 0, 1)
    heat = np.clip(heat * 150, 0, 1) * min(1, t / 2.5)
    rgb = np.zeros((H, W, 3))
    paper = np.array([233, 229, 220]) / 255; warm = np.array([255, 150, 70]) / 255
    rgb += base[..., None] * paper
    rgb += (heat[..., None] * warm) * 0.55
    rgb += np.clip(el * 3.0, 0, 1)[..., None] * np.array([1.0, 0.97, 0.9])
    fade = min(1, t / 1.2)
    Image.fromarray((np.clip(rgb * fade, 0, 1) ** 0.9 * 255).astype(np.uint8)).save(f'{out}/{f:05d}.png')
    if f % 48 == 0: print(f, nf, flush=True)
