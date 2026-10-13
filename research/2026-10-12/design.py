"""Batched static-program design on the GPU (2026-10-12). D designs (different seeds / starting pump) of ONE task are
optimised together through gtwin.GTwin: fields are (D, B, n, n), parameters carry a leading D axis, losses are per design
and summed (Adam is element-wise, so designs do not interact). Task builders are those of ../2026-09-14/08-design.py plus
the latch formulations below. Every saved design is a spec in the 08 format (+ `arch`) and is re-verified by verify.py
(GPU, float64, every trip) and verify.ts (JS simulator) — nothing reported comes from the float32 design rollout.

usage: python design.py <task> '<json overrides>'     (D = len(seeds); "seeds": [..], optional "G0s": [..] per design)
"""
import importlib.util, json, math, os, sys, time
import numpy as np
import torch
from torch.utils.checkpoint import checkpoint

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gtwin import GTwin, TAU

_s = importlib.util.spec_from_file_location('d08', os.path.join(HERE, '..', '2026-09-14', '08-design.py'))
d08 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(d08)
torch.set_default_dtype(torch.float32)  # 08-design imports twin.py, which sets float64 globally
TASKS = dict(d08.TASKS)
OUT = os.environ.get('PHASER_OUT', os.path.join(HERE, 'out', 'designs'))


# ───────────────────────────── new tasks ─────────────────────────────

def _pulse(cell, t0, length, amp, phase=0.0):
    """a held input: the same coherent injection on `length` consecutive trips (a CW input switched on for length × 0.67 ns)."""
    return [dict(t=t, cell=cell, amp=amp, phase=phase) for t in range(t0, t0 + length)]


def task_srff(P):
    """set/reset flip-flop from two mutually inhibiting cells Q, Qb (cross-gain), each with an excitatory input S → Q, R → Qb.
    Exactly one of Q, Qb is ON after the initial write. A held pulse on S (R) must leave Q = 1 (0) after it ends, and S, R must
    go dark again (they are transient inputs, not stored bits). Cases cover both starting states and both orders."""
    w, d = P['w'], P['dist']
    c = P.get('centre', 32) - w // 2
    cells = {'S': [c - d - d // 2, c, w], 'Q': [c - d // 2, c, w], 'Qb': [c + d - d // 2, c, w], 'R': [c + 2 * d - d // 2, c, w]}
    if P.get('vertical_io'):  # S above Q, R above Qb (keeps the input cells out of the Q–Qb axis)
        cells['S'] = [c - d // 2, c - d, w]
        cells['R'] = [c + d - d // 2, c - d, w]
    rails = [f'rail{i}' for i in range(P.get('rails', 0))]
    for i, r in enumerate(rails):
        cells[r] = [c + (i - (len(rails) - 1) / 2).__int__() * (w + 2), c + d, w]
    T, tp, pl, st, gap = P['T'], P['t_pulse'], P['pulse_len'], P['settle'], P.get('gap', 120)
    A, Ap = P['inj_amp'], P.get('pulse_amp', P['inj_amp'] * 0.3)
    t2 = tp + gap
    rail = [j for r in rails for j in _pulse(r, 1, 1, A)]
    wQ, wQb = [dict(t=1, cell='Q', amp=A, phase=0.0)], [dict(t=1, cell='Qb', amp=A, phase=0.0)]
    S = lambda t: _pulse('S', t, pl, Ap)
    R = lambda t: _pulse('R', t, pl, Ap)

    def tg(q_segments):
        """q_segments: [(t_from, t_to, q)] → targets for Q, Qb (complementary), S and R dark outside their pulses."""
        out = []
        for a, b, q in q_segments:
            out += [dict(cell='Q', value=q, t_from=a, t_to=b), dict(cell='Qb', value=1 - q, t_from=a, t_to=b)]
        return out

    def quiet(pulses):
        """S/R must be OFF from `st` trips after each pulse ends until the next pulse on that cell (or T)."""
        out = []
        for cell in ('S', 'R'):
            ts = sorted(t for t, cc in pulses if cc == cell)
            windows = [(st, (ts[0] - 1) if ts else T)] + [(t + pl + st, (ts[i + 1] - 1) if i + 1 < len(ts) else T) for i, t in enumerate(ts)]
            out += [dict(cell=cell, value=0, t_from=a, t_to=b) for a, b in windows if b >= a]
        return out

    cases = [
        dict(name='hold1', inject=rail + wQ, targets=tg([(st, T, 1)]) + quiet([])),
        dict(name='hold0', inject=rail + wQb, targets=tg([(st, T, 0)]) + quiet([])),
        dict(name='set_from0', inject=rail + wQb + S(tp), targets=tg([(st, tp - 1, 0), (tp + pl + st, T, 1)]) + quiet([(tp, 'S')])),
        dict(name='set_from1', inject=rail + wQ + S(tp), targets=tg([(st, T, 1)]) + quiet([(tp, 'S')])),
        dict(name='reset_from1', inject=rail + wQ + R(tp), targets=tg([(st, tp - 1, 1), (tp + pl + st, T, 0)]) + quiet([(tp, 'R')])),
        dict(name='reset_from0', inject=rail + wQb + R(tp), targets=tg([(st, T, 0)]) + quiet([(tp, 'R')])),
        dict(name='set_then_reset', inject=rail + wQb + S(tp) + R(t2), targets=tg([(tp + pl + st, t2 - 1, 1), (t2 + pl + st, T, 0)]) + quiet([(tp, 'S'), (t2, 'R')])),
        dict(name='reset_then_set', inject=rail + wQ + R(tp) + S(t2), targets=tg([(tp + pl + st, t2 - 1, 0), (t2 + pl + st, T, 1)]) + quiet([(tp, 'R'), (t2, 'S')])),
    ]
    for c_ in cases:
        c_['init_on'] = []
        if P.get('preserve_rails'):
            c_['targets'] += [dict(cell=r, value=1, t_from=st, t_to=T) for r in rails]
    return cells, cases


def task_latch2(P):
    """single bistable Q with an excitatory set input S and an inhibitory reset input R, both HELD for pulse_len trips and
    required to be dark afterwards (08-design task_latch used one-trip pulses and never asked S/R to go dark)."""
    w, d = P['w'], P['dist']
    c = P.get('centre', 32) - w // 2
    cells = {'S': [c - d, c, w], 'Q': [c, c, w], 'R': [c + d, c, w]}
    T, tp, pl, st, gap = P['T'], P['t_pulse'], P['pulse_len'], P['settle'], P.get('gap', 120)
    A, Ap = P['inj_amp'], P.get('pulse_amp', P['inj_amp'] * 0.3)
    t2 = tp + gap
    q1 = [dict(t=1, cell='Q', amp=A, phase=0.0)]
    S = lambda t: _pulse('S', t, pl, Ap)
    R = lambda t: _pulse('R', t, pl, Ap, P.get('reset_phase', 0.0))
    Qt = lambda segs: [dict(cell='Q', value=q, t_from=a, t_to=b) for a, b, q in segs]

    def quiet(pulses):
        out = []
        for cell in ('S', 'R'):
            ts = sorted(t for t, cc in pulses if cc == cell)
            windows = [(st, (ts[0] - 1) if ts else T)] + [(t + pl + st, (ts[i + 1] - 1) if i + 1 < len(ts) else T) for i, t in enumerate(ts)]
            out += [dict(cell=cell, value=0, t_from=a, t_to=b) for a, b in windows if b >= a]
        return out

    cases = [
        dict(name='hold0', inject=[], targets=Qt([(st, T, 0)]) + quiet([])),
        dict(name='hold1', inject=q1, targets=Qt([(st, T, 1)]) + quiet([])),
        dict(name='set_from0', inject=S(tp), targets=Qt([(st, tp - 1, 0), (tp + pl + st, T, 1)]) + quiet([(tp, 'S')])),
        dict(name='set_from1', inject=q1 + S(tp), targets=Qt([(st, T, 1)]) + quiet([(tp, 'S')])),
        dict(name='reset_from1', inject=q1 + R(tp), targets=Qt([(st, tp - 1, 1), (tp + pl + st, T, 0)]) + quiet([(tp, 'R')])),
        dict(name='reset_from0', inject=R(tp), targets=Qt([(st, T, 0)]) + quiet([(tp, 'R')])),
        dict(name='set_then_reset', inject=S(tp) + R(t2), targets=Qt([(tp + pl + st, t2 - 1, 1), (t2 + pl + st, T, 0)]) + quiet([(tp, 'S'), (t2, 'R')])),
        dict(name='reset_then_set', inject=q1 + R(tp) + S(t2), targets=Qt([(tp + pl + st, t2 - 1, 0), (t2 + pl + st, T, 1)]) + quiet([(tp, 'R'), (t2, 'S')])),
    ]
    for c_ in cases:
        c_['init_on'] = []
    return cells, cases


def task_osc(P):
    """autonomous clock: cells A and B must alternate (A ON for the first half of each period, B for the second) after one
    start pulse into A at t=1, with `margin` trips of slack around each transition. Exp. 21b found cross-gain limit cycles
    (periods 160–4100 trips); this asks for one with a set period and a clean two-phase output."""
    w, d, Pd, mg, T = P['w'], P['dist'], P['period'], P.get('margin', 20), P['T']
    c = P.get('centre', 32) - w // 2
    cells = {'A': [c - d // 2, c, w], 'B': [c + d - d // 2, c, w]}
    for i in range(P.get('rails', 0)):
        cells[f'rail{i}'] = [c + (i - (P['rails'] - 1) / 2).__int__() * (w + 2), c + d, w]
    rails = [k for k in cells if k.startswith('rail')]
    t0 = P.get('t_start', Pd)  # first period is free (start-up)
    tg = []
    for k in range((T - t0) // Pd + 1):
        a = t0 + k * Pd
        for (lo, hi, va) in ((a + mg, a + Pd // 2 - mg, 1), (a + Pd // 2 + mg, a + Pd - mg, 0)):
            lo, hi = max(lo, 1), min(hi, T)
            if hi >= lo:
                tg += [dict(cell='A', value=va, t_from=lo, t_to=hi), dict(cell='B', value=1 - va, t_from=lo, t_to=hi)]
    inj = [dict(t=1, cell='A', amp=P['inj_amp'], phase=0.0)] + [dict(t=1, cell=r, amp=P['inj_amp'], phase=0.0) for r in rails]
    return cells, [dict(name='run', init_on=[], inject=inj, targets=tg)]


TASKS['osc'] = task_osc
TASKS['srff'] = task_srff
TASKS['latch2'] = task_latch2


# ───────────────────────────── batched problem ─────────────────────────────

class Batch:
    def __init__(self, P):
        self.P = P
        dt = P.get('dtype', 'c64')
        fused_ok = dt == 'c64' and not P.get('linear') and not P.get('kerr') and P.get('fused', True)
        self.tw = GTwin(P['twin'], dt, fused=fused_ok and GTwin.grid_n(P['twin']) == 64)
        tw = self.tw
        lin = bool(P.get('linear'))
        tw.set_media(Ig=P['Ig'], Ld=P.get('Ld') or 0.0, s=P['s'], Ia=P['Ia'], kerr=P.get('kerr', 0.0), linear=lin, Glin=P.get('Glin', 1.0))
        n = self.n = tw.n
        dev, rdt, cdt = tw.dev, tw.rdt, tw.cdt
        self.cells = P['cells']
        self.names = list(self.cells)
        K = len(self.names)
        cases = P['cases']
        B = self.B = len(cases)
        seeds = P['seeds']
        D = self.D = len(seeds)
        # cell averaging matrix (K, n*n)
        A = torch.zeros(K, n * n, dtype=rdt)
        for k, (x0, y0, w) in enumerate(self.cells.values()):
            for j in range(w):
                A[k, (y0 + j) * n + x0:(y0 + j) * n + x0 + w] = 1.0 / (w * w)
        self.Acell = A.to(dev)
        self.offcell = (A.sum(0) == 0).to(dev)
        E0 = torch.zeros(B, n * n, dtype=cdt)
        for b, c in enumerate(cases):
            for nm in c.get('init_on', []):
                E0[b, A[self.names.index(nm)] > 0] = math.sqrt(P['I_init'])
        self.E0 = E0.reshape(1, B, n, n).to(dev)
        inj = {}
        for b, c in enumerate(cases):
            for j in c['inject']:
                t = j['t']
                if t not in inj:
                    inj[t] = torch.zeros(B, n * n, dtype=cdt)
                inj[t][b, A[self.names.index(j['cell'])] > 0] += j['amp'] * complex(math.cos(j['phase']), math.sin(j['phase']))
        self.inj = {t: v.reshape(1, B, n, n).to(dev) for t, v in inj.items()}
        self.T = max(max((tg['t_to'] for c in cases for tg in c['targets']), default=1), max(inj, default=0))
        tgt = torch.full((self.T + 1, B, K), float('nan'), dtype=rdt)
        for b, c in enumerate(cases):
            for tg in c['targets']:
                tgt[tg['t_from']:tg['t_to'] + 1, b, self.names.index(tg['cell'])] = tg['value']
        self.tgt = tgt.to(dev)
        # parameters, one slice per design
        ry, rx = tw.res['slm']
        th = []
        for s in seeds:
            g = torch.Generator().manual_seed(int(s))
            th.append(math.pi + P.get('init_noise', 0.05) * torch.randn(ry, rx, generator=g))
        self.theta = torch.nn.Parameter(torch.stack(th).to(rdt).to(dev))
        G0s = P.get('G0s') or [P['G0']] * D
        self.logG = torch.nn.Parameter(torch.log(torch.tensor(G0s, dtype=rdt) - 1).to(dev))
        self.z_amp = None
        if 'amp' in tw.res:
            ay, ax = tw.res['amp']
            z0 = np.full((ay, ax), float(P.get('amp_bg', -4.0)))
            mg = P.get('amp_margin', 0)
            for (x0, y0, w) in self.cells.values():
                z0[max(0, y0 - mg):y0 + w + mg, max(0, x0 - mg):x0 + w + mg] = 4.0
            self.z_amp = torch.nn.Parameter(torch.tensor(np.repeat(z0[None], D, 0), dtype=rdt, device=dev))

    def masks(self, theta, z):
        m = {'slm': theta}
        if z is not None:
            m['amp'] = TAU * 0.999 * torch.sigmoid(z)
        return m

    def cellI(self, E):
        I = (E.real ** 2 + E.imag ** 2).reshape(self.D, self.B, -1)
        return I @ self.Acell.T, I.masked_fill(~self.offcell, 0).amax(-1)

    def rollout(self, theta, z, logG, T=None, chunk=None, noise=0.0):
        T = T or self.T
        if chunk is None:  # checkpoint only when the stored activations would exceed ~16 GB (≈ 8 fields per trip kept)
            per_trip = 8 * self.D * self.B * self.n * self.n * (8 if self.tw.cdt == torch.complex64 else 16)
            chunk = self.P.get('chunk') or (10 if per_trip * T > 16e9 or self.tw.segs is None else 0)
        G0 = 1 + torch.exp(logG)
        E = self.E0.expand(self.D, -1, -1, -1).clone()
        if noise:
            E = E + noise * torch.complex(torch.randn_like(E.real), torch.randn_like(E.real))
        lin = bool(self.P.get('linear'))
        P0 = (E.real ** 2 + E.imag ** 2).sum((-2, -1)).detach()
        c0, _ = self.cellI(E)
        cI, bgs, dEs = [c0], [], []

        def run(E, theta, z, G0, P0, t0, t1):
            tr = self.tw.transmissions(self.masks(theta, z))
            rec, bg, de = [], [], []
            for t in range(t0, t1):
                inj = self.inj.get(t)
                Ep = E
                E = self.tw.trip(E, tr, G0, inject=inj)
                if lin:  # global gain clamp (exact for linear optics), as 08-design
                    Pt = (E.real ** 2 + E.imag ** 2).sum((-2, -1))
                    if inj is not None:
                        P0 = torch.maximum(P0, Pt.detach())
                    E = E * torch.sqrt(torch.where(Pt > 1e-30, P0 / Pt.clamp_min(1e-30), torch.zeros_like(Pt)))[..., None, None]
                de.append(((E - Ep).abs() ** 2).sum((-2, -1)) / ((E.abs() ** 2).sum((-2, -1)) + 1e-12))
                c, b = self.cellI(E)
                rec.append(c)
                bg.append(b)
            return E, P0, torch.stack(rec), torch.stack(bg), torch.stack(de)

        if not chunk:
            E, P0, r, b, d = run(E, theta, z, G0, P0, 1, T + 1)
            cI.append(r); bgs.append(b); dEs.append(d)
        else:
            for t0 in range(1, T + 1, chunk):
                t1 = min(T + 1, t0 + chunk)
                E, P0, r, b, d = checkpoint(run, E, theta, z, G0, P0, t0, t1, use_reentrant=False)
                cI.append(r); bgs.append(b); dEs.append(d)
        return torch.cat([cI[0][None]] + cI[1:], 0), torch.cat(bgs, 0), torch.cat(dEs, 0)  # (T+1,D,B,K) (T,D,B) (T,D,B)

    def loss(self, cI, bg, dE):
        P = self.P
        tgt = self.tgt[:cI.shape[0]][:, None]  # (T+1,1,B,K)
        m1, m0 = (tgt == 1), (tgt == 0)
        cnt = (m1 | m0).sum((0, 2, 3)).clamp_min(1)  # same for every design
        if P.get('loss_log'):  # hinge on log intensity: bounded gradients when cells flood, a restoring push when the field dies
            lc = torch.log(cI.clamp_min(1e-6))
            l_on = (torch.relu(math.log(P['I_hi']) - lc) ** 2 * m1).sum((0, 2, 3))
            l_off = (torch.relu(lc - math.log(P['I_lo'])) ** 2 * m0).sum((0, 2, 3))
        else:
            l_on = (torch.relu(P['I_hi'] - cI) ** 2 * m1).sum((0, 2, 3))
            l_off = (torch.relu(cI - P['I_lo']) ** 2 * m0).sum((0, 2, 3))
        l = (l_on + l_off) / cnt
        L = l + P.get('w_bg', 0) * (torch.relu(bg - P['bg_max']) ** 2).mean((0, 2))
        if P.get('w_stat', 0) > 0:
            k0 = int(cI.shape[0] * (1 - P.get('stat_frac', 0.4)))
            L = L + P['w_stat'] * (((cI[k0 + 1:] - cI[k0:-1]) ** 2).mean((0, 2, 3)) + dE[k0:].mean((0, 2)))
        if P.get('w_margin', 0) > 0:  # optional: reward distance from threshold on every target sample (robustness)
            thr = 0.5 * (P['I_hi'] + P['I_lo'])
            mm = (torch.relu(1.5 * P['I_hi'] - cI) * m1 + torch.relu(cI - 0.5 * P['I_lo']) * m0).sum((0, 2, 3)) / cnt
            L = L + P['w_margin'] * mm / thr
        return L, l

    def accuracy(self, cI):
        thr = 0.5 * (self.P['I_hi'] + self.P['I_lo'])
        tgt = self.tgt[:cI.shape[0]][:, None].expand_as(cI)
        m = ~torch.isnan(tgt)
        ok = ((cI > thr).to(cI.dtype) == torch.nan_to_num(tgt)) & m
        return ok.sum((0, 2, 3)) / m.sum((0, 2, 3))

    def train(self, iters, lr):
        P = self.P
        groups = [{'params': [self.theta], 'lr': lr}, {'params': [self.logG], 'lr': lr * 0.1 if P.get('learn_gain', True) else 0.0}]
        if self.z_amp is not None:
            groups.append({'params': [self.z_amp], 'lr': P.get('lr_amp', lr * 4)})
        opt = torch.optim.Adam(groups)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, iters, eta_min=lr * P.get('lr_min_frac', 0.1)) if P.get('cosine', True) else None
        D = self.D
        best = torch.full((D,), float('inf'), device=self.tw.dev)
        self.best = (self.theta.detach().clone(), self.logG.detach().clone(), None if self.z_amp is None else self.z_amp.detach().clone())
        self.best_acc = torch.zeros(D, device=self.tw.dev)
        hist = []
        t0 = time.time()
        jit = P.get('jitter', 0.0)
        for it in range(iters):
            opt.zero_grad(set_to_none=True)
            th = self.theta + jit * torch.randn_like(self.theta) if jit else self.theta
            cI, bg, dE = self.rollout(th, self.z_amp, self.logG, noise=P.get('noise', 0.0))
            L, lt = self.loss(cI, bg, dE)
            L.sum().backward()
            opt.step()
            if sched:
                sched.step()
            with torch.no_grad():
                self.logG.clamp_(math.log(0.05), math.log(6))
                acc = self.accuracy(cI.detach())
                better = L.detach() < best
                best = torch.where(better, L.detach(), best)
                self.best_acc = torch.where(better, acc, self.best_acc)
                for k, src in enumerate((self.theta, self.logG, self.z_amp)):
                    if src is not None:
                        self.best[k][better] = src.detach()[better]
            if it % P.get('log_every', 20) == 0 or it == iters - 1:
                Lc, ac = L.detach().cpu().numpy(), acc.cpu().numpy()
                hist.append(dict(it=it, loss=Lc.tolist(), acc=ac.tolist()))
                print(f"it {it} loss min {Lc.min():.3e} med {np.median(Lc):.3e} | acc max {ac.max():.3f} med {np.median(ac):.3f} | n(acc=1) {(ac >= 1).sum()}/{D} [{time.time() - t0:.0f}s]", flush=True)
        return hist

    def save(self, tag, hist):
        os.makedirs(OUT, exist_ok=True)
        th, lg, za = self.best
        keep = ('task', 'twin', 'Ig', 'Ld', 's', 'Ia', 'kerr', 'I_init', 'I_hi', 'I_lo', 'linear', 'Glin', 'cells', 'cases')
        out = []
        for d, seed in enumerate(self.P['seeds']):
            base = os.path.join(OUT, f'{tag}_d{d}')
            np.asarray(torch.remainder(th[d], TAU).double().cpu().numpy()).tofile(base + '_mask.f64')
            spec = {k: self.P[k] for k in keep if k in self.P}
            spec.update(tag=f'{tag}_d{d}', run=tag, seed=seed, n=self.n, mask_file=base + '_mask.f64', G0=float(1 + torch.exp(lg[d])),
                        T_train=self.T, design_acc=float(self.best_acc[d]), params={k: v for k, v in self.P.items() if k not in ('cells', 'cases', 'eval_cases')})
            if za is not None:
                (TAU * 0.999 * torch.sigmoid(za[d])).double().cpu().numpy().tofile(base + '_amp.f64')
                spec.update(amp_file=base + '_amp.f64', amp_dark=0.0)
            if 'eval_cases' in self.P:
                spec['train_cases'], spec['cases'] = spec['cases'], self.P['eval_cases']
            json.dump(spec, open(base + '_spec.json', 'w'), indent=1)
            out.append(base + '_spec.json')
        json.dump(dict(tag=tag, specs=out, history=hist), open(os.path.join(OUT, f'{tag}_run.json'), 'w'))
        print('saved', len(out), 'designs:', os.path.join(OUT, tag + '_d*'), flush=True)
        return out


BASE = dict(d08.BASE, twin='A64s_amp', dtype='c64', iters=1000, lr=0.05, seeds=[0, 1, 2, 3, 4, 5, 6, 7])

if __name__ == '__main__':
    task = sys.argv[1]
    P = dict(BASE)
    P.update(json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
    cells, cases = TASKS[task](P)
    P.update(task=task, cells=cells, cases=cases)
    tag = P.get('tag', task)
    torch.manual_seed(P.get('torch_seed', 0))
    b = Batch(P)
    print(f'{tag}: {len(cells)} cells, {len(cases)} cases, T={b.T}, D={b.D}, twin {P["twin"]} {P["dtype"]}{" fused" if b.tw.segs is not None else ""}', flush=True)
    hist = b.train(P['iters'], P['lr'])
    b.save(tag, hist)
