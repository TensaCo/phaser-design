'use client'
/**
 * One substrate, several workloads. The trunk is the total circulating power of the simulated Exp. 15 reservoir, trip by
 * trip (from the same field data as the hero). Branches go only to workloads the simulations support; one branch ends.
 */
import { useEffect, useRef, useState } from 'react'
import { useInView, useReducedMotion } from 'framer-motion'
import { Evidence } from '../Evidence'
import type { EvidenceId } from '@/data/evidence'
import { BASE } from '@/lib/heroState'
import s from './Branches.module.css'

type Branch = { title: string; body: React.ReactNode; ev: EvidenceId[]; status: string; open?: boolean }
const BRANCHES: Branch[] = [
  { title: 'Streaming signal processing', body: <>6.7 ns per input step, with no weights moved between steps. The cavity supplies the recurrence; a small digital readout does the rest.</>, ev: ['inputRate', 'mcOptical'], status: 'simulated' },
  { title: 'Closed-loop control', body: <>A toy tracking task: the optical state, never reset, carries target velocity through occlusion.</>, ev: ['control'], status: 'simulated' },
  { title: 'Optical memory', body: <>A static absorbing program holds bits for 10⁶ round trips with zero errors, at 69 bits/mm².</>, ev: ['memory1e6', 'density'], status: 'simulated' },
  { title: 'In-cavity logic', body: <>Persistent NAND and NOT, checked every trip. They need a cross-gain medium that has not been realised physically.</>, ev: ['nand', 'logicEnergy'], status: 'simulated · physics open' },
  { title: 'Autonomous clocks', body: <>Cross-gain produces stable limit cycles. They have not yet been turned into a sequencer.</>, ev: ['limitCycle'], status: 'simulated' },
  { title: 'General-purpose computing, large models', body: <>Not supported. No latch, no multi-gate circuit and no associative memory compiled. At the simulated scale, energy is at parity.</>, ev: ['parity'], status: 'not yet', open: true },
]

export function Branches() {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-20% 0px' })
  const reduced = useReducedMotion() ?? false
  const [trace, setTrace] = useState<number[] | null>(null)
  useEffect(() => {
    fetch(`${BASE}/field-apre.bin`).then((r) => r.arrayBuffer()).then((b) => {
      const a = new Uint8Array(b)
      const n = 64 * 64, T = a.length / (2 * n)
      const p: number[] = []
      for (let t = 0; t < T; t++) { let q = 0; for (let i = 0; i < n; i++) { const v = a[2 * (t * n + i)] / 255; q += v * v } p.push(q) }
      const mx = Math.max(...p)
      setTrace(p.map((v) => v / mx))
    }).catch(() => {})
  }, [])

  const W = 1000, H = 640, tx = 330, ty = H / 2
  const ys = BRANCHES.map((_, k) => ((k + 0.5) * H) / BRANCHES.length)
  const trunk = trace
    ? trace.map((v, i) => `${i ? 'L' : 'M'}${((i / (trace.length - 1)) * tx).toFixed(1)},${(ty - (v - 0.5) * 90).toFixed(1)}`).join('')
    : `M0,${ty}L${tx},${ty}`

  return (
    <div ref={ref} className={s.wrap} data-in={inView || reduced || undefined} data-reduced={reduced || undefined}>
      <svg className={s.svg} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden>
        <path d={trunk} className={s.trunk} />
        {ys.map((y, k) => {
          const open = BRANCHES[k].open
          const end = open ? tx + 170 : W
          const d = `M${tx},${ty} C${tx + 120},${ty} ${tx + 90},${y} ${tx + 230},${y} L${end},${y}`
          return (
            <g key={k}>
              <path d={d} className={open ? s.branchOpen : s.branch} style={{ ['--d' as string]: `${k * 0.12}s` }} />
              {!open && <path d={d} className={s.pulse} style={{ ['--d' as string]: `${1.2 + k * 0.37}s` }} />}
              {open && <path d={`M${end - 6},${y - 6}L${end + 6},${y + 6}M${end - 6},${y + 6}L${end + 6},${y - 6}`} className={s.stop} />}
            </g>
          )
        })}
      </svg>
      <p className={s.trunkLabel}>total circulating power, trip by trip · simulated</p>
      <ol className={s.list}>
        {BRANCHES.map((b, k) => (
          <li key={k} className={s.item} data-open={b.open || undefined} style={{ ['--d' as string]: `${0.3 + k * 0.1}s` }}>
            <span className={`mono ${s.status}`}>{b.status}</span>
            <h3 className={s.title}>{b.title}{b.ev.map((e) => <Evidence key={e} id={e} />)}</h3>
            <p className={s.body}>{b.body}</p>
          </li>
        ))}
      </ol>
    </div>
  )
}
