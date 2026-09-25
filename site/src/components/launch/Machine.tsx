'use client'
import dynamic from 'next/dynamic'
import { useRef } from 'react'
import type { Machine } from '../machine/engine'
import { Denoise, type DenoiseHandle } from './Denoise'
import s from './Machine.module.css'

const MachineCanvas = dynamic(() => import('../machine/MachineCanvas'), { ssr: false, loading: () => null })

const REPO = 'https://github.com/JacobFV/phaser-design'

type Pt = { x: number; y: number }
type Lead = 'time' | 'io' | 'rate'

export function MachineSection() {
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
    <section className={s.sec} id="machine" aria-labelledby="machine-h">
      <div className="wrap">
        <p className="eyebrow">02 / The machine</p>
        <h2 id="machine-h" className={s.h}>Optical computation</h2>
        <p className={s.lede}>Algorithms are mapped onto the diffusion process photons perform as they bounce within a resonance chamber.</p>

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

        <div className={s.close}>
          <p className={s.body}>
            Pushing charge through a wire costs energy every time. Light passing through glass doesn’t: it interferes with itself on the
            way through, and that interference is the arithmetic. PHASER only pays to keep the light going.
          </p>
          <div className={s.cta}>
            <a href={`${REPO}/blob/main/research/2026-09-14/REPORT.md`}>Read the research <span>↗</span></a>
            <a href={`${REPO}/tree/main/research/2026-09-14/out/29`}>See the energy model <span>↗</span></a>
          </div>
        </div>
      </div>
    </section>
  )
}
