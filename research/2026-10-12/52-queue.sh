#!/bin/bash
# Exp. 52 (2026-10-13): the trained rings under shot noise (signal photons D; reference light on top). After 51-queue.sh.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/52.log
while pgrep -f "51-queue.sh" > /dev/null; do sleep 20; done
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
export DGRID=1e6,1e7,1e8,1e9,1e10
LOAD=n64_b4_K2_c100_mpc_i1500_s0 run $PY 50-train.py 64 4 2 100 mpc 0
LOAD=n128_b4_K2_c100_mpc_i1500_s0 run $PY 50-train.py 128 4 2 100 mpc 0 256
run $PY 50-train.py 128 4 2 100 none 0
echo ALLDONE >> $L
