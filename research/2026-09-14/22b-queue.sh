#!/bin/bash
# Experiment 22 follow-up (2026-09-23): the B-4f points that held to 3000 trips, run to 3×10⁴; a second absorber operating
# point; and a 128² grid (4 mm window) check of FFT wrap-around. Slot-limited (wait-slot.sh).
cd "$(dirname "$0")"
source ./wait-slot.sh
while pgrep -f 22-queue.sh > /dev/null; do sleep 30; done
wait_slot; npx vite-node 22-b4f-amp.ts 3 2,4 3,3.5 -0.8:0.2 30000 long > out/22/logs/long.log 2>&1
wait_slot; npx vite-node 22-b4f-amp.ts 3,4 2,3,4 2.2,2.6,3,3.5 -0.6:0.05,-0.9:0.3 3000 absorbers > out/22/logs/absorbers.log 2>&1
wait_slot; npx vite-node 22-b4f-amp.ts 3 2,4 3 -0.8:0.2 3000 grid128 128 > out/22/logs/grid128.log 2>&1
echo 22b done
