# PHASER research sprint — 2026-10-12: GPU design engine, physical cross-gain, latch

> Continues `research/2026-09-14/REPORT.md` (Experiments 1–35). It picks up the "Next experiments" of Exp. 28: the latch,
> a physical realisation of cross-gain, composition, the phase-stability budget and a clock. Heavy jobs run on the compute
> peer `gb10-direct` (GB10, direct cable); `sync.sh` pushes code there and pulls results back.

## Experiment 36 — GPU design and verification engine

**Why.** Exp. 27 concluded that whole circuits were "not achieved", but its designs ran for 250 iterations on one CPU thread
(≈ 25 min each, loss still falling). That was a compute budget, not a finding about the physics.

**What was built** (all in this folder):

| file | role |
|---|---|
| `gtwin.py` | the 2026-09-14 torch twin with a leading **design axis**: fields (D, B, n, n), per-design SLM/amplitude programs and pump G0. `c128` for verification, `c64` for design. |
| `fused.py` | CUDA kernels compiled at first use. (1) Each linear run of the round trip (≈ 20 angular-spectrum steps + lenses, mirrors, flips) is applied to a 64×64 field held in shared memory, one block per sample, with 64-point FFTs done as an 8×8 four-step decomposition in registers. Its backward pass is the exact adjoint (same kernel, reversed and conjugated program). (2) The nonlinear head (injection, SLM × amplitude program, saturable absorber) and the gain are elementwise kernels with hand-written gradients. |
| `design.py` | batched designer: D seeds of one task optimised together (Adam, cosine schedule), 08-design task builders plus the new latch tasks. Saves every design as an 08-format spec plus `twin`/`n`. |
| `verify.py` | float64 GPU verification at **every trip**: every target window, then each cell's final value to the horizon H. Gain noise, static phase error, phase flicker, G0 detuning. |
| `verify.ts` / `vlib.ts` | the same rule in the JS simulator (authoritative), on any architecture in `arch-twins.ts`. |
| `arch-twins.ts`, `dump.ts` | twin geometries for this sprint (gain-offset rings, a 128² ring); `arch.ts` gained `gainOffset`. |
| `run-job.sh`, `queue.sh` | design → float64 verification to 10⁴ trips, N concurrent jobs on the peer. |

**Validation.**

| check | result |
|---|---|
| `gtwin` c128 vs the 2026-09-14 float64 twin (itself 1e-13 vs JS), 200 sustained trips, cross-gain L_d 100 µm, 3 designs × 4 cases | **4×10⁻¹³** (A64s_amp_xg), 4×10⁻¹³ (gain sheet 3 mm) |
| `gtwin` c64 vs the same | 9×10⁻⁴, 6×10⁻⁴ |
| fused linear run vs torch ops (27 ops) | 2×10⁻⁶ forward; adjoint identity ⟨Lx, y⟩ = ⟨x, Lᴴy⟩ to 2.5×10⁻⁷ |
| fused trip vs unfused c64, 200 trips | 3×10⁻⁴ |
| fused gradients (30 trips) vs torch autograd | SLM program 6×10⁻⁵, G0 5×10⁻⁶ |
| `verify.py` on the Exp. 26 NAND | noiseless 4/4 to 10⁴ (as Exp. 26); **0.03 rad static phase error: case 01 fails** (as Exp. 26) |
| `verify.ts` on the Exp. 26 NAND | 4/4 to 2000 trips |

**Speed** (fwd + bwd, 128 samples, measured while two other jobs shared the GPU): torch 16 ms/trip, fused **4.9 ms/trip**, no
checkpoint recomputation needed (one forward pass instead of two). The old CPU path was ≈ 3 ms per *sample*-trip; the fused
GPU path is ≈ 0.04 ms per sample-trip. A Rust rewrite was considered and rejected: the expensive step is gradients through
hundreds of trips, which needs autodiff on the GPU, not a faster CPU forward.

**A lesson on the Exp. 21b NAND.** The same recipe (L_d 100 µm, T = 200, 250 iterations) rerun on 8 seeds: 3 seeds reach 100 %
inside the training window, but **none holds to 10⁴ trips** (first failures at trips 322, 540, 2094). The verified Exp. 21b
NAND was a lucky seed. Training windows of 200 trips do not enforce persistence, so this sprint trains on 400–600 trips with
more seeds and verifies every design at every trip.

## Experiment 37 — a physical cross-gain: the gain medium off the image plane

**Question.** The Exp. 21/26 NAND needs gain saturation shared over ≈ one cell pitch (L_d ≈ 100 µm). Real carrier diffusion
is 1–10 µm. Exp. 28 proposed putting the gain medium out of the image plane, so each cell's light is defocused there and
saturates a disc about a pitch wide. Does that reproduce the model?

**37a — the inhibition kernel, measured directly** (`37-kernel.py`, `out/37/kernel_G02.8.json`). Two-cell hand-built absorbing
lattice (3×3 px clear windows, everything else dark, flat SLM, G0 2.8, s −0.8, I_a 0.2). Cell A is held ON at its steady state.
A weak probe sits in cell B, r px away. **Gain depletion** = 1 − ⟨g⟩_B / G0: the gain map at the gain plane with A ON,
weighted by B's own light there.

| mechanism | I_A (steady) | depletion at r = 4 px | 5 px | **6 px (120 µm, the gate pitch)** | 8 px | 12 px | 18 px |
|---|---|---|---|---|---|---|---|
| in-plane local gain | 0.15 | 0 | 0 | 0 | 0 | 0 | 0 |
| in-plane diffusion L_d 20 µm | 1.8 | 0.38 | 0.007 | 0.002 | 0 | 0 | 0 |
| in-plane diffusion L_d 40 µm | 4.2 | 0.40 | 0.044 | 0.026 | 0.008 | 0.001 | 0 |
| in-plane diffusion L_d 60 µm | 7.2 | 0.41 | 0.084 | 0.059 | 0.027 | 0.006 | 0.001 |
| **in-plane diffusion L_d 100 µm (the NAND's model)** | 14.2 | 0.42 | 0.40 | **0.40** | 0.068 | 0.027 | 0.007 |
| local gain sheet, z = 0.5–2 mm | 0.15–0.22 | 0 | 0 | 0 | 0 | 0 | 0 |
| sheet z = 3 mm | 0.41 | 0.009 | 0 | 0 | 0 | 0 | 0 |
| sheet z = 5 mm | 2.7 | 0.37 | 0.015 | 0.007 | 0.001 | 0 | 0 |
| sheet z = 8 mm | 6.5 | 0.37 | 0.040 | 0.027 | 0.011 | 0.001 | 0 |
| **local gain sheet, z = 12 mm** | 12.7 | 0.36 | 0.36 | **0.37** | 0.032 | 0.010 | 0.001 |

(r = 3 px: the windows touch; every mechanism couples there.)

**Result.** A plain, locally saturating gain sheet **≈ 12 mm downstream of the SLM** depletes a neighbour at the 120 µm gate
pitch by 37 %, against 40 % for the L_d = 100 µm diffusion model. It also cuts off more sharply beyond the pitch (8 px: 0.032 vs
0.068). The steady ON level of a cell (12.7 vs 14.2) agrees as well. The equivalence is approximate, z ≈ 8 mm ↔ L_d ≈ 40–60 µm and
z ≈ 12 mm ↔ L_d ≈ 100 µm. In this ring the SLM-to-relay-lens leg is 40 mm, so a gain chip at 12 mm fits. The off-plane sheet is
the first concrete physical candidate for the cross-gain the logic needs.

**Net coupling is excitatory.** The linear-response round-trip gain of the probe *rises* when A is ON, in every mechanism
(`net_coupling` < 0 in the JSON). A's spill light also saturates the absorber over B, and with a flat program that outweighs
the gain depletion. Inhibition between cells therefore has to be arranged by the static program (keeping A's light off B's
absorber while sharing the gain), which is what the gate designs do.

**37b — gates with the gain sheet.** NOT and NAND designed with a local gain sheet at z = 2, 3, 5, 8 and 12 mm (no
diffusion), and with the in-plane L_d = 100 µm model as reference. Same recipe for all: 16 seeds (G0 2.4–3.0), T = 400 trips,
500 iterations, fused c64 engine. Every saved design was verified in float64 at every trip to 10⁴ (`verify.py`); the passes
were re-run in the JS simulator (`verify.ts`, 10⁴).

| cross-gain | NOT, pass 10⁴ (GPU) | NAND, pass 10⁴ (GPU) | NAND, pass 10⁴ (GPU **and** JS) |
|---|---|---|---|
| sheet z = 2 mm | 0/16 | 0/16 | — |
| sheet z = 3 mm (no cross-gain, control) | 0/16 | 0/16 | — |
| sheet z = 5 mm | 0/16 | 0/16 | — |
| sheet z = 8 mm | 0/16 | 0/16 | — |
| **sheet z = 12 mm** | 0/16 | **1/16** (d1) | **1/16** |
| in-plane L_d = 100 µm (reference) | 0/16 | 2/16 (d8, d11) | 1/16 (d8 fails NAND11 at trip 3877 in JS) |

**Result.** A NAND built on a **plain, locally saturating gain chip 12 mm off the image plane** holds all four cases for
10⁴ trips in both simulators. This is the first verified cross-gain gate on a physically plausible mechanism (every earlier one
needed ≈ 100 µm in-plane carrier diffusion). Its yield (1/16) matches the reference model's (1/16 after the JS check), and
nothing closer than 12 mm works, as the kernel in 37a predicts. Caveats: the sheet NAND is fragile under SLM phase error
(table in Exp. 40), and d8 shows that a GPU/JS disagreement after thousands of trips is possible for marginal designs, so
both checks are required.

**NOT never trained**, for any mechanism: every seed sits at loss 0.090, accuracy 0.75 (output dark in both cases) from the
first iterations. NAND, a harder gate, trains with the same code, so this is a problem of the NOT task's set-up
(single input, `io_dx` 6, no rail), not of the physics. Open.

## Experiment 38 — latch with held set/reset pulses: not achieved

Every earlier latch used one-trip S/R pulses and never required S/R to go dark again. The new tasks hold S or R for 20 trips
(13 ns) and require S and R to be dark afterwards:
- `srff`: two cells Q, Q̄ that inhibit each other (cross-gain), with S exciting Q and R exciting Q̄. It needs only the
  follower and inhibition, both verified in Exp. 26.
- `latch2`: the Exp. 9/21 single-Q task with held pulses.

Five runs (srff pulse amplitude 1.5 and 3, vertical I/O, 40-trip pulses, the 12 mm sheet; latch2), 16 seeds each,
T = 600: **0 designs reach 100 % in training.** All srff runs collapse within 25 iterations to the same flat loss (0.0862 in
every seed: the field dark, accuracy 0.76); latch2 sits at 0.842. The held pulses flood the field at iteration 0 (loss 39–88),
and the optimiser escapes to the dark state, the failure Exp. 21e saw in sequencers. The intensity hinge loss is the cause;
the next attempt should use the log-intensity loss (below) together with a curriculum (short T first).

## Experiment 40 — NAND trained against SLM phase error

The Exp. 26 NAND fails case 01 at 0.03 rad rms static phase error. Here the designer perturbs the SLM program with fresh
Gaussian phase noise every iteration (`jitter`), L_d = 100 µm, T = 400, 800 iterations.

| run | seeds | pass 10⁴ noiseless (GPU, JS) |
|---|---|---|
| jitter 0.03 rad | 0–15 | 1/16 (d12; also passes **10⁵**) |
| jitter 0.03 rad | 16–31 | **5/16** (d4, d5, d8, d10, d12), all confirmed in JS |
| jitter 0.05 rad | 0–15 | 1/16 (d2) |
| same recipe, no jitter (Exp. 37b reference) | 0–15 | 2/16 (1/16 after JS) |

Robustness of every passing NAND: static per-pixel phase error, 3 independent draws per level, `verify.py --jitter`, 10⁴ trips,
all four cases must pass.

| design | trained with | 0.01 rad | 0.02 rad | **0.03 rad** | 0.05 rad |
|---|---|---|---|---|---|
| Exp. 26 NAND (Exp. 36 check) | none | — | — | fails (1 draw) | — |
| e37_ld100_NAND_d8 | none | — | 3/3 | 1/3 | 0/3 |
| e37_ld100_NAND_d11 | none | — | 1/3 | 1/3 | 1/3 |
| **e37_go12_NAND_d1 (gain sheet)** | none | — | 1/3 | 1/3 | 0/3 |
| e40_jit03_d12 | 0.03 | 3/3 | 3/3 | 1/3 | 1/3 |
| **e40_jit03_s16_d10** | 0.03 | — | 3/3 | **3/3** | **2/3** |
| **e40_jit03_s16_d4** | 0.03 | — | 3/3 | **3/3** | 1/3 |
| **e40_jit03_s16_d8** | 0.03 | — | 3/3 | **3/3** | 1/3 |
| e40_jit03_s16_d12 | 0.03 | — | 3/3 | 2/3 | 2/3 |
| e40_jit03_s16_d5 | 0.03 | — | 2/3 | 2/3 | 0/3 |
| e40_jit05_d2 | 0.05 | — | 0/3 | 0/3 | 0/3 |

**Result.** Training against 0.03 rad phase error roughly triples the yield of working NANDs (6/32 against 1/16), and three
of them (s16_d4, d8, d10) **pass every draw at 0.03 rad**, the level at which the Exp. 26 NAND fails. The best (d10) passes 2
of 3 draws at 0.05 rad. Untrained designs, including the gain-sheet NAND, pass about one draw in three at 0.02–0.03 rad.
Training at 0.05 rad over-shoots: its one design is less robust than any other. The failing case is almost always NAND11
(22 of 46 failures) or NAND01 (16): the "1" input that must switch the output off. Next: jitter-trained NANDs on the 12 mm
sheet, and a larger draw count (≥ 20) for the three robust designs.

## Experiment 41 — a clock (two-phase oscillator): not achieved

Task `osc`: cells A and B alternate with a set period (200 or 400 trips) after one start pulse into A. Seven runs, 16 seeds each:
- intensity hinge loss (3 runs): the start pulse floods every cell (loss 70–146), then the optimiser escapes to the dark state
  (loss 0.180, accuracy 0.5), as with the latches;
- **log-intensity hinge loss** (`loss_log`, 4 runs: period 200 and 400, with an always-on rail, the 12 mm sheet): the gradients
  stay bounded, but every seed ends in the opposite state, both cells permanently ON (loss 88.5, accuracy 0.5). No design passes;
  verification fails at trip 220, the first A→B transition.

Neither loss finds an oscillation from a cold start. Exp. 21b's cross-gain limit cycles appeared by accident in random programs;
the next step is to start from those (search for limit cycles first, then tune the period), not from a gradient on a target
waveform.

## Experiment 42 — phase-error training on the 12 mm gain sheet

The Exp. 40 recipe on the `A64s_amp_go12` twin (local gain sheet 12 mm off the image plane, no diffusion), 16 seeds per run.

| run | training jitter | seeds | pass 10⁴ (GPU and JS) |
|---|---|---|---|
| jit03_s16, jit03_s32 | 0.03 rad | 16–47 | 0/32 |
| jit02 | 0.02 rad | 0–15 | 1/16 (d0) |
| jit02_s16 | 0.02 rad | 16–31 | 1/16 (d8) |

| design | 0.01 rad | 0.02 rad | 0.03 rad | 0.05 rad |
|---|---|---|---|---|
| e37_go12_NAND_d1 (no jitter training) | — | 1/3 | 1/3 | 0/3 |
| e42_go12_NAND_jit02_d0 | 0/3 | 1/3 | 1/3 | 0/3 |
| e42_go12_NAND_jit02_s16_d8 | **3/3** | 1/3 | 1/3 | 0/3 |

**Result.** The gain sheet now has three verified NANDs, but none is robust: the best (s16_d8) is clean at 0.01 rad and passes
one draw in three from 0.02 rad. Training at 0.03 rad finds nothing on the sheet (it does with the L_d 100 µm model, Exp. 40),
so the sheet's NAND has less margin than the diffusion model's. Failures are again NAND11 and NAND01. The phase-stability
budget for a sheet-based gate is therefore ≈ 0.01 rad rms static SLM error with the current recipe. Next: an explicit margin
term (`w_margin`), longer training at 0.02 rad, and more seeds.

## Status at the end of the day (2026-10-12)

| experiment | status |
|---|---|
| 36 engine | done, validated (table above) |
| 37a kernel | done |
| 37b gates on a gain sheet | **NAND verified on a 12 mm sheet (1/16)**; NOT not trained on any mechanism |
| 38 latch, held pulses | not achieved (dark collapse) |
| 39 composition | not started (needs the 128² ring; the fused kernel is 64²-only) |
| 40 phase-error-trained NAND | **3 designs pass 3/3 draws at 0.03 rad** |
| 42 same, on the 12 mm sheet | 3 sheet NANDs verified; best is clean only to 0.01 rad |
| 41 clock | not achieved |
