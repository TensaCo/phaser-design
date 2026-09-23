// JS re-evaluation of a designed static program (spec from 08-design.py) in the actual simulator, over long horizons.
// usage: npx vite-node 08-eval.ts <spec.json> <horizon> [noiseRel] [phaseJitter]
// Reports per case: decoded cell bits over time (log-spaced + every trip for the first 400), accuracy vs targets extended to the
// horizon (the final target value of each cell is required to persist), settling time, margins, energy.
// The shared code lives in eval-lib.ts; import from there, not from this file.
import { readFileSync } from 'node:fs'
import { gaussian, mulberry32 } from '../../src/core/common/random'
import { buildSystem, localFile, runCase, scoreCase, type Spec } from './eval-lib'
import { OUT, writeJson } from './util'

export { buildSystem, localFile, runCase, scoreCase, type Spec } from './eval-lib'

if (process.argv[2]) {
  const [specPath, horizonS, noiseS, jitterS] = process.argv.slice(2)
  const spec: Spec = JSON.parse(readFileSync(specPath, 'utf8'))
  const horizon = Number(horizonS ?? 10000)
  const noiseRel = Number(noiseS ?? 0)
  let maskOverride: Float64Array | undefined
  if (Number(jitterS ?? 0) > 0) {
    const m = new Float64Array(readFileSync(localFile(spec.mask_file)).buffer.slice(0))
    const r = mulberry32(77)
    maskOverride = m.map((v) => v + Number(jitterS) * gaussian(r))
  }
  const rec = (t: number) => t <= 400 || t % Math.max(1, Math.floor(horizon / 400)) === 0 || t === horizon
  const results = []
  const t0 = performance.now()
  for (let ci = 0; ci < spec.cases.length; ci++) {
    const sys = buildSystem(spec, { noiseRel, seed: 11 + ci, maskOverride })
    const { trace } = runCase(spec, sys, ci, horizon, rec)
    const sc = scoreCase(spec, ci, trace, horizon)
    results.push({ ...sc, trace })
    console.log(`${spec.tag} ${sc.case}: acc(train window) ${sc.acc_train_window.toFixed(3)} firstFail ${sc.first_fail_train_window} extended-survival ${sc.survived_to}/${horizon} margin ${sc.min_margin_ratio.toFixed(2)}`)
  }
  const suffix = `${horizon}${noiseRel ? `_n${noiseRel}` : ''}${Number(jitterS ?? 0) ? `_j${jitterS}` : ''}`
  writeJson(`${OUT}08/eval_${spec.tag}_${suffix}.json`, { tag: spec.tag, horizon, noiseRel, jitter: Number(jitterS ?? 0), names: Object.keys(spec.cells), G0: spec.G0, results, seconds: (performance.now() - t0) / 1000 })
}
