# Energy per multiply: electrons vs photons (PHASER notes, 2026-09-25)

Sources for the numbers the website may quote about energy per multiply, and how PHASER's own figures are derived. Model
details and raw data: `research/2026-09-14/REPORT.md` Experiments 29–34, `34-energy.py`, `out/34/energy.json`.

Wording rules:
- **Estimated** means not simulated: datasheets, literature, or closed-form arithmetic.
- **Modeled** means computed from our simulator's results plus the stated device assumptions.
- No PHASER hardware has been built or measured.
- Never quote 10⁶×.

## 1. What counts as "a multiply"

| term | definition | use |
|---|---|---|
| digital MAC | one multiply-accumulate (2 ops): 1 MAC = 2 / (TOPS/W) pJ | chip figures |
| **equivalent MAC** (PHASER) | PHASER's energy per input step ÷ the MACs per step of the **dense digital recurrent network (echo-state network, ESN) of equal task quality**: N_eq² + N_eq for N_eq units | **the only figure the site should use** |
| physical "optical MAC" | energy per step ÷ (K trips × N_modes² complex products of the round-trip operator) | **do not use.** The operator is fixed and random, so these "MACs" are worth far fewer digital MACs (4096 modes ≈ 64–165 ESN units, Exp. 31). |

## 2. Electrons: published digital figures

| figure | energy | scope | source |
|---|---|---|---|
| 8-bit int multiply / add, 45 nm | 0.2 / 0.03 pJ, so an 8-bit MAC ≈ **0.23 pJ** | arithmetic only | Horowitz, "Computing's energy problem", ISSCC 2014, Fig. 1.1.9, https://gwern.net/doc/cs/hardware/2014-horowitz-2.pdf |
| FP16 multiply / add, 45 nm | 1.1 / 0.4 pJ, so an FP16 MAC ≈ **1.5 pJ** | arithmetic only | same |
| FP32 multiply / add, 45 nm | 3.7 / 0.9 pJ, so an FP32 MAC ≈ 4.6 pJ | arithmetic only | same |
| SRAM read, 64 bit (8 KB / 32 KB / 1 MB) | 10 / 20 / 100 pJ | data movement | same |
| DRAM access, 64 bit | 1.3–2.6 nJ | data movement | same |
| 5 nm inference accelerator (4-bit, VS-Quant) | 95.6 TOPS/W, ≈ **21 fJ/MAC** | accelerator with its SRAM | Keller et al. (NVIDIA), JSSC 2023, https://research.nvidia.com/publication/2023-01_956-topsw-deep-learning-inference-accelerator-vector-scaled-4-bit-quantization |
| NVIDIA H100 SXM, INT8 dense | 1,979 TOPS at 700 W, ≈ **0.71 pJ/MAC** | whole chip + HBM, at peak | https://www.nvidia.com/en-us/data-center/h100/ |
| Google TPU v4 | 275 TOPS at 170 W mean, ≈ **1.24 pJ/MAC** | whole chip | Jouppi et al., ISCA 2023, https://arxiv.org/abs/2304.01433 |
| H100, compute-bound BF16 (measured) | ≈ 1 pJ/FLOP ≈ **2 pJ/MAC**; 10–1000× worse at small batch | whole chip | Adiletta, Wei & Brooks, arXiv 2602.18568, https://arxiv.org/pdf/2602.18568 |
| A100 as used by optical-transformer projections | ≈ 0.3 pJ/MAC | system estimate | Anderson et al., "Optical Transformers", https://arxiv.org/abs/2302.10360 |

In short: arithmetic alone is 0.02–0.2 pJ per 8-bit MAC (5–45 nm). Real accelerators at chip level spend about 0.7–2 pJ per
MAC. At batch 1, when weights stream from memory, a GPU can spend tens to hundreds of pJ per MAC. That last range is our
estimate: 3.35 TB/s at 34–100 % of 700 W.

The site's "**2.0 pJ per multiply in silicon**" matches an FP16/FP32-class MAC at 45 nm or a batched GPU at chip level. It
does not describe the best modern 8-bit hardware, which is 0.02–0.7 pJ.

## 3. Photons: published optical figures (for context)

| claim | value | source |
|---|---|---|
| Standard quantum limit of photoelectric multiplication | 50–100 zJ/MAC (large N); ~10 fJ/MAC projected for a system including electronics | Hamerly et al., PRX 9, 021032 (2019), https://link.aps.org/doi/10.1103/PhysRevX.9.021032 |
| < 1 photon per multiplication (MNIST) | ≈ 0.64 detected photons per multiply at 90 % accuracy (≈ 2.5×10⁻¹⁹ J optical); ~10⁻¹⁶ J per multiply projected with electronics | Wang et al., Nat. Commun. 13, 123 (2022), https://arxiv.org/abs/2104.13467 |
| Optical transformers | energy/MAC ∝ 1/width; ~100× projected over GPUs for large models | Anderson et al. 2023, https://arxiv.org/abs/2302.10360 |
| LightOn OPU (free-space random projection) | "1500 TOPS at 30 W" ≈ 20 fJ/op (vendor claim) | Hesslow et al., https://arxiv.org/pdf/2104.14429 |
| Interconnect energy targets | ~10 fJ/bit links; receivers 0.17–1.4 pJ/bit | Miller, JLT 35, 346 (2017), https://www-ee.stanford.edu/~dabm/448.pdf |

These are projections for feed-forward matrix products with programmable weights. PHASER is different: its operator is a
fixed random recurrent one, so its "multiplies" have to be converted into equivalent digital MACs (section 1).

## 4. Boundary electronics and optics (inputs to our model)

| item | value used (low / nominal / high) | source |
|---|---|---|
| 8-bit ADC per sample, < 1 GS/s | 0.3 / 2.6 / 20 pJ | Murmann ADC survey, https://github.com/bmurmann/ADC-survey (best ≈ 2.55 pJ at 1 GS/s; median ≈ 20 pJ) |
| 8-bit ADC per sample, 1–20 GS/s | 2.2 / 5 / 33 pJ | same (best 2.2 pJ at 10 GS/s, ISSCC 2025; median ≈ 33 pJ) |
| photodiode + TIA per sample | 0.1 / 1 / 5 pJ | IBM 64 Gb/s 1.4 pJ/bit; 0.17 pJ/bit 3-D receiver (Miller 2017) |
| DAC + modulator per input sample | 0.1 / 1 / 10 pJ | TFLN ≈ 1 fJ/bit (modulator only); 10 GS/s DAC ≈ 10 pJ/sample (Anderson 2023) |
| electrical → circulating light | 0.45 / 0.27 / 0.1 | red AlGaInP LD 45 % WPE (Ushio 2024, https://www.ushio.co.jp/en/laser/news/501180.html); blue pump 48 % (https://www.furukawaelectric.com/en/rd/review/fr052/fr52_03.pdf) × quantum defect × overlap |
| static SLM hold / thermal control | 0 / 0.1 / 1 W; 0.05 / 0.3 / 1 W | estimated (0 W for a fabricated plate) |
| digital MAC for the baseline | 0.05 / 0.2 / 1 pJ | 8-bit ASIC incl. local SRAM (table 2) |

Optical loss coefficients (N-BK7, AR coatings, LCOS, mirrors) are listed with sources in REPORT.md Experiment 33.

## 5. PHASER: energy per input step and per equivalent MAC (modeled)

Photon cost (Exp. 34). The detector integrates the output tap T over the K trips of a step, so it collects
D = K·T·QE·N_c photoelectrons. The gain must replace the whole round-trip loss L. That gives

  E_pump = D·hν·(L/T) / (QE·η).

D_req is the smallest detected-photon budget per step that reaches the stated task quality (Exp. 30). "Bundle29" is
NARMA10 ≤ 0.127, memory capacity ≥ 33.7 and delayed XOR ≥ 0.989: the Exp. 29 operating point. All figures below are
nominal, with the low…high range in brackets. The 64² grid has 4096 modes, which Exp. 31 found equivalent to N_eq ≈ 64–165
tuned ESN units, i.e. 4.2k–27k dense MACs per step.

| scenario (64² modes, bundle29 quality) | D_req | J per input step | steps/s per system | per equivalent MAC |
|---|---|---|---|---|
| Exp. 29 point (ring, K = 10, as modelled) | 4×10⁹ | 44 nJ (25–130) | 1.5×10⁸ | 1.6–10 pJ |
| tuned ring (K = 2, Exp. 30) | 3.2×10⁷ | 1.9 nJ (0.40–10) | 7.5×10⁸ | 68–450 fJ |
| + static fabricated plate, low-loss glass, 30 % tap | 3.2×10⁷ | 1.5 nJ (0.22–8.3) | 6.8×10⁸ | 54–350 fJ |
| + 13 time slots (fast gain, τ ≈ 1 ns) | 3.2×10⁷ | 1.7 nJ (0.64–10) | **8.9×10⁹** | 61–400 fJ |
| linear stack, 4 fabricated plates, K = 1 | 10⁶ | 1.7 nJ (0.62–10) | 3.9×10⁹ | 61–400 fJ |
| short-memory task, 8×8 bins, plate, 13 slots | 10⁷ | 0.46 nJ (0.17–2.7) | 8.9×10⁹ | 17–110 fJ |

After tuning, photons are no longer the cost. The pump is 0.002–0.3 nJ. **Detection electronics (0.4–2.8 nJ) and static
power dominate.**

Same quality on a digital machine, from fairly tuned baselines (Exp. 30b), at 0.2 pJ/MAC (range 0.05–1):

| baseline | MACs/step | J/step |
|---|---|---|
| NG-RC (40 delay taps + quadratic monomials of the first 12) | 196 | **0.04 nJ** (0.01–0.2) |
| two small ESNs (64 linear + 64 tanh) | 8,320 | 1.7 nJ (0.4–8.3) |
| one tanh ESN (needs N = 1024 to meet all three metrics) | 1.05 M | 210 nJ (52–1050) |

**Result at 64²:**
- PHASER is at parity with two small ESNs.
- It is about 40× worse than the cheapest digital algorithm for these benchmark tasks (NG-RC).
- It is about 140× better only than a single large ESN, which is an unfair baseline.

**Scaling (modeled from Exp. 31 + 34).** Exp. 31 measured the modes-per-unit equivalence at 64², 128² and 256² modes: it
holds at about **16–64 modes per ESN unit** up to 65,536 modes, provided the detector bins scale with the modes (16 modes
per bin). Extrapolated beyond that with the same photons per mode:

| modes | equivalent dense ESN | PHASER J/step (nominal) | dense 8-bit ASIC ESN J/step | ratio | PHASER per equivalent MAC |
|---|---|---|---|---|---|
| 4,096 (simulated) | 64–256 units | 1.5 nJ | 0.8–13 nJ | 0.6–9× | 22–350 fJ |
| 65,536 (simulated, equivalence measured) | 1,000–4,100 | 17 nJ | 0.2–3.4 µJ | 12–200× | 1–16 fJ |
| 10⁶ (extrapolated) | 16k–66k | 0.26 µJ | 54 µJ – 0.86 mJ | **200–3,300×** | **0.06–1 fJ** |
| 1,000× point | needs ≈ 0.3–5×10⁶ modes (16…64 modes per unit, nominal devices) | | | | |

These ratios are against a **dense** ESN. A sparse ESN, or NG-RC, is linear in N and removes the advantage (Exp. 29: at
best 17× worse). A task that really needs dense high-dimensional recurrence at 10⁶-mode scale has not been demonstrated.

## 6. Sentences the website may use

- Silicon: "Today's AI chips spend roughly **0.7–2 pJ per multiply-accumulate** at chip level (NVIDIA H100, Google TPU v4),
  and far more when weights stream from memory."
- PHASER: "**Modeled** at one million optical modes, PHASER's recurrent optics would spend about **0.06–1 fJ per equivalent
  multiply**. That is roughly 200–3,000× less energy per step than an equally capable dense recurrent network on an 8-bit
  chip. This assumes the mode-to-neuron equivalence we measured up to 65,000 modes continues to hold at that scale. At
  today's simulated size (4,096 modes) PHASER is at parity with small digital networks."
- Short form, for a stat tile: "**~1 fJ per equivalent multiply (modeled, 10⁶ modes)** vs **~1 pJ** on today's AI chips."
  The caveat link must go to the long form.
- Do not say: "0.002 pJ per multiply in PHASER" without "equivalent" and "modeled". Do not say "1,000× less energy" without
  "modeled at 10⁶ modes, vs a dense recurrent network". Never quote 10⁶×.
