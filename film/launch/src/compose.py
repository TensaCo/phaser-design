"""Compositor: EDL → graded frames + typography + the persistent label → H.264, and the sound mix (audio.py).
python src/compose.py <version>   versions: master | vertical | nonarr | notype | cut60 | cut30 | cut15 | cut60v ...
Every frame carries the centre label PLANNED FUTURE PRODUCT LAUNCH VIDEO (no version removes it)."""
import copy, glob, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
sys.path.insert(0, os.path.dirname(__file__))
from edl import EDL, CUTS

FF = os.path.join(os.path.dirname(__file__), 'ffmpeg')
FPS = 24
FONT = 'assets/fonts/'
PAPER, GRAPHITE, RED = (233, 229, 220), (138, 133, 124), (255, 42, 18)
LABEL = 'PLANNED FUTURE PRODUCT LAUNCH VIDEO'


def archivo(size, wght=600, wdth=100):
    f = ImageFont.truetype(FONT + 'Archivo-VF.ttf', size)
    try: f.set_variation_by_axes([wght, wdth])  # Archivo axes: Weight, Width
    except Exception: pass
    return f
def mono(size, weight='Regular'): return ImageFont.truetype(FONT + f'IBMPlexMono-{weight}.ttf', size)


def tracked(draw, xy, text, font, fill, track=0.0, anchor='ls'):
    """draw text with letter spacing (em); returns width. anchor: 'ls' left-baseline or 'ms' centre-baseline"""
    size = font.size
    widths = [draw.textlength(c, font=font) + track * size for c in text]
    w = sum(widths) - (track * size if text else 0)
    x, y = xy
    if anchor == 'ms': x -= w / 2
    for c, cw in zip(text, widths):
        draw.text((x, y), c, font=font, fill=fill, anchor='ls'); x += cw
    return w


def wrap(draw, text, font, maxw, track=0.0):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=font) + track * font.size * len(t) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    return lines + [cur]


def text_layer(W, H, item):
    """RGBA layer for one text item"""
    kind, content = item[2], item[3:]
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if kind in ('num', 'end', 'lower', 'note'):
        a = np.clip((np.arange(H) / H - 0.55) / 0.4, 0, 1) ** 1.5 * (190 if kind == 'end' else 150)
        sc = np.zeros((H, W, 4), np.uint8); sc[..., 3] = a[:, None].astype(np.uint8)
        im = Image.fromarray(sc, 'RGBA')
    d = ImageDraw.Draw(im)
    v = H > W; M = 80 if v else 150; s = 0.92 if v else 1.0
    if kind == 'line':
        f = archivo(int(64 * s), 500, 100)
        lines = wrap(d, content[0], f, W - 2 * M)
        y = H * (0.73 if v else 0.74)
        for k, ln in enumerate(lines): tracked(d, (W / 2, y + k * f.size * 1.2), ln, f, PAPER + (255,), -0.005, 'ms')
    elif kind == 'num':
        big, cap, q = content
        col = PAPER if 'weeks' in big else RED
        f = archivo(int(150 * s), 700, 75)
        y0 = H * (0.72 if v else 0.73)
        tracked(d, (M, y0), big, f, col + (255,), -0.01)
        fc = archivo(int(28 * s), 450, 100)
        y = y0 + 52 * s
        for ln in wrap(d, cap, fc, W - 2 * M): d.text((M, y), ln, font=fc, fill=PAPER + (240,), anchor='ls'); y += 36 * s
        fq = mono(int(19 * s), 'Medium')
        for ln in wrap(d, q.upper(), fq, W - 2 * M, 0.12): tracked(d, (M, y + 6), ln, fq, GRAPHITE + (255,), 0.12); y += 26 * s
    elif kind == 'lower':
        name, sub = content
        f = archivo(int(36 * s), 600, 100); fs = mono(int(16 * s), 'Medium')
        y = H * (0.80 if v else 0.83)
        d.text((M, y), name, font=f, fill=PAPER + (255,), anchor='ls')
        tracked(d, (M, y + 34 * s), sub.upper(), fs, PAPER + (190,), 0.12)
    elif kind == 'note':
        fs = mono(int(18 * s), 'Medium')
        y = H * (0.86 if v else 0.9)
        for ln in wrap(d, content[0].upper(), fs, W - 2 * M, 0.1): tracked(d, (M, y), ln, fs, PAPER + (220,), 0.1); y += 28 * s
    elif kind == 'slate':
        fs = mono(int(17 * s), 'Medium'); y = H * 0.88
        for ln in content: tracked(d, (M, y), ln, fs, GRAPHITE + (255,), 0.16); y += 28
    elif kind == 'credits':
        fs = mono(int(17 * s), 'Medium'); y = H * (0.66 if v else 0.68)
        for para in content:
            for ln in wrap(d, para.upper(), fs, W - 2 * M, 0.1):
                tracked(d, (W / 2, y), ln, fs, GRAPHITE + (255,), 0.1, 'ms'); y += 27 * s
            y += 12 * s
    elif kind == 'end':
        word, tag, url = content
        f = archivo(int(128 * s), 700, 75); ft = archivo(int(32 * s), 400, 100); fu = mono(int(19 * s), 'Medium')
        y = H * (0.73 if v else 0.74)
        tracked(d, (W / 2, y), word, f, PAPER + (255,), 0.06, 'ms')
        for k, ln in enumerate(wrap(d, tag, ft, W - 2 * M)): d.text((W / 2, y + 58 * s + k * 40 * s), ln, font=ft, fill=PAPER + (235,), anchor='ms')
        tracked(d, (W / 2, y + (126 if v else 112) * s), url.upper(), fu, GRAPHITE + (255,), 0.16, 'ms')
    return np.asarray(im).astype(np.float32) / 255


def label_layer(W, H):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    v = H > W
    lines = ['PLANNED FUTURE', 'PRODUCT LAUNCH VIDEO'] if v else [LABEL]
    f = mono(40 if v else 34, 'SemiBold'); tr = 0.14
    ws = [sum(d.textlength(c, font=f) + tr * f.size for c in ln) - tr * f.size for ln in lines]
    lh = f.size * 1.35; bw = max(ws) + 64; bh = lh * len(lines) + 34
    x0, y0 = (W - bw) / 2, (H - bh) / 2
    d.rectangle([x0, y0, x0 + bw, y0 + bh], fill=(0, 0, 0, 125), outline=PAPER + (170,), width=2)
    for k, ln in enumerate(lines): tracked(d, (W / 2, y0 + 17 + lh * (k + 0.78)), ln, f, PAPER + (245,), tr, 'ms')
    return np.asarray(im).astype(np.float32) / 255


def tag_layer(W, H, text):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    v = H > W; f = mono(15 if not v else 20, 'Medium'); M = 80 if v else 150
    w = sum(d.textlength(c, font=f) + 0.12 * f.size for c in text)
    tracked(d, (W - M - w, H * 0.06 + 10), text, f, PAPER + (175,), 0.12)
    return np.asarray(im).astype(np.float32) / 255


class Layer:
    """an RGBA overlay cropped to the rows/cols it touches"""
    def __init__(self, rgba):
        m = rgba[..., 3] > 0
        ys, xs = np.where(m.any(1))[0], np.where(m.any(0))[0]
        if len(ys) == 0: self.box = None; return
        self.box = (ys[0], ys[-1] + 1, xs[0], xs[-1] + 1)
        y0, y1, x0, x1 = self.box; c = rgba[y0:y1, x0:x1]
        self.a = c[..., 3:4].copy(); self.rgb = c[..., :3] * self.a

def over(img, layer, a=1.0):
    if not isinstance(layer, Layer): layer = Layer(layer)
    if layer.box is None or a <= 0: return img
    y0, y1, x0, x1 = layer.box
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - layer.a * a) + layer.rgb * a
    return img


# ── sources ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def frames_mp4(path, t_in, dur, speed, crop):
    n = int(round(dur * FPS)); src_len = dur * speed + 0.3
    vf = []
    if crop: x0, y0, x1, y1 = crop; vf.append(f'crop=iw*{x1 - x0}:ih*{y1 - y0}:iw*{x0}:ih*{y0}')
    vf.append('scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080')
    if speed != 1: vf += [f'setpts=PTS/{speed}', 'minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1']
    else: vf.append('fps=24')
    cmd = [FF, '-loglevel', 'error', '-ss', str(t_in), '-i', path, '-t', str(src_len), '-vf', ','.join(vf), '-threads', '4',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, 1080, 1920, 3)
    if len(arr) < n: arr = np.concatenate([arr, np.repeat(arr[-1:], n - len(arr), 0)])
    return arr[:n]


def frames_png(d, t_in, dur):
    fs = sorted(glob.glob(d + '/*.png')); n = int(round(dur * FPS)); k0 = int(round(t_in * FPS))
    return [fs[min(len(fs) - 1, k0 + i)] for i in range(n)]


# ── grading ───────────────────────────────────────────────────────────────────────────────────────────────────────────
VIG = {}
def vignette(W, H, k):
    key = (W, H, k)
    if key not in VIG:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); r = np.hypot((x - W / 2) / (W / 2), (y - H / 2) / (H / 2)) / 1.414
        VIG[key] = (1 - k * r ** 2.2)[..., None]
    return VIG[key]

rng = np.random.default_rng(1)
def grade(img, kind):
    H, W = img.shape[:2]
    if kind == 'studio':
        small = img[::4, ::4]
        glow = np.clip(small - 0.25, 0, None); glow[..., 1:] *= 0.35
        glow = gaussian_filter(glow, (5, 5, 0))
        img = img + 0.55 * np.repeat(np.repeat(glow, 4, 0), 4, 1)[:H, :W]
        img = np.clip((img - 0.012) / 0.988, 0, 1) * vignette(W, H, 0.28); g = 0.010
    elif kind == 'doc':
        lum = img.mean(2, keepdims=True); img = lum + (img - lum) * 0.9
        img = 0.018 + img * 0.97; img = img + 0.06 * (img - 0.5) * (1 - np.abs(2 * img - 1))
        img = img * np.array([1.012, 1.0, 0.985], np.float32); img = img * vignette(W, H, 0.18); g = 0.022
    elif kind == 'world':
        lum = img.mean(2, keepdims=True); img = lum + (img - lum) * 0.8
        img = 0.014 + img * 0.975; img = img * vignette(W, H, 0.16); g = 0.02
    else:
        img = img * vignette(W, H, 0.2); g = 0.008
    noise = grain(H, W)
    lum = img[..., 1:2]
    img += (g * noise) * (0.35 + 0.65 * lum)
    return np.clip(img, 0, 1, out=img)

GRAIN = {}
def grain(H, W):
    """16 precomputed grain frames (2-px grain), picked at random each frame"""
    if (H, W) not in GRAIN:
        GRAIN[(H, W)] = [np.repeat(np.repeat(rng.standard_normal((H // 2, W // 2), dtype=np.float32), 2, 0), 2, 1)[:H, :W, None] for _ in range(16)]
    return GRAIN[(H, W)][rng.integers(16)]


def zoom(img, z, cx=0.5, cy=0.5):
    if abs(z - 1) < 1e-4: return img
    H, W = img.shape[:2]; w, h = W / z, H / z
    x0 = min(max(0, cx * W - w / 2), W - w); y0 = min(max(0, cy * H - h / 2), H - h)
    im = Image.fromarray((img * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))
    return np.asarray(im).astype(np.float32) / 255


# ── build ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def build_edl(version):
    base = version.replace('v', '') if version.endswith('v') and version.startswith('cut') else version
    if base.startswith('cut'):
        by = {c['id']: c for c in EDL}; out = []
        for cid, ov in CUTS[base]:
            c = copy.deepcopy(by[cid]); c.update(ov); out.append(c)
        return out
    return copy.deepcopy(EDL)


def render(version):
    vertical = version == 'vertical' or version.endswith('v') and version.startswith('cut')
    notype = version == 'notype'
    W, H = (1080, 1920) if vertical else (1920, 1080)
    edl = build_edl(version)
    os.makedirs('out', exist_ok=True)
    silent = f'out/.{version}-video.mp4'
    enc = subprocess.Popen([FF, '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                            '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-threads', '4',
                            '-movflags', '+faststart', silent], stdin=subprocess.PIPE)
    label = Layer(label_layer(W, H))
    tags = {'people': Layer(tag_layer(W, H, 'DRAMATIZATION · AI-GENERATED PEOPLE, PLACES AND VOICES')),
            'gen': Layer(tag_layer(W, H, 'AI-GENERATED IMAGERY')),
            'stock': Layer(tag_layer(W, H, 'STOCK FOOTAGE'))}
    t_total = 0
    for c in edl:
        dur, t_in, speed = c['dur'], c.get('in', 0.0), c.get('speed', 1.0)
        n = int(round(dur * FPS))
        src = c['src']
        if src == 'black': frames = [None] * n
        elif src.startswith('png:'): frames = frames_png(src[4:], t_in, dur)
        else: frames = frames_mp4(src[4:], t_in, dur, speed, c.get('crop'))
        layers = [] if notype else [(it[0], it[1], Layer(text_layer(W, H, it))) for it in c.get('text', [])]
        tag = None
        if src.startswith('mp4:gen/'): tag = tags['people'] if c.get('people') else tags['gen']
        elif src.startswith('mp4:assets/stock'): tag = tags['stock']
        z0, z1 = c.get('push', (1.0, 1.0))
        for i in range(n):
            t = i / FPS
            f = frames[i]
            if f is None: img = np.zeros((1080, 1920, 3), np.float32)
            elif isinstance(f, str): img = np.asarray(Image.open(f).convert('RGB')).astype(np.float32) / 255
            else: img = f.astype(np.float32) / 255
            img = zoom(img, z0 + (z1 - z0) * i / max(1, n - 1))
            if src != 'black': img = grade(img, c.get('grade', 'doc'))
            if vertical:
                cw = 1080 * 1080 / 1920; cx = c.get('vx', 0.5) * 1920
                x0 = int(min(max(0, cx - cw / 2), 1920 - cw))
                img = np.asarray(Image.fromarray((img[:, x0:x0 + int(cw)] * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
            for t0, t1, L in layers:
                if t0 <= t <= t1:
                    a = min(1, (t - t0) / 0.45, (t1 - t) / 0.35)
                    img = over(img, L, max(0, a))
            if tag is not None: img = over(img, tag, 1.0)
            if c.get('fadeout') and t > dur - c['fadeout']: img = img * max(0, (dur - t) / c['fadeout'])
            img = over(img, label, 1.0)
            enc.stdin.write((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        t_total += dur
        print(f"{version} {c['id']} done t={t_total:.1f}s", flush=True)
    enc.stdin.close(); enc.wait()
    return silent, edl, t_total


if __name__ == '__main__':
    import audio
    v = sys.argv[1]
    only_audio = '--audio' in sys.argv
    if not only_audio: silent, edl, T = render(v)
    else: silent, edl = f'out/.{v}-video.mp4', build_edl(v); T = sum(c['dur'] for c in edl)
    wav = audio.mix(edl, T, v, narration=(v != 'nonarr'))
    names = {'master': 'PHASER-launch-film-master-1080p', 'vertical': 'PHASER-launch-film-9x16', 'nonarr': 'PHASER-launch-film-clean-no-narration',
             'notype': 'PHASER-launch-film-clean-no-typography', 'cut60': 'PHASER-launch-60s', 'cut30': 'PHASER-launch-30s', 'cut15': 'PHASER-reveal-15s',
             'cut60v': 'PHASER-launch-60s-9x16', 'cut30v': 'PHASER-launch-30s-9x16', 'cut15v': 'PHASER-reveal-15s-9x16'}
    out = f"out/{names.get(v, v)}.mp4"
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', silent, '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', out], check=True)
    print('wrote', out)
