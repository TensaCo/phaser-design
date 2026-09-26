"""v4 mix: music edited on the beat from three composed cues, multiband sidechain under voices, a voice chain, sound design
synced to the picture, and a master bus. Everything is deterministic (seeded)."""
import json, os, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, fftconvolve
import audio as A  # shared helpers: load, amb, sfx, reverb, room, db, bp, noise, pink, brown, tone, hum

SR = A.SR
rng = np.random.default_rng(11)
db = A.db


def starts(edl):
    t, out = 0.0, {}
    for c in edl: out[c['id']] = (t, t + c['dur']); t += c['dur']
    return out


def stereo_load(p):
    return A.load_stereo(p)


# ── beat grid ─────────────────────────────────────────────────────────────────────────────────────────────────────
def beat_grid(x):
    """tempo (s per beat) and the time of the first downbeat, from onset-strength autocorrelation"""
    m = x.mean(1) if x.ndim == 2 else x
    hop = 512; fr = len(m) // hop
    e = np.array([np.sum(m[i * hop:(i + 1) * hop] ** 2) for i in range(fr)])
    on = np.maximum(0, np.diff(np.log(e + 1e-9), prepend=0))
    on -= on.mean()
    ac = np.correlate(on, on, 'full')[len(on) - 1:]
    lo, hi = int(0.33 * SR / hop), int(0.75 * SR / hop)  # 80–180 bpm
    per = lo + int(np.argmax(ac[lo:hi]))
    ph = int(np.argmax([on[p::per].sum() for p in range(per)]))
    beat = per * hop / SR
    # downbeat: the beat phase (of 4) with the most energy
    bars = [on[ph + k * per::4 * per].sum() for k in range(4)]
    first = (ph + int(np.argmax(bars)) * per) * hop / SR
    return beat, first


def snap(t, beat, first, bars=True):
    step = beat * (4 if bars else 1)
    return first + round((t - first) / step) * step


def splice(parts, fade=0.12):
    """concatenate [(array, t0, t1)] with equal-power crossfades"""
    n = int(fade * SR); out = None
    for x, t0, t1 in parts:
        seg = x[int(t0 * SR):int(t1 * SR)].copy()
        if out is None: out = seg; continue
        w = np.linspace(0, np.pi / 2, n)[:, None]
        head = seg[:n] * np.sin(w); tail = out[-n:] * np.cos(w)
        out = np.concatenate([out[:-n], tail + head, seg[n:]])
    return out


def fit(x, length, loop_from, loop_to, beat, first):
    """make a cue exactly `length` s long by repeating the bar-aligned loop [loop_from, loop_to) before its tail"""
    a, b = snap(loop_from, beat, first), snap(loop_to, beat, first)
    L = len(x) / SR
    parts = [(x, 0, b)]
    need = length - L
    while need > 0.2:
        take = min(b - a, need)
        take = max(beat * 4, round(take / (beat * 4)) * beat * 4)
        parts.append((x, b - take, b)); need -= take
    parts.append((x, b, L))
    y = splice(parts)
    if len(y) / SR > length: y = y[:int(length * SR)]
    return y


# ── sound design ──────────────────────────────────────────────────────────────────────────────────────────────────
def pan(x, p):
    """p in -1..1 (constant power), x mono → stereo"""
    p = np.clip(p, -1, 1); a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def whoosh(dur=0.9, up=True, lr=True, level=-17):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 1.6 * (t if up else (1 - t)) ** 0.3
    x = A.pink(n)
    # a moving band: sweep the centre frequency
    out = np.zeros(n, np.float32); blocks = 24
    for k in range(blocks):
        i0, i1 = k * n // blocks, (k + 1) * n // blocks
        f = (300 + 3500 * (k / blocks)) if up else (3800 - 3400 * (k / blocks))
        out[i0:i1] = A.bp(x, max(60, f * 0.5), min(16000, f * 2.2))[i0:i1]
    out *= env * db(level)
    return pan(A.reverb(out, 0.8, 0.2, 9000), np.linspace(-0.8, 0.8, n) if lr else np.linspace(0.8, -0.8, n))


def tick(level=-24):
    n = int(0.25 * SR); t = np.arange(n) / SR
    x = A.bp(A.noise(n), 2500, 11000) * np.exp(-t * 60) + A.tone(n, 5200) * np.exp(-t * 90) * 0.3
    return pan(x * db(level), rng.uniform(-0.5, 0.5))


def sub_drop(level=-9):
    n = int(2.5 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 1.4) + 28) / SR) * np.exp(-t * 1.1)
    return pan(x * db(level), 0)


def breaker(level=-16):
    n = int(0.6 * SR); t = np.arange(n) / SR
    x = A.bp(A.noise(n), 150, 3000) * np.exp(-t * 40) + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 25) * 0.8
    return pan(A.room(x) * db(level), 0.1)


def ignite(level=-10):
    """electrical crackle that blooms into a clean optical chord, with a sub underneath"""
    n = int(5 * SR); t = np.arange(n) / SR
    crk = np.zeros(n, np.float32); idx = rng.integers(0, int(0.9 * SR), 260); crk[idx] = rng.uniform(-1, 1, 260)
    crk = A.bp(crk, 1500, 9000) * 5 * np.clip(1 - t / 1.0, 0, 1)
    bloom = sum(A.tone(n, f) * a for f, a in ((440, 1), (660, .6), (880, .5), (1320, .3), (1760, .2))) * np.clip((t - 0.8) / 0.15, 0, 1) * np.exp(-np.maximum(0, t - 0.8) * 0.9)
    sub = np.sin(2 * np.pi * 42 * t) * np.clip((t - 0.8) / 0.05, 0, 1) * np.exp(-np.maximum(0, t - 0.8) * 1.3)
    x = A.reverb(crk * db(-8) + bloom * db(-14) + sub * db(-4), 3.5, 0.4, 9000)
    return pan(x * db(level + 8), 0)


def swell(dur=5.0, level=-16):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    x = A.bp(A.brown(n), hi=220) * 3 + A.tone(n, 36) * 0.5
    return pan(x * np.sin(np.pi * t) ** 2 * db(level), 0)


def night_bed(dur):
    """the hushed 'night' under the ignition story: a low drone, a slow heartbeat and a clock tick"""
    n = int(dur * SR); t = np.arange(n) / SR
    drone = (A.tone(n, 55) + 0.5 * A.tone(n, 82.4) + 0.25 * A.tone(n, 110.3)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t))
    beat = np.zeros(n, np.float32)
    for s in np.arange(0.5, dur, 1.05):
        for k, g in ((0, 1.0), (0.22, 0.6)):
            i = int((s + k) * SR); m = min(n - i, int(0.3 * SR))
            if m > 0: beat[i:i + m] += np.sin(2 * np.pi * 50 * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 14) * g
    tk = np.zeros(n, np.float32)
    for s in np.arange(0.25, dur, 0.525):
        i = int(s * SR); m = min(n - i, 600)
        if m > 0: tk[i:i + m] += A.bp(A.noise(m), 3000, 9000) * np.exp(-np.arange(m) / 80)
    fade = np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 0.3, 0, 1)
    x = drone * db(-26) + beat * db(-20) + tk * db(-38)
    return np.stack([x, x], 1) * fade[:, None] * 1.0


def field_bed(n):
    t = np.arange(n) / SR
    x = A.bp(A.pink(n), 2000, 9000) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t)) * db(-44)
    x += sum(A.tone(n, f) * (0.5 + 0.5 * np.sin(2 * np.pi * r * t)) for f, r in ((523.3, 0.13), (784, 0.21), (1046.5, 0.17))) * db(-48)
    return x


# ── voice and bus processing ─────────────────────────────────────────────────────────────────────────────────────
def voice_chain(x, sync):
    x = sosfilt(butter(2, 90, 'highpass', fs=SR, output='sos'), x)
    pres = sosfilt(butter(2, [2500, 5000], 'bandpass', fs=SR, output='sos'), x); x = x + 0.25 * pres
    x = compress(x, -24, 3.0, 0.005, 0.12)
    return A.room(x, 0.3, 0.07) if sync else x


def envelope(x, att, rel):
    a, r = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR)); e = np.zeros_like(x); v = 0.0
    ax = np.abs(x)
    # vectorised-enough: process in blocks of 64 samples
    B = 64; out = np.zeros(len(x) // B + 1, np.float32)
    for i in range(len(out)):
        s = ax[i * B:(i + 1) * B]; m = s.max() if len(s) else 0
        v = m + (v - m) * (a ** B if m > v else r ** B); out[i] = v
    return np.repeat(out, B)[:len(x)]


def compress(x, thr_db, ratio, att, rel):
    env = envelope(x if x.ndim == 1 else x.mean(1), att, rel)
    lvl = 20 * np.log10(env + 1e-9); over = np.maximum(0, lvl - thr_db)
    g = db(-over * (1 - 1 / ratio))
    return x * (g if x.ndim == 1 else g[:, None])


def multiband_duck(mus, voice, depth=(3, 10, 5)):
    """under speech, carve the music's midrange (where the voice lives) and dip the ends a little"""
    env = envelope(voice, 0.03, 0.4); k = np.clip(env / 0.05, 0, 1)
    lo = sosfiltfilt(butter(4, 250, 'lowpass', fs=SR, output='sos'), mus, axis=0)
    hi = sosfiltfilt(butter(4, 4000, 'highpass', fs=SR, output='sos'), mus, axis=0)
    mid = mus - lo - hi
    g = [db(-d * k)[:, None] for d in depth]
    return lo * g[0] + mid * g[1] + hi * g[2]


# ── the mix ──────────────────────────────────────────────────────────────────────────────────────────────────────
def mix(edl, T, version, narration=True, meta=None):
    meta = meta or {}
    n = int((T + 1.0) * SR); S = starts(edl)
    ids = set(S)
    V = np.zeros(n, np.float32); VO = np.zeros(n, np.float32)
    FX = np.zeros((n, 2), np.float32); BED = np.zeros(n, np.float32); MUS = np.zeros((n, 2), np.float32)
    def put(buf, x, t):
        if buf.ndim == 2 and x.ndim == 1: x = np.stack([x, x], 1)
        i = int(t * SR)
        if i >= n or i + len(x) <= 0: return
        j0 = max(0, -i); x = x[j0:]; i = max(0, i)
        buf[i:i + len(x)] += x[:n - i]
    # voices
    for c in edl:
        t0 = S[c['id']][0]
        for v in c.get('vo', []):
            ts, lid = v[0], v[1]; sync = len(v) > 2 and v[2] == 'sync'
            if not sync and not narration: continue
            x = voice_chain(A.load(f"{meta['vo_dir']}/{lid}.mp3"), sync)
            put(V if sync else VO, x * db(-1), t0 + ts)
        # ambience beds (the old palette plus the new ones)
        m = int(c['dur'] * SR) + int(0.2 * SR)
        a = field_bed(m) if c.get('amb') == 'field' else A.amb(c.get('amb'), m)
        f = int(0.15 * SR); a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
        put(BED, a, t0)
        for ts, name in c.get('sfx', []):
            x = ignite() if name == 'ignite' else A.sfx(name)
            put(FX, x if x.ndim == 2 else np.stack([x, x], 1), t0 + ts)
    # picture-synced design
    fast = [k for k in ('B2', 'B3', 'B4', 'B5', 'B7', 'B9', 'B10') if k in ids]
    for k, cid in enumerate(fast): put(FX, whoosh(0.8, up=k % 2 == 0, lr=k % 2 == 0), S[cid][0] - 0.45)
    for cid in [c['id'] for c in edl if c['id'].startswith('E') and c['id'] not in ('E1', 'E13', 'E19', 'E20')]: put(FX, tick(), S[cid][0])
    for cid in ('E1', 'E13', 'E19'):
        if cid in ids: put(FX, swell(S[cid][1] - S[cid][0] + 1.5, -18), S[cid][0] - 0.5)
    if 'B12' in ids: put(FX, sub_drop(), S['B12'][0])
    if 'A2' in ids:
        TL = S['A2'][0] + 2.46  # the lights come on
        put(FX, A.sfx('riser'), TL - 2.0); put(FX, np.stack([A.sfx('impact')] * 2, 1), TL); put(FX, breaker(), TL - 0.02)
    else: TL = 0.0
    if 'F1' in ids and 'F6' in ids: put(MUS, night_bed(S['F6'][0] + 1.7 - S['F1'][0] + 0.4), S['F1'][0])
    if 'G2' in ids: put(FX, np.stack([A.sfx('impact')] * 2, 1) * 1.2, S['G2'][1] - 0.05)
    if 'H1' in ids: put(FX, np.stack([A.sfx('optical')] * 2, 1), S['H1'][0] + 0.45)
    # music: hero from the lights to the name, tech under the customer and the explainer, end from the planet on
    def cue(name, start, end, loop, level=0.0, fade_out=0.8, tail_hit=None):
        x = stereo_load(f'gen/v4/music/{name}.mp3'); beat, first = beat_grid(x)
        L = end - start
        if tail_hit is not None:  # stretch so the cue's final hit (at tail_hit s) lands on `end`
            y = fit(x, len(x) / SR + (L - tail_hit), *loop, beat, first)
        else:
            y = fit(x, L + fade_out, *loop, beat, first)
        g = np.ones(len(y), np.float32); fo = int(fade_out * SR)
        if tail_hit is None and fo: g[-fo:] = np.linspace(1, 0, fo)
        put(MUS, y * g[:, None] * db(level), start)
        return beat
    if 'A2' in ids and 'B14' in ids: cue('hero-2', TL, S['B14'][0] + 0.05, (5.0, 21.0), level=-1.0, tail_hit=35.0)
    if 'C1' in ids and 'D6' in ids: cue('tech-1', S['C1'][0], S['D6'][1] + 0.5, (16.0, 44.0), level=-4.0)
    if 'E1' in ids and 'F1' in ids:
        x = stereo_load('gen/v4/music/end-1.mp3'); beat, first = beat_grid(x)
        planet = fit(x, S['F1'][0] - S['E1'][0] + 1.2, 4.0, 26.0, beat, first); fo = int(1.2 * SR); planet[-fo:] *= np.linspace(1, 0, fo)[:, None]
        put(MUS, planet * db(-1.5), S['E1'][0])
        if 'F6' in ids and 'G2' in ids:  # after the night: back in, full, on the ignition
            t_ign = S['F6'][0] + 1.7; t_end = S['G2'][1] + 0.1
            i0 = snap(36.0, beat, first); seg = x[int(i0 * SR):]
            need = int((t_end - t_ign + 1.0) * SR)
            if len(seg) < need: seg = np.concatenate([seg, np.zeros((need - len(seg), 2), np.float32)])
            seg = seg[:need].copy(); fo = int(0.6 * SR); seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
            put(MUS, seg * db(0.5), t_ign)
    # the mix
    voice = V + VO
    MUS = multiband_duck(MUS, voice)
    dia = np.stack([V, V], 1); nar = np.stack([VO, VO], 1)
    bed = np.stack([BED, BED], 1) * db(-2)
    total = dia + nar + MUS * db(-2.0) + FX + bed
    total = compress(total, -16, 2.0, 0.02, 0.25)  # glue
    tail = np.clip((T - np.arange(n) / SR) / 0.8, 0, 1)[:, None]
    total *= tail
    os.makedirs(meta.get('stems_dir', 'out/stems-v4'), exist_ok=True)
    def wav(path, x):
        subprocess.run([A.FF, '-loglevel', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', path], input=x.astype(np.float32).tobytes(), check=True)
    raw = f"out/.{meta.get('tag', '')}{version}-mix-raw.wav"; out = f"out/.{meta.get('tag', '')}{version}-mix.wav"
    wav(raw, total)
    r = subprocess.run([A.FF, '-hide_banner', '-i', raw, '-af', 'loudnorm=I=-16:TP=-1.5:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex('{'):r.rindex('}') + 1]); gain = -16.0 - float(m['input_i'])
    subprocess.run([A.FF, '-loglevel', 'error', '-y', '-i', raw, '-af', f"volume={gain:.2f}dB,alimiter=limit=0.78:attack=1:release=50:level=false", '-ar', str(SR), out], check=True)
    if version == 'master':
        sd = meta.get('stems_dir')
        for k, x in (('dialogue', dia), ('narration', nar), ('music', MUS * db(-2.0)), ('effects-ambience', FX + bed)): wav(f'{sd}/{k}.wav', x * tail)
    return out
