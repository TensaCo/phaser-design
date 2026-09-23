// Experiment 22 (2026-09-23): absorbing-mask persistent memory on the B-4f linear LCD cavity (the architecture with the most
// long-lived linear modes, 155 vs 85 on A). Same recipe as 02-nl-amp.ts on A: local saturable gain + saturable absorber at the
// start mirror, a static absorbing amplitude LCD in the same (self-imaged) plane with cell pixels clear and gap pixels dark,
// zero phase program. Random patterns written by one pulse (I = 2 per cell sample), fixed decoder I = 0.25, BER at log
// checkpoints, fixed-point residual and Benettin exponent when a pattern survives.
// usage: npx vite-node 22-b4f-amp.ts <cellPx,...> <gapPx,...> <G0,...> <s:Ia,...> <T> <tag> [n=64] [fovHalf_um=700]
// env: SEEDS, NOISE, LD (as 02-nl-amp.ts)
import { AssetStore } from '../../src/core/physics/assets'
import type { RunContext } from '../../src/core/physics/elements/element'
import { cloneField, createField, type Field } from '../../src/core/physics/field/grid'
import { CompiledSystem } from '../../src/core/physics/system'
import { mulberry32 } from '../../src/core/common/random'
import { linear4f } from './arch'
import { OUT, writeCsv } from './util'

const NOIN: RunContext = { cycle: 0, inputs: { take: () => null }, taps: { record: () => {} } }
const PITCH = 63.5e-6, SPP = 2, RES = 64

function lattice(cellPx: number, pitchPx: number, n: number, fovHalf: number) {
  // LCD pixel p (0..63) spans x ∈ [(p − 32)·pitch, (p − 31)·pitch); grid sample j centre (j − n/2 + 0.5)·pitch/SPP
  const fovPx = Math.floor((2 * fovHalf) / PITCH)
  const cells = Math.max(1, Math.floor((fovPx - cellPx) / pitchPx) + 1)
  const span = (cells - 1) * pitchPx + cellPx
  const p0 = 32 - Math.floor(span / 2)
  const drive = new Float64Array(RES * RES)
  const idx: number[][] = []
  for (let cy = 0; cy < cells; cy++) for (let cx = 0; cx < cells; cx++) {
    const a: number[] = []
    for (let dy = 0; dy < cellPx; dy++) for (let dx = 0; dx < cellPx; dx++) {
      const px = p0 + cx * pitchPx + dx, py = p0 + cy * pitchPx + dy
      drive[py * RES + px] = 2 * Math.PI * (255 / 256)
      for (let sy = 0; sy < SPP; sy++) for (let sx = 0; sx < SPP; sx++) a.push((n / 2 + (py - 32) * SPP + sy) * n + n / 2 + (px - 32) * SPP + sx)
    }
    idx.push(a)
  }
  return { cells, idx, drive }
}

function build(cellPx: number, gapPx: number, G0: number, s: number, Ia: number, n: number, fovHalf: number) {
  const store = new AssetStore()
  const L = lattice(cellPx, cellPx + gapPx, n, fovHalf)
  const cfg = linear4f({
    n, spp: SPP,
    gain: { G0, sat: process.env.LD ? { kind: 'diffusive', saturationIntensity: 1, diffusionLength: Number(process.env.LD) } : { kind: 'local', saturationIntensity: 1 }, noise: Number(process.env.NOISE ?? 0) > 0 ? { kind: 'additive-gaussian', meanIntensity: Number(process.env.NOISE), seed: 17 } : undefined },
    nl: { amplitude: { kind: 'saturable', strength: s, saturationIntensity: Ia }, phase: { kind: 'none' } },
    ampMask: { dark: 0, program: { kind: 'array', ref: store.put(`amp_${cellPx}_${gapPx}`, RES, RES, L.drive) } },
  })
  return { sys: new CompiledSystem(cfg, store), L }
}

const cellI = (f: Field, idx: number[][]) => idx.map((a) => a.reduce((s, i) => s + f.re[i] ** 2 + f.im[i] ** 2, 0) / a.length)

function run(cellPx: number, gapPx: number, G0: number, s: number, Ia: number, T: number, seed: number, n: number, fovHalf: number) {
  const { sys, L } = build(cellPx, gapPx, G0, s, Ia, n, fovHalf)
  const r = mulberry32(seed)
  const bits = L.idx.map(() => (r() < 0.5 ? 1 : 0))
  if (bits.every((b) => b === bits[0])) bits[0] = 1 - bits[0]
  const f = createField(sys.grid)
  L.idx.forEach((a, k) => { if (bits[k]) for (const i of a) f.re[i] = Math.sqrt(2) })
  const checkpoints = new Set([1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000].filter((c) => c <= T).concat([T]))
  const rows: Record<string, number | string>[] = []
  const thr = 0.25
  for (let t = 1; t <= T; t++) {
    sys.roundTrip(f, NOIN)
    if (!checkpoints.has(t)) continue
    const I = cellI(f, L.idx)
    const on = I.filter((_, k) => bits[k]), off = I.filter((_, k) => !bits[k])
    const ber = I.reduce((a, v, k) => a + ((v > thr ? 1 : 0) !== bits[k] ? 1 : 0), 0) / I.length
    rows.push({ arch: 'B_4f', n, noise: Number(process.env.NOISE ?? 0), Ld: Number(process.env.LD ?? 0), cellPx, gapPx, pitch_um: +((cellPx + gapPx) * PITCH * 1e6).toFixed(1), cells: L.idx.length,
      bits_per_mm2: +(1 / ((cellPx + gapPx) * PITCH * 1e3) ** 2).toFixed(2), G0, s, Ia, seed, t, ber, on_min: Math.min(...on), on_mean: on.reduce((a, b) => a + b, 0) / on.length, off_max: Math.max(0, ...off) })
  }
  let lyap = NaN, residual = NaN
  if (rows[rows.length - 1].ber === 0) {
    // intensity fixed-point residual (the field may carry a constant round-trip phase) and Benettin exponent over 400 trips
    const g = cloneField(f)
    sys.roundTrip(g, NOIN)
    let d2 = 0, n2 = 0
    for (let i = 0; i < f.re.length; i++) { const a = f.re[i] ** 2 + f.im[i] ** 2, b = g.re[i] ** 2 + g.im[i] ** 2; d2 += (a - b) ** 2; n2 += a * a }
    residual = Math.sqrt(d2 / n2)
    const eps = 1e-8, rr = mulberry32(seed + 99)
    const p = cloneField(f)
    const u = new Float64Array(2 * f.re.length).map(() => rr() - 0.5)
    const pn = Math.sqrt(u.reduce((a, v) => a + v * v, 0))
    for (let i = 0; i < f.re.length; i++) { p.re[i] += (eps * u[2 * i]) / pn; p.im[i] += (eps * u[2 * i + 1]) / pn }
    let acc = 0, cnt = 0
    for (let t = 1; t <= 400; t++) {
      sys.roundTrip(f, NOIN); sys.roundTrip(p, NOIN)
      if (t % 20 === 0) {
        let dd = 0
        for (let i = 0; i < f.re.length; i++) dd += (p.re[i] - f.re[i]) ** 2 + (p.im[i] - f.im[i]) ** 2
        dd = Math.sqrt(dd)
        if (t > 100) { acc += Math.log(dd / eps); cnt += 20 }
        for (let i = 0; i < f.re.length; i++) { p.re[i] = f.re[i] + ((p.re[i] - f.re[i]) * eps) / dd; p.im[i] = f.im[i] + ((p.im[i] - f.im[i]) * eps) / dd }
      }
    }
    lyap = acc / cnt
  }
  for (const row of rows) { row.lyapunov_at_end = lyap; row.intensity_residual = residual }
  return rows
}

if (process.argv[2]) {
  const [cellS, gapS, G0S, sIaS, TS, tag, nS, fovS] = process.argv.slice(2)
  const SEEDS = (process.env.SEEDS ?? '1,2,3').split(',').map(Number)
  const T = Number(TS), n = Number(nS ?? 64), fovHalf = Number(fovS ?? 700) * 1e-6
  const all: Record<string, number | string>[] = []
  for (const c of cellS.split(',').map(Number)) for (const gp of gapS.split(',').map(Number)) for (const G0 of G0S.split(',').map(Number)) for (const sIa of sIaS.split(',')) {
    const [s, Ia] = sIa.split(':').map(Number)
    const t0 = performance.now()
    const res = SEEDS.flatMap((seed) => run(c, gp, G0, s, Ia, T, seed, n, fovHalf))
    all.push(...res)
    const fin = res.filter((q) => q.t === T)
    console.log(`B4f amp n ${n} cell ${c} gap ${gp} (${fin[0].cells} cells, ${fin[0].bits_per_mm2}/mm²) G0 ${G0} s ${s} Ia ${Ia}: BER@${T} ${fin.map((q) => (+q.ber).toFixed(3)).join('/')} onMean ${fin.map((q) => (+q.on_mean).toFixed(2)).join('/')} offMax ${fin.map((q) => (+q.off_max).toFixed(3)).join('/')} λL ${fin.map((q) => (+q.lyapunov_at_end).toExponential(1)).join('/')} [${((performance.now() - t0) / 1000).toFixed(0)}s]`)
    writeCsv(`${OUT}22/amp_${tag}.csv`, all)
  }
}
