#!/bin/bash
# Exp. 51 (2026-10-13): end-to-end trained digital baselines for Exp. 50. One job at a time.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/51.log
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
for N in 256 1024; do for act in tanh quad; do run $PY 51-train-rnn.py $N $act 3000; done; done
run $PY 51-train-rnn.py 4096 tanh 3000 256
echo ALLDONE >> $L
