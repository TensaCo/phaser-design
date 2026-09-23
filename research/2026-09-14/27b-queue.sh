#!/bin/bash
# Experiment 27b (2026-09-23): associative memory with cross-gain saturation (L_d = 100 µm). The local-gain design
# (amp_assoc16_3pat) held only 1 of 3 stored patterns as a fixed point; Hopfield attractors need inhibitory couplings, which
# cross-gain supplies. Same 4×4 / 6 px layout and patterns; then the JS basin study and Hopfield baselines. Slot-limited.
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"twin":"A64s_amp","G0":2.6,"Ld":100e-6,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.4'
wait_slot
PHASER_DEVICE=cpu ./run-job.sh assoc "{$A,\"side\":4,\"pitch\":6,\"patterns\":[\"rand1\",\"rand2\",\"rand3\"],\"train_flips\":[1,2],\"reps\":2,\"T\":200,\"settle\":100,\"iters\":250,\"amp_margin\":0,\"amp_bg\":-1,\"tag\":\"xg100_assoc16_3pat\"}"
echo 27b done
