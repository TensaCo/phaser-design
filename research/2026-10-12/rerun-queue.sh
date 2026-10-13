#!/bin/bash
# After the 2026-10-12 21:36 reboot (unified-memory exhaustion from five concurrent jobs): the remaining Exp. 43/45 work,
# strictly ONE job at a time; the 1024² rings with one input amplitude per run (≈ 40 GB peak while scoring).
cd "$(dirname "$0")"; PY=/home/brandonin/work/ext/venvs/psi/bin/python; L=out/rerun.log
run() { echo "== $(date +%T) $*" >> $L; "$@" >> $L 2>&1; echo "   exit $? $(free -g | awk '/Mem/{print "free",$7,"GB"}')" >> $L; }
run $PY 45-ks.py ngrc 3
run $PY 45-ks.py esn2 1024 4096
run $PY 45-ks.py opt 512 4 2 100 300
run $PY 45-ks.py opt 512 4 10 100 300
run $PY 45-ks.py opt 1024 4 2 100
run $PY 45-ks.py opt 1024 4 10 100
run $PY 43-scale.py run 1024 10 16000 4 g1024
run $PY 43-scale.py score g1024 1 16mpb
run $PY 43-scale.py esn 16384
echo ALLDONE >> $L
