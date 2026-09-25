#!/bin/bash
# After the master: the other versions (sequential, to respect the CPU cap), the 4K upscale and keyframes.
set -e
cd "$(dirname "$0")/.."
. /tmp/claude-1000/-home-brandonin-Documents-phaser-design/d5f9ebeb-f3e5-46ca-9bfd-d4a3fb3e83c8/scratchpad/fv/bin/activate
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
cp out/.master-video.mp4 out/.nonarr-video.mp4 && python src/compose.py nonarr --audio
for v in cut60 cut30 cut15 cut60v cut30v cut15v vertical notype; do python src/compose.py $v; done
src/ffmpeg -loglevel error -y -i out/PHASER-launch-film-master-1080p.mp4 -vf scale=3840:2160:flags=lanczos -c:v libx264 -preset slow -crf 16 \
  -pix_fmt yuv420p -threads 4 -c:a copy -movflags +faststart out/PHASER-launch-film-master-2160p.mp4
python - <<'PY'
import sys, subprocess; sys.path.insert(0, 'src')
from edl import EDL
import os; os.makedirs('out/keyframes', exist_ok=True); t = 0
for c in EDL:
    m = t + c['dur'] * 0.55
    subprocess.run(['src/ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{m:.3f}', '-i', 'out/PHASER-launch-film-master-1080p.mp4', '-frames:v', '1', '-q:v', '2', f"out/keyframes/{c['id']}.jpg"])
    t += c['dur']
PY
echo FINALIZE DONE
