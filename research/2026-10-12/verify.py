"""Strict every-trip verification of designed static programs on the GPU twin in float64 (2026-10-12).

Stricter than 26-verify.ts: (1) every target window is checked at EVERY trip (the intermediate states of latch cases too),
(2) the final value of each target cell must then hold at every trip to the horizon H. Designs that share a twin, media and
case set are verified together (D axis). The float64 twin matches the JS simulator to ~1e-13 per 200 trips (gtwin.validate);
verify.ts repeats the check in JS for the designs reported.

Non-idealities: --noise (additive gain noise, mean intensity per sample per trip, as JS 'additive-gaussian'), --jitter (static
per-pixel SLM phase error, rad rms), --flicker RAD:PERIOD (fresh per-pixel phase error every PERIOD trips), --g0scale.
Noise realisations come from torch's generator, not JS mulberry32: statistically, not bitwise, equivalent.

usage: python verify.py <spec.json>... [--H 100000] [--noise 0] [--jitter 0] [--flicker 0:0] [--g0scale 1] [--out f.json]
"""
import argparse, glob, json, math, os, sys, time
from collections import defaultdict
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gtwin import GTwin, TAU


def local(p):
    if os.path.exists(p):
        return p
    for d in (os.path.join(HERE, 'out', 'designs'), os.path.join(HERE, '..', '2026-09-14', 'out', '08')):
        q = os.path.join(d, os.path.basename(p))
        if os.path.exists(q):
            return q
    raise FileNotFoundError(p)


def group_key(s):
    return json.dumps([s['twin'], s.get('Ld') or 0, s['s'], s['Ia'], s['Ig'], s.get('kerr', 0), bool(s.get('linear')), s['cells'], s['cases']], sort_keys=True)


def verify_group(specs, a, gen):
    tw = GTwin(specs[0]['twin'], 'c128')
    s0 = specs[0]
    tw.set_media(Ig=s0['Ig'], Ld=s0.get('Ld') or 0.0, s=s0['s'], Ia=s0['Ia'], kerr=s0.get('kerr', 0.0), linear=bool(s0.get('linear')), Glin=s0.get('Glin', 1.0))
    n, dev, cdt, rdt = tw.n, tw.dev, tw.cdt, tw.rdt
    D = len(specs)
    names = list(s0['cells'])
    K = len(names)
    cases = s0['cases']
    B = len(cases)
    A = torch.zeros(K, n * n, dtype=rdt)
    for k, (x0, y0, w) in enumerate(s0['cells'].values()):
        for j in range(w):
            A[k, (y0 + j) * n + x0:(y0 + j) * n + x0 + w] = 1.0 / (w * w)
    A = A.to(dev)
    thr = 0.5 * (s0['I_hi'] + s0['I_lo'])
    rd = lambda p: torch.from_numpy(np.fromfile(local(p), dtype=np.float64).reshape(tw.res['slm'])).to(dev)
    masks = {'slm': torch.stack([rd(s['mask_file']) for s in specs])}
    if 'amp' in tw.res:
        masks['amp'] = torch.stack([rd(s['amp_file']) for s in specs])
    G0 = torch.tensor([s['G0'] * a.g0scale for s in specs], dtype=rdt, device=dev)
    E = torch.zeros(D, B, n * n, dtype=cdt, device=dev)
    for b, c in enumerate(cases):
        for nm in c.get('init_on', []):
            E[:, b, A[names.index(nm)] > 0] = math.sqrt(s0['I_init'])
    E = E.reshape(D, B, n, n)
    inj = {}
    for b, c in enumerate(cases):
        for j in c['inject']:
            inj.setdefault(j['t'], torch.zeros(B, n * n, dtype=cdt, device=dev))
            inj[j['t']][b, A[names.index(j['cell'])] > 0] += j['amp'] * complex(math.cos(j['phase']), math.sin(j['phase']))
    inj = {t: v.reshape(1, B, n, n) for t, v in inj.items()}
    # targets: windows (t_from..t_to, value) and the final value per (case, cell), held from the end of its last window to H
    Tw = max(tg['t_to'] for c in cases for tg in c['targets'])
    H = max(a.H, Tw)
    win = torch.full((Tw + 1, B, K), float('nan'), dtype=rdt, device=dev)
    final = torch.full((B, K), float('nan'), dtype=rdt, device=dev)
    final_from = torch.full((B, K), H + 1, dtype=torch.long, device=dev)
    for b, c in enumerate(cases):
        last = {}
        for tg in c['targets']:
            k = names.index(tg['cell'])
            win[tg['t_from']:tg['t_to'] + 1, b, k] = tg['value']
            if tg['cell'] not in last or tg['t_to'] > last[tg['cell']]['t_to']:
                last[tg['cell']] = tg
        for cell, tg in last.items():
            k = names.index(cell)
            final[b, k] = tg['value']
            final_from[b, k] = tg['t_from']  # inside the window the window target applies; after it, the final value
    first_bad = torch.full((D, B), -1, dtype=torch.long, device=dev)
    nbad = torch.zeros(D, B, dtype=torch.long, device=dev)
    minOn = torch.full((D, B, K), float('inf'), dtype=rdt, device=dev)
    maxOff = torch.zeros(D, B, K, dtype=rdt, device=dev)
    lo = torch.full((D, B, K), float('inf'), dtype=rdt, device=dev)
    hi = torch.zeros(D, B, K, dtype=rdt, device=dev)
    fl_rad, fl_per = (float(x) for x in a.flicker.split(':'))
    base = {k: v.clone() for k, v in masks.items()}
    if a.jitter:
        base['slm'] = base['slm'] + a.jitter * torch.randn(base['slm'].shape, generator=gen, device=dev, dtype=rdt)
    tr = tw.transmissions(base)
    t0 = time.time()
    for t in range(1, H + 1):
        if fl_rad and (t - 1) % int(fl_per) == 0:
            m = dict(base)
            m['slm'] = base['slm'] + fl_rad * torch.randn(base['slm'].shape, generator=gen, device=dev, dtype=rdt)
            tr = tw.transmissions(m)
        E = tw.trip(E, tr, G0, inject=inj.get(t), noise=a.noise, gen=gen)
        if s0.get('linear'):
            raise NotImplementedError('linear designs: use 08-eval.ts')
        I = (E.real ** 2 + E.imag ** 2).reshape(D, B, -1) @ A.T  # (D,B,K)
        tgt = win[t] if t <= Tw else torch.full((B, K), float('nan'), dtype=rdt, device=dev)
        ext = (t >= final_from) & ~torch.isnan(final) & (torch.isnan(tgt) if t <= Tw else torch.ones_like(final, dtype=torch.bool))
        want = torch.where(~torch.isnan(tgt), tgt, torch.where(ext, final, torch.full_like(final, float('nan'))))
        chk = ~torch.isnan(want)
        on = (I > thr).to(rdt)
        bad = ((on != torch.nan_to_num(want)) & chk).any(-1)  # (D,B)
        nbad += bad
        first_bad = torch.where((first_bad < 0) & bad, torch.full_like(first_bad, t), first_bad)
        fin = ext & (final == 1)
        minOn = torch.where(fin, torch.minimum(minOn, I), minOn)
        fin0 = ext & (final == 0)
        maxOff = torch.where(fin0, torch.maximum(maxOff, I), maxOff)
        if t > 0.9 * H:
            lo, hi = torch.minimum(lo, I), torch.maximum(hi, I)
        if t % 20000 == 0:
            print(f'  t={t} [{time.time() - t0:.0f}s] failing designs so far: {int((nbad.sum(1) > 0).sum())}/{D}', flush=True)
    res = []
    for d, s in enumerate(specs):
        rows = []
        for b, c in enumerate(cases):
            rows.append(dict(case=c['name'], ok=int(nbad[d, b]) == 0, n_bad_trips=int(nbad[d, b]), first_violation=int(first_bad[d, b]) if first_bad[d, b] >= 0 else None,
                             min_on=float(minOn[d, b][torch.isfinite(minOn[d, b])].min()) if torch.isfinite(minOn[d, b]).any() else None,
                             max_off=float(maxOff[d, b][final[b] == 0].max()) if (final[b] == 0).any() else None,
                             ripple=float((hi[d, b] - lo[d, b]).max())))
        res.append(dict(tag=s['tag'], spec=s['_path'], H=H, noise=a.noise, jitter=a.jitter, flicker=a.flicker, g0scale=a.g0scale,
                        passed=sum(r['ok'] for r in rows), cases=len(rows), all_ok=all(r['ok'] for r in rows), rows=rows))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('specs', nargs='+')
    ap.add_argument('--H', type=int, default=10000)
    ap.add_argument('--noise', type=float, default=0.0)
    ap.add_argument('--jitter', type=float, default=0.0)
    ap.add_argument('--flicker', default='0:0')
    ap.add_argument('--g0scale', type=float, default=1.0)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    paths = sorted({p for g in a.specs for p in glob.glob(g)})
    groups = defaultdict(list)
    for p in paths:
        s = json.load(open(p))
        s['_path'] = p
        if s.get('task') == 'osc':  # periodic targets: regenerate the schedule out to the horizon (no "final value")
            from design import task_osc
            s['cells'], s['cases'] = task_osc(dict(s['params'], T=max(a.H, s['T_train'])))
        groups[group_key(s)].append(s)
    gen = torch.Generator(device='cuda').manual_seed(a.seed)
    allres = []
    for specs in groups.values():
        t0 = time.time()
        r = verify_group(specs, a, gen)
        for x in r:
            print(f"{x['tag']}: {x['passed']}/{x['cases']} cases {'PASS' if x['all_ok'] else 'fail'} to H={x['H']}"
                  + ''.join(f" | {row['case']}:{'ok' if row['ok'] else 'x@' + str(row['first_violation'])}" for row in x['rows']), flush=True)
        print(f'  group of {len(specs)} verified in {time.time() - t0:.0f}s', flush=True)
        allres += r
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(allres, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
