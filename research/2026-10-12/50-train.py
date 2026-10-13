"""Experiment 50 (2026-10-13): TRAINED optics for the passive linear ring — does gradient training of the phase mask (and of
the input / reference patterns) lift the capability ceiling of the random ring?

The Exp. 48 ring (passive: gain 1, constant; signal Σ x_i P_i plus a constant reference c·P_c injected each step; features =
|E|² summed over the K trips of a step, binned) is differentiable end to end. Trained by Adam:
  m  the SLM phase mask φ (the round-trip program; amplitude = the SLM's reflectivity map, unchanged)
  2  a second phase plane after the first relay lens (an extra SLM / plate; its insertion loss is NOT modelled)
  p  the 64 input patterns (free complex, each renormalised to its initial power)
  c  the reference pattern (free complex, renormalised to its initial power)
Objective: the generalisation error of a ridge readout. Each iteration draws B windows of the KS training split (W washout
steps + S scored steps), runs the ring, fits ridge in closed form on half of the windows (features standardised, x(t) appended,
λ learned) and back-propagates the error on the other half. No readout weights are carried between iterations.
Evaluation: the trained optics run the full 32k-step stream and are scored with the Exp. 45 protocol (KS.score), so numbers
are directly comparable with Exps. 45/48 (test split never seen by the training windows).
env LOAD=<tag> evaluates saved optics; env DGRID=1e8,1e9,… adds shot noise at D signal photons per step (homodyne accounting).
Exp. 53 additions:
  s  the reference strength c is trained too (log-parameter, initialised at <carrier>)
  a  a per-mode saturable absorber at the SLM plane: power transmission 1 − A0/(1 + |E|²/Is), A0 = 0.6, Is trained
     (a local nonlinearity inside the loop: features beyond quadratic)
  env NOISE_D=<photons>: shot noise INSIDE training and evaluation at D detected photons per step IN TOTAL (signal + reference),
     + 2 e⁻ read noise per detector bin — the optics then have to earn their reference light.
usage: python 50-train.py <n> <bin> <K> <carrier> <what: any of m2pc, or 'none'> <iters> [B=384] [seed=0]
→ out/45/results.json (kind 'optical-trained'), out/50/<tag>.pt (trained parameters), out/50/<tag>.log.json (loss curve)
"""
import importlib.util, json, math, os, sys, time
import numpy as np
import torch
from res_gpu import Reservoir

HERE = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location('KS45', os.path.join(HERE, '45-ks.py'))
_argv, sys.argv = sys.argv, ['45-ks.py', 'none']
KS = importlib.util.module_from_spec(_s); _s.loader.exec_module(KS)
sys.argv = _argv

n, bin_, K, carrier, what, iters = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), sys.argv[5], int(sys.argv[6])
B = int(sys.argv[7]) if len(sys.argv) > 7 else 384
seed = int(sys.argv[8]) if len(sys.argv) > 8 else 0
what = '' if what == 'none' else what
ND = float(os.environ['NOISE_D']) if os.environ.get('NOISE_D') else None
tag = f'n{n}_b{bin_}_K{K}_c{carrier:g}_{what or "none"}_i{iters}_s{seed}' + (f'_D{ND:g}' if ND else '')
A0 = 0.6
OUT = os.path.join(HERE, 'out', '50'); os.makedirs(OUT, exist_ok=True)
torch.manual_seed(seed)
R = Reservoir(n, d_in=KS.Q)
dev, cdt = R.dev, R.cdt
Q, nb = KS.Q, n // bin_

# ── the ring as an explicit op list (gain skipped: passive) with the SLM made trainable ─────────────────────────────────
ops, lens_seen = [], 0
for o in R.ops:
    k = o['op']
    if k == 'scale': ops.append(('scale', o['a']))
    elif k == 'inject': ops.append(('inject', o['coupling']))
    elif k == 'mul':
        ops.append(('slm', None) if o.get('id') == 'slm' else ('mul', o['T']))
        if o.get('kind') == 'lens':
            lens_seen += 1
            if lens_seen == 1: ops.append(('plane2', None))
    elif k == 'prop': ops.append(('prop', (o['H'], o['W'])))
    elif k == 'gain': pass
    else: raise NotImplementedError(k)
slm0 = next(o['T'] for o in R.ops if o.get('id') == 'slm')
slm_amp = slm0.abs()
P0 = R.patterns[:Q]
g = torch.Generator().manual_seed(7)
sgn = (torch.randint(0, 2, (Q,), generator=g) * 2 - 1).to(dev, cdt)
Pc0 = torch.einsum('d,dxy->xy', sgn, P0) / math.sqrt(Q)  # the Exp. 48 reference field
pn0 = P0.abs().pow(2).sum((-2, -1), keepdim=True).sqrt()
cn0 = Pc0.abs().pow(2).sum().sqrt()

prm = dict(phi=torch.angle(slm0).float().clone(), phi2=torch.zeros(n, n, device=dev),
           P=torch.view_as_real(P0 / pn0 * n).clone(), Pc=torch.view_as_real(Pc0 / cn0 * n).clone(), loglam=torch.tensor(-2.0, device=dev))
prm['logc'] = torch.tensor(math.log(max(carrier, 1e-3)), device=dev)
prm['logIs'] = torch.tensor(0.0, device=dev)
inj_c = next(o['coupling'] for o in R.ops if o['op'] == 'inject')
Is0 = float((inj_c * max(carrier, 1.0)) ** 2 * (Pc0.abs() ** 2).mean())  # the injected reference's mean intensity: absorber half-bleached
train = [k for k, f in (('phi', 'm'), ('phi2', '2'), ('P', 'p'), ('Pc', 'c'), ('logc', 's'), ('logIs', 'a')) if f in what] + ['loglam']


def cval():
    return torch.exp(prm['logc']) if 's' in what else carrier


def noisy(F):
    """shot + read noise at ND detected photons per step in total (Gaussian approximation, differentiable)"""
    if ND is None: return F
    sc = ND / F.sum(-1).mean().detach()
    return F + torch.sqrt(F.clamp_min(0) / sc + 1e-30) * torch.randn_like(F) + (2.0 / sc) * torch.randn_like(F)
if os.environ.get('LOAD'):  # evaluate saved optics (out/50/<LOAD>.pt) without training
    for k, v in torch.load(os.path.join(OUT, os.environ['LOAD'] + '.pt')).items(): prm[k] = v.to(dev)
    iters = 0
for k in train: prm[k].requires_grad_(True)


def optics():
    P = torch.view_as_complex(prm['P']); P = P / P.abs().pow(2).sum((-2, -1), keepdim=True).sqrt() * pn0
    Pc = torch.view_as_complex(prm['Pc']); Pc = Pc / Pc.abs().pow(2).sum().sqrt() * cn0
    return slm_amp * torch.exp(1j * prm['phi']), torch.exp(1j * prm['phi2']), P, Pc


def trip(E, inj, slm, p2):
    for k, x in ops:
        if k == 'scale': E = E * x
        elif k == 'inject':
            if inj is not None: E = E + x * inj
        elif k == 'slm':
            E = E * slm
            if 'a' in what:
                E = E * torch.sqrt(1 - A0 / (1 + (E.real ** 2 + E.imag ** 2) / (Is0 * torch.exp(prm['logIs']))))
        elif k == 'plane2':
            if '2' in what: E = E * p2
        elif k == 'mul': E = E * x
        elif k == 'prop':
            E = torch.fft.ifft2(torch.fft.fft2(E) * x[0])
            if x[1] is not None: E = E * x[1]
    return E


def features(U, o, keep_from=0):
    """U: (B, T, Q) real → (B, T − keep_from, nb²) binned intensities summed over the K trips of each step"""
    slm, p2, P, Pc = o
    E = torch.zeros(U.shape[0], n, n, dtype=cdt, device=dev)
    out = []
    for t in range(U.shape[1]):
        inj = torch.einsum('bd,dxy->bxy', U[:, t].to(cdt), P) + cval() * Pc
        acc = 0
        for k in range(K):
            E = trip(E, inj if k == 0 else None, slm, p2)
            acc = acc + E.real ** 2 + E.imag ** 2
        if t >= keep_from:
            out.append(acc.reshape(-1, nb, bin_, nb, bin_).sum((2, 4)).reshape(-1, nb * nb))
    return torch.stack(out, 1)


X = torch.as_tensor(KS.X, dtype=torch.float32, device=dev)
Y = torch.as_tensor(KS.Y, dtype=torch.float32, device=dev)
a, b = KS.a, KS.b
WASH, S = 12, 16
T = WASH + S
opt = torch.optim.Adam([dict(params=[prm[k] for k in train if k != 'loglam'], lr=0.02), dict(params=[prm['loglam']], lr=0.05)])
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, max(iters, 1), eta_min=0.002)
curve, t0 = [], time.time()
for it in range(iters):
    st = torch.randint(a, b - T - max(KS.H), (B,), device=dev)
    idx = st[:, None] + torch.arange(T, device=dev)[None]
    F = noisy(features(X[idx] / math.sqrt(Q), optics(), WASH)).double()   # (B, S, nb²)
    xs, ys = X[idx[:, WASH:]].double(), Y[idx[:, WASH:]].double()
    h = B // 2
    mu, sd = F[:h].mean((0, 1)), F[:h].std((0, 1)) + 1e-9 * F[:h].std()
    Z = torch.cat([(F - mu) / sd, xs, torch.ones(B, S, 1, dtype=torch.float64, device=dev)], 2)
    Zf, Yf, Ze, Ye = Z[:h].reshape(h * S, -1), ys[:h].reshape(h * S, -1), Z[h:].reshape((B - h) * S, -1), ys[h:].reshape((B - h) * S, -1)
    lam = torch.exp(prm['loglam'].double() * math.log(10)) * Zf.shape[0]
    Wr = torch.linalg.solve(Zf.T @ Zf + lam * torch.eye(Zf.shape[1], dtype=torch.float64, device=dev), Zf.T @ Yf)
    err = ((Ze @ Wr - Ye) ** 2).mean(0) / Ye.var(0)                        # per target NMSE on the held-out windows
    loss = torch.log(err).mean()                                           # geometric mean: every horizon counts
    opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    if it % 25 == 0 or it == iters - 1:
        e = err.detach().reshape(len(KS.H), Q).mean(1).tolist()
        curve.append(dict(it=it, loss=float(loss), nmse=e, loglam=float(prm['loglam']), secs=time.time() - t0))
        print(f'it {it} loss {float(loss):.3f} nmse h1/h4/h16 {e[0]:.2e} {e[1]:.2e} {e[2]:.3f} loglam {float(prm["loglam"]):.2f} {time.time() - t0:.0f}s', flush=True)
if not os.environ.get('LOAD'):
    json.dump(curve, open(os.path.join(OUT, tag + '.log.json'), 'w'))
    torch.save({k: v.detach().cpu() for k, v in prm.items()}, os.path.join(OUT, tag + '.pt'))

# ── evaluation: full stream, Exp. 45 scoring ────────────────────────────────────────────────────────────────────────
@torch.no_grad()
def run_full(c):
    slm, p2, P, Pc = optics()
    E = torch.zeros(1, n, n, dtype=cdt, device=dev)
    Fall = torch.empty(KS.STEPS, nb * nb, dtype=torch.float32, device=dev)
    U = X / math.sqrt(Q)
    for t in range(KS.STEPS):
        inj = torch.einsum('d,dxy->xy', U[t].to(cdt), P)[None] + (cval() if c is None else c) * Pc
        acc = 0
        for k in range(K):
            E = trip(E, inj if k == 0 else None, slm, p2)
            acc = acc + E.real ** 2 + E.imag ** 2
        Fall[t] = acc.reshape(nb, bin_, nb, bin_).sum((1, 3)).reshape(-1)
    return noisy(Fall).cpu().numpy() if c is None else Fall.cpu().numpy()


Fall = run_full(None if (ND or 's' in what) else carrier)
sig0 = run_full(0.0).astype(np.float64).sum(1).mean() if (ND or 's' in what) else None
extra = dict(kind='optical-trained', n=n, modes=n * n, bin=bin_, K=K, G0=1.0, carrier=carrier, trained=what or 'none', iters=iters,
             B=B, seed=seed, train_secs=time.time() - t0, loaded=os.environ.get('LOAD'), D_total=ND, c_final=float(cval()),
             logIs=float(prm['logIs']), signal_fraction=None if sig0 is None else float(sig0 / run_full(float(cval())).astype(np.float64).sum(1).mean()))
if os.environ.get('DGRID'):
    # shot noise, homodyne accounting (Exp. 48d): D = the SIGNAL's detected photons per step (the carrier-0 run sets the photon
    # scale); the reference's light and its shot noise come on top; 2 e⁻ read noise per detector bin
    sc0 = run_full(0.0).astype(np.float64).sum(1).mean()
    rng = np.random.default_rng(0)
    del X, Y; torch.cuda.empty_cache()
    for D in (float(v) for v in os.environ['DGRID'].split(',')):
        lam = np.maximum(Fall.astype(np.float64), 0) * (D / sc0)
        Fn = ((lam + np.sqrt(lam) * rng.normal(size=lam.shape) + 2.0 * rng.normal(size=lam.shape)) / (D / sc0)).astype(np.float32)
        KS.score(Fn, None, f'optical-trained n={n}', dict(extra, D=D, dref='signal', carrier_photons=float(Fall.sum(1).mean() / sc0 * D)))
else:
    del X, Y; torch.cuda.empty_cache()
    KS.score(Fall, None, f'optical-trained n={n}', extra)
