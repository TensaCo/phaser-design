// Experiment 25b (2026-09-23): is threshold-1 coupling directional? Take a designed persistent wire / gate (spec from 08-design.py)
// and write a bit into cells the design treated as OUTPUTS only, then check whether the INPUT cells switch on (back-propagation).
// Reciprocal passive optics + phase-insensitive local gain give no built-in direction; a usable wire must not drive its source.
// usage: npx vite-node 25-direction.ts <spec.json> <cell,...to write> [T=3000]
import { readFileSync } from 'node:fs'
import { buildSystem, runCase, type Spec } from './eval-lib'
import { OUT, writeJson } from './util'

const [specPath, cellsS, TS] = process.argv.slice(2)
const spec: Spec & { inj_amp: number } = JSON.parse(readFileSync(specPath, 'utf8'))
const T = Number(TS ?? 3000)
const write = cellsS.split(',')
const names = Object.keys(spec.cells)
// keep rails (always-on power cells) as the design wrote them; write only the requested cells
const rails = names.filter((n) => n.startsWith('rail'))
const c = { name: `write_${write.join('+')}`, init_on: [], targets: [], inject: [...write, ...rails].map((cell) => ({ t: 1, cell, amp: spec.inj_amp, phase: 0 })) }
const s2 = { ...spec, cases: [c] }
const { trace } = runCase(s2, buildSystem(s2), 0, T, (t) => [1, 10, 30, 80, 200, 500, 1000, 2000, 3000, 5000, 10000].includes(t) || t === T)
const thr = 0.5 * (spec.I_hi + spec.I_lo)
for (const s of trace) console.log(`t ${s.t}: ` + names.map((n, k) => `${n} ${s.I[k].toFixed(2)}${s.I[k] > thr ? '*' : ''}`).join('  '))
writeJson(`${OUT}25/direction_${spec.tag}_${write.join('+')}.json`, { tag: spec.tag, write, thr, names, trace })
