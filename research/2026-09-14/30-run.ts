// Experiments 30–34 (2026-09-25): one reservoir run, NOISE-FREE detector features saved for post-hoc noise and readout
// (Exp. 29d showed post-hoc shot noise reproduces the in-loop noise, so photon budgets are applied in Python).
// Generalises 15-reservoir.ts / 29-noise.ts:
//  - arch: 'ring' (slmRing, Exp. 15 Apre_lin geometry) or 'stack' (arch.ts stackCavity, the website's linear stack)
//  - gain: 'global' (core element, as Apre_lin) | 'rho' (fixed linear gain: loop spectral radius set to rho, no saturation)
//          | 'slot' (script-side shared gain with carrier recovery time tau, for M time-multiplexed slots)
//  - M time slots (wavefront multiplexing): M independent input streams circulate in the same route; they interact only
//    through the shared gain (and an optional injected in-cavity leakage epsCav between neighbouring slots)
//  - features: |E|² of the circulating field summed over the K trips of each input step, binned by saveBin, float32.
//    For slots ≥ 1 also the cross term Re(E_m·E*_{m−1}) (for coherent detector crosstalk, post hoc).
// usage: npx vite-node 30-run.ts '<json config>'   (see Cfg)
import { writeFileSync, existsSync, readFileSync } from 'node:fs'
import { AssetStore } from '../../src/core/physics/assets'
import type { RunContext } from '../../src/core/physics/elements/element'
import type { OpticalElementSpec } from '../../src/core/physics/elements/types'
import { createField, sampleX, sampleY, type Field, type GridSpec } from '../../src/core/physics/field/grid'
import { CompiledSystem, type PhysicsConfig } from '../../src/core/physics/system'
import { mulberry32, gaussian } from '../../src/core/common/random'
import { slmRing, stackCavity, type RingOptions, type StackOptions } from './arch'
import { OUT, ensure, writeJson } from './util'

interface Cfg {
  tag: string; dir?: string
  arch: 'ring' | 'stack'
  n?: number; focal?: number; lensAperture?: number; maskDepth?: number; maskSeed?: number
  ring?: Partial<RingOptions>; stack?: Partial<StackOptions>
  K: number; steps: number; inputAmp?: number; streams?: ('uniform' | 'bits' | 'ext')[]
  /** optional (not used in Exps. 30–34): d-channel input from a float64 file (steps × d, relative to out/); channel i has its own static pattern (seed 101 + i) */
  ext?: { file: string; d: number }
  gain: { kind: 'global'; G0: number; Is: number } | { kind: 'rho'; rho: number } | { kind: 'slot'; G0: number; Is: number; tau: number }
  M?: number; saveSlots?: number; epsCav?: number; saveBin?: number
  patternCount?: number; patternCorr?: number
}
const c: Cfg = JSON.parse(process.argv[2])
const dir = `${OUT}${c.dir ?? '30'}/`
const n = c.n ?? 64, M = c.M ?? 1, K = c.K, steps = c.steps
const saveSlots = Math.min(M, c.saveSlots ?? 4)
const inputAmp = c.inputAmp ?? 6

function build(withGain: boolean, G?: number): PhysicsConfig {
  const gain = !withGain ? undefined
    : c.gain.kind === 'global' ? { G0: c.gain.G0, sat: { kind: 'global' as const, saturationIntensity: c.gain.Is } }
      : { G0: G!, sat: { kind: 'none' as const } }
  const mask = { kind: 'random' as const, seed: c.maskSeed ?? 3, depth: c.maskDepth ?? 0.1 }
  if (c.arch === 'ring') return slmRing({ n, spp: 1, focal: c.focal ?? 40e-3, inputFirst: true, mask, lensAperture: c.lensAperture, ...(gain ? { gain } : {}), ...c.ring })
  return stackCavity({ n, spp: 1, ...(c.maskDepth !== undefined || c.maskSeed !== undefined ? { masks: Array.from({ length: c.stack?.planes ?? 4 }, (_, k) => ({ ...mask, seed: mask.seed + k })) } : {}), ...(gain ? { gain } : {}), ...c.stack })
}

const power = (f: Field) => { let s = 0; for (let i = 0; i < f.re.length; i++) s += f.re[i] ** 2 + f.im[i] ** 2; return s }
const scale = (f: Field, a: number) => { for (let i = 0; i < f.re.length; i++) { f.re[i] *= a; f.im[i] *= a } }

// ── passive spectral radius (power iteration, no gain) and passive retention of the dominant mode
const passive = new CompiledSystem(build(false), new AssetStore())
const g: GridSpec = passive.grid
const NULLCTX: RunContext = { cycle: 0, inputs: { take: () => null }, taps: { record: () => {} } }
let lam2 = 0
{
  const r = mulberry32(99), f = createField(g)
  for (let i = 0; i < f.re.length; i++) { f.re[i] = gaussian(r); f.im[i] = gaussian(r) }
  for (let t = 0; t < 1500; t++) { const p0 = power(f); passive.roundTrip(f, NULLCTX); const p1 = power(f); lam2 = p1 / p0; scale(f, 1 / Math.sqrt(p1)) }
}
const Grho = c.gain.kind === 'rho' ? c.gain.rho ** 2 / lam2 : undefined
const sys = c.gain.kind === 'slot' ? passive : new CompiledSystem(build(true, Grho), new AssetStore())
const gainEl = sys.elements.get('gain')

// ── input pattern (Exp. 15: smooth complex random, 40 Gaussians per 64² window, scaled with area) and streams
function pattern(seed: number) {
  const r = mulberry32(seed), f = createField(g), L = g.nx * g.dx * 0.3
  const count = c.patternCount ?? Math.round(40 * (n / 64) ** 2), corr = c.patternCorr ?? 3
  for (let k = 0; k < count; k++) {
    const cx = (r() * 2 - 1) * L, cy = (r() * 2 - 1) * L, a = gaussian(r), b = gaussian(r)
    const R = 4 * corr * g.dx, i0 = Math.max(0, Math.floor(cx / g.dx + g.nx / 2 - R / g.dx)), i1 = Math.min(g.nx - 1, Math.ceil(cx / g.dx + g.nx / 2 + R / g.dx))
    const j0 = Math.max(0, Math.floor(cy / g.dy + g.ny / 2 - R / g.dy)), j1 = Math.min(g.ny - 1, Math.ceil(cy / g.dy + g.ny / 2 + R / g.dy))
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
      const e = Math.exp(-((sampleX(g, i) - cx) ** 2 + (sampleY(g, j) - cy) ** 2) / (2 * (corr * g.dx) ** 2))
      f.re[j * g.nx + i] += a * e; f.im[j * g.nx + i] += b * e
    }
  }
  let m = 0
  for (let i = 0; i < f.re.length; i++) m = Math.max(m, Math.hypot(f.re[i], f.im[i]))
  for (let i = 0; i < f.re.length; i++) { f.re[i] /= m; f.im[i] /= m }
  return f
}
/** stream generator: slot 0 reproduces 15-reservoir.ts (seed 2024, uniform and bits drawn alternately) for any length */
function streams(slot: number) {
  const r = mulberry32(2024 + slot), uni = new Float64Array(steps), bits = new Float64Array(steps)
  for (let s = 0; s < steps; s++) { uni[s] = 0.5 * r(); bits[s] = r() < 0.5 ? 0 : 1 }
  return { uniform: uni, bits: bits.map((b) => 0.5 * b) }
}

const bin = c.saveBin ?? Math.max(1, n / 64), B = n / bin
const P = pattern(101) // one static input pattern shared by all slots (same optical program)
const EXT = c.ext ? new Float64Array(new Uint8Array(readFileSync(`${OUT}${c.ext.file}`)).buffer) : null
const PX = c.ext ? Array.from({ length: c.ext.d }, (_, i) => (i === 0 ? P : pattern(101 + i))) : []
const t0 = performance.now()
const meta: Record<string, unknown> = { cfg: c, lam2_passive: lam2, G_rho: Grho, t_rt: sys.timing().roundTripTime, modes: n * n, B, saveSlots }
for (const stream of c.streams ?? ['uniform', 'bits']) {
  const name = `${dir}${c.tag}_${stream}`
  if (existsSync(`${name}.json`)) { console.log('exists', name); continue }
  const U = Array.from({ length: M }, (_, m) => (stream === 'ext' ? new Float64Array(steps) : streams(m)[stream]))
  const F = Array.from({ length: M }, () => createField(g))
  const prev = createField(g)
  const inj = createField(g)
  let pending = false
  const ctx: RunContext = { cycle: 0, inputs: { take: (p) => (p === 'in' && pending ? (pending = false, inj) : null) }, taps: { record: () => {} } }
  const feats = Array.from({ length: saveSlots }, () => new Float32Array(steps * B * B))
  const xterm = Array.from({ length: saveSlots }, (_, m) => (m >= 1 && M > 1 ? new Float32Array(steps * B * B) : null))
  let x = 0 // slot gain: low-pass filtered mean intensity (same units as the core global saturation)
  const Delta = sys.timing().roundTripTime / M
  const decay = c.gain.kind === 'slot' ? Math.exp(-Delta / c.gain.tau) : 0
  let pSum = 0, pN = 0, gSum = 0, gN = 0, retSum = 0, retN = 0, injSum = 0
  for (let s = 0; s < steps; s++) {
    for (let k = 0; k < K; k++) {
      for (let m = 0; m < M; m++) {
        const f = F[m]
        if (k === 0 && EXT) { // d-channel input: Σ_i x_i(t)·P_i
          inj.re.fill(0); inj.im.fill(0)
          for (let ch = 0; ch < c.ext!.d; ch++) { const a = inputAmp * EXT[s * c.ext!.d + ch], Q = PX[ch]; for (let i = 0; i < f.re.length; i++) { inj.re[i] += a * Q.re[i]; inj.im[i] += a * Q.im[i] } }
          pending = true; if (m === 0) injSum += power(inj)
        } else if (k === 0) { const a = inputAmp * U[m][s]; for (let i = 0; i < f.re.length; i++) { inj.re[i] = a * P.re[i]; inj.im[i] = a * P.im[i] }; pending = true; if (m === 0) injSum += a * a * power(P) }
        const p0 = power(f)
        sys.roundTrip(f, ctx)
        if (c.gain.kind === 'slot') {
          const I = power(f) / f.re.length
          const gg = 1 + (c.gain.G0 - 1) / (1 + x / c.gain.Is)
          scale(f, Math.sqrt(gg)); if (m === 0) { gSum += gg; gN++ }
          x = decay * x + (1 - decay) * I
          if (k > 0 && m === 0 && p0 > 0) { retSum += (power(f) / gg) / p0; retN++ }
        } else if (k > 0 && m === 0 && p0 > 0) {
          const gg = c.gain.kind === 'global' ? (gainEl?.state().gain ?? 1) : Grho!
          gSum += gg; gN++; retSum += power(f) / gg / p0; retN++
        }
      }
      if (c.epsCav && M > 1) { // in-cavity coherent leakage from the previous slot (pulse tails), per trip
        for (let m = M - 1; m >= 0; m--) { const src = F[(m + M - 1) % M]; for (let i = 0; i < prev.re.length; i++) { F[m].re[i] += c.epsCav * src.re[i]; F[m].im[i] += c.epsCav * src.im[i] } }
      }
      for (let m = 0; m < saveSlots; m++) {
        const f = F[m], fe = feats[m], xt = xterm[m], o = s * B * B, fp = m >= 1 ? F[m - 1] : null
        for (let j = 0; j < g.ny; j++) for (let i = 0; i < g.nx; i++) {
          const q = j * g.nx + i, b = o + Math.floor(j / bin) * B + Math.floor(i / bin)
          fe[b] += f.re[q] ** 2 + f.im[q] ** 2
          if (xt && fp) xt[b] += f.re[q] * fp.re[q] + f.im[q] * fp.im[q]
        }
      }
      pSum += power(F[0]); pN++
    }
  }
  for (let m = 0; m < saveSlots; m++) {
    writeFileSync(ensure(`${name}_s${m}.f32`), new Uint8Array(feats[m].buffer))
    if (xterm[m]) writeFileSync(`${name}_x${m}.f32`, new Uint8Array(xterm[m]!.buffer))
  }
  const secs = (performance.now() - t0) / 1000
  writeJson(`${name}.json`, { ...meta, stream, steps, K, M, meanP_fieldUnits: pSum / pN, meanGain: gSum / Math.max(1, gN), passiveRetention: retSum / Math.max(1, retN),
    injectedFieldUnitsPerStep: injSum / steps, secs })
  console.log(`${c.tag} ${stream}: ${secs.toFixed(0)} s, |λ|² ${lam2.toFixed(4)}, gain ${(gSum / Math.max(1, gN)).toFixed(4)}, retention ${(retSum / Math.max(1, retN)).toFixed(4)}, meanP ${(pSum / pN).toExponential(3)}`)
}
