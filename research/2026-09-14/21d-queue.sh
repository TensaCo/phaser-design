#!/bin/bash
# Experiment 21d (2026-09-23): cross-gain sequencers. Cross-gain NOT/latch designs (21b) fell into stable relaxation limit
# cycles (periods ≈ 160–4100 trips), i.e. nonlinear autonomous oscillation, which no Exp. 10 sequencer produced. Can a designed
# static program turn that into a 2-cell toggle / 4-cell one-hot ring with 100-trip ticks? A64s_amp (self-imaging) and
# A64sd5_amp (5 mm defocus), L_d = 60 µm, G0 start 2.8. Slot-limited, JS to 1e4 trips (targets extended by 08-eval only for the
# final tick, so survival is judged mainly by in-window accuracy and the trace).
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"G0":2.8,"Ld":60e-6,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"amp_margin":0,"amp_bg":-1,"iters":250'
jobs=out/21/logs/21d-jobs.txt
{
echo "toggle|{$A,\"twin\":\"A64s_amp\",\"radius\":4,\"period\":100,\"settle\":20,\"T\":400,\"tag\":\"xg60e-6_toggle_p100\"}"
echo "ring|{$A,\"twin\":\"A64s_amp\",\"N\":4,\"radius\":6,\"period\":100,\"settle\":20,\"T\":500,\"tag\":\"xg60e-6_ring4_p100\"}"
echo "toggle|{$A,\"twin\":\"A64sd5_amp\",\"radius\":4,\"period\":100,\"settle\":20,\"T\":400,\"tag\":\"xg60e-6_sd5_toggle_p100\"}"
} > $jobs
while IFS='|' read -r t j; do wait_slot; PHASER_DEVICE=cpu ./run-job.sh "$t" "$j" & sleep 60; done < $jobs
wait
echo 21d done
