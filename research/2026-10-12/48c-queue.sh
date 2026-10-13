#!/bin/bash
# Exp. 48c (2026-10-13): the passive linear ring with a carrier under shot noise. Waits for 48b-queue.sh to finish.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/48.log
while pgrep -f "48b-queue.sh" > /dev/null; do sleep 20; done
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
DGRID=1e8,1e9,1e10,1e11,1e12 run $PY 48-linear.py 256 4 2 1.0 0 30 100 300
echo ALLDONE-C >> $L
