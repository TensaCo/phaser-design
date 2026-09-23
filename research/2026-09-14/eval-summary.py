"""Print per-case cell intensities at selected trips from an 08-eval JSON (2026-09-23 helper for the report tables).
usage: python eval-summary.py out/08/eval_<tag>_10000.json [t1,t2,...]"""
import json, sys
d = json.load(open(sys.argv[1]))
ts = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else '1,60,120,240,1000,10000').split(',')]
names = d['names']
print(d['tag'], 'G0', round(d['G0'], 3), 'cells', ' '.join(names))
for r in d['results']:
    tr = {s['t']: s for s in r['trace']}
    avail = sorted(tr)
    line = []
    for t in ts:
        tt = min(avail, key=lambda a: abs(a - t))
        line.append(f"t{tt}: " + ' '.join(f'{v:.2f}' for v in tr[tt]['I']) + f" bg {tr[tt]['bg']:.2f}")
    print(f"{r['case']:<14} surv {r['survived_to']:>5} acc {r['acc_train_window']:.2f} | " + ' | '.join(line))
