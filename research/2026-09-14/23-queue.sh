#!/bin/bash
# Experiment 23 (2026-09-23): non-idealities on the persistent lattice, one at a time, then the 10⁶-trip noisy run.
# Waits for the Exp. 22 queue (one CPU lane).
cd "$(dirname "$0")"
while pgrep -f "22-queue.sh|21-xg-memory.sh" > /dev/null; do sleep 30; done
r() { local tag=$1 T=$2; shift 2; env "$@" npx vite-node 23-robust.ts "$T" "$tag" > "out/23/logs/$tag.log" 2>&1; }
r base 10000
for f in 0.001 -0.001 0.003 -0.003 0.005 -0.005 0.01; do r focal$f 10000 FOCAL=$f; done
for d in 0.001 0.01 0.03; do r dark$d 10000 DARK=$d; done
for n in 0.003 0.01 0.03; do r noise$n 10000 NOISE=$n; done
for p in 1000 100; do for s in 0.03 0.1 0.3; do r flicker${s}_p$p 10000 FLICKER=$s FLICKER_PERIOD=$p; done; done
r long1e6_noise1e-3 1000000 NOISE=0.001
echo 23 done
