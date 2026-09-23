import type { EvidenceLevel } from './evidence'
import X from './exp29.json'

/**
 * Experiment 29 (research/2026-09-14/REPORT.md, "Experiment 29"): energy per input step of the best reservoir operating
 * point, a tuned equal-quality digital baseline, and a modeled scaling law. Numbers are copied from out/29 by
 * site/scripts/build-energy.py; nothing here is typed in by hand except labels and assumptions.
 */
export const PENDING_EXP29 = false

export const EXP29_SOURCE = 'https://github.com/JacobFV/phaser-design/blob/main/research/2026-09-14/REPORT.md'
export const EXP29_DATA = 'https://github.com/JacobFV/phaser-design/tree/main/research/2026-09-14/out/29'

export interface EnergySeries {
  id: string
  label: string
  /** which side of the comparison: digital baseline, optical system, or a physical floor */
  kind: 'digital' | 'optical' | 'floor'
  level: EvidenceLevel
  /** joules per input step, aligned with EnergyModel.N (NaN where undefined) */
  joulesPerStep: number[]
  assumptions: string[]
  /** series sharing a band id are drawn as a filled range (e.g. 4 vs 32 optical modes per digital unit) */
  band?: string
  /** the series the ratio ruler divides by / into */
  ratioRole?: 'numerator' | 'denominator-optimistic' | 'denominator-pessimistic'
}

export interface EnergyComponent {
  id: 'pump' | 'source' | 'static' | 'detection' | 'modulator' | 'readout'
  label: string
  low: number
  nominal: number
  high: number
}

/** a point where the energy is modeled but the quality it buys was simulated */
export interface EnergyAnchor {
  id: string
  label: string
  kind: 'digital' | 'optical'
  energyLevel: EvidenceLevel
  qualityLevel: EvidenceLevel
  /** equivalent digital units: a range for the optical reservoir (4–32 modes per unit), a point for digital */
  N: [number, number]
  J: { low: number; nominal: number; high: number }
  quality: string
}

export interface QualityPoint { photons: number; memoryCapacity: number; narma10: number; xor: number; detectedPerStep: number }

export interface EnergyModel {
  /** equivalent digital reservoir units (optical: modes ÷ 4…32) */
  N: number[]
  /** input rate at which the optical step energy was computed (K = 10 trips per input) */
  inputRateHz: number
  series: EnergySeries[]
  anchors: EnergyAnchor[]
  components: EnergyComponent[]
  /** N (equivalent units) at which dense 8-bit ASIC / optical reaches a ratio, by optical assumption */
  nForRatio: { ratio: number; optimistic: number | null; pessimistic: number | null; floor: number | null }[]
  crossover: { optimistic: number; pessimistic: number }
  sparseBestRatio: number
  /** hardware scale marks, in equivalent units */
  hardware: { label: string; pixels: number; N: [number, number] }[]
  quality: { sweep: QualityPoint[]; clean: { memoryCapacity: number; narma10: number; xor: number }; operatingPhotons: number }
  notes: string[]
  source: string
}

const S = X.series
const nanify = (a: number[]) => a.map((v) => (v == null ? NaN : v))

export const ENERGY: EnergyModel = {
  N: X.N,
  inputRateHz: 1 / X.step_time_s,
  series: [
    {
      id: 'digital-dense-gpu', label: 'dense digital · GPU', kind: 'digital', level: 'modeled', joulesPerStep: nanify(S.digital_dense_gpu),
      assumptions: ['N² MACs per step (dense recurrent matrix)', '2 pJ/MAC effective, batch-1 GPU'],
    },
    {
      id: 'digital-dense-asic', label: 'dense digital · 8-bit ASIC', kind: 'digital', level: 'modeled', joulesPerStep: nanify(S.digital_dense_asic),
      ratioRole: 'numerator',
      assumptions: ['N² MACs per step (dense recurrent matrix)', '0.2 pJ/MAC, 8-bit ASIC incl. local SRAM'],
    },
    {
      id: 'digital-sparse-asic', label: 'sparse digital · ASIC', kind: 'digital', level: 'modeled', joulesPerStep: nanify(S.digital_sparse_asic),
      assumptions: ['10 nonzeros per row: cost linear in N', '0.2 pJ/MAC'],
    },
    {
      id: 'optical-4', label: 'PHASER · 4 modes/unit', kind: 'optical', level: 'modeled', joulesPerStep: nanify(S.optical_modeled_4), band: 'optical',
      ratioRole: 'denominator-optimistic',
      assumptions: [`${(X.per_mode_J * 1e12).toFixed(1)} pJ per mode per step (pump replaces 31.6 % loss/trip × 10 trips at 30 % wall-plug)`, `${(X.per_bin_J * 1e12).toFixed(1)} pJ per detector bin`, `${(X.static_J * 1e9).toFixed(1)} nJ static (SLM hold + thermal) per 6.7 ns step`, 'optimistic: 4 optical modes worth 1 digital unit (unverified at scale)'],
    },
    {
      id: 'optical-32', label: 'PHASER · 32 modes/unit', kind: 'optical', level: 'modeled', joulesPerStep: nanify(S.optical_modeled_32), band: 'optical',
      ratioRole: 'denominator-pessimistic',
      assumptions: ['as above; pessimistic: 32 optical modes per digital unit'],
    },
    {
      id: 'photon-floor', label: 'photon floor · 4 modes/unit', kind: 'floor', level: 'theoretical', joulesPerStep: nanify(S.optical_photon_floor_4),
      assumptions: [`${X.photons_per_mode.toExponential(1)} photons per mode per step at 650 nm`, 'η = 1, no electronics, no static power'],
    },
  ],
  anchors: [
    {
      id: 'optical-4096', label: 'PHASER, 4096 modes (Exp. 15 reservoir)', kind: 'optical', energyLevel: 'modeled', qualityLevel: 'measured',
      N: [128, 1024], J: { low: X.optical_total.low, nominal: X.optical_total.nominal, high: X.optical_total.high },
      quality: `MC ${X.operating_point.memory_capacity.toFixed(1)}, NARMA10 ${X.operating_point.narma10_nmse.toFixed(3)} at 10¹⁰ circulating photons`,
    },
    {
      id: 'esn-128', label: 'tuned ESN-128', kind: 'digital', energyLevel: 'modeled', qualityLevel: 'measured',
      N: [128, 128], J: { low: X.esn128.low, nominal: X.esn128.nominal, high: X.esn128.high },
      quality: 'matches the optical NARMA10 and XOR',
    },
    {
      id: 'esn-1024', label: 'tuned ESN-1024', kind: 'digital', energyLevel: 'modeled', qualityLevel: 'measured',
      N: [1024, 1024], J: { low: X.esn1024.low, nominal: X.esn1024.nominal, high: X.esn1024.high },
      quality: 'beats the optical reservoir on every metric',
    },
  ],
  components: [
    { id: 'pump', label: 'gain pump (replaces 31.6 % loss per trip)', low: X.components.low.pump, nominal: X.components.nominal.pump, high: X.components.high.pump },
    { id: 'source', label: 'input light (ideal coupler)', low: X.components.low.source_ideal_coupler, nominal: X.components.nominal.source_ideal_coupler, high: X.components.high.source_ideal_coupler },
    { id: 'static', label: 'SLM hold + thermal, per step', low: X.components.low.static, nominal: X.components.nominal.static, high: X.components.high.static },
    { id: 'detection', label: '256 × receiver + 8-bit ADC', low: X.components.low.detection, nominal: X.components.nominal.detection, high: X.components.high.detection },
    { id: 'readout', label: 'digital linear readout', low: X.components.low.readout, nominal: X.components.nominal.readout, high: X.components.high.readout },
    { id: 'modulator', label: 'input DAC + modulator', low: X.components.low.input_dac_mod, nominal: X.components.nominal.input_dac_mod, high: X.components.high.input_dac_mod },
  ],
  nForRatio: Object.entries(X.N_for_ratio).map(([r, v]) => ({
    ratio: Number(r),
    optimistic: (v as Record<string, number | null>).optical_modeled_4 ?? null,
    pessimistic: (v as Record<string, number | null>).optical_modeled_32 ?? null,
    floor: (v as Record<string, number | null>).optical_photon_floor_4 ?? null,
  })),
  crossover: { optimistic: X.crossover_vs_dense_asic.optical_modeled_4, pessimistic: X.crossover_vs_dense_asic.optical_modeled_32 },
  sparseBestRatio: X.vs_sparse_asic_max_ratio,
  hardware: [
    { label: 'simulated today (64² grid)', pixels: 4096, N: [128, 1024] },
    { label: '1080p SLM', pixels: 1920 * 1080, N: [(1920 * 1080) / 32, (1920 * 1080) / 4] },
  ],
  quality: {
    sweep: X.sweep.map((p) => ({ photons: p.Nc, memoryCapacity: p.memory_capacity, narma10: p.narma10_nmse, xor: p.xor_d2, detectedPerStep: p.detected_per_step })),
    clean: { memoryCapacity: X.clean.memory_capacity, narma10: X.clean.narma10_nmse, xor: X.clean.xor_d2 },
    operatingPhotons: X.operating_point.Nc,
  },
  notes: [
    'At the simulated scale the optical reservoir is at parity with an equal-quality digital reservoir.',
    'Any advantage comes only against dense O(N²) digital recurrences at large N, and assumes the 4–32 modes-per-unit equivalence holds as the optics scales.',
  ],
  source: EXP29_SOURCE,
}
