"""Experiment 43 (2026-10-12): the modes-per-unit equivalence beyond 65k modes (Exp. 31 stopped at 256²).

run:     python 43-scale.py run <n> <K> <steps> <bin> [tag]     → out/43/{tag}_{uniform,bits}.f32 (+ .json)
         Exp. 31 reservoir (Apre_lin ring, global gain G0 1.6, input amplitude 6, relay aperture ∝ n) on the GPU engine,
         uniform and bits streams of 30-lib.streams (the inputs of Exp. 31), features binned bin×bin.
score:   python 43-scale.py score <tag> <bin2> [feats_label]      → out/43/scores.json[tag/bin2]
         capacity metrics (30-lib protocol, GPU ridge) after a further bin2×bin2 binning of the saved features.
digital: python 43-scale.py esn <N> [N …]                         → out/43/esn_N{N}.json  (30-lib ESN grid for N > 512)
"""
import json, os, sys, time
import numpy as np
import torch
import res_lib as RL

D = os.path.join(RL.OUT, '43')
os.makedirs(D, exist_ok=True)
cmd = sys.argv[1]

if cmd == 'run':
    from res_gpu import Reservoir
    n, K, steps, b = (int(x) for x in sys.argv[2:6])
    tag = sys.argv[6] if len(sys.argv) > 6 else f'n{n}_K{K}_s{steps}_b{b}'
    u, bb = RL.L30.streams(steps)
    R = Reservoir(n)
    t = time.time()
    U = np.stack([u, 0.5 * bb])[:, :, None]
    path = {s: os.path.join(D, f'{tag}_{s}.f32') for s in ('uniform', 'bits')}
    nb = (n // b) ** 2
    mm = np.lib.format.open_memmap(os.path.join(D, f'{tag}_tmp.npy'), mode='w+', dtype=np.float32, shape=(2, steps, nb))
    R.run(U, K, R.meta['inputAmp'], bin=b, out=mm)
    for i, s in enumerate(('uniform', 'bits')):
        mm[i].tofile(path[s])
        json.dump(dict(n=n, K=K, steps=steps, bin=b, modes=n * n, features=nb, t_rt=R.meta['roundTripTime'], G0=R.meta['G0'],
                       Is=R.meta['Is'], inputAmp=R.meta['inputAmp'], secs=time.time() - t, meanF=float(mm[i, RL.WASH:].mean())),
                  open(os.path.join(D, f'{tag}_{s}.json'), 'w'), indent=1)
    del mm; os.remove(os.path.join(D, f'{tag}_tmp.npy'))
    print(f'{tag}: {time.time() - t:.0f} s', flush=True)

elif cmd == 'score':
    tag, b2 = sys.argv[2], int(sys.argv[3])
    label = sys.argv[4] if len(sys.argv) > 4 else f'b{b2}'
    Fu, m = RL.load(tag, 'uniform'); Fb, _ = RL.load(tag, 'bits')
    Fu, Fb = RL.binf(Fu, b2), RL.binf(Fb, b2)
    u, bb = RL.L30.streams(m['steps'])
    t = time.time()
    r = RL.capacity_score(Fu, Fb, u, bb)
    r.update(tag=tag, n=m['n'], K=m['K'], modes=m['modes'], features=int(Fu.shape[1]), modes_per_feature=m['modes'] / Fu.shape[1],
             steps=m['steps'], secs=time.time() - t)
    p = os.path.join(D, 'scores.json')
    allr = json.load(open(p)) if os.path.exists(p) else {}
    allr[f'{tag}/{label}'] = r
    json.dump(allr, open(p, 'w'), indent=1)
    print(json.dumps(r), flush=True)

elif cmd == 'esn':
    steps = 16000
    u, bb = RL.L30.streams(steps)
    grid = [g for g in RL.L30.ESN_GRID if g[3] == 'tanh' and g[1] in (0.1, 0.5)] + [(0.99, 0.5, 1.0, 'linear')]
    for N in (int(x) for x in sys.argv[2:]):
        p = os.path.join(D, f'esn_N{N}.json')
        if os.path.exists(p): continue
        rows = []
        for rho, ins, leak, act in grid:
            t = time.time()
            Hu = RL.esn_features(N, rho, ins, leak, act, u); Hb = RL.esn_features(N, rho, ins, leak, act, bb * 0.5)
            r = RL.capacity_score(Hu, Hb, u, bb, which=('raw',)); r.update(N=N, rho=rho, ins=ins, leak=leak, act=act, secs=time.time() - t)
            rows.append(r); print(json.dumps(r), flush=True)
            del Hu, Hb; torch.cuda.empty_cache()
        json.dump(rows, open(p, 'w'), indent=1)
