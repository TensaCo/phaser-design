// Dumps the actual simulated circulating field of the Experiment 15 reservoir configuration (A_preset, preset random SLM
// program, global gain clamp) for the site's hero visual. Read-only use of the simulator and research configs.
// usage (repo root): npx vite-node site/scripts/dump-field.ts
import { writeFileSync } from 'node:fs'
import { AssetStore } from '../../src/core/physics/assets'
import type { RunContext } from '../../src/core/physics/elements/element'
import { createField } from '../../src/core/physics/field/grid'
import { CompiledSystem } from '../../src/core/physics/system'
import { OPS, inputPattern } from '../../research/2026-09-14/15-reservoir'

const TRIPS = 160, K = 10
const op = OPS.Apre_lin
const sys = new CompiledSystem(op.cfg(), new AssetStore())
const g = sys.grid
const P = inputPattern(g, 101)
const f = createField(g), inj = createField(g)
let pending = false
const ctx: RunContext = { cycle: 0, inputs: { take: (p) => (p === 'in' && pending ? (pending = false, inj) : null) }, taps: { record: () => {} } }
const n = g.nx * g.ny
const I = new Float32Array(TRIPS * n), PH = new Float32Array(TRIPS * n)
const us = [0.42, 0.13, 0.31, 0.05, 0.48, 0.22, 0.37, 0.09, 0.27, 0.45, 0.18, 0.33, 0.02, 0.41, 0.25, 0.11]
let umax = 0
for (let t = 0; t < TRIPS; t++) {
  if (t % K === 0) {
    const u = us[(t / K) % us.length]
    for (let i = 0; i < n; i++) { inj.re[i] = op.inputAmp * u * P.re[i]; inj.im[i] = op.inputAmp * u * P.im[i] }
    pending = true
  }
  sys.roundTrip(f, ctx)
  for (let i = 0; i < n; i++) { const v = f.re[i] ** 2 + f.im[i] ** 2; I[t * n + i] = v; PH[t * n + i] = Math.atan2(f.im[i], f.re[i]); if (v > umax) umax = v }
}
const out = new Uint8Array(TRIPS * n * 2)
for (let k = 0; k < TRIPS * n; k++) {
  out[2 * k] = Math.round(255 * Math.sqrt(I[k] / umax))
  out[2 * k + 1] = Math.round(((PH[k] + Math.PI) / (2 * Math.PI)) * 255) & 255
}
writeFileSync('site/public/field-apre.bin', out)
const meta = { config: 'A_preset (Exp. 15 Apre_lin)', nx: g.nx, ny: g.ny, dx: g.dx, trips: TRIPS, inputEvery: K, inputs: us, roundTripTime: sys.timing().roundTripTime, encoding: 'interleaved uint8 [sqrt(I/Imax)*255, (phase+pi)/2pi*255], row-major per trip', Imax: umax }
writeFileSync('site/public/field-apre.json', JSON.stringify(meta, null, 1))
console.log(meta)
