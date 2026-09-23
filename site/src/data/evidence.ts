/**
 * Every number on the site comes from here. "measured" means measured in the PHASER simulator (there is no hardware yet);
 * the copy says "simulated". Sources link to the exact lines of the research report or code.
 */
export type EvidenceLevel = 'measured' | 'modeled' | 'theoretical' | 'target'

export const LEVEL_LABEL: Record<EvidenceLevel, string> = {
  measured: 'simulated',
  modeled: 'modeled',
  theoretical: 'theoretical',
  target: 'target',
}

export const REPO = 'https://github.com/JacobFV/phaser-design'
export const REPORT = `${REPO}/blob/main/research/2026-09-14/REPORT.md`
const report = (from: number, to: number) => `${REPORT}?plain=1#L${from}-L${to}`
const file = (path: string) => `${REPO}/blob/main/${path}`

export interface Evidence {
  id: string
  value: string
  unit?: string
  label: string
  level: EvidenceLevel
  /** experiment / benchmark identifier */
  ref: string
  source: string
  derivation: string
}

const E = <T extends Record<string, Omit<Evidence, 'id'>>>(o: T) =>
  Object.fromEntries(Object.entries(o).map(([id, v]) => [id, { id, ...v }])) as { [K in keyof T]: Evidence }

export const EV = E({
  tripTime: {
    value: '0.667', unit: 'ns', label: 'one round trip = one compute step', level: 'measured', ref: 'Config A_preset §0.2',
    source: report(26, 33),
    derivation: 'Σ n_g·L / c over the modelled route of the reflective LCOS ring (≈ 200 mm of air): 0.667 ns, i.e. 1.50 GHz.',
  },
  tripRate: {
    value: '1.5', unit: 'GHz', label: 'round-trip rate', level: 'measured', ref: 'Config A_preset §0.2',
    source: report(26, 33), derivation: '1 / 0.667 ns.',
  },
  inputRate: {
    value: '150', unit: 'MHz', label: 'input rate at K = 10 trips per input', level: 'measured', ref: 'Exp. 15 / 17',
    source: report(309, 331),
    derivation: 'K = 10 recurrences per input × 0.667 ns = 6.7 ns per input step. The best reservoir and control results use K = 10.',
  },
  mcOptical: {
    value: '34.6', label: 'memory capacity, optical reservoir (A_preset, K = 10)', level: 'measured', ref: 'Exp. 15',
    source: report(309, 331),
    derivation: 'Σ r² of reconstructing u(t−k), k = 1…60, with a digital ridge readout of 256 binned detector intensities; test steps 2200–3200. Absolute figure: tuned digital reservoirs of the same size reach similar or higher values, so the case is speed and energy per step, not quality.',
  },
  control: {
    value: '0.87', label: 'closed-loop tracking error under occlusion, optical K = 10 (memoryless readout: 1.57)', level: 'measured', ref: 'Exp. 17',
    source: report(604, 616),
    derivation: 'Target tracking under occlusion, 4 unseen 600-frame episodes; optical state never reset; oracle 0.146. Shows the cavity carries usable memory; no comparison against tuned digital recurrent models is claimed.',
  },
  memory1e6: {
    value: '10⁶', unit: 'trips', label: 'persistent bits held with zero errors (667 µs)', level: 'measured', ref: 'Exp. 23',
    source: report(1456, 1480),
    derivation: 'Absorbing-mask lattice, 3 random 9-bit patterns, gain noise 10⁻³ per trip, full-field JS simulation, every pattern BER 0.',
  },
  density: {
    value: '69', unit: 'bits/mm²', label: 'persistent storage density', level: 'measured', ref: 'Exp. 2 (nonlinear)',
    source: report(1113, 1121), derivation: '3 px cells on a 6 px (120 µm) pitch, 20 µm pixels.',
  },
  nand: {
    value: '10⁵', unit: 'trips', label: 'persistent NAND, verified every trip', level: 'measured', ref: 'Exp. 26',
    source: report(1397, 1414),
    derivation: 'Cross-gain saturation shared over L_d = 100 µm; all 4 input cases hold from trip 400 to 10⁵; tolerates 10⁻³ gain noise; fails at 0.03 rad static phase error.',
  },
  nandSettle: {
    value: '53', unit: 'ns', label: 'gate settling time (≈ 80 trips)', level: 'measured', ref: 'Exp. 28',
    source: report(1521, 1534), derivation: '≈ 80 round trips × 0.667 ns.',
  },
  modes: {
    value: '85', label: 'long-lived modes (τ > 10⁵ trips), self-imaging ring', level: 'measured', ref: 'Exp. 5',
    source: report(120, 130), derivation: 'Eigen-decomposition of the explicit 4096 × 4096 round-trip operator.',
  },
  limitCycle: {
    value: '160–4100', unit: 'trips', label: 'autonomous limit-cycle periods with cross-gain', level: 'measured', ref: 'Exp. 21b',
    source: report(1358, 1396), derivation: 'Stable oscillation over 10⁴ trips; 0.1–2.7 µs periods. Not yet turned into a sequencer.',
  },
  structured: {
    value: 'N', label: 'programmable parameters per SLM plane', level: 'theoretical', ref: 'Physics model',
    source: file('docs/ARCHITECTURE.md'),
    derivation: 'Propagation couples every sample to every other (angular-spectrum operator), but the program sets one phase per pixel: a structured dense transform with N parameters, not an arbitrary N × N matrix.',
  },
  target1e6: {
    value: '10⁶×', label: 'lower energy per step: what it would take', level: 'target', ref: 'Exp. 29 §5',
    source: report(1605, 1611),
    derivation: 'Modeled: a dense 8-bit ASIC reservoir costs N² × 0.2 pJ; the optical step costs 8.4 pJ per mode + 3.8 pJ per bin + 2.7 nJ static. The ratio reaches 10⁶ only at ≈ 1.9×10⁸ equivalent units, i.e. ≥ 7.5×10⁸ optical modes. A 1080p SLM has 2.1×10⁶ pixels. Out of reach; shown as a target, not a result.',
  },
  parity: {
    value: '38', unit: 'nJ', label: 'per input step, optical reservoir at its quality operating point (range 21–124 nJ)', level: 'modeled', ref: 'Exp. 29 §4',
    source: report(1589, 1604),
    derivation: 'Pump replacing 31.6 % loss per trip over 10 trips dominates (32 nJ nominal). Equal-quality tuned ESN-128: 3.3 nJ (≈ 10× less); ESN-1024, which beats it on every metric: 210 nJ (≈ 5× more). Quality simulated; energy modeled from device assumptions.',
  },
  photons: {
    value: '10¹⁰', unit: 'photons', label: 'circulating photons needed for full quality (≈ 4.6 W circulating)', level: 'measured', ref: 'Exp. 29 §2–3',
    source: report(1581, 1588),
    derivation: 'In-loop ASE plus detector shot and read noise, swept 10²…10¹² photons in the simulator. 10¹⁰ is the lowest budget within 10 % of noise-free on NARMA10 and MC. Shot noise binds; memory depth is why.',
  },
  crossover: {
    value: '260–1600', unit: 'units', label: 'break-even vs a dense 8-bit ASIC reservoir', level: 'modeled', ref: 'Exp. 29 §5',
    source: report(1605, 1611),
    derivation: 'Equivalent digital units, for 4 vs 32 optical modes per unit. 10× needs 1.8k–15k units, 100× 19k–155k, 1000× 0.18–1.4 M.',
  },
  sparse: {
    value: '17×', label: 'worse, at best, than a sparse digital reservoir', level: 'modeled', ref: 'Exp. 29 §5',
    source: report(1605, 1611), derivation: 'A sparse ESN (10 nonzeros per row) costs linear in N, like the optics, with a smaller constant. The optical reservoir never wins against it.',
  },
  logicEnergy: {
    value: '≈ 14', unit: 'nJ', label: 'per switch of a 120 µm saturable-gain cell', level: 'theoretical', ref: 'Exp. 29 note',
    source: report(1624, 1628),
    derivation: 'F_sat × A_cell with F_sat = hν/σ ≈ 10⁻⁴ J/cm² for a semiconductor gain medium. CMOS gates switch at ~10⁻¹⁶ J. Persistent optical logic is not an energy path.',
  },
  digitalStepCpu: {
    value: '1.6', unit: 'µs', label: 'assumed step of an equal-quality digital reservoir (ESN-128) on one CPU core', level: 'modeled', ref: 'assumption',
    source: report(1577, 1580),
    derivation: 'Assumption, not a measurement: 128² = 16,384 multiply-accumulates at an assumed 10 GMAC/s sustained on one SIMD core. ESN-128 is the smallest tuned digital reservoir matching the optical NARMA10 and XOR (Exp. 29).',
  },
  digitalStepAsic: {
    value: '128', unit: 'ns', label: 'assumed step of ESN-128 on a dedicated ASIC', level: 'modeled', ref: 'assumption',
    source: report(1577, 1580),
    derivation: 'Assumption: 128 parallel MAC units at 1 GHz, one matrix row per unit, 128 cycles per step, ignoring memory latency.',
  },
})

export type EvidenceId = keyof typeof EV
