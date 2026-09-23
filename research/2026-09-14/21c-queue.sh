#!/bin/bash
# Experiment 21c (2026-09-23): cross-gain NOT, longer horizon. At L_d 40/60 µm the 200-trip NOT designs invert correctly inside
# the training window, but with the input ON the inhibited output relaxes back up and the circuit becomes a slow relaxation
# oscillator (period ≈ 1.5×10³ / 4.3×10³ trips). Here the stationarity window covers trips 240–600 so drift is penalised.
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"twin":"A64s_amp","G0":2.8,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.6,"amp_margin":0,"amp_bg":-1'
for L in 60e-6 80e-6; do
  wait_slot; PHASER_DEVICE=cpu ./run-job.sh gate "{$A,\"Ld\":$L,\"gate\":\"NOT\",\"dist\":6,\"rails\":1,\"T\":600,\"settle\":80,\"iters\":250,\"tag\":\"xg${L}_gate_NOT_T600\"}" &
  sleep 60
done
wait
echo 21c done
