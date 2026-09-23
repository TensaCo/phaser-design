// Experiment 26 (2026-09-23): strict verification of a designed persistent circuit in the JS simulator. Unlike 08-eval.ts (which
// samples every horizon/400 trips after trip 400), EVERY trip is checked: for each case and each target cell, the final target
// value must hold at every trip from `from` to the horizon. Reports min ON / max OFF levels (decision margins), first violation,
// and the peak-to-peak ripple of each output over the last 10 % (oscillation check). Optional gain noise and a static SLM
// phase error (jitter, rad rms per pixel) — the non-idealities of Exp. 23.
// usage: npx vite-node 26-verify.ts <spec.json> <horizon> [from=400] [noiseRel=0] [jitter=0] [tag]
import { readFileSync } from 'node:fs'
import { gaussian, mulberry32 } from '../../src/core/common/random'
import { buildSystem, localFile, type Spec } from './eval-lib'
import type { RunContext } from '../../src/core/physics/elements/element'
import { createField, type Field } from '../../src/core/physics/field/grid'
import { OUT, writeJson } from './util'

const [specPath, hS, fromS, noiseS, jitS, tagS] = process.argv.slice(2)
const spec: Spec = JSON.parse(readFileSync(specPath, 'utf8'))
const H = Number(hS), from = Number(fromS ?? 400), noiseRel = Number(noiseS ?? 0), jitter = Number(jitS ?? 0)
const thr = 0.5 * (spec.I_hi + spec.I_lo)
const names = Object.keys(spec.cells)
const idx = Object.fromEntries(names.map((k) => { const c = spec.cells[k]; const a: number[] = []; for (let j = 0; j < c[2]; j++) for (let i = 0; i < c[2]; i++) a.push((c[1] + j) * 64 + c[0] + i); return [k, a] }))
let maskOverride: Float64Array | undefined
if (jitter > 0) {
  const m = new Float64Array(readFileSync(localFile(spec.mask_file)).buffer.slice(0))
  const r = mulberry32(77)
  maskOverride = m.map((v) => v + jitter * gaussian(r))
}
const rows = []
let allOk = true
for (let ci = 0; ci < spec.cases.length; ci++) {
  const c = spec.cases[ci]
  const sys = buildSystem(spec, { noiseRel, seed: 11 + ci, maskOverride })
  const f: Field = createField(sys.grid)
  const byT = new Map<number, Field>()
  for (const j of c.inject) {
    let fl = byT.get(j.t)
    if (!fl) byT.set(j.t, (fl = createField(sys.grid)))
    for (const i of idx[j.cell]) { fl.re[i] += j.amp * Math.cos(j.phase); fl.im[i] += j.amp * Math.sin(j.phase) }
  }
  let now = 0
  const ctx: RunContext = { cycle: 0, inputs: { take: (p) => (p === 'in' ? byT.get(now) ?? null : null) }, taps: { record: () => {} } }
  const last: Record<string, number> = {}
  let tLast = 0
  for (const tg of c.targets) { last[tg.cell] = tg.value; tLast = Math.max(tLast, tg.t_from) }
  const start = Math.max(from, tLast)
  const cells = Object.keys(last)
  const minOn: Record<string, number> = {}, maxOff: Record<string, number> = {}, lo: Record<string, number> = {}, hi: Record<string, number> = {}
  for (const k of cells) { minOn[k] = Infinity; maxOff[k] = 0; lo[k] = Infinity; hi[k] = 0 }
  let firstViolation: number | null = null
  for (let t = 1; t <= H; t++) {
    now = t
    sys.roundTrip(f, ctx)
    if (t < start) continue
    for (const k of cells) {
      let s = 0
      for (const i of idx[k]) s += f.re[i] ** 2 + f.im[i] ** 2
      const I = s / idx[k].length
      if (last[k]) minOn[k] = Math.min(minOn[k], I); else maxOff[k] = Math.max(maxOff[k], I)
      if ((I > thr ? 1 : 0) !== last[k] && firstViolation === null) firstViolation = t
      if (t > 0.9 * H) { lo[k] = Math.min(lo[k], I); hi[k] = Math.max(hi[k], I) }
    }
  }
  const ok = firstViolation === null
  allOk &&= ok
  const detail = cells.map((k) => `${k}=${last[k]} ${last[k] ? `minON ${minOn[k].toFixed(3)}` : `maxOFF ${maxOff[k].toFixed(3)}`} ripple ${(hi[k] - lo[k]).toFixed(3)}`).join(' | ')
  console.log(`${spec.tag} ${c.name}: ${ok ? 'OK' : `VIOLATION at ${firstViolation}`} (checked every trip ${start}–${H}) ${detail}`)
  rows.push({ case: c.name, ok, firstViolation, start, minOn, maxOff, ripple: Object.fromEntries(cells.map((k) => [k, hi[k] - lo[k]])) })
}
console.log(`${spec.tag}: ${allOk ? 'ALL CASES HOLD' : 'FAILED'} to ${H} trips (noise ${noiseRel}, jitter ${jitter}) threshold ${thr}`)
writeJson(`${OUT}26/verify_${spec.tag}_${tagS ?? `${H}_n${noiseRel}_j${jitter}`}.json`, { tag: spec.tag, horizon: H, noiseRel, jitter, thr, allOk, rows })
