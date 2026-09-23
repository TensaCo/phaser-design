#!/bin/bash
# 2026-09-23: the queue stopped on 2026-09-14 (amp-queue2.sh tail, amp-wire-queue.sh, 11t2-queue.sh), unchanged parameters,
# run 4 jobs at a time (designs on the GPU, JS evaluations on one core each).
cd "$(dirname "$0")"
A='"twin":"A64s_amp","G0":3.0,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.4'
L='"gap":3,"x_in":20,"x_out":38,"rail_x":29,"rail_y":44,"preserve_inputs":true'
AW='"twin":"A64s_amp","G0":3.0,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.4,"amp_margin":0,"amp_bg":-1'
NL='"twin":"A64s","G0":2.2,"s":-0.6,"Ia":0.05,"I_hi":0.5,"I_lo":0.08,"bg_max":3.0,"w_bg":0.05,"lr":0.05,"noise":0.01,"w":3'
LT='"gap":3,"x_in":20,"x_out":38,"rail_x":29,"rail_y":44'
{
echo "assoc|{$A,\"pitch\":5,\"w\":3,\"patterns\":[\"circle\",\"cross\",\"smile\",\"rand1\",\"rand2\"],\"train_flips\":[4,8],\"reps\":2,\"T\":200,\"settle\":100,\"iters\":250,\"amp_margin\":0,\"amp_bg\":-1,\"tag\":\"amp_assoc_5pat\"}"
for fn in fulladd satstep2 parity4; do echo "boolfn|{$A,$L,\"fn\":\"$fn\",\"rails\":1,\"T\":240,\"settle\":80,\"iters\":250,\"amp_margin\":0,\"amp_bg\":-1,\"tag\":\"amp2_bool_${fn}\"}"; done
echo "countdown|{$A,\"w_stat\":2.0,\"stat_frac\":0.3,\"N\":4,\"period\":20,\"settle\":6,\"T\":160,\"iters\":250,\"amp_margin\":0,\"amp_bg\":-1,\"tag\":\"amp_countdown4\"}"
echo "wire|{$AW,\"dist\":6,\"T\":200,\"settle\":80,\"reps\":2,\"iters\":250,\"tag\":\"amp_wire_d6\"}"
echo "gate|{$AW,\"gate\":\"OR\",\"dist\":6,\"rails\":1,\"T\":200,\"settle\":80,\"iters\":250,\"tag\":\"amp_gate_OR_rail\"}"
for fn in halfadd fulladd parity4 add2 satstep2; do echo "boolfn|{$NL,$LT,\"fn\":\"$fn\",\"rails\":1,\"T\":60,\"settle\":30,\"iters\":250,\"tag\":\"bool2_${fn}_transient\"}"; done
} > out/08/logs/finish-jobs.txt
# resource cap (≤ 25 % of the machine): four single-thread CPU lanes (one GPU twin alone shows ~75 % GPU utilisation, so no GPU);
# lane = job line number mod 4.
run_lane() { local lane=$1 dev=cpu
  awk -v l="$lane" 'NR % 4 == l' out/08/logs/finish-jobs.txt | while IFS='|' read -r t j; do PHASER_DEVICE=$dev ./run-job.sh "$t" "$j"; done; }
for lane in 0 1 2 3; do run_lane $lane & done
wait
echo finish-queue done
