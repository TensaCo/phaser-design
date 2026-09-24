'use client'
import dynamic from 'next/dynamic'
import { useEffect, useRef, useState } from 'react'
import X from '@/data/exp29.json'
import type { Machine } from '../machine/engine'
import { Denoise, type DenoiseHandle } from './Denoise'
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

type Pt = { x: number; y: number }
type Lead = 'time' | 'io' | 'rate'

export function Economics() {
  const grid = useRef<HTMLDivElement>(null)
  const [shown, setShown] = useState(false)
  useEffect(() => {
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setShown(true); io.disconnect() } }, { threshold: 0.35 })
    if (grid.current) io.observe(grid.current)
    return () => io.disconnect()
  }, [])

  const stage = useRef<HTMLDivElement>(null)
  const denoise = useRef<DenoiseHandle>(null)
  const from = useRef<Record<Lead, HTMLElement | null>>({ time: null, io: null, rate: null })
  const lines = useRef<Record<Lead, SVGPolylineElement | null>>({ time: null, io: null, rate: null })
  const dots = useRef<Record<Lead, SVGCircleElement | null>>({ time: null, io: null, rate: null })
  const dim = useRef<SVGGElement>(null)
  const lastPass = useRef(-1)

  const onFrame = (m: Machine) => {
    const st = stage.current, canvas = st?.querySelector('canvas')
    if (!st || !canvas) return
    // one denoising step per round trip (the machine injects three wavefronts per round trip)
    const trip = Math.floor(m.pulses / 3)
    if (trip !== lastPass.current) { if (lastPass.current >= 0) denoise.current?.pass(); lastPass.current = trip }

    const sr = st.getBoundingClientRect(), cr = canvas.getBoundingClientRect()
    const a = m.anchors()
    const loc = (p: Pt): Pt => ({ x: p.x + cr.left - sr.left, y: p.y + cr.top - sr.top })
    const top = loc(a.mirrorTop), bot = loc(a.mirrorBot)
    // dimension line between the two mirrors
    const g = dim.current
    if (g) {
      const [l, t1, t2, lab] = Array.from(g.children) as SVGElement[]
      l.setAttribute('x1', String(top.x)); l.setAttribute('y1', String(top.y)); l.setAttribute('x2', String(bot.x)); l.setAttribute('y2', String(bot.y))
      const tick = (el: SVGElement, p: Pt) => { el.setAttribute('x1', String(p.x - 7)); el.setAttribute('x2', String(p.x + 7)); el.setAttribute('y1', String(p.y)); el.setAttribute('y2', String(p.y)) }
      tick(t1, top); tick(t2, bot)
      lab.setAttribute('x', String((top.x + bot.x) / 2 - 12)); lab.setAttribute('y', String((top.y + bot.y) / 2))
    }
    const target: Record<Lead, Pt> = {
      time: { x: (top.x + bot.x) / 2, y: (top.y + bot.y) / 2 + 26 },
      io: loc(a.pinhole), rate: loc(a.beam),
    }
    for (const k of ['time', 'io', 'rate'] as Lead[]) {
      const el = from.current[k], line = lines.current[k], dot = dots.current[k]
      if (!el || !line || !dot) continue
      const r = el.getBoundingClientRect()
      const right = r.left + r.width / 2 > sr.left + sr.width / 2
      const x0 = (right ? r.left - 10 : r.right + 10) - sr.left
      const y0 = (k === 'io' ? r.top + r.height * 0.3 : r.top + 34) - sr.top
      const t = target[k]
      const xm = x0 + (right ? -24 : 24)
      line.setAttribute('points', `${x0},${y0} ${xm},${y0} ${t.x},${t.y}`)
      dot.setAttribute('cx', String(t.x)); dot.setAttribute('cy', String(t.y))
    }
  }

  return (
    <section className={s.sec} id="economics" aria-labelledby="econ-h">
      <div className="wrap">
        <p className="eyebrow">01 / The economics</p>
        <h2 id="econ-h" className={s.h}>
          <span>A GPU burns a thousand of these.</span>
          <span className={s.red}>Light burns one.</span>
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
          <figcaption className={s.cap}>One step of a 135,000-neuron layer. Each square is what PHASER spends on the whole step. Modeled.</figcaption>
        </figure>

        <div className={s.anatomy} ref={stage}>
          <div className={s.col}>
            <div className={s.metric} ref={(el) => { from.current.time = el }}>
              <span className="num">6.7<small>ns</small></span>
              <p>One step: ten trips of light between two mirrors 10 cm apart.</p>
            </div>
          </div>
          <div className={s.mini} aria-hidden="true">
            <MachineCanvas frameX={0} frameY={0} distance={25} onFrame={onFrame} />
          </div>
          <div className={`${s.col} ${s.colR}`}>
            <div className={s.program} ref={(el) => { from.current.io = el }}>
              <Denoise ref={denoise} />
              <p>Each pass is programmed. Here, one pass is one step of an image model: noise in, less noise out.</p>
            </div>
            <div className={s.metric} ref={(el) => { from.current.rate = el }}>
              <span className="num">10<small>B</small></span>
              <p>steps per second from one stack: 67 wavefronts in flight, 10 ps apart, 100 GHz in and out.</p>
            </div>
          </div>
          <svg className={s.leaders} aria-hidden="true">
            <g ref={dim} className={s.dim}>
              <line /><line /><line />
              <text textAnchor="end">10 cm</text>
            </g>
            {(['time', 'io', 'rate'] as Lead[]).map((k) => (
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
