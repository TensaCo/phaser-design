#!/bin/bash
# v2: every version after the master, sequentially (CPU cap), then 4K upscale, a share copy and keyframes.
set -e
cd "$(dirname "$0")/.."
. /tmp/claude-1000/-home-brandonin-Documents-phaser-design/d5f9ebeb-f3e5-46ca-9bfd-d4a3fb3e83c8/scratchpad/fv/bin/activate
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
E=--edl=edl_v3
cp out/.edl_v3-master-video.mp4 out/.edl_v3-nonarr-video.mp4 && python src/compose.py nonarr $E --audio
for v in cut60 cut30 cut15 cut60v cut30v cut15v vertical notype; do python src/compose.py $v $E; done
M=out/PHASER-launch-film-master-1080p-v3.mp4
src/ffmpeg -loglevel error -y -i $M -vf scale=3840:2160:flags=lanczos -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -threads 4 -c:a copy -movflags +faststart out/PHASER-launch-film-master-2160p-v3.mp4
src/ffmpeg -loglevel error -y -i $M -c:v libx264 -preset slow -crf 24 -threads 4 -c:a copy -movflags +faststart out/PHASER-launch-film-share-1080p-v3.mp4
python - <<'PY'
import sys, subprocess, os; sys.argv = ['x']; sys.path.insert(0, 'src')
from edl_v3 import EDL
os.makedirs('out/keyframes-v3', exist_ok=True); t = 0
for c in EDL:
    subprocess.run(['src/ffmpeg', '-loglevel', 'error', '-y', '-ss', f"{t + c['dur'] * 0.55:.3f}", '-i', 'out/PHASER-launch-film-master-1080p-v3.mp4', '-frames:v', '1', '-q:v', '2', f"out/keyframes-v3/{c['id']}.jpg"])
    t += c['dur']
PY
echo FINALIZE V3 DONE
