'use client'
/**
 * Photon vs electron. Left: a complex optical wave packet moving through free space. The field is drawn as its rotating
 * phasor (Re, Im) along the propagation axis inside a Gaussian envelope, coloured by phase (blue ↔ orange), with the
 * wavefront planes it carries. Right: an electron pushed through a crystal lattice. Each collision knocks an atom into
 * vibration (heat) that lingers, so the lattice slowly warms.
 */
import { useEffect, useRef } from 'react'
import s from './Carriers.module.css'

const BLUE = [74, 144, 255], ORANGE = [255, 138, 42]
const mix = (t: number) => BLUE.map((b, i) => Math.round(b + (ORANGE[i] - b) * t))

function photon(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  ctx.clearRect(0, 0, w, h)
  const cy = h / 2, amp = h * 0.26
  const L = w * 1.3
  const x0 = ((t * w * 0.16) % L) - w * 0.15 // packet centre, wraps
  const sigma = w * 0.16, k = 0.085 * (320 / Math.max(260, w)) * 3.2
  // axis
  ctx.strokeStyle = 'rgba(233,229,220,0.14)'
  ctx.lineWidth = 1
  ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(w, cy); ctx.stroke()
  // wavefront planes (seen edge-on, tilted): one per crest inside the envelope
  const lambda = (2 * Math.PI) / k
  const phase0 = -t * 7
  const first = Math.ceil((x0 - 3 * sigma - phase0 / k) / lambda)
  for (let n = first; ; n++) {
    const x = n * lambda + (-phase0 / k) % lambda
    if (x > x0 + 3 * sigma) break
    const e = Math.exp(-((x - x0) ** 2) / (2 * sigma * sigma))
    if (e < 0.04) continue
    ctx.strokeStyle = `rgba(233,229,220,${0.18 * e})`
    ctx.beginPath(); ctx.ellipse(x, cy, amp * 0.28 * e + 2, amp * 1.15 * e + 4, 0, 0, Math.PI * 2); ctx.stroke()
  }
  // helix: phasor (cos, sin) → (screen y, depth); draw back half first, then front
  for (const front of [false, true]) {
    for (let x = Math.max(0, x0 - 3.2 * sigma); x < Math.min(w, x0 + 3.2 * sigma); x += 1.5) {
      const e = Math.exp(-((x - x0) ** 2) / (2 * sigma * sigma))
      const ph = k * x + phase0
      const re = Math.cos(ph), im = Math.sin(ph)
      if ((im > 0) !== front) continue
      const y = cy - re * amp * e
      const depth = 0.55 + 0.45 * im
      const [r, g, b] = mix((re + 1) / 2)
      ctx.fillStyle = `rgba(${r},${g},${b},${(0.25 + 0.75 * depth) * Math.min(1, e * 1.6)})`
      const size = 1.2 + 2.4 * depth * e
      ctx.beginPath(); ctx.arc(x + im * amp * 0.18 * e, y, size, 0, Math.PI * 2); ctx.fill()
    }
  }
  // envelope trace (intensity), faint
  ctx.strokeStyle = 'rgba(255,138,42,0.25)'
  ctx.beginPath()
  for (let x = 0; x < w; x += 3) {
    const e = Math.exp(-((x - x0) ** 2) / (2 * sigma * sigma))
    const y = cy + amp * 1.25 - e * amp * 0.35
    x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  }
  ctx.stroke()
}

interface Lattice { atoms: { x: number; y: number; heat: number; ph: number }[]; ex: number; ey: number; vx: number; vy: number; hits: number; trail: { x: number; y: number }[] }

function makeLattice(w: number, h: number): Lattice {
  const atoms = []
  const pitch = Math.max(26, Math.min(40, w / 11))
  for (let y = pitch * 0.7; y < h - pitch * 0.3; y += pitch)
    for (let x = pitch * 0.5; x < w; x += pitch) atoms.push({ x, y, heat: 0, ph: Math.random() * 6.28 })
  return { atoms, ex: 0, ey: h * 0.4, vx: 80, vy: 30, hits: 0, trail: [] }
}

function electron(ctx: CanvasRenderingContext2D, w: number, h: number, L: Lattice, t: number, dt: number) {
  ctx.clearRect(0, 0, w, h)
  // drift field pushes right; random thermal kicks; collisions scatter and deposit heat
  L.vx += 160 * dt
  L.vy += (Math.random() - 0.5) * 900 * dt // thermal jitter
  L.ex += L.vx * dt
  L.ey += L.vy * dt
  if (L.ey < 12 || L.ey > h - 12) L.vy *= -1
  for (const a of L.atoms) {
    const dx = L.ex - a.x, dy = L.ey - a.y
    const d = Math.hypot(dx, dy)
    if (d < 12) {
      // scatter: random new direction, lose most of the momentum to the atom
      const ang = (Math.random() - 0.5) * 2.6
      const sp = Math.hypot(L.vx, L.vy) * 0.25 + 20
      L.vx = Math.cos(ang) * sp
      L.vy = Math.sin(ang) * sp * 1.6
      L.ex = a.x + (dx / (d || 1)) * 13
      L.ey = a.y + (dy / (d || 1)) * 13
      a.heat = Math.min(1, a.heat + 0.7)
      L.hits++
    }
  }
  if (L.ex > w + 10) { L.ex = -10; L.ey = h * (0.25 + Math.random() * 0.5); L.trail = []; L.vx = 80; L.vy = 30 }
  L.trail.push({ x: L.ex, y: L.ey })
  if (L.trail.length > 40) L.trail.shift()
  for (const a of L.atoms) {
    a.heat *= Math.pow(0.55, dt) // heat lingers
    const j = a.heat * 3.2
    const x = a.x + Math.sin(t * 38 + a.ph) * j, y = a.y + Math.cos(t * 31 + a.ph * 1.7) * j
    const [r, g, b] = mix(0.5 + a.heat * 0.5)
    ctx.fillStyle = a.heat > 0.03 ? `rgba(${r},${Math.round(g * (1 - a.heat * 0.5))},${b},${0.35 + a.heat * 0.65})` : 'rgba(233,229,220,0.22)'
    ctx.beginPath(); ctx.arc(x, y, 4.2 + a.heat * 2.2, 0, Math.PI * 2); ctx.fill()
    if (a.heat > 0.08) {
      const g2 = ctx.createRadialGradient(x, y, 0, x, y, 22 * a.heat + 6)
      g2.addColorStop(0, `rgba(255,120,40,${0.35 * a.heat})`); g2.addColorStop(1, 'rgba(255,120,40,0)')
      ctx.fillStyle = g2; ctx.beginPath(); ctx.arc(x, y, 22 * a.heat + 6, 0, Math.PI * 2); ctx.fill()
    }
  }
  // electron + its jagged path
  ctx.strokeStyle = 'rgba(74,144,255,0.45)'
  ctx.lineWidth = 1
  ctx.beginPath()
  L.trail.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)))
  ctx.stroke()
  const ge = ctx.createRadialGradient(L.ex, L.ey, 0, L.ex, L.ey, 14)
  ge.addColorStop(0, 'rgba(140,190,255,0.9)'); ge.addColorStop(1, 'rgba(74,144,255,0)')
  ctx.fillStyle = ge; ctx.beginPath(); ctx.arc(L.ex, L.ey, 14, 0, Math.PI * 2); ctx.fill()
  ctx.fillStyle = 'rgb(200,225,255)'
  ctx.beginPath(); ctx.arc(L.ex, L.ey, 3.4, 0, Math.PI * 2); ctx.fill()
}

export function Carriers() {
  const a = useRef<HTMLCanvasElement>(null)
  const b = useRef<HTMLCanvasElement>(null)
  const hits = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    const ca = a.current!, cb = b.current!
    const xa = ca.getContext('2d')!, xb = cb.getContext('2d')!
    let lat: Lattice | null = null
    let raf = 0, visible = false, last = performance.now(), t = 0
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
    io.observe(ca)
    const size = (c: HTMLCanvasElement, x: CanvasRenderingContext2D) => {
      const d = Math.min(devicePixelRatio || 1, 2)
      const w = c.clientWidth, h = c.clientHeight
      if (c.width !== Math.round(w * d)) { c.width = Math.round(w * d); c.height = Math.round(h * d); x.setTransform(d, 0, 0, d, 0, 0); return true }
      return false
    }
    const loop = (now: number) => {
      raf = requestAnimationFrame(loop)
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      if (!visible && lat) return
      t += reduced ? 0 : dt
      size(ca, xa)
      if (size(cb, xb) || !lat) lat = makeLattice(cb.clientWidth, cb.clientHeight)
      photon(xa, ca.clientWidth, ca.clientHeight, t + 2.2)
      electron(xb, cb.clientWidth, cb.clientHeight, lat, t, reduced ? 0 : dt)
      if (hits.current) hits.current.textContent = String(lat.hits).padStart(4, '0')
    }
    raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); io.disconnect() }
  }, [])
  return (
    <div className={s.pair}>
      <figure>
        <canvas ref={a} aria-hidden="true" />
        <figcaption><span>Photon · through glass</span><span>Energy lost to the medium: ~0</span></figcaption>
      </figure>
      <figure>
        <canvas ref={b} aria-hidden="true" />
        <figcaption><span>Electron · through silicon</span><span>Collisions → heat: <b ref={hits}>0000</b></span></figcaption>
      </figure>
    </div>
  )
}
