// Dump GPU twins for the 2026-10-12 architectures. usage: npx vite-node dump.ts <arch> [...]
// (dynamic import: twin-dump.ts runs its own CLI block on whatever process.argv holds)
import { ARCHS } from './arch-twins'
import { slmRing } from '../2026-09-14/arch'

const names = process.argv.splice(2)
const { dump } = await import('../2026-09-14/twin-dump')
const rnd = { mask: { kind: 'random' as const, seed: 9, depth: 0.3 } }
for (const n of names) {
  const a = ARCHS[n]
  if (!a) throw new Error(`unknown arch ${n}`)
  dump(n, slmRing({ ...a, ...rnd, ampMask: a.ampMask ? { dark: a.ampMask.dark, program: { kind: 'random', seed: 5, depth: 1 } } : undefined }))
}
