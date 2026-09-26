#!/bin/bash
# v2 end to end once fal has credit: stills → motion + voices → lip-sync → compositing of every version.
# Each fal stage skips outputs that already exist, so this can be re-run after any failure.
set -e
cd "$(dirname "$0")/.."
. /tmp/claude-1000/-home-brandonin-Documents-phaser-design/d5f9ebeb-f3e5-46ca-9bfd-d4a3fb3e83c8/scratchpad/fv/bin/activate
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
python src/prompts_v2.py && python src/script_v2.py
fail() { grep -q "^FAIL\|^TIMEOUT" "$1" && { echo "fal stage failed:"; grep "^FAIL\|^TIMEOUT" "$1"; exit 1; } || true; }
python src/jobs.py gen/v2/stills.json -j 4 > /dev/null || true; python src/jobs.py gen/v2/stills.json -j 4 | tee out/.v2-stills.log; fail out/.v2-stills.log
python - <<'PY'
from PIL import Image; import glob
for f in glob.glob('gen/v2/stills/*.png'): Image.open(f).convert('RGB').resize((1920, 1072)).save(f[:-4] + '.jpg', quality=93)
PY
python src/jobs.py gen/v2/vo.json -j 5 > /dev/null || true; python src/jobs.py gen/v2/vo.json -j 5 | tee out/.v2-vo.log; fail out/.v2-vo.log
python src/jobs.py gen/v2/video.json -j 5 > /dev/null || true; python src/jobs.py gen/v2/video.json -j 5 | tee out/.v2-video.log; fail out/.v2-video.log
python src/lipsync_v2.py && python src/jobs.py gen/v2/ls.json -j 5 | tee out/.v2-ls.log; fail out/.v2-ls.log
echo "fal stages done"
