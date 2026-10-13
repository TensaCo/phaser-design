// Exp. 43 (2026-10-12): export the Exp. 30/31 reservoir ring (Apre_lin: slmRing, random phase mask seed 3 depth 0.1, f 40 mm,
// global gain) at any grid size for the GPU reservoir engine (res_gpu.py), plus d input patterns built exactly as 30-run.ts
// builds them, plus a short JS reference run (binned features) to validate the GPU engine against.
// Every element that is not a propagation, coupler, mirror or gain is static and linear here, so it is exported as its
// measured transmission map (probe with a field of ones).
// usage: npx vite-node 2026-10-12/res-dump.ts <n> [d=1] [refSteps=40] [K=10] [slmR]   → .big/res_n{n}/
import { AssetStore } from '../../src/core/physics/assets'
import { NULL_CONTEXT, type RunContext } from '../../src/core/physics/elements/element'
import { createField, sampleX, sampleY, type Field } from '../../src/core/physics/field/grid'
import { CompiledSystem } from '../../src/core/physics/system'
import { mulberry32, gaussian } from '../../src/core/common/random'
import { slmRing } from '../2026-09-14/arch'
import { BIG, writeF64, writeJson } from '../2026-09-14/util'

const n = Number(process.argv[2]), d = Number(process.argv[3] ?? 1), refSteps = Number(process.argv[4] ?? 40), K = Number(process.argv[5] ?? 10)
const slmR = process.argv[6] ? Number(process.argv[6]) : undefined  // Exp. 47: SLM reflectivity (default 0.75, aluminium LCOS)
const G0 = 1.6, Is = 0.05, inputAmp = 6
const cfg = slmRing({ n, spp: 1, focal: 40e-3, inputFirst: true, mask: { kind: 'random', seed: 3, depth: 0.1 }, lensAperture: 1.2e-3 * n / 64, ...(slmR ? { losses: { slmR } } : {}),
  gain: { G0, sat: { kind: 'global', saturationIntensity: Is } } })
const dir = `${BIG}res_n${n}${d === 1 ? '' : `_d${d}`}${slmR ? `_R${slmR}` : ''}/`
const sys = new CompiledSystem(cfg, new AssetStore())
const g = sys.grid
const c128 = (re: Float64Array, im: Float64Array) => { const a = new Float64Array(2 * re.length); for (let i = 0; i < re.length; i++) { a[2 * i] = re[i]; a[2 * i + 1] = im[i] } return a }
let fileNo = 0
const save = (re: Float64Array, im: Float64Array) => { const fn = `a${fileNo++}.c128`; writeF64(dir + fn, c128(re, im)); return fn }
const ops: Record<string, unknown>[] = []
const boundary: Float64Array | null = (sys as any).boundary
const bfile = boundary ? save(boundary, new Float64Array(boundary.length)) : null
for (const st of (sys as any).steps) {
  if (st.kind === 'propagate') { ops.push({ op: 'prop', kernel: save(st.kernel.re, st.kernel.im), boundary: bfile }); continue }
  const el = st.element, spec = el.spec, side = st.side as 'front' | 'back'
  if (spec.kind === 'coupler') {
    ops.push({ op: 'scale', a: Math.sqrt(spec.retained[side]) })
    if (spec.inputPort && side === 'front') ops.push({ op: 'inject', coupling: Math.sqrt(spec.inputCoupling ?? 1 - spec.retained.front) })
  } else if (spec.kind === 'mirror') {
    ops.push({ op: 'scale', a: Math.sqrt(spec.reflectivity[side]) })
    if (spec.parity !== 'none') ops.push({ op: spec.parity })
  } else if (spec.kind === 'gain') {
    ops.push({ op: 'gain', G0: spec.smallSignalGain, saturation: spec.saturation })
  } else {
    const f = createField(g); f.re.fill(1); el.apply(f, side, NULL_CONTEXT)
    ops.push({ op: 'mul', t: save(f.re, f.im), id: spec.id, kind: spec.kind })
  }
}

// input patterns exactly as 30-run.ts pattern(seed): channel i uses seed 101 + i
function pattern(seed: number) {
  const r = mulberry32(seed), f = createField(g), L = g.nx * g.dx * 0.3
  const count = Math.round(40 * (n / 64) ** 2), corr = 3
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
const patterns: string[] = []
const P0 = pattern(101)
for (let i = 0; i < d; i++) { const P = i === 0 ? P0 : pattern(101 + i); patterns.push(`pattern${i}.c128`); writeF64(dir + `pattern${i}.c128`, c128(P.re, P.im)) }

// JS reference: the 30-run.ts loop (uniform stream, slot 0) for refSteps steps, features |E|² summed over K trips, full resolution
const r = mulberry32(2024), u = new Float64Array(refSteps)
for (let s = 0; s < refSteps; s++) { u[s] = 0.5 * r(); r() }
const f = createField(g), inj = createField(g)
let pending = false
const ctx: RunContext = { cycle: 0, inputs: { take: (p) => (p === 'in' && pending ? (pending = false, inj) : null) }, taps: { record: () => {} } }
const feats = new Float64Array(refSteps * n * n)
for (let s = 0; s < refSteps; s++) for (let k = 0; k < K; k++) {
  if (k === 0) { const a = inputAmp * u[s]; for (let i = 0; i < f.re.length; i++) { inj.re[i] = a * P0.re[i]; inj.im[i] = a * P0.im[i] }; pending = true }
  sys.roundTrip(f, ctx)
  for (let i = 0; i < f.re.length; i++) feats[s * n * n + i] += f.re[i] ** 2 + f.im[i] ** 2
}
writeF64(dir + 'ref_feats.f64', feats)
writeF64(dir + 'ref_u.f64', u)
writeJson(dir + 'res.json', { n, dx: g.dx, roundTripTime: sys.timing().roundTripTime, G0, Is, inputAmp, K, refSteps, ops, patterns, boundary: bfile })
console.log(`res_n${n}: ${ops.length} ops, ${d} patterns, JS reference ${refSteps} steps → ${dir}`)
