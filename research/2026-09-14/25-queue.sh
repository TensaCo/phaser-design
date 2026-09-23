#!/bin/bash
# Experiment 25 (2026-09-23): Exp. 8 gates re-laid out. In the original gate layout the output sits 2·dist = 12 px from the
# inputs (input column at c − dist, output at c + dist); the persistent wire (amp_wire_d6) shows threshold-1 copy works across
# 6 px. Here the output is io_dx = 6 px right of the input column (inputs at ±3 px vertically → 6.7 px centre distance, rail
# 6 px below the output). Local gain (L_d = 0) and cross-gain (L_d = 60 µm) variants. Slot-limited, JS to 1e4 trips.
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"twin":"A64s_amp","s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.4,"amp_margin":0,"amp_bg":-1,"dist":6,"io_dx":6,"T":200,"settle":80,"iters":250'
jobs=out/08/logs/25-jobs.txt
{
echo "gate|{$A,\"G0\":3.0,\"gate\":\"OR\",\"rails\":0,\"tag\":\"io6_gate_OR\"}"
echo "gate|{$A,\"G0\":3.0,\"gate\":\"NOT\",\"rails\":1,\"tag\":\"io6_gate_NOT\"}"
echo "gate|{$A,\"G0\":2.8,\"Ld\":60e-6,\"gate\":\"NOT\",\"rails\":1,\"tag\":\"io6_xg60e-6_gate_NOT\"}"
echo "gate|{$A,\"G0\":3.0,\"gate\":\"NAND\",\"rails\":1,\"tag\":\"io6_gate_NAND\"}"
echo "gate|{$A,\"G0\":2.8,\"Ld\":60e-6,\"gate\":\"NAND\",\"rails\":1,\"tag\":\"io6_xg60e-6_gate_NAND\"}"
echo "gate|{$A,\"G0\":3.0,\"gate\":\"XOR\",\"rails\":1,\"tag\":\"io6_gate_XOR\"}"
echo "gate|{$A,\"G0\":2.8,\"Ld\":60e-6,\"gate\":\"XOR\",\"rails\":1,\"tag\":\"io6_xg60e-6_gate_XOR\"}"
} > $jobs
N=2
for lane in $(seq 0 $((N - 1))); do
  ( awk -v l="$lane" -v n="$N" '(NR - 1) % n == l' $jobs | while IFS='|' read -r t j; do wait_slot; PHASER_DEVICE=cpu ./run-job.sh "$t" "$j"; done ) &
done
wait
echo 25 done
