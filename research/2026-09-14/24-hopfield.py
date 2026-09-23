"""Experiment 24 (2026-09-23): digital baselines for the Exp. 16 associative-memory basin study.

Same stored patterns (read from the optical design's spec), same corruption levels and repetitions as 16-basin.ts, same outcome
classes (recovered: Hamming ≤ 1 to the source; other_stored; spurious). Baselines on the 8×8 cell lattice:
  hopfield_full    classical Hopfield, Hebbian (bias-removed ±1 patterns, zero diagonal), asynchronous updates to convergence
  hopfield_pinv    projection (pseudo-inverse) rule, all-to-all
  hopfield_local   Hebbian restricted to cells within a Chebyshev radius r (1 = nearest + diagonal neighbours), the connectivity
                   a relay PSF of a few pixels can physically provide
  nearest          ideal nearest-pattern decoder (upper bound: minimum-Hamming stored pattern)
usage: python 24-hopfield.py <spec.json> [reps=50]
"""
import json, os, sys
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), 'out', '24')
os.makedirs(OUT, exist_ok=True)
LEVELS = [0, 2, 4, 6, 8, 12, 16, 24, 32]


def hebb(X, mask=None):
    """X: (P, N) in ±1 after removing the mean activity."""
    W = X.T @ X / X.shape[1]
    np.fill_diagonal(W, 0)
    return W if mask is None else W * mask


def pinv_rule(X):
    W = X.T @ np.linalg.pinv(X @ X.T) @ X
    np.fill_diagonal(W, 0)
    return W


def local_mask(side, r):
    ij = np.array([(i, j) for i in range(side) for j in range(side)])
    d = np.abs(ij[:, None, :] - ij[None, :, :]).max(-1)
    return (d <= r).astype(float)


def run_net(W, theta, s0, rng, max_sweeps=100):
    s = s0.copy()
    for _ in range(max_sweeps):
        changed = False
        for i in rng.permutation(len(s)):
            v = 1.0 if W[i] @ s - theta[i] >= 0 else -1.0
            if v != s[i]:
                s[i] = v
                changed = True
        if not changed:
            break
    return s


def main(spec_path, reps=50):
    spec = json.load(open(spec_path))
    stored = {k: np.array(v) for k, v in spec['stored'].items()}
    names = list(stored)
    P = np.stack([stored[k] for k in names]).astype(float)  # 0/1
    N = P.shape[1]
    global LEVELS
    if N < 64:
        LEVELS = [0, 1, 2, 3, 4, 6, 8]  # as 16-basin.ts for small lattices
    side = int(round(np.sqrt(N)))
    a = P.mean()
    X = 2 * P - 1
    Xc = (P - a) * 2  # bias-removed
    nets = {
        'hopfield_full': (hebb(Xc), None),
        'hopfield_pinv': (pinv_rule(X), None),
        'hopfield_local_r1': (hebb(Xc, local_mask(side, 1)), None),
        'hopfield_local_r2': (hebb(Xc, local_mask(side, 2)), None),
    }
    rng = np.random.default_rng(2718)
    rows = []
    for pname, pat in stored.items():
        for k in LEVELS:
            for rep in range(reps):
                cue = pat.copy()
                idx = rng.permutation(N)[:k]
                cue[idx] = 1 - cue[idx]
                s0 = 2 * cue.astype(float) - 1
                res = {}
                for nn, (W, _) in nets.items():
                    # threshold compensates the mean-activity bias of the Hebbian rule (Amit-Gutfreund-Sompolinsky style)
                    theta = W @ np.full(N, 2 * a - 1) if nn.startswith('hopfield_local') or nn == 'hopfield_full' else np.zeros(N)
                    res[nn] = ((run_net(W, theta, s0, rng) + 1) / 2).astype(int)
                d = [int(np.sum(cue != stored[q])) for q in names]
                res['nearest'] = stored[names[int(np.argmin(d))]]
                for nn, fin in res.items():
                    dists = {q: int(np.sum(fin != stored[q])) for q in names}
                    near = min(dists.items(), key=lambda x: x[1])
                    outcome = 'recovered' if dists[pname] <= 1 else ('other_stored' if near[1] <= 1 else 'spurious')
                    rows.append(dict(model=nn, pattern=pname, flips=k, rep=rep, outcome=outcome, hamming_to_source=dists[pname]))
    summary = {}
    for nn in list(nets) + ['nearest']:
        summary[nn] = {k: float(np.mean([r['outcome'] == 'recovered' for r in rows if r['model'] == nn and r['flips'] == k])) for k in LEVELS}
        print(nn, ' '.join(f'k={k}:{v:.2f}' for k, v in summary[nn].items()))
    tag = spec['tag']
    json.dump(dict(tag=tag, levels=LEVELS, reps=reps, mean_activity=a, summary=summary, rows=rows), open(os.path.join(OUT, f'hopfield_{tag}.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 50)
