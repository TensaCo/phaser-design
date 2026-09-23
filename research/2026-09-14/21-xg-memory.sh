#!/bin/bash
# Experiment 21a (2026-09-23): does the absorbing-mask persistent memory survive cross-gain (carrier-diffusion) saturation?
# Hand-built 3 px cells / 3 px gaps, s −0.8, I_a 0.2, ideal contrast, 3000 trips, 3 seeds, sweep L_d × G0.
cd "$(dirname "$0")"
for L in 10e-6 20e-6 40e-6 60e-6 100e-6; do
  LD=$L npx vite-node 02-nl-amp.ts 3 3 2.6,3,3.4,4,5 -0.8:0.2 0 3000 xg_Ld$L > out/21/logs/xg_mem_Ld$L.log 2>&1
done
echo 21a done
