"""2026-09-23 helper: one line per design — cases correct at steady state (every trip from max(settle,…) to the horizon, final
targets extended) and at t = horizon only, plus per-case output level at the horizon. usage: python scorecard.py <eval.json>..."""
import json, sys
for p in sys.argv[1:]:
    d = json.load(open(p))
    spec = json.load(open(p.replace('eval_', '').replace('_10000.json', '_spec.json')))
    thr = 0.5 * (spec['I_hi'] + spec['I_lo'])
    names = d['names']
    persistent = sum(r['survived_to'] >= d['horizon'] and r['acc_train_window'] > 0.999 for r in d['results'])
    final_ok = 0
    outs = []
    for c, r in zip(spec['cases'], d['results']):
        last = {}
        for tg in c['targets']:
            if tg['cell'] not in last or tg['t_to'] >= last[tg['cell']]['t_to']:
                last[tg['cell']] = tg
        I = r['trace'][-1]['I']
        ok = all((I[names.index(k)] > thr) == bool(tg['value']) for k, tg in last.items())
        final_ok += ok
        o = [k for k in names if k.startswith('o') or k in ('out', 'Q', 'dst')] or names
        outs.append(f"{c['name']}:" + '/'.join(f'{I[names.index(k)]:.2f}' for k in o))
    print(f"{d['tag']:<28} persistent {persistent}/{len(d['results'])}  correct@{d['horizon']} {final_ok}/{len(d['results'])}  G0 {d['G0']:.2f}  | {' '.join(outs)}")
