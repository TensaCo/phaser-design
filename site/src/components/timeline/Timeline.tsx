'use client'
/**
 * A log-zooming time ruler. Every lane is drawn at its real period: 0.667 ns per round trip, 6.7 ns per input step,
 * 53 ns gate settling, 667 µs of held bits. The digital lanes use stated assumptions (see the evidence markers).
 */
import { useEffect, useRef, useState } from 'react'
import { useInView, useReducedMotion } from 'framer-motion'
import { Evidence } from '../Evidence'
import type { EvidenceId } from '@/data/evidence'
import { sci } from '@/lib/format'
import s from './Timeline.module.css'

type Lane = { id: string; label: string; ev: EvidenceId; color: string; period?: number; span?: number; kind: 'optical' | 'digital' }
const LANES: Lane[] = [
  { id: 'trip', label: 'round trip', ev: 'tripTime', color: '#5fe3f0', period: 0.6673e-9, kind: 'optical' },
  { id: 'input', label: 'input step (10 trips)', ev: 'inputRate', color: '#5fe3f0', period: 6.673e-9, kind: 'optical' },
  { id: 'gate', label: 'NAND settles', ev: 'nandSettle', color: '#9d8cff', span: 53e-9, kind: 'optical' },
  { id: 'hold', label: 'bits held (measured)', ev: 'memory1e6', color: '#9d8cff', span: 667e-6, kind: 'optical' },
  { id: 'asic', label: 'ESN-128 step · ASIC', ev: 'digitalStepAsic', color: '#ff9d5c', period: 128e-9, kind: 'digital' },
  { id: 'cpu', label: 'ESN-128 step · CPU core', ev: 'digitalStepCpu', color: '#ff9d5c', period: 1.6384e-6, kind: 'digital' },
]
const MIN = Math.log10(4e-9), MAX = Math.log10(2e-3)

function fmtT(t: number) {
  if (t >= 1e-3) return `${+(t * 1e3).toPrecision(3)} ms`
  if (t >= 1e-6) return `${+(t * 1e6).toPrecision(3)} µs`
  if (t >= 1e-9) return `${+(t * 1e9).toPrecision(3)} ns`
  return `${+(t * 1e12).toPrecision(3)} ps`
}
function niceStep(W: number, target: number) {
  const raw = W / target
  const e = 10 ** Math.floor(Math.log10(raw))
  for (const m of [1, 2, 5, 10]) if (m * e >= raw) return m * e
  return 10 * e
}
const fmtN = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })

export function Timeline() {
  const wrap = useRef<HTMLDivElement>(null)
  const cv = useRef<HTMLCanvasElement>(null)
  const readout = useRef<HTMLSpanElement>(null)
  const live = useRef<HTMLSpanElement>(null)
  const [zoom, setZoom] = useState(0.18) // 0..1 on the log window
  const [auto, setAuto] = useState(true)
  const reduced = useReducedMotion() ?? false
  const inView = useInView(wrap, { margin: '0px 0px -10% 0px' })
  const z = useRef(zoom)
  const redraw = useRef<() => void>(() => {})
  z.current = zoom

  useEffect(() => { if (reduced) setAuto(false) }, [reduced])

  useEffect(() => {
    const c = cv.current
    if (!c || !inView) return
    const ctx = c.getContext('2d')!
    let raf = 0, last = performance.now(), dir = 1
    const t0 = performance.now()
    const render = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      if (live.current) live.current.textContent = fmtN.format(((now - t0) / 1000) * 1.4985e9)
      if (auto) {
        let nz = z.current + dir * dt * 0.035
        if (nz > 1) { nz = 1; dir = -1 } else if (nz < 0) { nz = 0; dir = 1 }
        z.current = nz
        setZoomQuiet(nz)
      }
      const dpr = Math.min(2, window.devicePixelRatio || 1)
      const W = c.clientWidth, H = c.clientHeight
      if (c.width !== Math.round(W * dpr) || c.height !== Math.round(H * dpr)) { c.width = Math.round(W * dpr); c.height = Math.round(H * dpr) }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, W, H)
      const narrow = W < 640
      const L = narrow ? 8 : 190, R = 16
      const span = 10 ** (MIN + (MAX - MIN) * z.current) // seconds across the ruler
      const px = (t: number) => L + ((W - L - R) * t) / span

      // ruler
      const top = 34
      const step = niceStep(span, narrow ? 4 : 8)
      ctx.font = '10.5px ui-monospace, "JetBrains Mono", monospace'
      ctx.textBaseline = 'alphabetic'
      for (let t = 0; t <= span * 1.0001; t += step) {
        const x = px(t)
        ctx.fillStyle = 'rgba(236,235,230,0.10)'
        ctx.fillRect(Math.round(x), top, 1, H - top - 8)
        ctx.fillStyle = 'rgba(236,235,230,0.55)'
        ctx.fillText(t === 0 ? '0' : fmtT(t), x + 3, top - 8)
      }
      for (let t = 0; t <= span; t += step / 5) { ctx.fillStyle = 'rgba(236,235,230,0.22)'; ctx.fillRect(Math.round(px(t)), top, 1, 5) }

      const laneH = (H - top - 20) / LANES.length
      LANES.forEach((ln, k) => {
        const y0 = top + 14 + k * laneH
        const h = Math.min(26, laneH * 0.55)
        const ym = y0 + laneH / 2 - h / 2
        if (!narrow) {
          ctx.fillStyle = ln.kind === 'digital' ? 'rgba(255,157,92,0.85)' : 'rgba(236,235,230,0.75)'
          ctx.fillText(ln.label, 16, ym + h / 2 + 4)
        }
        ctx.fillStyle = 'rgba(236,235,230,0.05)'
        ctx.fillRect(L, ym + h / 2, W - L - R, 1)
        if (ln.period) {
          const n = span / ln.period
          const gap = (W - L - R) / n
          ctx.save()
          ctx.beginPath(); ctx.rect(L, 0, W - L - R, H); ctx.clip()
          if (gap >= 2.2) {
            ctx.fillStyle = ln.color
            ctx.globalAlpha = ln.kind === 'digital' ? 0.9 : Math.min(1, 0.35 + gap / 20)
            for (let i = 0; i <= n; i++) {
              const x = px(i * ln.period)
              if (ln.kind === 'digital') ctx.fillRect(x + 1, ym + 3, Math.max(1, gap - 2), h - 6)
              else ctx.fillRect(Math.round(x), ym, 1, h)
            }
          } else {
            // too dense to draw one by one: a band whose weave shows the density
            ctx.fillStyle = ln.color
            ctx.globalAlpha = 0.16
            ctx.fillRect(L, ym, W - L - R, h)
            ctx.globalAlpha = 0.5
            for (let x = L; x < W - R; x += 2) ctx.fillRect(x, ym, 1, h)
          }
          ctx.restore()
          const txt = n >= 1 ? `${n >= 1e4 ? sci(n, 2) : fmtN.format(Math.floor(n))} in view` : `one step = ${fmtT(ln.period)}; ${(n * 100).toFixed(n < 0.01 ? 2 : 0)} % shown`
          const tw = ctx.measureText(txt).width
          ctx.fillStyle = 'rgba(5,6,8,0.85)'
          ctx.fillRect(W - R - tw - 12, ym + h / 2 - 9, tw + 10, 16)
          ctx.fillStyle = ln.kind === 'digital' ? '#ff9d5c' : '#ecebe6'
          ctx.fillText(txt, W - R - tw - 7, ym + h / 2 + 4)
        } else if (ln.span) {
          const x1 = Math.min(px(ln.span), W - R)
          ctx.fillStyle = ln.color
          ctx.globalAlpha = 0.22
          ctx.fillRect(L, ym + h * 0.2, x1 - L, h * 0.6)
          ctx.globalAlpha = 1
          ctx.fillRect(L, ym + h * 0.2, x1 - L, 1)
          if (px(ln.span) <= W - R) ctx.fillRect(x1 - 1, ym, 1, h)
          ctx.fillStyle = 'rgba(236,235,230,0.9)'
          const lab = px(ln.span) <= W - R ? fmtT(ln.span) : `${fmtT(ln.span)} →`
          ctx.fillText(lab, Math.min(x1 + 6, W - R - ctx.measureText(lab).width), ym - 2)
        }
        if (narrow) {
          ctx.fillStyle = ln.kind === 'digital' ? 'rgba(255,157,92,0.9)' : 'rgba(236,235,230,0.7)'
          ctx.fillText(ln.label, L, ym - 3)
        }
      })
      if (readout.current) readout.current.textContent = fmtT(span)
    }
    const loop = (now: number) => { render(now); raf = requestAnimationFrame(loop) }
    render(performance.now()) // paint immediately (and for hidden tabs / thumbnails)
    redraw.current = () => render(performance.now())
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [inView, auto])

  // keep the slider in step with the auto zoom without re-rendering every frame
  const slider = useRef<HTMLInputElement>(null)
  function setZoomQuiet(v: number) { if (slider.current) slider.current.value = String(v) }

  return (
    <div ref={wrap} className={s.wrap}>
      <div className={s.top}>
        <div>
          <p className="eyebrow">window</p>
          <p className={`mono ${s.win}`}><span ref={readout}>—</span></p>
        </div>
        <label className={s.zoom}>
          <span className="eyebrow">zoom</span>
          <input ref={slider} type="range" min={0} max={1} step={0.001} defaultValue={zoom}
            onPointerDown={() => setAuto(false)}
            onChange={(e) => { setAuto(false); setZoom(Number(e.target.value)); z.current = Number(e.target.value); redraw.current() }}
            aria-label="Time window (log scale), 4 ns to 2 ms" />
        </label>
        <button className={s.auto} aria-pressed={auto} onClick={() => setAuto((a) => !a)}>{auto ? 'pause' : 'auto-zoom'}</button>
        <div className={s.live}>
          <p className="eyebrow">round trips since you scrolled here, at 1.5 GHz<Evidence id="tripRate" /></p>
          <p className={`mono ${s.liveN}`}><span ref={live}>0</span></p>
        </div>
      </div>
      <canvas ref={cv} className={s.canvas} role="img"
        aria-label="Time ruler. Optical round trips every 0.667 nanoseconds and input steps every 6.7 nanoseconds, against assumed digital reservoir steps of 128 nanoseconds on an ASIC and 1.6 microseconds on a CPU core." />
      <ul className={s.legend}>
        {LANES.map((l) => (
          <li key={l.id}><i style={{ background: l.color }} />{l.label}<Evidence id={l.ev} /></li>
        ))}
      </ul>
    </div>
  )
}
