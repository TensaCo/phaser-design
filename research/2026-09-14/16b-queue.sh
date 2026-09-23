#!/bin/bash
# Experiment 16, corrected layout (2026-09-23). The queued 8×8 design (amp_assoc_5pat) used a 5 px pitch = 2 px gaps, which
# Exp. 2nl showed cannot hold bits; it collapsed to near-dark in JS. Here: 4×4 cells, 3 px cells on a 6 px pitch (inside the
# flat FOV, the memory lattice that held to 10⁵ trips), 3 random patterns (40 % ON), cues with 1–2 flips for training.
# Then the JS basin study (unseen cues, 0–8 flips) and the digital Hopfield baselines on the same patterns. Slot-limited.
cd "$(dirname "$0")"
source ./wait-slot.sh
A='"twin":"A64s_amp","G0":3.0,"s":-0.8,"Ia":0.2,"I_hi":0.6,"I_lo":0.1,"bg_max":10,"w_bg":0,"lr":0.05,"lr_amp":0.2,"noise":0.01,"w":3,"w_stat":5.0,"stat_frac":0.4'
wait_slot
PHASER_DEVICE=cpu ./run-job.sh assoc "{$A,\"side\":4,\"pitch\":6,\"patterns\":[\"rand1\",\"rand2\",\"rand3\"],\"train_flips\":[1,2],\"reps\":2,\"T\":200,\"settle\":100,\"iters\":250,\"amp_margin\":0,\"amp_bg\":-1,\"tag\":\"amp_assoc16_3pat\"}"
source "${PHASER_VENV:-$HOME/.venvs/phaser}/bin/activate"
for t in amp_assoc16_3pat amp_assoc_5pat; do CUDA_VISIBLE_DEVICES= python 24-hopfield.py out/08/${t}_spec.json 50 > out/16/logs/hopfield_$t.log 2>&1; done
echo 16b done
