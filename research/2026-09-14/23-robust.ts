// Experiment 23 (2026-09-23): real-device non-idealities on the hand-built absorbing-mask persistent lattice (A ring, 3 px cells,
// 3 px gaps, G0 3, s −0.8, I_a 0.2 — the Exp. 2nl round-3 memory). One non-ideality per run, 3 random patterns each:
//   FOCAL   fractional focal-length error of lensR (the self-imaging condition is broken by a small defocus)
//   DARK    amplitude-LCD dark transmission (1e-3 = 1000:1, 1e-2 = 100:1)
//   NOISE   additive gain noise (spontaneous-emission-like), relative mean intensity per trip
//   FLICKER LCOS phase flicker: a fresh random per-pixel phase offset (σ rad rms) every FLICKER_PERIOD trips. Real LCOS flicker
//           is at the ~kHz drive frame rate, i.e. quasi-static for ~10⁵–10⁶ trips; a shorter period is the harsher test.
//   LD      carrier diffusion length (m) of the gain medium (cross-gain saturation, spatial hole burning smoothed over L_d)
// Reports BER at log checkpoints, first trip with any bit error, ON/OFF levels. Scalar thin-element model throughout.
// usage: npx vite-node 23-robust.ts <T> <tag>     (non-idealities from env; SEEDS default 1,2,3)
import { AssetStore } from '../../src/core/physics/assets'
import type { RunContext } from '../../src/core/physics/elements/element'
import { createField, type Field } from '../../src/core/physics/field/grid'
import type { OpticalElementSpec } from '../../src/core/physics/elements/types'
import type { CustomTopology } from '../../src/core/physics/topology/topology'
import { CompiledSystem } from '../../src/core/physics/system'
import { gaussian, mulberry32 } from '../../src/core/common/random'
import { slmRing } from './arch'
import { OUT, writeCsv } from './util'

const NOIN: RunContext = { cycle: 0, inputs: { take: () => null }, taps: { record: () => {} } }
const env = (k: string, d: number) => Number(process.env[k] ?? d)
const CELL = env('CELL', 3), GAP = env('GAP', 3), G0 = env('G0', 3), S = -0.8, IA = 0.2
const FOCAL = env('FOCAL', 0), DARK = env('DARK', 0), NOISE = env('NOISE', 0), FLICKER = env('FLICKER', 0), FLICKER_PERIOD = env('FLICKER_PERIOD', 1000), LD = env('LD', 0)

function lattice(cellPx: number, pitchPx: number, fovPx = 20, res = 64) {
  const cells = Math.max(1, Math.floor((fovPx - cellPx) / pitchPx) + 1)
  const span = (cells - 1) * pitchPx + cellPx
  const off = Math.floor((res - span) / 2)
  const idx: number[][] = []
  const inCell = new Uint8Array(res * res)
  for (let cy = 0; cy < cells; cy++) for (let cx = 0; cx < cells; cx++) {
    const a: number[] = []
    for (let dy = 0; dy < cellPx; dy++) for (let dx = 0; dx < cellPx; dx++) { const k = (off + cy * pitchPx + dy) * res + off + cx * pitchPx + dx; a.push(k); inCell[k] = 1 }
    idx.push(a)
  }
  return { idx, inCell }
}

function build(seed: number) {
  const store = new AssetStore()
  const L = lattice(CELL, CELL + GAP)
  const cfg = slmRing({
    n: 64, spp: 1, roof: true, inputFirst: true, maxStep: 10e-3, focalErrorR: FOCAL,
    gain: { G0, sat: LD ? { kind: 'diffusive', saturationIntensity: 1, diffusionLength: LD } : { kind: 'local', saturationIntensity: 1 }, noise: NOISE > 0 ? { kind: 'additive-gaussian', meanIntensity: NOISE, seed: 17 + seed } : undefined },
    nl: { amplitude: { kind: 'saturable', strength: S, saturationIntensity: IA }, phase: { kind: 'none' } },
  })
  const drive = new Float64Array(64 * 64)
  for (let i = 0; i < drive.length; i++) drive[i] = L.inCell[i] ? 2 * Math.PI * (255 / 256) : 0
  const amp: OpticalElementSpec = {
    kind: 'transmissive-lcd', id: 'amp', label: 'static absorbing cell mask',
    pixels: { resolution: { x: 64, y: 64 }, pitch: { x: 20e-6, y: 20e-6 }, fillFactor: 1, offset: { x: 0, y: 0 } },
    modulation: { kind: 'amplitude', darkTransmission: DARK, levels: 256 },
    clearTransmission: 1, surfaces: { front: { transmission: 1, reflection: 0 }, back: { transmission: 1, reflection: 0 } },
    polarizerTransmission: 1, deadZoneTransmission: 0, switchingTime: 0.01, designWavelength: 650e-9,
    program: { kind: 'array', ref: store.put('amp', 64, 64, drive) },
  }
  cfg.elements.push(amp)
  const topo = cfg.topology as CustomTopology
  topo.route.splice(topo.route.findIndex((r) => r.kind === 'element' && r.elementId === 'slm') + 1, 0, { kind: 'element', elementId: 'amp', side: 'front' })
  return { sys: new CompiledSystem(cfg, store), store, L }
}

const cellI = (f: Field, idx: number[][]) => idx.map((a) => a.reduce((s, i) => s + f.re[i] ** 2 + f.im[i] ** 2, 0) / a.length)

function run(T: number, seed: number) {
  const { sys, store, L } = build(seed)
  const r = mulberry32(seed)
  const bits = L.idx.map(() => (r() < 0.5 ? 1 : 0))
  if (bits.every((b) => b === bits[0])) bits[0] = 1 - bits[0]
  const f = createField(sys.grid)
  L.idx.forEach((a, k) => { if (bits[k]) for (const i of a) f.re[i] = Math.sqrt(2) })
  const fr = mulberry32(1000 + seed)
  const flick = new Float64Array(64 * 64)
  const checkpoints = new Set([10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000, 300000, 1000000].filter((c) => c <= T).concat([T]))
  const thr = 0.25
  const rows: Record<string, number | string>[] = []
  let firstError = -1
  const t0 = performance.now()
  for (let t = 1; t <= T; t++) {
    if (FLICKER > 0 && (t - 1) % FLICKER_PERIOD === 0) {
      // zero program + fresh flicker offsets (commanded phase, wrapped by the device model)
      for (let i = 0; i < flick.length; i++) flick[i] = FLICKER * gaussian(fr)
      sys.loadProgram('slm', { kind: 'array', ref: store.put('flicker', 64, 64, flick) })
    }
    sys.roundTrip(f, NOIN)
    // every 100 trips (cheap): first error time
    if (t % 100 === 0 || checkpoints.has(t)) {
      const I = cellI(f, L.idx)
      const nerr = I.reduce((a, v, k) => a + ((v > thr ? 1 : 0) !== bits[k] ? 1 : 0), 0)
      if (nerr && firstError < 0) firstError = t
      if (checkpoints.has(t)) {
        const on = I.filter((_, k) => bits[k]), off = I.filter((_, k) => !bits[k])
        rows.push({ focal_err: FOCAL, dark: DARK, noise: NOISE, flicker_rad: FLICKER, flicker_period: FLICKER_PERIOD, Ld: LD, G0, seed, t, ber: nerr / I.length,
          on_min: Math.min(...on), on_mean: on.reduce((a, b) => a + b, 0) / on.length, off_max: Math.max(0, ...off), first_error: firstError })
        if (t >= 100000) console.log(`  seed ${seed} t ${t} ber ${(nerr / I.length).toFixed(3)} on ${Math.min(...on).toFixed(2)} off ${Math.max(0, ...off).toFixed(4)} [${((performance.now() - t0) / 1000).toFixed(0)}s]`)
      }
    }
  }
  return rows
}

if (process.argv[2]) {
  const [TS, tag] = process.argv.slice(2)
  const T = Number(TS)
  const SEEDS = (process.env.SEEDS ?? '1,2,3').split(',').map(Number)
  const all = SEEDS.flatMap((s) => run(T, s))
  const fin = all.filter((q) => q.t === T)
  console.log(`${tag}: focal ${FOCAL} dark ${DARK} noise ${NOISE} flicker ${FLICKER}/${FLICKER_PERIOD} Ld ${LD} G0 ${G0} → BER@${T} ${fin.map((q) => (+q.ber).toFixed(3)).join('/')} first error ${fin.map((q) => q.first_error).join('/')} on_min ${fin.map((q) => (+q.on_min).toFixed(2)).join('/')} off_max ${fin.map((q) => (+q.off_max).toFixed(4)).join('/')}`)
  writeCsv(`${OUT}23/robust_${tag}.csv`, all)
}
