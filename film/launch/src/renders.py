"""Camera choreography for every product shot, rendered through the site's own scene (harness/). One JSON per shot.
Axis: +y, beam at x = z = 0; plates at y = 5, 10, 15, 20 mm; end mirror 25 mm; dev board about -31 mm."""
import json, math, os, sys
FPS = 24
def ease(t): return t * t * (3 - 2 * t)
def lerp(a, b, t): return [x + (y - x) * t for x, y in zip(a, b)] if isinstance(a, list) else a + (b - a) * t
def shot(name, secs, fn):
    n = round(secs * FPS); fr = []
    for i in range(n):
        t = i / max(1, n - 1); d = fn(t, i)
        base = dict(dt=1 / FPS, light=1, hardware=1, packets=None, beamGain=1.3, plates=True)
        base.update(d); fr.append(base)
    os.makedirs('gen/render', exist_ok=True)
    json.dump(fr, open(f'gen/render/{name}.json', 'w'))
C = lambda pos, target, fov=30: dict(pos=pos, target=target, fov=fov)
SHOTS = {
 # Act 1 end: first light. black, only the field, one packet
 'r-firstlight': (4, lambda t, i: dict(cam=C(lerp([0, 16, 9], [0, 17, 12], t), [0, 10, 0], 32), follow=1.0, light=0, hardware=0, plates=False, packets=1, beamGain=5.0 * min(1, t * 2.5), dt=1 / FPS * 0.35)),
 # Act 2: track with the field while the machine emerges from darkness
 'r-reveal': (7, lambda t, i: dict(cam=C(lerp([14, 2, 30], [22, 20, 44], ease(t)), lerp([0, 6, 0], [0, 14, 0], ease(t)), 30),
                                    light=0.55 * ease(min(1, t * 1.3)), hardware=1, packets=1, beamGain=2.0, dt=1 / FPS * 0.8)),
 # the field crossing a plate: look down on plate 2
 'r-plate': (6, lambda t, i: dict(cam=C(lerp([9, 17, 12], [7, 16, 9], ease(t)), [0, 10, 0], 26), light=0.5, packets=None, beamGain=1.6, dt=1 / FPS * 0.5)),
 # one round trip, side view of the cavity
 'r-roundtrip': (6, lambda t, i: dict(cam=C([16, 34, 44], [0, 12.5, 0], 19), light=0, hardware=0, packets=1, beamGain=3.0, dt=1 / FPS * 3.2 / 5.2)),
 # multiplexing: pulses fill the cavity, time accelerates
 'r-multiplex': (6, lambda t, i: dict(cam=C(lerp([16, 34, 44], [20, 36, 40], ease(t)), [0, 12.5, 0], 19), light=0, hardware=0, packets=max(1, round(36 * ease(t))), beamGain=2.6, dt=1 / FPS * (0.6 + 3.5 * ease(t)))),
 # energy beat: wide three-quarter, full light
 'r-energy': (6, lambda t, i: dict(cam=C(lerp([80, 50, 170], [72, 54, 158], t), [0, -2, 0], 24), light=1, beamGain=1.6)),
 # hero: immaculate, slow orbit + push
 'r-hero': (5, lambda t, i: dict(cam=C([180 * math.sin(0.35 + 0.12 * t), 46 + 4 * t, 180 * math.cos(0.35 + 0.12 * t)], [0, -2, 0], lerp(24, 22, ease(t))), light=1, beamGain=1.6)),
 # act 5: "changes the slope" — beam close
 'r-slope': (4, lambda t, i: dict(cam=C(lerp([6, 8, 26], [6, 16, 26], ease(t)), [0, 12, 0], 30), light=0.25, beamGain=2.0)),
 # act 7: resolution — pulse enters the cavity in the dark, machine faintly lit
 'r-resolve': (8, lambda t, i: dict(cam=C(lerp([26, 16, 48], [16, 14, 32], ease(t)), [0, 12.5, 0], 30), light=0.3, packets=min(36, 1 + int(t * 5)), beamGain=2.4, dt=1 / FPS * 0.7)),
 # act 7: thesis — slow crane down the lit stack while pulses circulate
 'r-thesis': (6.5, lambda t, i: dict(cam=C(lerp([34, 30, 58], [30, 10, 52], ease(t)), lerp([0, 16, 0], [0, 8, 0], ease(t)), 26), light=0.6, beamGain=2.0, dt=1 / FPS * 0.5)),
 # act 8: end frame — black studio, one pulse, slow push toward the optical path
 'r-end': (12, lambda t, i: dict(cam=C(lerp([70, 44, 150], [22, 20, 46], ease(t)), lerp([0, 2, 0], [0, 12, 0], ease(t)), 30), light=0.7 * (1 - 0.6 * ease(max(0, t - 0.5) * 2)), packets=1, beamGain=2.4, dt=1 / FPS * 0.7)),
}

# ── v2 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def orbit(t, a0, a1, r, h, target, fov):
    a = a0 + (a1 - a0) * t
    return C([r * math.sin(a), h, r * math.cos(a)], target, fov)
SHOTS.update({
 # darkroom assembly: the parts float apart in the dark and come together into the machine as the camera circles;
 # the light arrives only once the cavity is closed
 'r2-assemble': (6.5, lambda t, i: dict(cam=orbit(ease(t), -0.9, 0.35, lerp(330, 185, ease(t)), lerp(80, 46, ease(t)), [0, lerp(12, 3, ease(t)), 0], 30),
     explode=1 - ease(min(1, t / 0.82)), light=0.25 + 0.75 * ease(t), packets=0 if t < 0.86 else 1 + int((t - 0.86) * 60), beamGain=2.2, depth=True)),
 # white studio hero: slow turntable
 'r2-studio-hero': (5.5, lambda t, i: dict(cam=orbit(t, 0.25, 0.55, 215, 50, [-24 * math.cos(0.25 + 0.3 * t), 3, 24 * math.sin(0.25 + 0.3 * t)], 24), studio=1, light=1, beamGain=1.4, depth=True)),
 # white studio exploded view, held long enough to read
 'r2-studio-explode': (8.0, lambda t, i: dict(cam=orbit(ease(t), 0.55, 0.75, lerp(215, 330, ease(t)), lerp(50, 70, ease(t)), [0, lerp(3, 10, ease(t)), 0], 30),
     studio=1, light=1, explode=ease(min(1, t / 0.7)), packets=0, beamGain=0, depth=True)),
})

# ── v3: one continuous fly-through (Catmull-Rom through keyframes) ─────────────────────────────────────────────────────
def catmull(keys, t):
    """keys: [(time, value or list)], smooth through every key"""
    ts = [k[0] for k in keys]
    i = max(0, min(len(keys) - 2, next((j for j in range(len(ts) - 1) if ts[j] <= t <= ts[j + 1]), len(ts) - 2)))
    p0, p1, p2, p3 = (keys[max(0, i - 1)][1], keys[i][1], keys[i + 1][1], keys[min(len(keys) - 1, i + 2)][1])
    u = (t - ts[i]) / max(1e-9, ts[i + 1] - ts[i])
    f = lambda a, b, c, d: 0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3)
    return [f(*z) for z in zip(p0, p1, p2, p3)] if isinstance(p1, list) else f(p0, p1, p2, p3)
def piece(keys, t):
    """piecewise-smooth scalar (no overshoot)"""
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1: return a + (b - a) * ease((t - t0) / max(1e-9, t1 - t0))
    return keys[-1][1] if t > keys[-1][0] else keys[0][1]
FLY_POS = [(0, [0, 1.5, 11.5]), (4, [4, 9, 11.5]), (8, [15, 15, 19]), (12, [30, 26, 30]), (14, [30, 48, 40]), (16, [16, 68, 44]), (20, [-40, 50, 90]),
           (25, [-160, 70, 300]), (28, [-90, 52, 230]), (30, [-66, 48, 212])]
FLY_TGT = [(0, [0, 12, 0]), (4, [0, 14, 0]), (8, [0, 13, 0]), (12, [0, 14, 0]), (14, [0, 24, 0]), (16, [0, 22, 0]), (20, [0, 10, 0]), (25, [0, 7, 0]), (28, [0, 4, 0]), (30, [0, 3, 0])]
FLY_FOV = [(0, 62), (4, 54), (8, 42), (12, 36), (14, 34), (16, 36), (20, 32), (25, 30), (30, 25)]
def fly(t, i):
    T = t * 30
    return dict(cam=C(catmull(FLY_POS, T), catmull(FLY_TGT, T), catmull(FLY_FOV, T)),
                light=piece([(0, 0.14), (6, 0.3), (12, 0.45), (16, 0.6), (19, 0.7), (23, 1.0), (30, 1.0)], T),
                studio=piece([(0, 0), (19, 0), (23, 1), (30, 1)], T),
                explode=piece([(0, 0), (18.5, 0), (23, 1), (26.5, 1), (29.5, 0), (30, 0)], T),
                packets=int(piece([(0, 1), (7, 1), (12, 36), (30, 36)], T)),
                beamGain=piece([(0, 3.2), (12, 2.4), (18, 2.0), (22, 0.6), (26, 0.0), (29, 1.2), (30, 1.4)], T),
                dt=1 / FPS * piece([(0, 0.45), (7, 0.6), (12, 2.4), (16, 1.0), (30, 0.8)], T), depth=True)
SHOTS['r3-fly'] = (30.0, fly)

# ── v4: short, fast, low "grazing" moves, rendered at SUB sub-frames per frame and averaged (src/blur.py) ─────────────
SUB = 4
def fast(name, secs, keys_pos, keys_tgt, keys_fov, **scalars):
    """scalars: name -> [(t, v)] keyframes in seconds (piecewise-smooth) or a constant"""
    n = round(secs * FPS * SUB); fr = []
    for i in range(n):
        T = i / (FPS * SUB)
        d = dict(cam=C(catmull(keys_pos, T), catmull(keys_tgt, T), catmull(keys_fov, T)), light=1, hardware=1, packets=None, beamGain=1.6,
                 plates=True, dt=1 / (FPS * SUB), depth=(i % SUB == SUB // 2))
        for k, v in scalars.items(): d[k] = piece(v, T) if isinstance(v, list) else v
        if 'packets' in d and d['packets'] is not None: d['packets'] = int(d['packets'])
        if 'dtscale' in d: d['dt'] = d.pop('dtscale') / (FPS * SUB)
        fr.append(d)
    os.makedirs('gen/v4/render', exist_ok=True)
    json.dump(fr, open(f'gen/v4/render/{name}.json', 'w'))
V4 = {
 # skim low over the dev board toward the stack, then pull up the cage
 'r4-board': lambda: fast('r4-board', 3.2, [(0, [-6, -26.5, 40]), (1.6, [-2, -25.5, 14]), (3.2, [3, -6, 12])],
                          [(0, [0, -27, 0]), (1.6, [0, -18, -4]), (3.2, [0, 10, 0])], [(0, 58), (3.2, 50)], light=[(0, 0.5), (3.2, 0.7)], dtscale=0.8),
 # rocket up the canyon between the rods and the cells, beam streaking alongside
 'r4-canyon': lambda: fast('r4-canyon', 2.6, [(0, [7, 1, 8]), (1.3, [8, 13, 7]), (2.6, [6, 27, 9])], [(0, [0, 9, 0]), (1.3, [0, 20, 0]), (2.6, [0, 34, 0])],
                           [(0, 64), (2.6, 58)], light=0.45, packets=36, beamGain=2.6, dtscale=2.5),
 # graze the etched face of phase plate 2: its 64 x 64 pixels of phase
 'r4-plate': lambda: fast('r4-plate', 3.0, [(0, [-0.35, 11.1, 0.55]), (1.5, [0.0, 11.0, 0.25]), (3.0, [0.35, 10.9, -0.1])],
                          [(0, [-0.2, 10.0, -0.1]), (1.5, [0.15, 10.0, -0.35]), (3.0, [0.45, 10.0, -0.65])], [(0, 54), (3.0, 48)], light=0.55, beamGain=1.2, dtscale=0.4),
 # the round trip, whipping: science layer, one pulse, two trips in two seconds
 'r4-trip': lambda: fast('r4-trip', 2.6, [(0, [14, 30, 38]), (2.6, [18, 34, 32])], [(0, [0, 12.5, 0]), (2.6, [0, 12.5, 0])], [(0, 20), (2.6, 19)],
                         light=0, hardware=0, packets=1, beamGain=3.2, dtscale=5.0),
 # white studio: a quick expand and snap back, then the hero
 'r4-expand': lambda: fast('r4-expand', 5.0, [(0, [-150, 60, 250]), (2.2, [-120, 70, 290]), (5.0, [-62, 46, 205])],
                           [(0, [0, 6, 0]), (2.2, [0, 10, 0]), (5.0, [0, 3, 0])], [(0, 30), (5.0, 25)], studio=1,
                           explode=[(0, 0), (0.9, 0.75), (2.4, 0.75), (3.4, 0), (5, 0)], packets=36, beamGain=[(0, 1.0), (2.8, 0.2), (4, 1.4)], dtscale=1.0),
 # ignition: the machine in the dark, the gain crosses threshold and the cavity lights up
 'r4-ignite': lambda: fast('r4-ignite', 6.0, [(0, [36, 22, 64]), (6, [26, 18, 50])], [(0, [0, 12, 0]), (6, [0, 12.5, 0])], [(0, 30), (6, 30)],
                           light=[(0, 0.18), (3.0, 0.18), (3.3, 0.55), (6, 0.5)], packets=[(0, 0), (2.9, 0), (3.1, 36), (6, 36)],
                           beamGain=[(0, 0), (2.95, 0), (3.2, 5.0), (4.2, 2.6), (6, 2.4)], dtscale=1.2),
}
if __name__ == '__main__':
    if '--v4' in sys.argv:
        for f in V4.values(): f()
        print(' '.join(V4)); sys.exit()
    for k, (s, fn) in SHOTS.items(): shot(k, s, fn)
    print(' '.join(SHOTS))
