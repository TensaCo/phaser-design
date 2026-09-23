#!/bin/bash
# One design job: torch design (skipped if its spec exists) then JS re-evaluation. usage: run-job.sh <task> '<json>' [horizon]
# Used by the 2026-09-23 finishing queues (xargs -P N over a jobs file). PHASER_DEVICE=cuda puts the twin on the GPU (default cpu).
cd "$(dirname "$0")"
source "${PHASER_VENV:-$HOME/.venvs/phaser}/bin/activate"
export TORCH_THREADS=${TORCH_THREADS:-1} OMP_NUM_THREADS=1 PHASER_DEVICE=${PHASER_DEVICE:-cpu}
[ "$PHASER_DEVICE" = cpu ] && export CUDA_VISIBLE_DEVICES=
task=$1; json=$2; horizon=${3:-10000}
tag=$(python3 -c "import json,sys;print(json.loads(sys.argv[1])['tag'])" "$json")
mkdir -p out/08/logs
if [ ! -f "out/08/${tag}_spec.json" ]; then python 08-design.py "$task" "$json" > "out/08/logs/${tag}.log" 2>&1; fi
[ -f "out/08/${tag}_spec.json" ] && npx vite-node 08-eval.ts "out/08/${tag}_spec.json" "$horizon" > "out/08/logs/eval_${tag}.log" 2>&1
if [ "$task" = assoc ] && [ -f "out/08/${tag}_spec.json" ]; then mkdir -p out/16/logs; npx vite-node 16-basin.ts "out/08/${tag}_spec.json" 3000 > "out/16/logs/basin_${tag}.log" 2>&1; fi
echo "done $tag"
