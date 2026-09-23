// Experiment 29a: the Exp. 15 reservoir (Apre_lin, K = 10) with physical noise at a stated photon budget.
// N_c = mean photons circulating in the ring. Field units are mapped to photons by s = N_c / <Σ|E|²> (from a noise-free
// warm-up). Each trip adds amplified spontaneous emission: n_sp·(G−1) photons per grid sample (one sample ≈ one spatial
// mode at 1 sample/pixel), complex Gaussian. The detector sees the 5 % tap for K trips at quantum efficiency QE, with
// Poisson shot noise and Gaussian read noise per bin. usage: npx vite-node 29-noise.ts <Nc|inf> <uniform|bits>
import { readFileSync } from 'node:fs'
import { AssetStore } from '../../src/core/physics/assets'
import type { RunContext } from '../../src/core/physics/elements/element'
import { createField } from '../../src/core/physics/field/grid'
import { CompiledSystem } from '../../src/core/physics/system'
import { mulberry32, gaussian } from '../../src/core/common/random'
import { slmRing } from './arch'
import { inputPattern } from './15-reservoir'
import { OUT, writeF64, writeJson } from './util'

const K = 10, STEPS = 3200, WARM = 300
const RETAIN = 0.684, G = 1 / RETAIN, NSP = 1.5, N_ASE = NSP * (G - 1) // photons per mode per trip
const TAP = 0.05, QE = 0.8, READ_NOISE = 2 // electrons rms per bin per readout

const [NcS, tag] = process.argv.slice(2)
const Nc = NcS === 'inf' ? Infinity : Number(NcS)
const cfg = () => slmRing({ n: 64, spp: 1, focal: 40e-3, inputFirst: true, mask: { kind: 'random', seed: 3, depth: 0.1 }, gain: { G0: 1.6, sat: { kind: 'global', saturationIntensity: 0.05 } } })

const inputs = new Float64Array(new Uint8Array(readFileSync(`${OUT}15/inputs_${tag}.f64`)).buffer)
const u = tag === 'bits' ? inputs.map((b) => 0.5 * b) : inputs

const sys = new CompiledSystem(cfg(), new AssetStore())
const g = sys.grid
const P = inputPattern(g, 101)
const f = createField(g), inj = createField(g)
let pending = false
const ctx: RunContext = { cycle: 0, inputs: { take: (p) => (p === 'in' && pending ? (pending = false, inj) : null) }, taps: { record: () => {} } }
const inputAmp = 6
const power = () => { let s = 0; for (let i = 0; i < f.re.length; i++) s += f.re[i] ** 2 + f.im[i] ** 2; return s }
const inject = (x: number) => { for (let i = 0; i < f.re.length; i++) { inj.re[i] = inputAmp * x * P.re[i]; inj.im[i] = inputAmp * x * P.im[i] }; pending = true }

// noise-free warm-up on the first inputs to calibrate the photon scale (also gives injected-photon bookkeeping)
let pSum = 0, pN = 0, injSum = 0
for (let s = 0; s < WARM; s++) {
  inject(u[s]); for (let i = 0; i < inj.re.length; i++) injSum += inj.re[i] ** 2 + inj.im[i] ** 2
  for (let k = 0; k < K; k++) { sys.roundTrip(f, ctx); pSum += power(); pN++ }
}
const meanP = pSum / pN
const scale = Nc / meanP // photons per field unit
f.re.fill(0); f.im.fill(0)

const rng = mulberry32(7)
const sigField = Number.isFinite(Nc) ? Math.sqrt(N_ASE / scale / 2) : 0
const bin = g.nx / 16
const feats = new Float64Array(STEPS * 256)
const acc = new Float64Array(256)
let detTotal = 0
const t0 = performance.now()
for (let s = 0; s < STEPS; s++) {
  inject(u[s]); acc.fill(0)
  for (let k = 0; k < K; k++) {
    sys.roundTrip(f, ctx)
    if (sigField > 0) for (let i = 0; i < f.re.length; i++) { f.re[i] += sigField * gaussian(rng); f.im[i] += sigField * gaussian(rng) }
    for (let j = 0; j < g.ny; j++) for (let i = 0; i < g.nx; i++) acc[Math.floor(j / bin) * 16 + Math.floor(i / bin)] += f.re[j * g.nx + i] ** 2 + f.im[j * g.nx + i] ** 2
  }
  for (let b = 0; b < 256; b++) {
    if (!Number.isFinite(Nc)) { feats[s * 256 + b] = acc[b]; continue }
    const mean = acc[b] * scale * TAP * QE // detected photoelectrons over the K-trip integration window
    const n = poisson(mean, rng) + READ_NOISE * gaussian(rng)
    feats[s * 256 + b] = Math.max(n, 0); detTotal += mean
  }
}
const secs = (performance.now() - t0) / 1000
const name = `29/feat_Nc${NcS}_${tag}`
writeF64(`${OUT}${name}.f64`, feats)
writeJson(`${OUT}${name}.json`, { Nc, tag, K, steps: STEPS, meanP_fieldUnits: meanP, photonsPerFieldUnit: scale, nAsePerModePerTrip: N_ASE, modes: g.nx * g.ny,
  tap: TAP, qe: QE, readNoise: READ_NOISE, meanDetectedPerStep: detTotal / STEPS, injectedFieldUnitsPerStep: injSum / WARM,
  injectedPhotonsPerStep: (injSum / WARM) * scale, t_rt: sys.timing().roundTripTime, secs })
console.log(`${name}: ${secs.toFixed(0)} s; detected/step ${(detTotal / STEPS).toExponential(2)}; injected photons/step ${((injSum / WARM) * scale).toExponential(2)}`)

function poisson(m: number, r: () => number) {
  if (m > 50) return Math.max(0, Math.round(m + Math.sqrt(m) * gaussian(r)))
  const L = Math.exp(-m); let k = 0, p = 1
  do { k++; p *= r() } while (p > L)
  return k - 1
}
