#!/bin/bash
# Experiment 21e (2026-09-23): cross-gain sequencers, rerun. The 21d designs had a flat loss from iteration 0 (the lone written
# token died within 20 trips → zero gradient), i.e. a setup failure, not a result. Here G0 starts at 3.0 (inside the L_d = 60 µm
# memory window, Exp. 21a) and the write pulse is stronger (inj_amp 10). Slot-limited, JS to 1e4 trips.
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"G0":3.0,"inj_amp":10,"Ld":60e-6,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"amp_margin":0,"amp_bg":-1,"iters":250,"twin":"A64s_amp"'
wait_slot; PHASER_DEVICE=cpu ./run-job.sh toggle "{$A,\"radius\":4,\"period\":100,\"settle\":20,\"T\":400,\"tag\":\"xg60_g3_toggle_p100\"}" &
sleep 60
wait_slot; PHASER_DEVICE=cpu ./run-job.sh ring "{$A,\"N\":4,\"radius\":6,\"period\":100,\"settle\":20,\"T\":500,\"tag\":\"xg60_g3_ring4_p100\"}" &
wait
echo 21e done
