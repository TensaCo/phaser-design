#!/bin/bash
# Exp. 48b follow-up (2026-10-13): shorter memory than the passive ring (G0 < 1 = extra loss), stronger carriers, K = 1,
# and one point with more gain for the trend. One job at a time; waits for the 48-queue job still running.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/48.log
while pgrep -f "48-linear.py 256 4 2 1.2" > /dev/null; do sleep 10; done
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
run $PY 48-linear.py 256 4 2 1.0 30 100 300
for G in 0.7 0.5 0.3; do run $PY 48-linear.py 256 4 2 $G 3 10 30 100; done
for G in 1.0 0.7; do run $PY 48-linear.py 256 4 1 $G 10 30 100; done
run $PY 48-linear.py 256 4 2 1.4 0 10 100
echo ALLDONE >> $L
