#!/bin/bash
# Experiment 22 (2026-09-23): B-4f absorbing-mask memory sweep; waits for the Exp. 21a sweep (one CPU lane).
cd "$(dirname "$0")"
while pgrep -f 21-xg-memory.sh > /dev/null; do sleep 30; done
npx vite-node 22-b4f-amp.ts 1,2,3,4 1,2,3,4 1.8,2.2,2.6,3,3.5,4 -0.8:0.2 3000 sweep > out/22/logs/sweep.log 2>&1
echo 22 done
