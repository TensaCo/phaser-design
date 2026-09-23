#!/bin/bash
# Experiment 26 (2026-09-23): strict every-trip verification of the persistent cross-gain designs that passed the 08-eval
# scorecard (and the reference AND / wire / fan-out): 10⁴ noiseless, 10⁵ noiseless, 10⁴ with gain noise 1e-3, 10⁴ with a static
# 0.03 rad SLM phase error. Slot-limited.
cd "$(dirname "$0")"
source ./wait-slot.sh
v() { wait_slot; npx vite-node 26-verify.ts "out/08/$1_spec.json" "$2" 400 "${3:-0}" "${4:-0}" > "out/26/logs/$1_$2_n${3:-0}_j${4:-0}.log" 2>&1 & sleep 20; }
for d in xg100e-6_gate_NAND xg100e-6_gate_NOT io6_xg60e-6_gate_NOT xg100e-6_gate_AND xg60e-6_gate_AND amp_wire_d6 fanout2_s6; do v $d 10000; done
for d in xg100e-6_gate_NAND xg100e-6_gate_NOT io6_xg60e-6_gate_NOT; do v $d 10000 1e-3; v $d 10000 0 0.03; v $d 100000; done
wait
echo 26 done
