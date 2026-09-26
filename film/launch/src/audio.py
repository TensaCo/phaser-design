"""Sound: dialogue/narration placement, synthesized ambiences and effects, a restrained score, the mix, and stems.
Everything except the voices is synthesized here (no library music or samples), so there is nothing to license."""
import os, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from script import LINES

SR = 48000
FF = os.path.join(os.path.dirname(__file__), 'ffmpeg')
SPEAKER = {i: s for i, s, _ in LINES}
rng = np.random.default_rng(3)


def load(path):
    raw = subprocess.run([FF, '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def bp(x, lo=None, hi=None, order=2):
    if lo and hi: sos = butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
    elif lo: sos = butter(order, lo, 'highpass', fs=SR, output='sos')
    else: sos = butter(order, hi, 'lowpass', fs=SR, output='sos')
    return sosfilt(sos, x)

def noise(n): return rng.standard_normal(n).astype(np.float32)
def pink(n):
    w = np.fft.rfft(noise(n)); f = np.arange(len(w)); f[0] = 1
    return (np.fft.irfft(w / np.sqrt(f), n) * 30).astype(np.float32)
def brown(n):
    x = np.cumsum(noise(n)) ; x = bp(x - np.convolve(x, np.ones(4800) / 4800, 'same'), lo=20); return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)
def tone(n, f, a=1.0, ph=0.0): return (a * np.sin(2 * np.pi * f * np.arange(n) / SR + ph)).astype(np.float32)
def hum(n, f0, amps): return sum(tone(n, f0 * (k + 1), a) for k, a in enumerate(amps))
def db(x): return 10 ** (x / 20)

def reverb(x, secs=2.2, mix=0.3, damp=4000):
    n = int(secs * SR); ir = noise(n) * np.exp(-np.arange(n) / (SR * secs / 6.9)); ir = bp(ir, hi=damp); ir /= np.abs(ir).sum() ** 0.5 * 12
    return (1 - mix) * x + mix * fftconvolve(x, ir)[:len(x)]

def room(x, secs=0.35, mix=0.14):
    return reverb(x, secs, mix, 6000)


# ── ambiences (mono, per clip) ────────────────────────────────────────────────────────────────────────────────────────
def amb(kind, n):
    t = np.arange(n) / SR
    if kind in ('none', None): return np.zeros(n, np.float32)
    if kind == 'studio': return bp(pink(n), 40, 600) * db(-66)
    if kind == 'crt': return (tone(n, 15734, 1) * db(-58) + hum(n, 60, [1, .5, .3]) * db(-50) + bp(pink(n), 80, 3000) * db(-60))  # a CRT's line whine and hum
    if kind == 'space': return bp(brown(n), hi=120) * db(-44)
    if kind == 'studio_room': return bp(pink(n), 60, 3000) * db(-58)  # a quiet sound stage
    if kind == 'elec':
        ramp = np.linspace(0.2, 1.0, n)
        crack = np.zeros(n, np.float32); idx = rng.integers(0, n, int(n / SR * 30)); crack[idx] = rng.uniform(-1, 1, len(idx))
        crack = bp(crack, 2000, 9000) * 3
        return ramp * (hum(n, 60, [0.5, 0.3, 0.25, 0.1, 0.08]) * db(-38) + bp(brown(n), hi=300) * db(-34) + crack * db(-30) * ramp)
    if kind == 'fans': return bp(noise(n), 200, 3500) * db(-26) + hum(n, 120, [1, .4, .2]) * db(-34)
    if kind == 'garage':
        tick = np.zeros(n, np.float32)
        for s in rng.uniform(0, n / SR, max(1, int(n / SR / 4))): i = int(s * SR); tick[i:i + 300] += bp(noise(300), 1500, 6000) * np.exp(-np.arange(300) / 60)
        return bp(pink(n), 60, 1800) * db(-46) + hum(n, 60, [.4, .6, .2]) * db(-58) + tick[:n] * db(-44)
    if kind == 'office':
        clicks = np.zeros(n, np.float32)
        s = 0.3
        while s < n / SR - 0.1:
            i = int(s * SR); clicks[i:i + 240] += bp(noise(240), 1500, 7000) * np.exp(-np.arange(240) / 40); s += rng.exponential(0.25) + (rng.random() < 0.1) * 1.5
        return bp(pink(n), 80, 2500) * db(-44) + clicks * db(-50)
    if kind == 'datacenter': return bp(noise(n), 150, 6000) * db(-30) + hum(n, 120, [1, .5, .3, .2]) * db(-36)
    if kind == 'transformer': return hum(n, 120, [1, .55, .35, .2, .12, .08]) * db(-24) * (1 + 0.05 * np.sin(2 * np.pi * 0.3 * t)) + bp(pink(n), 100, 1500) * db(-44)
    if kind == 'wind': return bp(pink(n), 60, 900) * db(-34) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.17 * t + 1))
    if kind == 'hospital':
        beep = np.zeros(n, np.float32)
        for s in np.arange(0.4, n / SR, 1.1): i = int(s * SR); m = min(n - i, 3600); beep[i:i + m] += tone(m, 988) * np.exp(-np.arange(m) / 900)
        return bp(noise(n), 150, 2500) * db(-40) + beep * db(-40)
    if kind == 'pumps': return hum(n, 50, [1, .7, .4, .3, .2]) * db(-30) + bp(noise(n), 100, 1200) * db(-38)
    if kind == 'refrigeration': return hum(n, 100, [1, .5, .2]) * db(-36) + bp(noise(n), 300, 4000) * db(-42)
    if kind == 'store': return bp(pink(n), 200, 3000) * db(-40) + np.where((t % 1.7) < 0.08, tone(n, 2800), 0) * db(-44)
    if kind == 'steel': return bp(brown(n), hi=500) * db(-24) + bp(noise(n), 2000, 8000) * db(-40) * (rng.random(n) < 0.002) * 8
    if kind == 'city': return bp(pink(n), 40, 700) * db(-40)
    return np.zeros(n, np.float32)


# ── effects ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def sfx(name):
    if name in ('optical', 'optical_soft'):
        n = int(3.5 * SR); t = np.arange(n) / SR
        env = np.minimum(1, t / 0.004) * np.exp(-t / 0.9)
        x = (tone(n, 1760) + 0.5 * tone(n, 2640) + 0.25 * tone(n, 3520) + 0.15 * tone(n, 5280)) * env
        x += tone(n, 55) * np.minimum(1, t / 0.01) * np.exp(-t / 0.25) * 0.6
        x = reverb(x, 3.0, 0.45, 9000)
        return x * (db(-16) if name == 'optical' else db(-27))
    if name in ('cavity', 'cavity_fast'):
        secs = 6.0; n = int(secs * SR); x = np.zeros(n, np.float32); s = 0.2
        while s < secs - 0.1:
            i = int(s * SR); m = 900
            x[i:i + m] += tone(m, 3520) * np.exp(-np.arange(m) / 150)
            gap = 0.8 if name == 'cavity' else max(0.03, 0.8 * max(0.0, 1 - s / 4.2) ** 2.2)
            s += gap
        return reverb(x, 1.5, 0.35, 9000) * db(-30)
    if name == 'riser':  # 2 s swell that lands on an impact placed 2 s later
        n = 2 * SR; t = np.arange(n) / SR
        sw = bp(noise(n), 800, 9000) * (t / 2) ** 3 * db(-18)
        pitch = np.sin(2 * np.pi * np.cumsum(220 + 880 * (t / 2) ** 2) / SR) * (t / 2) ** 2.5 * db(-26)
        return reverb(sw + pitch, 1.2, 0.3)
    if name == 'impact':  # sub boom + a bright transient, long tail
        n = int(4 * SR); t = np.arange(n) / SR
        boom = np.sin(2 * np.pi * (38 + 30 * np.exp(-t * 9)) * t) * np.exp(-t * 1.6)
        hit = bp(noise(n), 1500, 12000) * np.exp(-t * 28)
        return reverb(boom * db(-7) + hit * db(-16), 3.0, 0.35, 7000)
    if name in ('click', 'key', 'plug'):
        m = 3000; c = bp(noise(m), 2500, 8000) * np.exp(-np.arange(m) / 90) + tone(m, 4200) * np.exp(-np.arange(m) / 300) * 0.3
        if name == 'plug': c = np.concatenate([c, np.zeros(2400, np.float32), c * 0.7, bp(noise(4800), hi=300) * np.exp(-np.arange(4800) / 600) * 2])
        return room(c) * (db(-26) if name != 'key' else db(-30))
    return np.zeros(1, np.float32)


# ── score ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
CHORDS = [[146.83, 220.0, 329.63, 440.0], [116.54, 174.61, 293.66, 440.0], [174.61, 261.63, 349.23, 523.25], [130.81, 196.0, 293.66, 392.0]]
def score(n, level):
    """slow pad (additive, detuned, soft attack) cycling D–Bb–F–C every 8 s, plus the PHASER tone (a clean A5 with a
    slight shimmer) that grows toward the end. `level` is a per-sample envelope from the EDL."""
    t = np.arange(n) / SR; pad = np.zeros(n, np.float32); step = 8 * SR
    for k in range(0, n, step):
        m = min(step + SR * 2, n - k); tt = np.arange(m) / SR
        env = np.minimum(1, tt / 2.5) * np.minimum(1, np.maximum(0, (m / SR - tt) / 2.0))
        ch = CHORDS[(k // step) % 4]
        for f in ch:
            for det, a in ((1.0, 1.0), (1.003, 0.5), (0.997, 0.5), (2.0, 0.12)):
                pad[k:k + m] += (a * env * np.sin(2 * np.pi * f * det * tt + rng.uniform(0, 6))).astype(np.float32)
    pad = bp(pad, 60, 2200) * db(-30)
    motif = tone(n, 880) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t)) * db(-40)
    grow = np.clip((t - (n / SR - 50)) / 30, 0, 1)
    return (pad * level + motif * level * grow).astype(np.float32)


def load_stereo(path):
    raw = subprocess.run([FF, '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def mix(edl, T, version, narration=True, meta=None):
    """meta (v2): vo_dir, speakers {line: speaker}, score (path to the composed score, starts at 0:00), score_db"""
    meta = meta or {}
    if meta.get('mixer') == 'v4':
        import audio_v4
        return audio_v4.mix(edl, T, version, narration, meta)
    speakers = meta.get('speakers', SPEAKER); vo_dir = meta.get('vo_dir', 'gen/vo')
    n = int((T + 0.5) * SR)
    dia, nar, fx, bed, lvl = (np.zeros(n, np.float32) for _ in range(5))
    t0 = 0.0
    fade = int(0.15 * SR)
    for c in edl:
        i0, m = int(t0 * SR), int(c['dur'] * SR)
        a = amb(c.get('amb'), m + fade)
        a[:fade] *= np.linspace(0, 1, fade); a[-fade:] *= np.linspace(1, 0, fade)
        bed[i0:i0 + len(a)] += a[:n - i0]
        lvl[i0:i0 + m] = c.get('music', 0.0)
        for ts, name in c.get('sfx', []):
            x = sfx(name); j = int((t0 + ts) * SR); fx[j:j + len(x)] += x[:max(0, n - j)]
        for v_ in c.get('vo', []):
            ts, lid = v_[0], v_[1]; sync = len(v_) > 2 and v_[2] == 'sync'
            x = load(f'{vo_dir}/{lid}.mp3'); spk = speakers[lid]
            if spk == 'NAR' or (meta and not sync):  # narration, or (v2) any voice-over
                if not narration: continue
                x = reverb(x, 0.6, 0.06, 9000); tgt = nar
            else:
                x = room(x, 0.35 if c.get('amb') == 'garage' else 0.25, 0.12 if c.get('amb') == 'garage' else 0.08); tgt = dia
            j = int((t0 + ts) * SR); tgt[j:j + len(x)] += x[:max(0, n - j)]
        t0 += c['dur']
    # smooth the score level, then duck it under voices
    k = int(1.2 * SR); lvl = np.convolve(lvl, np.ones(k) / k, 'same')
    voice = np.convolve(np.abs(dia) + np.abs(nar), np.ones(int(0.3 * SR)) / (0.3 * SR), 'same')
    duck = 1 - 0.45 * np.clip(voice / 0.02, 0, 1)
    if meta.get('score'):
        sc = load_stereo(meta['score'])[:n]
        mus2 = np.zeros((n, 2), np.float32); mus2[:len(sc)] = sc
        g = db(meta.get('score_db', -4.0)) * np.convolve(np.clip(1 - 0.68 * np.clip(voice / 0.02, 0, 1), 0, 1), np.ones(int(0.25 * SR)) / (0.25 * SR), 'same')
        if meta.get('score_automation'):
            kt, kv = zip(*meta['score_automation']); g = g * db(np.interp(np.arange(n) / SR, kt, kv)).astype(np.float32)
        mus2 *= g[:, None]
        mus = mus2.mean(1)
    else:
        mus2 = None
        mus = score(n, lvl) * duck
    # every version ends in near silence: the last second fades
    tail = np.clip((T - np.arange(n) / SR) / 1.2, 0, 1)
    stems = {'dialogue': dia * db(-1), 'narration': nar * db(0), 'music': mus, 'effects-ambience': (fx + bed) * tail}
    total = (stems['dialogue'] + stems['narration'] + stems['effects-ambience'] + (0 if mus2 is not None else mus)) * tail
    os.makedirs('out/stems', exist_ok=True)
    def wav(path, x):
        st = np.stack([x, x], 1) if x.ndim == 1 else x
        subprocess.run([FF, '-loglevel', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', path], input=st.astype(np.float32).tobytes(), check=True)
    tagv = meta.get('tag', ''); raw = f'out/.{tagv}{version}-mix-raw.wav'; out = f'out/.{tagv}{version}-mix.wav'
    # stereo: decorrelate the beds a little
    L = total.copy(); R = total.copy(); R += 0.15 * (bp(stems['effects-ambience'], 200) - np.roll(bp(stems['effects-ambience'], 200), 480))
    if mus2 is not None: L += mus2[:, 0] * tail; R += mus2[:, 1] * tail
    wav(raw, np.stack([L, R], 1))
    # two-pass linear loudness normalisation (keeps the film's dynamics: silence stays silent), then a true-peak limiter
    import json as _j
    r = subprocess.run([FF, '-hide_banner', '-i', raw, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=20:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = _j.loads(r[r.rindex('{'):r.rindex('}') + 1])
    gain = -16.0 - float(m['input_i'])  # plain linear gain to -16 LUFS; the limiter catches the few peaks above -1.5 dBTP
    af = f"volume={gain:.2f}dB,alimiter=limit=0.84:attack=2:release=60:level=false"
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', raw, '-af', af, '-ar', str(SR), out], check=True)
    if version == 'master':
        sd = meta.get('stems_dir', 'out/stems'); os.makedirs(sd, exist_ok=True)
        for k2, x in stems.items():
            if k2 == 'music' and mus2 is not None: wav(f'{sd}/{k2}.wav', mus2 * tail[:, None])
            else: wav(f'{sd}/{k2}.wav', x * tail)
    return out
