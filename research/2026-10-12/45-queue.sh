#!/bin/bash
# Exp. 45 chain: KS forecasting vs scale. Digital ESN N = 256 … 16384 (8 settings each) in one chain; optical rings
# 64² … 1024² (16 modes per detector bin), input amplitudes 10/30/100, K = 10 and K = 2, in another.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; mkdir -p out/45/logs
( $PY 45-ks.py esn 256 1024 4096 16384; echo ESNDONE ) > out/45/logs/esn.log 2>&1 &
( for n in 64 128 256 512 1024; do for K in 10 2; do $PY 45-ks.py opt $n 4 $K 10 30 100; done; done; echo OPTDONE ) > out/45/logs/opt.log 2>&1 &
wait
