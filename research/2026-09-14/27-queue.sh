#!/bin/bash
# Experiment 27 (2026-09-23): whole circuits with cross-gain saturation at L_d = 100 µm (where persistent NAND/NOT/AND were found,
# Exp. 21b). The same tasks that failed with local gain: persistent half/full adder (corrected amp2 layout, inputs latched),
# set/reset latch (second seed), XOR (6 px layout), 2-hop buffer chain, countdown-and-halt (needs "previous cell OFF").
# Slot-limited, JS to 1e4 trips; passing designs then go through 26-verify.ts.
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"twin":"A64s_amp","G0":2.6,"Ld":100e-6,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.4,"amp_margin":0,"amp_bg":-1,"iters":250'
L='"gap":3,"x_in":20,"x_out":38,"rail_x":29,"rail_y":44,"preserve_inputs":true'
jobs=out/08/logs/27-jobs.txt
{
echo "boolfn|{$A,$L,\"fn\":\"halfadd\",\"rails\":1,\"T\":240,\"settle\":80,\"tag\":\"xg100_bool_halfadd\"}"
echo "latch|{$A,\"seed\":1,\"dist\":6,\"rails\":1,\"T\":240,\"t_pulse\":60,\"gap\":80,\"settle\":25,\"tag\":\"xg100_latch_s1\"}"
echo "gate|{$A,\"gate\":\"XOR\",\"dist\":6,\"io_dx\":6,\"rails\":1,\"T\":200,\"settle\":80,\"tag\":\"xg100_io6_gate_XOR\"}"
echo "countdown|{$A,\"w_stat\":2.0,\"stat_frac\":0.3,\"N\":4,\"period\":20,\"settle\":6,\"T\":160,\"tag\":\"xg100_countdown4\"}"
echo "chain|{$A,\"step\":6,\"hops\":2,\"reps\":2,\"T\":200,\"settle\":80,\"tag\":\"xg100_chain2_s6\"}"
echo "boolfn|{$A,$L,\"fn\":\"fulladd\",\"rails\":1,\"T\":240,\"settle\":80,\"tag\":\"xg100_bool_fulladd\"}"
} > $jobs
while IFS='|' read -r t j; do wait_slot; PHASER_DEVICE=cpu ./run-job.sh "$t" "$j" & sleep 60; done < $jobs
wait
echo 27 done
