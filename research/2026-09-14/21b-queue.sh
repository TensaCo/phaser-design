#!/bin/bash
# Experiment 21b (2026-09-23): the decisive logic test — the Exp. 8/9 persistent gate and latch tasks (same layouts, same
# absorbing-mask architecture and operating point) re-designed with CROSS-GAIN saturation (carrier diffusion length L_d in
# the gain medium, 'diffusive' saturation). Can inhibition give RESET, NOT, XOR, NAND, OR? AND is the regression check.
# usage: LDS="40e-6:2.8 60e-6:2.8 100e-6:2.6" LANES=N 21b-queue.sh
# (2026-09-23: a first pass at L_d = 20 µm showed the NOT output uninhibited — diffusion ~e^(−r/L_d) is negligible across the
#  120 µm cell spacing — so L_d is set comparable to the spacing.) One CPU lane per job; every design re-evaluated in JS to 1e4
# trips. Jobs are ordered NOT, latch, XOR, NAND, OR, AND so the decisive inhibition tests finish first.
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"twin":"A64s_amp","G0":3.0,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.4,"amp_margin":0,"amp_bg":-1'
jobs=out/21/logs/21b-jobs.txt; : > $jobs.tmp
# LDS entries are L_d[:G0 start]; G0 starts inside that L_d's memory window (Exp. 21a: 2.6–3.0 at 40–60 µm, 2.6 at 100 µm)
for LG in ${LDS:-40e-6:2.8 60e-6:2.8 100e-6:2.6}; do
  L=${LG%%:*}; G=${LG#*:}; [ "$G" = "$LG" ] && G=3.0
  X="${A/\"G0\":3.0/\"G0\":$G},\"Ld\":$L"
  echo "latch|{$X,\"dist\":6,\"rails\":1,\"T\":240,\"t_pulse\":60,\"gap\":80,\"settle\":25,\"iters\":250,\"tag\":\"xg${L}_latch\"}" >> $jobs.tmp
  for g in NOT XOR NAND; do echo "gate|{$X,\"gate\":\"$g\",\"dist\":6,\"rails\":1,\"T\":200,\"settle\":80,\"iters\":250,\"tag\":\"xg${L}_gate_$g\"}" >> $jobs.tmp; done
  echo "gate|{$X,\"gate\":\"OR\",\"dist\":6,\"rails\":1,\"T\":200,\"settle\":80,\"iters\":250,\"tag\":\"xg${L}_gate_OR_rail\"}" >> $jobs.tmp
  echo "gate|{$X,\"gate\":\"AND\",\"dist\":6,\"rails\":0,\"T\":200,\"settle\":80,\"iters\":250,\"tag\":\"xg${L}_gate_AND\"}" >> $jobs.tmp
done
for k in _gate_NOT _latch _gate_XOR _gate_NAND _gate_OR_rail _gate_AND; do grep -F "$k\"}" $jobs.tmp; done > $jobs; rm $jobs.tmp
N=${LANES:-4}
for lane in $(seq 0 $((N - 1))); do
  ( awk -v l="$lane" -v n="$N" '(NR - 1) % n == l' $jobs | while IFS='|' read -r t j; do wait_slot; PHASER_DEVICE=cpu ./run-job.sh "$t" "$j"; done ) &
done
wait
echo 21b done
