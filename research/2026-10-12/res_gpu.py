"""Exp. 43 (2026-10-12): GPU reservoir engine — the 30-run.ts reservoir loop (global-gain SLM ring, static input pattern(s),
features = |E|² summed over the K trips of each input step) in torch, for grids far beyond what the JS loop can run
(256² took 26 min per 16k steps in JS; 1024² would take a day).

Physics is the exported route of res-dump.ts (propagation kernels, static element transmissions, coupler/mirror scalars,
global gain 1 + (G0 − 1)/(1 + ⟨|E|²⟩/Is) on the mean intensity of each sample's own grid). Batch axis = independent runs
(input streams, input amplitudes, …) sharing the optics.

API:
  R = Reservoir(n, dtype='c64')
  feats = R.run(U, K, amp, bin=…)   U: (B, steps, d) inputs; returns (B, steps, (n/bin)²) float32 binned features
usage (validation vs the JS reference in res_n{n}/): python res_gpu.py validate <n>
"""
import json, math, os, sys, time
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
BIG = os.path.join(HERE, '..', '.big') + '/'


def _c(path, n, dt):
    a = np.fromfile(path, dtype=np.float64).reshape(n, n, 2)
    return torch.complex(torch.from_numpy(a[..., 0].copy()), torch.from_numpy(a[..., 1].copy())).to(dt)


class Reservoir:
    def __init__(self, n, dtype='c64', device='cuda', d_in=1, suffix=''):
        d = BIG + f'res_n{n}' + ('' if d_in == 1 else f'_d{d_in}') + suffix + '/'
        self.meta = json.load(open(d + 'res.json'))
        self.n, self.dev = n, device
        self.cdt = torch.complex64 if dtype == 'c64' else torch.complex128
        self.rdt = torch.float32 if dtype == 'c64' else torch.float64
        cache = {}
        C = lambda f: cache.setdefault(f, _c(d + f, n, self.cdt).to(device))
        self.ops = []
        for op in self.meta['ops']:
            o = dict(op)
            if o['op'] == 'prop':
                o['H'] = C(op['kernel']); o['W'] = None if op['boundary'] is None else C(op['boundary']).real.contiguous()
            elif o['op'] == 'mul':
                o['T'] = C(op['t'])
            self.ops.append(o)
        # fold consecutive elementwise ops (mul/scale/boundary) into single maps where possible: fewer kernel launches
        self.prog = self._fold()
        self.patterns = torch.stack([C(p) for p in self.meta['patterns']])  # (d, n, n)

    def _fold(self):
        prog, acc = [], None
        def flush():
            nonlocal acc
            if acc is not None:
                prog.append(('mul', acc)); acc = None
        for o in self.ops:
            k = o['op']
            if k in ('mul', 'scale'):
                t = o['T'] if k == 'mul' else torch.tensor(o['a'], dtype=self.cdt, device=self.dev)
                acc = t if acc is None else acc * t
            elif k == 'prop':
                if acc is not None:  # fold the preceding multiplier into nothing (must apply before FFT): keep separate
                    flush()
                prog.append(('prop', o['H']))
                if o['W'] is not None:
                    acc = o['W'].to(self.cdt)
            else:
                flush(); prog.append((k, o))
        flush()
        return prog

    def trip(self, E, inj, G0, Is):
        for k, x in self.prog:
            if k == 'mul':
                E = E * x
            elif k == 'prop':
                E = torch.fft.ifft2(torch.fft.fft2(E) * x)
            elif k == 'inject':
                if inj is not None:
                    E = E + x['coupling'] * inj
            elif k == 'flip-x':
                E = torch.flip(E, dims=[-1])
            elif k == 'flip-y':
                E = torch.flip(E, dims=[-2])
            elif k == 'gain':
                I = (E.real ** 2 + E.imag ** 2).mean((-2, -1), keepdim=True)
                g = 1 + (G0 - 1) / (1 + I / Is)
                E = E * torch.sqrt(torch.clamp(g, min=0))
            else:
                raise NotImplementedError(k)
        return E

    @torch.no_grad()
    def run(self, U, K, amp, bin=1, G0=None, Is=None, E0=None, chunk=2000, out=None):
        """U: (B, steps, d) float array (inputs, channel i drives pattern i); amp: scalar or (B,) input amplitude.
        Returns float32 numpy (B, steps, (n/bin)²) features (or writes into memmap `out`)."""
        G0 = self.meta['G0'] if G0 is None else G0
        Is = self.meta['Is'] if Is is None else Is
        U = torch.as_tensor(U, dtype=self.rdt, device=self.dev)
        B, S, dch = U.shape
        n, nb = self.n, self.n // bin
        amp = torch.as_tensor(amp, dtype=self.rdt, device=self.dev).reshape(-1, 1, 1) if np.ndim(amp) else float(amp)
        P = self.patterns[:dch]
        E = torch.zeros(B, n, n, dtype=self.cdt, device=self.dev) if E0 is None else E0
        res = out if out is not None else np.empty((B, S, nb * nb), np.float32)
        buf = torch.zeros(min(chunk, S), B, nb * nb, dtype=torch.float32, device=self.dev)
        for s0 in range(0, S, chunk):
            s1 = min(S, s0 + chunk)
            buf.zero_()
            for s in range(s0, s1):
                inj = amp * torch.einsum('bd,dxy->bxy', U[:, s].to(self.cdt), P)
                acc = None
                for k in range(K):
                    E = self.trip(E, inj if k == 0 else None, G0, Is)
                    I = E.real ** 2 + E.imag ** 2
                    acc = I if acc is None else acc + I
                if bin > 1:
                    acc = acc.reshape(B, nb, bin, nb, bin).sum((2, 4))
                buf[s - s0] = acc.reshape(B, -1).float()
            res[:, s0:s1] = buf[:s1 - s0].transpose(0, 1).cpu().numpy()
        self.E = E
        return res


def validate(n, dtype='c128'):
    m = json.load(open(BIG + f'res_n{n}/res.json'))
    ref = np.fromfile(BIG + f'res_n{n}/ref_feats.f64').reshape(m['refSteps'], -1)
    u = np.fromfile(BIG + f'res_n{n}/ref_u.f64')
    R = Reservoir(n, dtype)
    t = time.time()
    F = R.run(u[None, :, None], m['K'], m['inputAmp'])[0].astype(np.float64)
    if R.dev == 'cuda': torch.cuda.synchronize()
    err = np.abs(F - ref).max() / np.abs(ref).max()
    per_step = [float(np.abs(F[s] - ref[s]).max() / (np.abs(ref[s]).max() + 1e-300)) for s in range(len(ref))]
    print(f'n={n} {dtype}: max rel err over {len(ref)} steps × K={m["K"]} = {err:.2e} (last step {per_step[-1]:.2e}); {time.time() - t:.1f}s', flush=True)
    return err


if __name__ == '__main__':
    if sys.argv[1] == 'validate':
        for dt in ('c128', 'c64'):
            validate(int(sys.argv[2]), dt)
