#!/bin/bash
# Experiment 25c (2026-09-23): composition of the directional threshold-1 primitive (persistent follower wire, amp_wire_d6).
# (a) OR with inputs 10 px apart (the 6 px-apart version flooded: one ON input switched the other); (b) 2-hop buffer chain
# src → m1 → dst, 6 px steps; (c) fan-out: src drives a follower on each side (6 px). Slot-limited, JS to 1e4 trips.
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"twin":"A64s_amp","G0":3.0,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.4,"amp_margin":0,"amp_bg":-1,"T":200,"settle":80,"iters":250'
jobs=out/08/logs/25c-jobs.txt
{
echo "gate|{$A,\"gate\":\"OR\",\"dist\":6,\"io_dx\":6,\"in_dy\":5,\"rails\":0,\"tag\":\"io6dy5_gate_OR\"}"
echo "chain|{$A,\"step\":6,\"hops\":2,\"reps\":2,\"tag\":\"chain2_s6\"}"
echo "chain|{$A,\"step\":6,\"hops\":1,\"fanout\":2,\"reps\":2,\"tag\":\"fanout2_s6\"}"
} > $jobs
while IFS='|' read -r t j; do wait_slot; PHASER_DEVICE=cpu ./run-job.sh "$t" "$j" & sleep 60; done < $jobs
wait
echo 25c done
