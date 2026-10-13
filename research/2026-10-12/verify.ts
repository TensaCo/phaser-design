// JS-simulator verification of design.py specs (see vlib.ts). usage: npx vite-node verify.ts <horizon> <spec.json>... [--noise x]
import { readFileSync } from 'node:fs'
import { verifyCase, type Spec } from './vlib'
const args = process.argv.slice(2)
const ni = args.indexOf('--noise')
const noise = ni >= 0 ? Number(args.splice(ni, 2)[1]) : 0
const H = Number(args[0])
for (const p of args.slice(1)) {
  const spec: Spec = JSON.parse(readFileSync(p, 'utf8'))
  const rows = spec.cases.map((_, ci) => verifyCase(spec, p, ci, H, noise))
  const ok = rows.filter((r) => r.ok).length
  console.log(`${spec.tag}: JS ${ok}/${rows.length} cases ${ok === rows.length ? 'PASS' : 'fail'} to H=${H}${noise ? ` noise ${noise}` : ''}` + rows.map((r) => ` | ${r.case}:${r.ok ? 'ok' : `x@${r.first_violation}`}`).join(''))
}
