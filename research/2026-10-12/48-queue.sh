#!/bin/bash
# Exp. 48 (2026-10-12): round-trip spectra, then the linear (below-threshold, constant-gain) ring on KS. One job at a time.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/48.log; mkdir -p out/48
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
run $PY 48-spectrum.py res_n256_d64 400
for G in 1.0 1.2 1.4 1.45; do run $PY 48-linear.py 256 4 2 $G 0 1 3 10; done
run $PY 48-spectrum.py res_n128 400
echo ALLDONE >> $L
