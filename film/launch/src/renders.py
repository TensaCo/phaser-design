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
if __name__ == '__main__':
    for k, (s, fn) in SHOTS.items(): shot(k, s, fn)
    print(' '.join(SHOTS))
