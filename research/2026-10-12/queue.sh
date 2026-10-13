#!/bin/bash
# run a jobs file (lines "task|json") with N concurrent jobs on the peer's GPU. usage: queue.sh <jobs file> [N=3]
cd "$(dirname "$0")"
N=${2:-3}
while IFS='|' read -r t j; do [ -n "$t" ] && printf '%s\0%s\0' "$t" "$j"; done < "$1" | xargs -0 -n 2 -P "$N" ./run-job.sh
echo "queue $1 finished"
