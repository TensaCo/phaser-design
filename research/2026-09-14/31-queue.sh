#!/bin/bash
# Exp. 31: does the modes-per-unit equivalence hold at larger grids? Apre_lin (global gain, K = 10) at 64², 128², 256² with
# the relay aperture scaled with the window (Fresnel number ∝ modes), 16000 steps each (capacity tasks need more samples).
cd "$(dirname "$0")"; source wait-slot.sh
for n in 256 128 64; do
  a=$(python3 -c "print(1.2e-3*$n/64)")
  wait_slot
  npx vite-node 30-run.ts "{\"tag\":\"g$n\",\"dir\":\"31\",\"arch\":\"ring\",\"n\":$n,\"lensAperture\":$a,\"K\":10,\"steps\":16000,\"gain\":{\"kind\":\"global\",\"G0\":1.6,\"Is\":0.05}}" > out/31/logs/g$n.log 2>&1 &
  sleep 30
done
wait; echo done
