#!/bin/bash
# One batched design job on the compute peer, then float64 every-trip verification of all its designs to 1e4 trips.
# usage: run-job.sh <task> '<json with "tag">'      (queues: xargs -P over a jobs file, see queue.sh)
cd "$(dirname "$0")"
PY=${PHASER_PY:-/home/brandonin/work/ext/venvs/psi/bin/python}
task=$1; json=$2
tag=$($PY -c "import json,sys;print(json.loads(sys.argv[1])['tag'])" "$json")
mkdir -p out/logs out/verify
if [ ! -f "out/designs/${tag}_run.json" ]; then $PY design.py "$task" "$json" 2>&1 | grep --line-buffered -v -e UserWarning -e "Triggered internally" > "out/logs/${tag}.log"; fi
[ -f "out/designs/${tag}_run.json" ] && $PY verify.py "out/designs/${tag}_d*_spec.json" --H ${VERIFY_H:-10000} --out "out/verify/${tag}_1e4.json" 2>&1 | grep --line-buffered -v Warn > "out/logs/verify_${tag}.log"
echo "done $tag: $(grep -c PASS out/logs/verify_${tag}.log 2>/dev/null) designs pass 1e4"
