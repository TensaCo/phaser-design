"""checks for fused.py: per-run forward accuracy, adjoint identity, 200-trip agreement, mask gradients, speed."""
import math, sys, time, torch
from gtwin import GTwin, TAU
name = sys.argv[1] if len(sys.argv) > 1 else 'A64s_amp'
tu, tf = GTwin(name, 'c64'), GTwin(name, 'c64', fused=True)
for t in (tu, tf):
    t.set_media(Ld=100e-6)
g = torch.Generator(device='cuda').manual_seed(0)
cr = lambda *s: torch.complex(torch.randn(*s, generator=g, device='cuda'), torch.randn(*s, generator=g, device='cuda'))
print('segments:', [(k if k == 'lin' else x['op']) + (f"[{len(x.pf)}]" if k == 'lin' else '') for k, x in tf.segs])
# 1+2: each linear run vs torch, and adjoint identity
import fused as F
i = 0
for k, run in tf.segs:
    if k != 'lin':
        continue
    ops = [o for o in tu.ops if o['op'] in F.LINEAR]
    x, y = cr(16, 64, 64), cr(16, 64, 64)
    Lx = run.apply(x)
    # torch reference: rebuild from the run's own program
    ref = x.clone()
    for (c, a, b, f) in run.pf.tolist():
        if c == 0:
            H = run.Hs[a][F.SWAP.argsort()][:, F.SWAP.argsort()]
            ref = torch.fft.ifft2(torch.fft.fft2(ref) * H)
            if not f & 4:
                ref = ref * run.Ws[b]
        elif c == 1: ref = ref * run.sc[a]
        elif c == 2: ref = ref * run.Ts[a]
        elif c == 3: ref = torch.flip(ref, dims=[-1])
        elif c == 4: ref = torch.flip(ref, dims=[-2])
    e = ((Lx - ref).abs().norm() / ref.abs().norm()).item()
    LHy = run.apply(y, adjoint=True)
    a1 = (Lx * y.conj()).sum(); a2 = (x * LHy.conj()).sum()
    print(f'run {i}: {len(run.pf)} ops, forward rel err {e:.2e}, adjoint identity rel err {(abs(a1 - a2) / abs(a1)).item():.2e}')
    i += 1
# 3: 200 sustained trips, fused vs unfused (both c64)
D, B = 3, 4
masks = {dev: (math.pi + 0.3 * torch.rand(D, *tu.res[dev], generator=g, device='cuda')) if dev == 'slm' else torch.full((D, *tu.res[dev]), 0.999 * TAU, device='cuda') for dev in tu.res}
E0 = cr(D, B, 64, 64) * 1.5
G0 = torch.tensor([2.4, 2.6, 2.9], device='cuda')
Eu, Ef = E0, E0
tru, trf = tu.transmissions(masks), tf.transmissions(masks)
with torch.no_grad():
    for t in range(200):
        Eu = tu.trip(Eu, tru, G0); Ef = tf.trip(Ef, trf, G0)
print(f'200 trips: fused vs unfused rel err {((Eu - Ef).abs().norm() / Eu.abs().norm()).item():.2e} (power {(Eu.abs()**2).sum().item():.3e})')
# 4: gradient wrt the SLM program and G0 through 30 trips
def grad(tw):
    th = masks['slm'].clone().requires_grad_(True); lg = G0.clone().requires_grad_(True)
    E = E0
    trr = tw.transmissions({'slm': th, 'amp': masks['amp']})
    for t in range(30):
        E = tw.trip(E, trr, lg)
    L = (E.abs() ** 2)[..., 20:40, 20:40].sum()
    L.backward()
    return th.grad, lg.grad
gu, gGu = grad(tu); gf, gGf = grad(tf)
print(f'grad wrt SLM rel err {((gu - gf).norm() / gu.norm()).item():.2e}, wrt G0 {((gGu - gGf).norm() / gGu.norm()).item():.2e}')
# 5: speed, fwd+bwd, D·B = 128, 50 trips
for tw, nm in ((tu, 'torch'), (tf, 'fused')):
    th = masks['slm'][:1].expand(32, -1, -1).clone().requires_grad_(True)
    am = masks['amp'][:1].expand(32, -1, -1).clone()
    Gx = torch.full((32,), 2.6, device='cuda')
    Eb = cr(32, 4, 64, 64)
    for rep in range(2):
        torch.cuda.synchronize(); t0 = time.time()
        trr = tw.transmissions({'slm': th, 'amp': am}); E = Eb
        for t in range(50):
            E = tw.trip(E, trr, Gx)
        (E.abs() ** 2).sum().backward()
        torch.cuda.synchronize()
    print(f'{nm}: fwd+bwd {(time.time() - t0) / 50 * 1e3:.2f} ms per trip at 128 samples')
