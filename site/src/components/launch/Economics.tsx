'use client'
import dynamic from 'next/dynamic'
import { useEffect, useRef, useState } from 'react'
import X from '@/data/exp29.json'
import type { Machine } from '../machine/engine'
import s from './Economics.module.css'

const MachineCanvas = dynamic(() => import('../machine/MachineCanvas'), { ssr: false, loading: () => null })

// Experiment 29 scaling model (research/2026-09-14/out/29): one step of a dense layer inside one 1080p modulator,
// at the pessimistic 32 optical modes per neuron.
const N = X.N as number[]
const I = N.findIndex((n) => n >= 135000)
const GPU_J = (X.series.digital_dense_gpu as number[])[I]
const LIGHT_J = (X.series.optical_modeled_32 as number[])[I]
const SQUARES = Math.round(GPU_J / LIGHT_J)
const COLS = 70 // only paces the reveal

type Anchor = 'beam' | 'slm' | 'pinhole'
const METRICS: { id: Anchor; side: 'l' | 'r'; value: string; unit: string; text: string; fn?: number }[] = [
  { id: 'beam', side: 'l', value: '6.7', unit: 'ns', text: 'One step. Light crosses the stack and the answer is already there.', fn: 2 },
  { id: 'slm', side: 'l', value: '0', unit: 'bytes', text: 'Weights fetched from memory per step. The weights are the glass.' },
  { id: 'pinhole', side: 'r', value: '150', unit: 'M', text: 'Steps per second, from one stack, with no batching.', fn: 2 },
]

export function Economics() {
  const grid = useRef<HTMLDivElement>(null)
  const [shown, setShown] = useState(false)
  useEffect(() => {
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setShown(true); io.disconnect() } }, { threshold: 0.35 })
    if (grid.current) io.observe(grid.current)
    return () => io.disconnect()
  }, [])

  // leaders: from each metric's inner edge to its part of the live machine
  const stage = useRef<HTMLDivElement>(null)
  const cards = useRef<Record<Anchor, HTMLDivElement | null>>({ beam: null, slm: null, pinhole: null })
  const lines = useRef<Record<Anchor, SVGPolylineElement | null>>({ beam: null, slm: null, pinhole: null })
  const dots = useRef<Record<Anchor, SVGCircleElement | null>>({ beam: null, slm: null, pinhole: null })
  const onFrame = (m: Machine) => {
    const st = stage.current
    if (!st) return
    const sr = st.getBoundingClientRect()
    const canvas = st.querySelector('canvas')
    if (!canvas) return
    const cr = canvas.getBoundingClientRect()
    const a = m.anchors()
    for (const k of ['beam', 'slm', 'pinhole'] as Anchor[]) {
      const card = cards.current[k], line = lines.current[k], dot = dots.current[k]
      if (!card || !line || !dot) continue
      const r = card.getBoundingClientRect()
      const left = METRICS.find((x) => x.id === k)!.side === 'l'
      const x0 = (left ? r.right + 12 : r.left - 12) - sr.left
      const y0 = r.top + 34 - sr.top
      const x1 = a[k].x + cr.left - sr.left
      const y1 = a[k].y + cr.top - sr.top
      const xm = x0 + (left ? 1 : -1) * 28
      line.setAttribute('points', `${x0},${y0} ${xm},${y0} ${x1},${y1}`)
      dot.setAttribute('cx', String(x1))
      dot.setAttribute('cy', String(y1))
    }
  }

  return (
    <section className={s.sec} id="economics" aria-labelledby="econ-h">
      <div className="wrap">
        <p className="eyebrow">01 / The economics</p>
        <h2 id="econ-h" className={s.h}>
          <span>A GPU burns a thousand of these.</span>
          <span className={s.red}>Light burns one.<sup className="fn"><a href="#r1">1</a></sup></span>
        </h2>

        <figure className={s.units} ref={grid}>
          <div className={s.gpu}>
            <div className={s.unitHead}><span>GPU</span><span>{(GPU_J * 1e3).toFixed(1)} mJ</span></div>
            <div className={`${s.squares} ${shown ? s.on : ''}`} role="img" aria-label={`${SQUARES} squares of energy for one GPU step`}>
              {Array.from({ length: SQUARES }, (_, i) => <i key={i} style={{ ['--d' as string]: `${Math.floor(i / COLS) * 30}ms` }} />)}
            </div>
          </div>
          <div className={s.light}>
            <div className={s.unitHead}><span>PHASER</span><span>{(LIGHT_J * 1e3).toFixed(3)} mJ</span></div>
            <div className={s.one} role="img" aria-label="one square of energy for one PHASER step"><i /></div>
          </div>
          <figcaption className={s.cap}>
            One step of a 135,000-neuron layer. Each square is what PHASER spends on the whole step. Modeled, not measured.
          </figcaption>
        </figure>

        <div className={s.anatomy} ref={stage}>
          <div className={s.col}>
            {METRICS.filter((m) => m.side === 'l').map((m) => (
              <div key={m.id} className={s.metric} ref={(el) => { cards.current[m.id] = el }}>
                <span className="num">{m.value}<small>{m.unit}</small></span>
                <p>{m.text}{m.fn && <sup className="fn"><a href={`#r${m.fn}`}>{m.fn}</a></sup>}</p>
              </div>
            ))}
          </div>
          <div className={s.mini} aria-hidden="true">
            <MachineCanvas frameX={0} frameY={0} distance={25} onFrame={onFrame} />
          </div>
          <div className={`${s.col} ${s.colR}`}>
            {METRICS.filter((m) => m.side === 'r').map((m) => (
              <div key={m.id} className={s.metric} ref={(el) => { cards.current[m.id] = el }}>
                <span className="num">{m.value}<small>{m.unit}</small></span>
                <p>{m.text}{m.fn && <sup className="fn"><a href={`#r${m.fn}`}>{m.fn}</a></sup>}</p>
              </div>
            ))}
          </div>
          <svg className={s.leaders} aria-hidden="true">
            {(['beam', 'slm', 'pinhole'] as Anchor[]).map((k) => (
              <g key={k}>
                <polyline ref={(el) => { lines.current[k] = el }} points="" />
                <circle ref={(el) => { dots.current[k] = el }} r="3.5" />
              </g>
            ))}
          </svg>
        </div>
      </div>
    </section>
  )
}
