#!/bin/bash
# Exp. 43 chain: replicate Exp. 31 (128², 256²), extend to 512², 1024² (16 modes per feature), 1024² with 2× the samples;
# digital ESN 4096 (cross-check vs Exp. 31), 8192, 16384 in a parallel chain.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; mkdir -p out/43/logs
( for n in 128 256 512 1024; do $PY 43-scale.py run $n 10 16000 4 g$n && $PY 43-scale.py score g$n 1 16mpb; done
  $PY 43-scale.py run 1024 10 32000 4 g1024L && $PY 43-scale.py score g1024L 1 16mpb
  echo OPTDONE ) > out/43/logs/optical.log 2>&1 &
( $PY 43-scale.py esn 4096 8192 16384; echo ESNDONE ) > out/43/logs/esn.log 2>&1 &
wait
