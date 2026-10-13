#!/bin/bash
# Exp. 48d (2026-10-13): homodyne photon accounting — fixed signal photons, the carrier's light (and shot noise) on top.
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/48.log
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
DREF=signal DGRID=1e6,1e7,1e8,1e9,1e10 run $PY 48-linear.py 256 4 2 1.0 0 10 30 100 300
echo ALLDONE-D >> $L
