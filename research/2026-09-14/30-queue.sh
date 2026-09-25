#!/bin/bash
# Exp. 30: fair tuning of the optical reservoir (one factor at a time around Apre_lin K = 10) + the linear stack.
# One job per line of out/30/jobs.txt (JSON config for 30-run.ts); each waits for a free slot (wait-slot.sh, ≤ 5 jobs).
cd "$(dirname "$0")"; source wait-slot.sh
while read -r j; do
  tag=$(python3 -c "import json,sys;print(json.loads(sys.argv[1])['tag'])" "$j")
  [ -f "out/30/${tag}_bits.json" ] && continue
  wait_slot
  npx vite-node 30-run.ts "$j" > "out/30/logs/$tag.log" 2>&1 &
  sleep 5
done < "${1:-out/30/jobs.txt}"
wait; echo done
