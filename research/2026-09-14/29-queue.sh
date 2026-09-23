#!/bin/bash
# Exp. 29a sweep: photon budget N_c × input stream, 4 lanes (resource cap).
cd "$(dirname "$0")"
for nc in inf 1e2 1e3 1e4 1e5 1e6 1e7 1e8 1e9 1e10 1e11 1e12; do for t in uniform bits; do echo "$nc $t"; done; done |
  xargs -P 4 -L 1 bash -c '[ -f out/29/feat_Nc$0_$1.json ] || npx vite-node 29-noise.ts $0 $1 > out/29/logs/Nc$0_$1.log 2>&1'
echo done
