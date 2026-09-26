"""Average groups of SUB rendered sub-frames into one frame (true motion blur); the middle sub-frame's depth is kept."""
import glob, os, shutil, sys
import numpy as np
from PIL import Image
src, sub = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4
dst = src + '-blur'; os.makedirs(dst, exist_ok=True)
fs = sorted(f for f in glob.glob(src + '/*.png') if not f.endswith('.depth.png'))
for k in range(len(fs) // sub):
    grp = fs[k * sub:(k + 1) * sub]
    acc = sum(np.asarray(Image.open(f).convert('RGB')).astype(np.float32) for f in grp) / sub
    Image.fromarray(np.clip(acc + 0.5, 0, 255).astype(np.uint8)).save(f'{dst}/{k:05d}.png')
    mid = grp[sub // 2].replace('.png', '.depth.png')
    if os.path.exists(mid):
        shutil.copy(mid, f'{dst}/{k:05d}.depth.png'); shutil.copy(mid.replace('.png', '.txt'), f'{dst}/{k:05d}.depth.txt')
print(dst, len(fs) // sub)
