#!/bin/bash
# Exp. 53 (2026-10-13): noise-aware training at a fixed TOTAL photon budget, trained reference strength, per-mode absorber.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/53.log
run() { echo "== $(date +%T) NOISE_D=$NOISE_D $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
run $PY 50-train.py 64 4 2 100 mpca 1500
for D in 1e10 1e12; do
  NOISE_D=$D run $PY 50-train.py 64 4 2 10 none 0
  NOISE_D=$D run $PY 50-train.py 64 4 2 10 mpcs 1500
  NOISE_D=$D run $PY 50-train.py 64 4 2 10 mpcsa 1500
done
for D in 1e10 1e12; do NOISE_D=$D run $PY 50-train.py 128 4 2 10 mpcs 1500 256; done
echo ALLDONE >> $L
