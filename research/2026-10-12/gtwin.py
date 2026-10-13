"""Batched GPU twin (2026-10-12). Same dumped route and laws as ../2026-09-14/twin.py, with a leading DESIGN axis:
fields are (D, B, n, n) — D independent designs (own SLM/amplitude programs and pump G0), B cases each — so many designs
are optimised or verified in one pass. dtype 'c64' is for design (fast), 'c128' for verification (validated against JS).

Media parameters (absorber, gain saturation law, diffusion length) are shared by all designs in a batch.
"""
import json, math, os, sys
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
BIG = os.environ.get('PHASER_BIG', os.path.join(HERE, '..', '.big', ''))
TAU = 2 * math.pi


def _load(path, n, dtype):
    a = np.fromfile(path, dtype=np.complex128).reshape(n, n)
    return torch.from_numpy(a.copy()).to(dtype)


class GTwin:
    def __init__(self, name, dtype='c64', device='cuda', fused=False):
        d = BIG + f'twin_{name}/'
        self.name = name
        self.meta = json.load(open(d + 'twin.json'))
        self.n = n = self.meta['grid']['nx']
        self.dx = self.meta['grid']['dx']
        self.dev = device
        self.cdt = torch.complex64 if dtype == 'c64' else torch.complex128
        self.rdt = torch.float32 if dtype == 'c64' else torch.float64
        cache = {}
        C = lambda f: cache.setdefault(f, _load(d + f, n, self.cdt).to(device))
        R = lambda f: cache.setdefault('r' + f, _load(d + f, n, torch.complex128).real.to(self.rdt).to(device))
        self.ops = []
        for op in self.meta['ops']:
            o = dict(op)
            k = op['op']
            if k == 'prop':
                o['H'] = C(op['kernel'])
                o['W'] = None if op['boundary'] is None else R(op['boundary'])
            elif k == 'mul':
                o['T'] = C(op['t'])
            elif k in ('pixelphase', 'pixelamp'):
                m = np.fromfile(d + op['map'], dtype=np.float64).astype(np.int64).reshape(n, n)
                o['map'] = torch.from_numpy(np.maximum(m, 0)).to(device)
                o['active'] = torch.from_numpy(m >= 0).to(device)
                if k == 'pixelamp':
                    o['inactive_amp'] = torch.from_numpy(np.where(m == -2, op['deadAmp'], op['outsideAmp'])).to(self.rdt).to(device)
                else:
                    amp = np.where(m >= 0, op['amp'], np.where(m == -2, op['deadAmp'], op['outsideAmp'])) * op['scale']
                    o['ampmap'] = torch.from_numpy(amp).to(self.rdt).to(device)
            self.ops.append(o)
        self.res = {o['device']: (o['resY'], o['resX']) for o in self.ops if o['op'] in ('pixelphase', 'pixelamp')}
        self.media = dict(Ig=1.0, Ld=0.0, s=-0.8, Ia=0.2, kerr=0.0, linear=False)
        self._diff = None
        self.segs = None
        if fused:  # fused CUDA linear runs (fused.py): complex64, 64×64 only
            assert dtype == 'c64' and n == 64, 'fused runs need c64 and a 64×64 grid'
            import fused as F
            self._F = F
            kinds = [o['op'] for o in self.ops[:5]]
            assert kinds == ['scale', 'inject', 'pixelphase', 'pixelamp', 'nonlinear'], kinds
            self._head = (self.ops[0]['a'], self.ops[1]['coupling'])
            self.segs = F.segments(self, self.ops[5:])

    @staticmethod
    def grid_n(name):
        return json.load(open(BIG + f'twin_{name}/twin.json'))['grid']['nx']

    # ── media ──
    def set_media(self, **kw):
        self.media.update(kw)
        self._diff = None

    def diffusion_response(self):
        L = self.media['Ld']
        if self._diff is None:
            k = TAU * torch.fft.fftfreq(self.n, self.dx, dtype=torch.float64)
            self._diff = (1 / (1 + (k[None, :] ** 2 + k[:, None] ** 2) * L * L)).to(self.rdt).to(self.dev)
        return self._diff

    # ── programs ──
    @staticmethod
    def achieved(o, cmd, quantize=False):
        """commanded phase (D, P) → achieved phase, as pixels.ts achievedPhase (gamma response)."""
        u = torch.clamp(torch.remainder(cmd, TAU) / o['phaseRange'], 0, 1)
        if quantize and o['levels'] >= 2:
            q = torch.round(u * (o['levels'] - 1)) / (o['levels'] - 1)
            u = u + (q - u).detach()
        r = o['response']
        if r['kind'] == 'gamma':
            u = torch.clamp(u, 1e-12, 1) ** r['gamma']
        elif r['kind'] != 'linear':
            raise NotImplementedError(r['kind'])
        return u * o['phaseRange'] * o['lambdaScale']

    def transmissions(self, masks, quantize=False):
        """per-design complex transmission maps (D, 1, n, n) of the programmable devices (computed once per rollout)."""
        out = {}
        for o in self.ops:
            k = o['op']
            if k not in ('pixelphase', 'pixelamp'):
                continue
            cmd = masks[o['device']]  # (D, ry, rx)
            D = cmd.shape[0]
            flat = cmd.reshape(D, -1)
            if k == 'pixelphase':
                ph = self.achieved(o, flat, quantize)[:, o['map']]
                ph = torch.where(o['active'], ph, torch.zeros_like(ph))
                t = o['ampmap'] * torch.polar(torch.ones_like(ph), ph)
            else:
                uu = torch.remainder(flat, TAU) / TAU
                if quantize and o['levels'] >= 2:
                    q = torch.round(uu * (o['levels'] - 1)) / (o['levels'] - 1)
                    uu = uu + (q - uu).detach()
                T = o['dark'] + (o['clear'] - o['dark']) * uu[:, o['map']]
                a = torch.where(o['active'], torch.sqrt(torch.clamp(T, min=0)), o['inactive_amp'])
                t = (a * o['scale']).to(self.cdt)
            out[id(o)] = t[:, None]
        if self.segs is not None:  # fused head: one combined program transmission per design
            ts = [out[id(o)] for o in self.ops if o['op'] in ('pixelphase', 'pixelamp')]
            c = ts[0]
            for x in ts[1:]:
                c = c * x
            out['comb'] = c.to(self.cdt).contiguous()
        return out

    # ── one round trip ──
    def trip(self, E, tr, G0, inject=None, noise=0.0, gen=None):
        """E (D, B, n, n) complex; tr from transmissions(); G0 (D,) small-signal power gain; inject (D|1, B, n, n) or None;
        noise: additive complex Gaussian with mean intensity `noise` per sample after the gain (JS 'additive-gaussian')."""
        if self.segs is not None:
            md, F = self.media, self._F
            assert not md['linear'] and not md['kerr'], 'fused path: saturable absorber + gain only'
            a, c = self._head
            E = F.pre(E, tr['comb'], inject, a, c, md['s'], md['Ia'])
            for kind, x in self.segs:
                if kind == 'lin':
                    E = F.lin(E, x)
                elif x['op'] == 'gain':
                    resp = self.diffusion_response()[:, :self.n // 2 + 1].contiguous() if md['Ld'] > 0 else None
                    E = F.gain(E, G0.to(self.rdt), md['Ig'], resp)
                    if noise:
                        s = math.sqrt(noise / 2)
                        E = E + s * torch.complex(torch.randn(E.shape, generator=gen, device=E.device, dtype=self.rdt),
                                                  torch.randn(E.shape, generator=gen, device=E.device, dtype=self.rdt))
                else:
                    E = self._op(E, x, tr, G0, inject, noise, gen)
            return E
        for o in self.ops:
            E = self._op(E, o, tr, G0, inject, noise, gen)
        return E

    def _op(self, E, o, tr, G0, inject, noise, gen):
        md = self.media
        if True:
            k = o['op']
            if k == 'prop':
                E = torch.fft.ifft2(torch.fft.fft2(E) * o['H'])
                if o['W'] is not None:
                    E = E * o['W']
            elif k == 'scale':
                E = E * o['a']
            elif k == 'flip-x':
                E = torch.flip(E, dims=[-1])
            elif k == 'flip-y':
                E = torch.flip(E, dims=[-2])
            elif k == 'mul':
                E = E * o['T']
            elif k == 'inject':
                if inject is not None:
                    E = E + o['coupling'] * inject
            elif k in ('pixelphase', 'pixelamp'):
                E = E * tr[id(o)]
            elif k == 'nonlinear':
                if md['linear']:
                    return E
                I = E.real ** 2 + E.imag ** 2
                g = 1 + md['s'] / (1 + I / md['Ia'])
                a = torch.sqrt(torch.clamp(g, min=0))
                E = E * (torch.polar(a, md['kerr'] * I) if md['kerr'] else a)
            elif k == 'gain':
                if md['linear']:
                    E = E * math.sqrt(md['Glin'])
                    return E
                I = E.real ** 2 + E.imag ** 2
                if md['Ld'] > 0:
                    I = torch.fft.ifft2(torch.fft.fft2(I) * self.diffusion_response()).real.clamp_min(0)
                G = G0.view(-1, 1, 1, 1)
                g = 1 + (G - 1) / (1 + I / md['Ig'])
                E = E * torch.sqrt(torch.clamp(g, min=0))
                if noise:
                    s = math.sqrt(noise / 2)
                    E = E + s * torch.complex(torch.randn(E.shape, generator=gen, device=E.device, dtype=self.rdt),
                                              torch.randn(E.shape, generator=gen, device=E.device, dtype=self.rdt))
        return E


def validate(name, trips=200, D=3, B=4, seed=0):
    """GTwin (c128 and c64) vs the reference float64 Twin of 2026-09-14 (itself validated against JS) on random masks and fields."""
    sys.path.insert(0, os.path.join(HERE, '..', '2026-09-14'))
    os.environ['PHASER_DEVICE'] = 'cpu'
    import twin as T0
    ref = T0.Twin(name)
    g = torch.Generator().manual_seed(seed)
    n = ref.n
    media = dict(Ig=1.0, Ld=100e-6, s=-0.8, Ia=0.2, kerr=0.0, linear=False)
    G0s = [2.4, 2.6, 2.9][:D]
    # light must keep circulating for the comparison to mean anything: clear amplitude program, weak random phase, bright start
    masks = {dev: (math.pi + 0.3 * torch.rand(D, *ref.res[dev], generator=g, dtype=torch.float64)) if dev == 'slm'
             else torch.full((D, *ref.res[dev]), 0.999 * TAU, dtype=torch.float64) for dev in ref.devices}
    E0 = torch.complex(torch.randn(D, B, n, n, generator=g, dtype=torch.float64), torch.randn(D, B, n, n, generator=g, dtype=torch.float64)) * 1.5
    out = {}
    for dt in ('c128', 'c64'):
        tw = GTwin(name, dt)
        tw.set_media(**media)
        tr = tw.transmissions({k: v.to(tw.rdt).cuda() for k, v in masks.items()})
        E = E0.to(tw.cdt).cuda()
        for _ in range(trips):
            E = tw.trip(E, tr, torch.tensor(G0s, dtype=tw.rdt, device='cuda'))
        out[dt] = E.cpu().to(torch.complex128)
    worst = {'c128': 0, 'c64': 0}
    for d in range(D):
        ref.set_active(gain=dict(G0=G0s[d], saturation=dict(kind='diffusive', saturationIntensity=1.0, diffusionLength=100e-6), noise=dict(kind='none')),
                       nl=dict(amplitude=dict(kind='saturable', strength=-0.8, saturationIntensity=0.2), phase=dict(kind='none')))
        E = E0[d]
        with torch.no_grad():
            for _ in range(trips):
                E = ref.trip(E, {k: v[d] for k, v in masks.items()})
        if d == 0:
            print(f'  design 0 final power {(E.abs() ** 2).sum().item():.3e}')
        for dt in worst:
            worst[dt] = max(worst[dt], (torch.linalg.norm(out[dt][d] - E) / torch.linalg.norm(E)).item())
    print(f'{name}: {trips} trips, {D} designs × {B} cases, relative error vs float64 Twin: c128 {worst["c128"]:.2e}, c64 {worst["c64"]:.2e}')
    return worst


if __name__ == '__main__':
    for nm in sys.argv[1:]:
        validate(nm)
