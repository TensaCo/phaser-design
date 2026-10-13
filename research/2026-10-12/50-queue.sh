#!/bin/bash
# Exp. 50 (2026-10-13): trained optics for the passive ring (KS, K 2, bin 4, carrier 100). One job at a time, after 49-queue.sh.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/50.log
while pgrep -f "49-queue.sh" > /dev/null; do sleep 20; done
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
run $PY 50-train.py 64 4 2 100 mpc 1500
run $PY 50-train.py 64 4 2 100 m 1500
run $PY 50-train.py 64 4 2 100 pc 1500
run $PY 50-train.py 64 4 2 100 m2pc 1500
run $PY 50-train.py 128 4 2 100 mpc 1500 256
run $PY 50-train.py 128 4 2 100 m2pc 1500 256
echo ALLDONE >> $L
