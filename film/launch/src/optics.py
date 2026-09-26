"""Photographic behaviour, applied after the grade so generated and rendered images read as photographed:
depth of field from the render's depth pass, handheld micro-motion, lens chromatic aberration, halation, exposure
breathing and rack focus. Everything is a pure function of (clip id, frame index): no unseeded randomness."""
import hashlib, math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom as ndzoom


def seed(*k):
    return int(hashlib.sha1('|'.join(map(str, k)).encode()).hexdigest()[:8], 16)


# ── depth of field ───────────────────────────────────────────────────────────────────────────────────────────────────
def load_depth(png):
    """linear distance (mm) from the 8-bit depth pass and its near/far sidecar; background → inf"""
    near, far, dist = map(float, open(png.replace('.png', '.txt')).read().split(','))
    v = np.asarray(Image.open(png))[..., 0].astype(np.float32) / 255
    zb = 1 - v  # BasicDepthPacking writes 1 - gl_FragCoord.z
    z = near * far / (far - zb * (far - near))
    z[v >= 0.995] = np.inf
    return z, dist


LEVELS = (0.0, 1.6, 3.5, 7.0, 12.0)
def depth_of_field(img, z, focus, strength):
    """thin-lens circle of confusion ∝ |1/z − 1/focus|; blend between a few blur levels"""
    with np.errstate(divide='ignore'):
        coc = strength * np.abs(1 / z - 1 / focus) * focus
    coc = np.clip(np.nan_to_num(coc, nan=0.0, posinf=LEVELS[-1]), 0, LEVELS[-1])
    coc = np.asarray(Image.fromarray(gaussian_filter(coc[::4, ::4], 1.0)).resize((coc.shape[1], coc.shape[0]), Image.BILINEAR))  # soften the depth edges
    out = np.zeros_like(img); wsum = np.zeros(img.shape[:2] + (1,), np.float32)
    H, W = img.shape[:2]
    for k, s in enumerate(LEVELS):
        if s == 0: b = img
        elif s < 2: b = gaussian_filter(img, (s, s, 0))
        else:  # larger blurs at reduced resolution (half, then quarter)
            r = 2 if s < 5 else 4
            q = gaussian_filter(img[::r, ::r], (s / r, s / r, 0))
            b = np.stack([np.asarray(Image.fromarray(q[..., c]).resize((W, H), Image.BILINEAR)) for c in range(3)], -1)
        w = np.clip(1 - np.abs(coc - s) / (LEVELS[min(k + 1, len(LEVELS) - 1)] - LEVELS[max(k - 1, 0)] + 1e-6) * 2, 0, 1)[..., None]
        out += b * w; wsum += w
    return out / np.maximum(wsum, 1e-4)


# ── camera ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def wobble(t, s, amp):
    r = np.random.default_rng(s)
    f = r.uniform([0.23, 0.51, 1.1, 5.7], [0.35, 0.8, 1.6, 7.3]); ph = r.uniform(0, 2 * np.pi, 4); a = np.array([1, 0.55, 0.22, 0.05])
    return amp * float(np.sum(a * np.sin(2 * np.pi * f * t + ph)))


def camera_motion(img, t, cid, kind):
    """handheld: a few px of drift and a hair of roll; 'breath': an interview on sticks (almost still)"""
    amp = {'handheld': 5.0, 'breath': 1.6, 'dolly': 0.8}.get(kind, 0)
    if not amp: return img
    H, W = img.shape[:2]
    dx, dy = wobble(t, seed(cid, 'x'), amp), wobble(t, seed(cid, 'y'), amp * 0.7)
    rot = math.radians(wobble(t, seed(cid, 'r'), amp * 0.03))
    z = 1 + (amp * 2.6 + 2) / W  # overscan so edges never show
    c, s_ = math.cos(rot) / z, math.sin(rot) / z
    cx, cy = W / 2, H / 2
    a, b, d, e = c, s_, -s_, c
    xo = cx - a * cx - b * cy + dx; yo = cy - d * cx - e * cy + dy
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).transform((W, H), Image.AFFINE, (a, b, xo, d, e, yo), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255


def lens(img, t, cid, ca=0.0009, halation=0.07, breathe=0.004):
    H, W = img.shape[:2]
    out = img.copy()
    # lateral chromatic aberration: red slightly larger, blue slightly smaller, about the centre
    for ch, k in ((0, 1 + 2 * ca),):  # red grows against green/blue; only enlarging, so no channel ever leaves an empty border
        a = 1 / k; cx, cy = W / 2, H / 2
        im = Image.fromarray((np.clip(img[..., ch], 0, 1) * 255).astype(np.uint8))
        out[..., ch] = np.asarray(im.transform((W, H), Image.AFFINE, (a, 0, cx - a * cx, 0, a, cy - a * cy), Image.BILINEAR)).astype(np.float32) / 255
    # halation: highlights bleed a warm glow into the emulsion
    if halation:
        q = out[::4, ::4]
        hl = np.clip(q.mean(2, keepdims=True) - 0.78, 0, None) * np.array([1.0, 0.42, 0.28], np.float32)
        hl = gaussian_filter(hl, (6, 6, 0))
        out += halation * np.repeat(np.repeat(hl, 4, 0), 4, 1)[:H, :W]
    # exposure breathing (auto-iris / shutter flicker), smooth
    out *= 1 + breathe * math.sin(2 * math.pi * 0.37 * t + seed(cid) % 7) + 0.002 * wobble(t, seed(cid, 'e'), 1)
    return out


def rack(img, t, dur=0.5, sigma=3.0):
    """a focus pull at the head of a shot: soft → sharp"""
    if t >= dur: return img
    s = sigma * (1 - t / dur) ** 2
    return gaussian_filter(img, (s, s, 0)) if s > 0.2 else img


# ── projection (for labels on the exploded view) ─────────────────────────────────────────────────────────────────────
def project(cam, p, W=1920, H=1080):
    pos, tgt = np.array(cam['pos'], float), np.array(cam['target'], float)
    f = tgt - pos; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    v = np.array(p, float) - pos
    x, y, zc = v @ r, v @ u, v @ f
    t = math.tan(math.radians(cam['fov']) / 2)
    return (W / 2 + (x / zc) / (t * W / H) * W / 2, H / 2 - (y / zc) / t * H / 2)
