# PHASER research sprint — 2026-10-12: GPU design engine, physical cross-gain, latch, economic viability

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

## Part 2 — is a built PHASER an economically viable alternative? (Exps. 43–47)

The question changed in the evening: not "can it compute" but "at what scale, for which workloads, would a built PHASER beat
buying GPUs", even if that only appears at ≥ $10k investment. Five experiments, all on the Exp. 30/31 reservoir ring
(`Apre_lin`: `slmRing`, random phase mask seed 3 depth 0.1, f 40 mm, global gain G0 1.6, Is 0.05, input amplitude 6,
aperture 1.2 mm·n/64). Code: `res-dump.ts` (exports the twin and a JS reference run), `res_gpu.py` (GPU twin), `res_lib.py`
(GPU ridge with the 30-lib protocol, GPU ESN), `43-scale.py`, `44-optread.py`, `ks.py` + `45-ks.py`, `46-econ.py`,
`47-effdim.py`; queues `43-queue.sh`, `45-queue.sh`, `rerun-queue.sh`.

**GPU twin.** `res_gpu.py` matches the JS reference to 3–6e-8 (complex128) and 1e-5 to 3e-5 (complex64) from 64² to 1024²;
1024² runs at 38 ms per step (K 10, batch 2), about 10 min per 16k steps.

**Incident.** At 21:25–21:27 five concurrent jobs exhausted the GB10's single 119 GB CPU+GPU memory pool
(`NVRM NV_ERR_NO_MEMORY`) and the peer rebooted at 21:36, killing everything. The remaining work was rerun one job at a time
(`rerun-queue.sh`). Rule since then: summed peak memory well under ~90 GB, big jobs sequential.

### Experiment 43 — reservoir scaling to 262k modes (GPU)

The Exp. 31 protocol (16 modes per detector bin, K 10 trips per input, 16k steps) on the GPU twin. It reproduces Exp. 31
exactly at 64²–256² and extends it to 512².

| ring | modes | features | capacity (lin + quad) | NARMA10 NMSE | MC 1–60 | XOR(d2) |
|---|---|---|---|---|---|---|
| g64 | 4,096 | 256 | 115.6 | 0.095 | 37.4 | 0.996 |
| g128 | 16,384 | 1,024 | 260.3 | 0.046 | 57.5 | 1.000 |
| g256 | 65,536 | 4,096 | 416.7 | 0.0080 | 59.8 | 1.000 |
| g512 | 262,144 | 16,384 | **431.7** | 0.0139 | 59.8 | 1.000 |
| ESN 4096 (best NARMA of 9 settings) | — | 4,096 | 256.5 | 0.0048 | 46.3 | 1.000 |
| ESN 8192 (best NARMA) | — | 8,192 | 261.9 | 0.0034 | 51.3 | 1.000 |

**Result.** Capacity saturates between 65k and 262k modes (417 → 432) and NARMA10 gets slightly *worse* (16k training samples
for 16k features is part of it, but the capacity metric is less sample-limited). The 1024² run (`g1024`) was cancelled when the
work was wound down; it needs ≈ 40 GB while scoring and would take ≈ 2 h.

### Experiment 44 — optical readout: 2 detectors per output instead of one per 16 modes

The readout's weighted sum done in optics: an amplitude mask (one pixel per mode) in front of a polarising beam splitter and
two bucket detectors, D+ − D− = Σ (2T_p − 1) n_p. Weights are trained offline on noise-free full-resolution features (a
calibration camera), quantised, and the noise of each output is the shot noise of all the tapped light. 128² ring at full
resolution (`g128full`), NMSE of NARMA10 on the test split at D detected photons per step:

| D (photons/step) | optical, 1 output (2 det.) | optical, 64 outputs (128 det.) | electronic, bin 4 (1,024 det.) | electronic, bin 16 (64 det.) |
|---|---|---|---|---|
| 1e6 | 0.166 | 0.715 | 0.139 | 0.435 |
| 1e7 | 0.074 | 0.295 | 0.108 | 0.357 |
| 1e8 | **0.026** | 0.117 | 0.083 | 0.319 |
| 1e9 | 0.021 | 0.055 | 0.064 | 0.296 |
| 1e10 | 0.018 | 0.024 | 0.055 | 0.291 |
| noise-free | 0.018 | 0.018 | 0.046 | 0.290 |

8-bit mask transmissions lose almost nothing (0.019 noise-free), 6-bit is close, 4-bit gives ≈ 0.075. 64 outputs split the
light 64 ways and need ≈ 1e9–1e10 photons per step in total to match one output at 1e8.

**Result.** The optical readout beats 1,024 per-bin detectors at every photon budget from 1e7 up, with 2 detectors instead of
1,024, because it reads every mode at full resolution. This removes the electronics that dominated the Exp. 34 energy and
the Exp. 46 cost. Caveat: the weights are trained offline, so the cavity, mask and gain must stay stable between calibrations;
drift was not modelled.

### Experiment 45 — Kuramoto–Sivashinsky forecasting (a harder, high-dimensional task)

KS on L 60, simulated on 128 points with ETDRK4 (h 0.025) and kept at Q 64 channels, sampled every 0.25 (`ks.py`; two fixes
were needed: project to real each step, because round-off's imaginary part grew at the unstable wavenumbers, and zero the
odd derivative at Nyquist). 32,000 samples. The reservoir sees the 64 channels through 64 fixed input patterns; the target is
the open-loop forecast x(t + h), h = 1, 4, 16 samples. NMSE on the test split; best setting per model:

| model | features | h 1 | h 4 | h 16 |
|---|---|---|---|---|
| linear in x(t) (floor) | — | 4.0e-3 | 0.060 | 0.54 |
| optical 64² (K 10, amp 100) | 256 | 2.2e-3 | 0.035 | 0.42 |
| optical 128² (K 10, amp 100) | 1,024 | 8.6e-5 | 0.0054 | 0.33 |
| optical 256² (K 2, amp 100) | 4,096 | 3.4e-5 | **0.0029** | 0.33 |
| optical 512² (K 2, amp 300) | 16,384 | 2.7e-5 | 0.0029 | 0.36 |
| NG-RC k 2 (quadratic monomials of 2 lags) | 8,384 | 2.7e-6 | 0.0015 | 0.32 |
| ESN 256, untuned grid | 256 | 4.5e-4 | 0.0105 | 0.34 |
| ESN 16384, untuned grid | 16,384 | 5.8e-5 | 0.0037 | 0.32 |
| **ESN 1024, tuned (rho 0.7, input 0.01)** | 1,024 | 1.2e-6 | **0.00043** | 0.22 |
| **ESN 4096, tuned (rho 0.7, input 0.01)** | 4,096 | 4.1e-7 | **0.00035** | 0.21 |

**Result.** On KS a *tuned* 1,024-unit ESN beats the 65k-mode ring by ≈ 7× at h 4 (and ≈ 30× at h 1), and the ring stops
improving from 65k to 262k modes. The ESN only won after its input scale was cut to 0.01 (a nearly linear regime); with the
first grid (input 0.1–0.5) a 16k-unit ESN was no better than the ring. The optical side was tuned on three knobs only (trips
per input K, input amplitude, nothing else) and was still improving slightly with input amplitude at 300. The 512² K 10 and
1024² runs were cancelled when the work was wound down.

**What this means for the Exp. 31 equivalence.** Exp. 31 found 16–44 modes per ESN unit against a *fixed-recipe* ESN on
capacity tasks. Against a tuned ESN on KS the ratio is > 64 modes per unit at 65k modes, and it grows with size because the ring
saturates. The scaling assumption in Exp. 46 is therefore optimistic.

### Experiment 47a — professional SLM (higher reflectivity), gain unchanged

The same 256² ring with the SLM reflectivity raised from 0.75 (aluminium LCOS, the default) to 0.95 and 0.99 (dielectric-mirror
SLMs), KS, K 2:

| SLM reflectivity | h 1 | h 4 | h 16 |
|---|---|---|---|
| 0.75 (default) | 3.4e-5 | **0.0029** | 0.33 |
| 0.95 | 3.6e-4 | 0.0093 | 0.40 |
| 0.99 | 8.3e-4 | 0.0133 | 0.41 |

**Result: worse, but not a fair test.** G0 was left at 1.6, so with less loss the ring runs much further above threshold, the
global gain saturates harder and the dominant mode takes more of the energy. A real comparison needs G0 (or the pump) re-tuned
to the same distance from threshold at each reflectivity; that was not run. What this does show is that the operating point
(net round-trip gain), not loss alone, sets reservoir quality.

### Experiment 47b — how many dimensions does the optical state use?

Eigen-spectrum of the centred feature covariance (one input channel, uniform stream, same input for all):

| state | eigenvalues > 1e-3 of the largest | > 1e-5 | > 1e-7 | participation ratio |
|---|---|---|---|---|
| optical 4k modes (g64) | 26 | 55 | 74 | 2.3 |
| optical 16k (g128) | 78 | 229 | 305 | 7.0 |
| optical 65k (g256) | 69 | 383 | 1,107 | 5.4 |
| optical 262k (g512) | 60 | 626 | 2,815 | 3.1 |
| ESN 1024 | 17 | 101 | 427 | 4.6 |
| ESN 4096 | 17 | 109 | 564 | 4.7 |

**Result.** The optical state is not low-dimensional next to an ESN (383 against 109 directions above 1e-5), but it grows
sublinearly: 64× more modes give ≈ 11× more weak directions and *no* more strong ones (60–80 above 1e-3 throughout). Most of the
variance sits in 3–7 directions.

### Experiment 46 — techno-economic model (MODELED)

`46-econ.py`: low/high price and power ranges for a prototype (lab parts) and volume (≥ 1k units) PHASER against H100-class GPUs
running a dense ESN of N = modes / r units, r = 16–44 modes per unit from Exp. 31. Every input is a stated assumption in the
script; nothing here is measured, and r is the optimistic Exp. 31 value (see Exp. 45). One input, one output, ring at
0.75 G steps/s, r 44:

| modes | readout | PHASER prototype | PHASER volume | PHASER power | GPUs for the same MAC rate | GPU single-stream max rate |
|---|---|---|---|---|---|---|
| 65k | optical | $21k–75k | $0.9k–5.4k | 13–79 W | 1.7–3.3 | 2e5 steps/s |
| 65k | electronic | $0.8M–4.2M | $21k–128k | 0.2–2.1 kW | 1.7–3.3 | 2e5 steps/s |
| 262k | optical | $21k–75k | $0.9k–5.4k | 13–79 W | 27–53 | 9e4 steps/s |
| 1M | optical | $21k–75k | $0.9k–5.4k | 13–79 W | 430–850 | 6e3 steps/s |

64 outputs raise the optical-readout power to ≈ 1 kW (photon budget). With a "digital efficiency" of 100 (a digital model 100×
cheaper per step than a dense ESN at the same quality, which NG-RC and a tuned small ESN already are on KS), the cost advantage
only appears around 1M modes, and Exps. 43 and 45 say the ring's capability has stopped growing well before that.

**Where it could still win.** A single stream at ≥ 1e8 steps/s: no number of GPUs runs one recurrent stream that fast (one
sequential step needs at least a kernel launch, ≈ 5 µs), while the ring runs at 0.75–1.5e9 steps/s. So the economic case is
latency-bound streaming (RF, optical-link or sensor streams at GHz rates with short memory), not throughput against batched
GPUs. Energy and power figures here are modelled (cf. Exp. 29), not measured.

### Conclusions of Part 2 — physics or algorithms?

Both.
* **Physics of this design.** The ring is linear in the field between gain passes with one *global* gain, so the features are
  quadratic in the input history (from detection); loss and the spectral gap set the memory; the input enters through a few
  fixed patterns; and the transfer operator is a few masks plus propagation, so mode count ≠ degrees of freedom. Result:
  dimension grows sublinearly and capability saturates at 65k–262k modes.
* **Algorithms and operating point.** The mask is random and untrained, the operating point barely tuned (Exp. 47a shows it
  matters a lot), and the digital baseline only won after tuning.

**Next experiments, in order.**
1. Gradient-train the phase masks for the task through the differentiable twin (the Exp. 36 engine).
2. A per-mode intracavity nonlinearity (saturable absorber or Kerr; already in the logic physics) to get past quadratic
   features.
3. Re-run 47a with G0 re-tuned to a fixed distance from threshold at each SLM reflectivity.
4. More input channels; workloads where digital costs explode (many channels, GHz streaming, long memory).
5. Finish the cancelled runs: 512² K 10, 1024² KS and capacity (`g1024`), ESN 16384 capacity.

## Experiment 48 (2026-10-13) — the ring as a linear feedback system: no gain, plus a reference beam

Question from the owner: would it help to boost the light every round trip and saturate it to a level, so the ring stays in a
linear feedback range? Code: `48-spectrum.py`, `48-linear.py`; queues `48-queue.sh`, `48b/c/d-queue.sh`; log `out/48.log`;
results in `out/45/results.json` (kind `optical-linear`) and `out/48/`.

### 48a — where the Exp. 30/31 ring actually operates

Eigenvalues of the passive round trip (gain set to 1) of the 64² ring, dense (`out/48/res_n64.json`):

* |λ_1| = 0.820 (33 % power loss per trip for the best mode); √G0·|λ_1| = **1.037: the ring is a laser just above threshold**.
  The fast global gain then clamps the net gain of the lasing mode to exactly 1.
* The cavity is nearly degenerate: **111 modes within 1 % of |λ_1|**, 162 within 10 %, 292 within 30 %. Relative to the lasing
  mode, ~100 modes have memories of hundreds to thousands of trips.
* The input patterns overlap weakly with the top modes: 3 % of their energy is in the top 10, 21 % in the top 50, 63 % in the
  top 100, 82 % in the top 400.

So the lasing ring's effective spectral radius is 1 for ~100 modes: memory far longer than KS wants (the tuned ESN's optimum is
ρ 0.5–0.7), and old inputs never wash out except through slow mode competition. This also explains Exp. 47a: a better SLM at the
same G0 runs further above threshold, so the circulating lasing light grows and the fixed-amplitude input becomes relatively
weaker. (The 256² eigen-solve with ARPACK, k 400, did not finish in 30 min on CPU and was stopped.)

### 48b — linear ring on KS, noise-free

`48-linear.py`: the same 256² ring and 64 input patterns, gain constant (no saturation; G0 = 1 is passive, G0 < 1 adds loss,
G0 > 1 is gain below threshold), plus a constant coherent carrier c·P_c injected with the signal (a fixed random-sign sum of the
input patterns at the signal's scale; physically, a DC offset on the input modulator). Detection |c·E_c + E_s|² then contains
the linear terms 2c·Re(E_c* E_s) (homodyne) as well as the quadratic |E_s|². Bin 4 (4,096 features), KS h = 1, 4, 16.

| G0 (per-trip amplitude ρ = √G0·0.82) | carrier 0 | 10 | 30 | 100 | 300 |
|---|---|---|---|---|---|
| 1.4 (ρ 0.97, below threshold) | 0.0375 | 0.0075 | — | 0.0017 | — |
| 1.2 (ρ 0.90) | 0.0062 | 0.0022 | — | — | — |
| **1.0 (ρ 0.82, passive: no gain)** | 0.0029 | 0.0018 | 0.00084 | 0.00051 | **0.00035** |
| 0.7 (ρ 0.69) | — | 0.0013 | 0.00089 | 0.00055 | — |
| 0.5 (ρ 0.58) | — | 0.0013 | 0.0011 | 0.00055 | — |
| 0.3 (ρ 0.45) | — | 0.0014 | 0.0012 | 0.00072 | — |
| K 1, G0 1.0 | — | 0.0023 | 0.0014 | 0.00066 | — |
| K 1, G0 0.7 | — | 0.0018 | 0.0011 | 0.00053 | — |

(NMSE at h 4. Lasing ring, Exp. 45: 0.0029. Tuned ESN-1024: 0.00043; tuned ESN-4096: 0.00035.)
The best point, passive with carrier 300: h1 7.9e-7, h4 **0.00035**, h16 **0.208**, equal to the tuned 4,096-unit ESN
(4.1e-7 / 0.00035 / 0.206) and better than ESN-1024. Passive with carrier 100 (0.00051 / 0.223) is at ESN-1024 parity.

**Result.** More gain is worse, monotonically: 0.0029 passive → 0.0062 at G0 1.2 → 0.0375 at G0 1.4 (no carrier). The gain
medium and its saturation were hurting, not helping. The passive ring at K 2 already has ρ_step ≈ 0.67, the ESN's sweet spot;
extra loss (G0 0.5–0.7) is neutral to slightly better at small carriers. The missing ingredient was the coherent reference:
it supplies the linear terms that intensity detection alone cannot, and it closes the noise-free 7–10× gap to tuned ESNs.

### 48c/d — the same under shot noise

Poisson + 2 e⁻ read noise per detector bin (4,096 bins). Two accountings: D = all detected photons per step including the
carrier's (48c), or D = the signal's photons with the carrier's light added on top (48d, homodyne accounting: the reference is
extra laser power whose shot noise is included). NMSE at h 4, passive ring:

| D (photons/step) | carrier 0 | c 10, D signal | c 30, D total | c 30, D signal | c 100, D signal | c 300, D signal |
|---|---|---|---|---|---|---|
| 1e6 | 0.0107 | 0.0107 | — | 0.0090 | 0.0088 | 0.0086 |
| 1e7 | 0.0066 | 0.0059 | — | 0.0045 | 0.0043 | 0.0041 |
| 1e8 | 0.0048 | 0.0037 | 0.0173 | 0.0026 | 0.0024 | 0.0022 |
| 1e9 | 0.0038 | 0.0027 | 0.0088 | 0.0017 | 0.0015 | 0.0013 |
| 1e10 | 0.0033 | 0.0023 | 0.0044 | 0.0013 | 0.00099 | 0.00078 |
| 1e12 | 0.0030 | — | 0.0017 | — | — | — |

**Result.** With homodyne accounting, the carrier helps at every signal budget (≈ 2× at 1e8–1e9, 4× at 1e10). But it costs light:
the carrier carries c² times the signal's power. At 0.75 G steps/s, 1e10 detected photons per step is ≈ 2.3 W of detected
light (hν = 3.1e-19 J). So at the full GHz rate a practical budget is ~1e10 photons per step *in total*, i.e. c ≈ 10 on 1e8 signal
photons → h4 ≈ 0.0037, no better than the lasing ring noise-free. The noise-free ESN parity needs either a lower step rate
(more photons per step at the same power; 10–100 MS/s gives 75–7.5 × 1e10 at 2.3 W) or a better readout. Untested: the optical
readout (Exp. 44) for KS, a local oscillator added only at the detector (not circulating), and balanced detection.

### Implications

* The answer to "boost and saturate each trip": for short-memory tasks like KS, *no* — the best ring is passive, and fast
  saturating gain is what made the lasing ring worse. For long-memory tasks (NARMA, linear memory capacity) the idea is right
  in the form "net gain just below threshold, held there by a SLOW servo" (a long-lifetime gain medium such as Er/Yb/Nd, or a
  pump feedback loop), never a per-trip saturation, which acts as a global nonlinearity and makes one mode win.
* A passive ring drops the gain chip and pump ($3–15k prototype, $0.3–2k volume, 2–20 W in Exp. 46), and its carrier is a DC
  offset on the input modulator. A constant-gain, linear ring also removes Exp. 32's ~1 ns gain-recovery requirement for time-slot
  multiplexing and lets wavelength channels share the optics without gain cross-talk.
* The ring is then a linear dynamical system read out by a quadratic detector: a second-order Volterra model with an optical
  memory. Tasks needing higher-order nonlinearity still need a per-mode nonlinear element.

## Experiments 49–53 (2026-10-13) — can training and scale break the ceiling?

Sprint goal set after Exp. 48: decide in simulation whether the passive ring's capability can be pushed past a small digital
network. KS, K 2, bin 4, passive ring with a reference beam throughout. Code: `50-train.py` (differentiable passive ring; trains
the SLM phase mask `m`, a second phase plane `2`, the 64 input patterns `p`, the reference pattern `c`, the reference strength
`s`, a per-mode saturable absorber `a`; shot noise inside training with `NOISE_D`), `51-train-rnn.py` (digital baseline trained
with the identical objective), queues `49-`…`53-queue.sh`, logs `out/49.log`…`out/53.log`, results in `out/45/results.json`.
The trained parameters (`out/50/*.pt`) stay on the peer (gitignored; regenerated by the seeded runs).

**Objective used for all training.** Each iteration draws windows of the KS training split, fits a ridge readout in closed
form on half of them and back-propagates the held-out error of the other half through the ring (or the RNN). Final numbers
come from the standard Exp. 45 scoring of a full 32k-step run; the test split is never seen in training. With nothing trained
the script reproduces Exp. 48 to four digits (0.0028677 vs 0.0028679).

### 49 — scaling of the untrained passive ring (noise-free)

| modes | detectors | h 4, carrier 100 | h 4, carrier 300 | h 16, carrier 300 |
|---|---|---|---|---|
| 4k (64²) | 256 | 0.0029 | 0.0020 | 0.233 |
| 16k (128²) | 1,024 | 0.00086 | 0.00063 | 0.210 |
| 65k (256²) | 4,096 | 0.00051 | 0.00035 | 0.208 |
| 262k (512²) | 16,384 | 0.00039 | 0.00031 | 0.195 |

It keeps improving, but slowly: 64× more modes buys ≈ 7× at h 4, and almost nothing from 65k to 262k.

### 50 — trained optics (noise-free, carrier 100, 1,500 Adam iterations)

| ring | trained | h 1 | h 4 | h 16 |
|---|---|---|---|---|
| 64² | nothing | 5.5e-5 | 0.0029 | 0.255 |
| 64² | mask only | 1.1e-5 | 0.0012 | 0.216 |
| 64² | input + reference patterns only | 7.1e-7 | 0.00032 | 0.181 |
| 64² | mask + patterns | 5.2e-7 | **0.00028** | 0.174 |
| 64² | + second phase plane | 4.6e-7 | 0.00026 | 0.170 |
| 64² | + per-mode saturable absorber (Exp. 53) | 5.9e-7 | 0.00031 | 0.182 |
| 128² | nothing | 4.8e-6 | 0.00086 | 0.233 |
| 128² | mask + patterns | 2.9e-7 | **0.00021** | 0.160 |
| 128² | + second phase plane | 2.4e-7 | 0.00019 | 0.166 |

Training gives 4–10× at h 4; most of it comes from the input and reference patterns, not the round-trip mask. A trained 4k-mode
ring with 256 detectors beats the *tuned* 4,096-unit ESN (0.00035 / 0.206). A second plane adds ≈ 10 %; the absorber adds
nothing. Scale now buys little: 4× more modes, 0.00028 → 0.00021.

### 51 — the fair digital baseline: an RNN trained the same way

| model | h 1 | h 4 | h 16 |
|---|---|---|---|
| tuned ESN-4096 (Exp. 45) | 4.1e-7 | 0.00035 | 0.206 |
| **trained tanh RNN, 256 units** | 1.8e-8 | **3.7e-5** | **0.114** |
| trained tanh RNN, 1,024 units | 3.6e-9 | 1.8e-5 | 0.115 |
| best trained ring (128², noise-free) | 2.4e-7 | 1.9e-4 | 0.160 |

(Not usable: the 4,096-unit RNN did not train with these settings, 0.0082; the 'quad' linear-recurrence variants diverged,
NMSE 1. Neither was tuned further.) **A 256-unit trained RNN is 5–6× better than the best trained ring at h 4 and clearly
better at h 16, noise-free.**

### 52/53 — shot noise

Trained noise-free, evaluated with noise (52; D = signal photons, reference light on top): the gain mostly disappears
(128² at 1e8 signal photons: trained 0.0024, untrained 0.0029), and the optics lean on a reference 2–3e4× brighter than the
signal. So Exp. 53 trains WITH noise at a fixed TOTAL photon budget (signal + reference; 2 e⁻ read noise per bin) and lets the
ring choose its reference strength:

| total photons / step | ring | trained | h 4 | h 16 | chosen reference strength |
|---|---|---|---|---|---|
| 1e10 (≈ 2.3 W detected at 0.75 GS/s) | 64² | nothing (c 10) | 0.0160 | 0.367 | — |
| 1e10 | 64² | mask, patterns, strength | 0.0033 | 0.251 | 194 |
| 1e10 | 64² | + absorber | 0.0028 | 0.245 | 131 |
| 1e10 | 128² | mask, patterns, strength | 0.0023 | 0.235 | 59 |
| 1e12 (≈ 10 MS/s at the same power) | 64² | nothing (c 10) | 0.0123 | 0.348 | — |
| 1e12 | 64² | mask, patterns, strength | 0.0018 | 0.230 | 392 |
| 1e12 | 64² | + absorber | 0.0015 | 0.224 | 270 |
| 1e12 | 128² | mask, patterns, strength | 0.0011 | 0.208 | 101 |

Noise-aware training recovers 5–10× over the untrained ring at the same budget, but the result is 30–60× worse at h 4 than the
256-unit digital RNN (3.7e-5), and 100× more photons buy only ≈ 2×.

### Verdict of the sprint

1. **Operating regime: settled.** Passive, linear, with a reference beam, trained input patterns. No gain medium.
2. **The ceiling is precision, not modes.** With per-bin detection, shot noise at any practical light power limits the ring to
   NMSE ~1e-3 on KS, where a small digital RNN reaches ~1e-5. Modes, masks, a second plane and an absorber do not change that.
3. **High-precision forecasting is not this machine's workload.** A 256-unit RNN is 65k multiply-adds per step: an FPGA runs
   it at ~10 MS/s. The ring can only win where (a) the stream is faster than digital hardware can step a recurrent model, and
   (b) the task tolerates ~1e-2–1e-3 analog precision: detection and classification of fast signals, not regression.
4. **Not yet tested:** the 2-detector optical readout on KS (all light on few detectors changes the noise), a reference added
   only at the detector, and any classification task. Next sprint: a fast-signal classification benchmark at 1e8–1e10 photons
   per step, trained ring against a trained digital network of the size that can run at that rate.

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
| 43 reservoir scaling | done to 262k modes; capacity saturates (417 → 432); 1024² cancelled |
| 44 optical readout | **done: 2 detectors beat 1,024 per-bin detectors from 1e7 photons/step** |
| 45 KS forecasting | done to 262k modes; tuned ESN-1024 beats the 65k ring ≈ 7× at h 4; 1024² cancelled |
| 46 economics (modeled) | done; viable only for single-stream GHz-rate workloads unless capability keeps scaling |
| 47a professional SLM | run at unchanged gain: worse; needs G0 re-tuned (not run) |
| 47b effective dimension | done; sublinear growth, 60–80 strong directions at every size |
| 48 linear ring (2026-10-13) | **passive ring + reference beam = tuned ESN-4096 on KS, noise-free**; gain is harmful; at a ~1e10-photon budget per step (≈ 2 W at 0.75 GS/s) the advantage shrinks to ≈ lasing-ring level |
| 49 passive-ring scaling | done to 262k modes: improves slowly (≈ 7× for 64× modes), flat past 65k |
| 50 trained optics | **done: 4–10× from training; a trained 4k-mode ring beats the tuned ESN-4096 noise-free** |
| 51 trained digital baseline | done: a trained 256-unit RNN is 5–6× better than the best trained ring |
| 52/53 noise, noise-aware training, absorber | done: at 1e10–1e12 photons/step the trained ring is 30–60× worse than the RNN; absorber ≈ no gain |
