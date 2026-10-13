#!/bin/bash
# Exp. 49 (2026-10-13): does the passive ring + reference beam scale with the mode count? KS, K 2, bin 4, G0 1 (passive).
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/49.log
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
for n in 64 128; do run $PY 48-linear.py $n 4 2 1.0 0 30 100 300; done
run $PY 48-linear.py 512 4 2 1.0 100 300
echo ALLDONE >> $L
