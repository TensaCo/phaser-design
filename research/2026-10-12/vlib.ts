// JS-simulator check of designs from design.py (2026-10-12; library part, CLI in verify.ts): the authoritative re-run. Same rule as verify.py — every target
// window at every trip, then each cell's final value at every trip to the horizon — on the architecture named by spec.twin
// (arch-twins.ts), any grid size. Optional additive gain noise.
import { readFileSync, existsSync } from 'node:fs'
import { basename, dirname } from 'node:path'
import { AssetStore } from '../../src/core/physics/assets'
import type { RunContext } from '../../src/core/physics/elements/element'
import { createField, type Field } from '../../src/core/physics/field/grid'
import { CompiledSystem } from '../../src/core/physics/system'
import { slmRing } from '../2026-09-14/arch'
import { ARCHS } from './arch-twins'

interface Inj { t: number; cell: string; amp: number; phase: number }
interface Tg { cell: string; value: number; t_from: number; t_to: number }
export interface Spec {
  tag: string; twin: string; n?: number; G0: number; Ig: number; Ld?: number; s: number; Ia: number; kerr?: number; I_init: number; I_hi: number; I_lo: number
  mask_file: string; amp_file?: string; amp_dark?: number
  cells: Record<string, [number, number, number]>
  cases: { name: string; init_on?: string[]; inject: Inj[]; targets: Tg[] }[]
}

const here = dirname(new URL(import.meta.url).pathname)
const local = (p: string, specPath: string) => [p, `${dirname(specPath)}/${basename(p)}`, `${here}/out/designs/${basename(p)}`, `${here}/../2026-09-14/out/08/${basename(p)}`].find(existsSync)!
const readF64 = (p: string) => new Float64Array(readFileSync(p).buffer.slice(0))

export function build(spec: Spec, specPath: string, noise = 0, seed = 1) {
  const arch = ARCHS[spec.twin]
  if (!arch) throw new Error(`unknown arch ${spec.twin}`)
  const n = spec.n ?? arch.n ?? 64
  const store = new AssetStore()
  const res = n // 1 sample per pixel in every 2026-10-12 twin
  const cfg = slmRing({
    ...arch,
    gain: { G0: spec.G0, sat: spec.Ld ? { kind: 'diffusive', saturationIntensity: spec.Ig, diffusionLength: spec.Ld } : { kind: 'local', saturationIntensity: spec.Ig }, noise: noise ? { kind: 'additive-gaussian', meanIntensity: noise, seed } : undefined },
    nl: { amplitude: { kind: 'saturable', strength: spec.s, saturationIntensity: spec.Ia }, phase: spec.kerr ? { kind: 'kerr', coefficient: spec.kerr } : { kind: 'none' } },
    mask: { kind: 'array', ref: store.put(`mask_${spec.tag}`, res, res, readF64(local(spec.mask_file, specPath))) },
    ampMask: arch.ampMask ? { dark: spec.amp_dark ?? arch.ampMask.dark, program: { kind: 'array', ref: store.put(`amp_${spec.tag}`, res, res, readF64(local(spec.amp_file!, specPath))) } } : undefined,
  })
  return new CompiledSystem(cfg, store)
}

export function verifyCase(spec: Spec, specPath: string, ci: number, H: number, noise = 0) {
  const sys = build(spec, specPath, noise, 11 + ci)
  const n = sys.grid.nx
  const names = Object.keys(spec.cells)
  const idx = names.map((k) => { const [x0, y0, w] = spec.cells[k]; const a: number[] = []; for (let j = 0; j < w; j++) for (let i = 0; i < w; i++) a.push((y0 + j) * n + x0 + i); return a })
  const c = spec.cases[ci]
  const f: Field = createField(sys.grid)
  for (const nm of c.init_on ?? []) for (const i of idx[names.indexOf(nm)]) f.re[i] = Math.sqrt(spec.I_init)
  const byT = new Map<number, Field>()
  for (const j of c.inject) {
    let fl = byT.get(j.t)
    if (!fl) byT.set(j.t, (fl = createField(sys.grid)))
    for (const i of idx[names.indexOf(j.cell)]) { fl.re[i] += j.amp * Math.cos(j.phase); fl.im[i] += j.amp * Math.sin(j.phase) }
  }
  const thr = 0.5 * (spec.I_hi + spec.I_lo)
  const last = new Map<string, Tg>()
  for (const tg of c.targets) { const l = last.get(tg.cell); if (!l || tg.t_to > l.t_to) last.set(tg.cell, tg) }
  let now = 0
  const ctx: RunContext = { cycle: 0, inputs: { take: (p) => (p === 'in' ? byT.get(now) ?? null : null) }, taps: { record: () => {} } }
  let nBad = 0, first: number | null = null
  for (let t = 1; t <= H; t++) {
    now = t
    sys.roundTrip(f, ctx)
    const I = idx.map((a) => a.reduce((s, i) => s + f.re[i] ** 2 + f.im[i] ** 2, 0) / a.length)
    let bad = false
    for (const [k, nm] of names.entries()) {
      let want: number | null = null
      for (const tg of c.targets) if (tg.cell === nm && t >= tg.t_from && t <= tg.t_to) want = tg.value
      const l = last.get(nm)
      if (want === null && l && t > l.t_to) want = l.value
      if (want !== null && (I[k] > thr ? 1 : 0) !== want) bad = true
    }
    if (bad) { nBad++; if (first === null) first = t }
  }
  return { case: c.name, ok: nBad === 0, n_bad_trips: nBad, first_violation: first }
}

