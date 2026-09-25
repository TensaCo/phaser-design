#!/bin/bash
# Exp. 32: wavefront (time-slot) multiplexing: M streams through one route with a shared gain (carrier time tau).
# One job per line of out/32/jobs.txt (JSON config for 30-run.ts), ≤ 5 jobs via wait-slot.sh.
cd "$(dirname "$0")"; source wait-slot.sh
while read -r j; do
  tag=$(python3 -c "import json,sys;print(json.loads(sys.argv[1])['tag'])" "$j")
  [ -f "out/32/${tag}_bits.json" ] && continue
  wait_slot
  npx vite-node 30-run.ts "$j" > "out/32/logs/$tag.log" 2>&1 &
  sleep 5
done < "${1:-out/32/jobs.txt}"
wait; echo done
