'use client'
/**
 * Photon vs electron, in 3-D and time.
 * Photon: a light wave packet in vacuum. E (orange) and B (blue) are in phase and at right angles, inside a Gaussian
 * envelope that moves rigidly forward at c (phase and group velocity are equal in vacuum). Nothing slows it or absorbs it.
 * Electron: a wave packet (phase fringes along its momentum) driven through a diamond-cubic silicon lattice. It travels a
 * short free path, scatters off an atom or a defect, stalls and spreads, then sets off in a new direction: a saccade.
 * Every scattering event hands energy to the lattice as heat.
 */
import { useEffect, useRef } from 'react'
import s from './Carriers.module.css'

type V3 = [number, number, number]
const BLUE: V3 = [74, 144, 255], ORANGE: V3 = [255, 138, 42]
const mixc = (t: number) => BLUE.map((b, i) => Math.round(b + (ORANGE[i] - b) * t)) as V3

function camera(w: number, h: number, yaw: number, pitch: number, scale: number, dist = 9) {
  const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch)
  return (p: V3) => {
    const x1 = p[0] * cy - p[2] * sy, z1 = p[0] * sy + p[2] * cy
    const y2 = p[1] * cp - z1 * sp, z2 = p[1] * sp + z1 * cp
    const f = dist / (dist + z2)
    return { x: w / 2 + x1 * f * scale, y: h / 2 - y2 * f * scale, z: z2, f }
  }
}

function drawPhoton(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  ctx.clearRect(0, 0, w, h)
  const P = camera(w, h, -0.55 + 0.22 * Math.sin(t * 0.15), 0.32, Math.min(w / 9.5, h / 4.2))
  const X = 4.6
  // floor grid for depth
  ctx.lineWidth = 1
  for (let i = -X; i <= X + 1e-6; i += 0.92) {
    const a = P([i, -1.3, -1.2]), b = P([i, -1.3, 1.2])
    ctx.strokeStyle = 'rgba(233,229,220,0.07)'; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke()
  }
  for (const zz of [-1.2, 0, 1.2]) {
    const a = P([-X, -1.3, zz]), b = P([X, -1.3, zz])
    ctx.strokeStyle = 'rgba(233,229,220,0.07)'; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke()
  }
  // propagation axis
  const a0 = P([-X, 0, 0]), a1 = P([X, 0, 0])
  ctx.strokeStyle = 'rgba(233,229,220,0.25)'; ctx.beginPath(); ctx.moveTo(a0.x, a0.y); ctx.lineTo(a1.x, a1.y); ctx.stroke()
  // packet moves at c; the whole pattern translates rigidly
  const span = 2 * X + 3
  const x0 = ((t * 1.25) % span) - X - 1.5
  const sigma = 0.95, k = 7.2
  const samples: { x: number; e: number; b: number; env: number }[] = []
  for (let x = -X; x <= X; x += 0.06) {
    const env = Math.exp(-((x - x0) ** 2) / (2 * sigma * sigma))
    if (env < 0.02) continue
    const ph = Math.cos(k * (x - x0))
    samples.push({ x, e: ph * env, b: ph * env, env })
  }
  const A = 1.05
  // B field: stems along depth (z), blue; E field: stems up (y), orange. Draw B first (it sits behind in this view).
  for (const [field, col] of [['b', BLUE], ['e', ORANGE]] as const) {
    ctx.lineWidth = 1.2
    for (const sm of samples) {
      const v = sm[field] * A
      const base = P([sm.x, 0, 0]), tip = P(field === 'e' ? [sm.x, v, 0] : [sm.x, 0, v])
      ctx.strokeStyle = `rgba(${col[0]},${col[1]},${col[2]},${0.18 + 0.5 * sm.env})`
      ctx.beginPath(); ctx.moveTo(base.x, base.y); ctx.lineTo(tip.x, tip.y); ctx.stroke()
    }
    ctx.lineWidth = 2
    ctx.strokeStyle = `rgb(${col[0]},${col[1]},${col[2]})`
    ctx.beginPath()
    samples.forEach((sm, i) => {
      const v = sm[field] * A
      const p = P(field === 'e' ? [sm.x, v, 0] : [sm.x, 0, v])
      i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)
    })
    ctx.stroke()
  }
  // direction and speed
  const h0 = P([x0 + 2.4 * sigma, 0, 0]), h1 = P([x0 + 2.4 * sigma + 0.7, 0, 0])
  ctx.strokeStyle = 'rgba(233,229,220,0.8)'; ctx.fillStyle = 'rgba(233,229,220,0.8)'; ctx.lineWidth = 1.2
  ctx.beginPath(); ctx.moveTo(h0.x, h0.y); ctx.lineTo(h1.x, h1.y); ctx.stroke()
  const ang = Math.atan2(h1.y - h0.y, h1.x - h0.x)
  ctx.beginPath(); ctx.moveTo(h1.x, h1.y); ctx.lineTo(h1.x - 8 * Math.cos(ang - 0.4), h1.y - 8 * Math.sin(ang - 0.4)); ctx.lineTo(h1.x - 8 * Math.cos(ang + 0.4), h1.y - 8 * Math.sin(ang + 0.4)); ctx.fill()
  ctx.font = '11px ui-monospace, monospace'
  ctx.fillText('c', h1.x + 6, h1.y + 4)
  const le = P([x0, A * 1.15, 0]), lb = P([x0, 0, A * 1.25])
  ctx.fillStyle = 'rgb(255,138,42)'; ctx.fillText('E', le.x - 4, le.y - 4)
  ctx.fillStyle = 'rgb(74,144,255)'; ctx.fillText('B', lb.x + 4, lb.y + 12)
}

// ---- electron ------------------------------------------------------------------------------------------------------
interface Atom { p: V3; heat: number; defect: boolean }
interface Walk { atoms: Atom[]; c: V3; dir: V3; seg: number; stall: number; spread: number; path: V3[]; hits: number; last: number }

function lattice(): Atom[] {
  // diamond cubic: fcc + basis (¼,¼,¼); a = 1 lattice constant, 2 × 1 × 1 cells, centred
  const fcc: V3[] = [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]]
  const out: Atom[] = []
  const seen = new Set<string>()
  for (let i = 0; i <= 2; i++) for (let j = 0; j <= 1; j++) for (let k = 0; k <= 1; k++) for (const f of fcc) for (const b of [[0, 0, 0], [0.25, 0.25, 0.25]]) {
    const p: V3 = [i + f[0] + b[0], j + f[1] + b[1], k + f[2] + b[2]]
    if (p[0] > 2.01 || p[1] > 1.01 || p[2] > 1.01) continue
    const key = p.map((v) => v.toFixed(2)).join(',')
    if (seen.has(key)) continue
    seen.add(key)
    out.push({ p: [p[0] - 1, p[1] - 0.5, p[2] - 0.5], heat: 0, defect: false })
  }
  // a few lattice defects / dopants that also scatter
  [5, 19, 31].forEach((n) => { if (out[n]) out[n].defect = true })
  return out
}

const norm = (v: V3): V3 => { const l = Math.hypot(...v) || 1; return [v[0] / l, v[1] / l, v[2] / l] }
function newDir(rnd: () => number): V3 {
  // random direction, biased along +x by the applied field
  return norm([0.9 + rnd() * 0.6, (rnd() - 0.5) * 2, (rnd() - 0.5) * 2])
}

function stepElectron(W: Walk, dt: number, rnd: () => number) {
  if (W.stall > 0) {
    W.stall -= dt
    W.spread = Math.min(1, W.spread + dt * 3)
    if (W.stall <= 0) { W.dir = newDir(rnd); W.seg = 0; W.spread = 1 }
    return
  }
  W.spread = Math.max(0, W.spread - dt * 2.5)
  const v = 0.9
  W.c = [W.c[0] + W.dir[0] * v * dt, W.c[1] + W.dir[1] * v * dt, W.c[2] + W.dir[2] * v * dt]
  W.seg += v * dt
  // keep inside the crystal: reflect off the side walls, re-enter on the left when it exits right
  for (const ax of [1, 2] as const) if (Math.abs(W.c[ax]) > 0.5) { W.dir[ax] *= -1; W.c[ax] = Math.sign(W.c[ax]) * 0.5 }
  if (W.c[0] > 1.15) { W.c = [-1.15, (rnd() - 0.5) * 0.6, (rnd() - 0.5) * 0.6]; W.path = [W.c]; W.last = -1 }
  // scatter: near an atom (after a short free path), or at the end of a random free path
  let hit = -1
  for (let i = 0; i < W.atoms.length; i++) {
    if (i === W.last) continue
    const a = W.atoms[i].p
    const d = Math.hypot(a[0] - W.c[0], a[1] - W.c[1], a[2] - W.c[2])
    if (d < (W.atoms[i].defect ? 0.26 : 0.17) && W.seg > 0.12) { hit = i; break }
  }
  if (hit >= 0 || W.seg > 0.42) {
    if (hit >= 0) { W.atoms[hit].heat = 1; W.last = hit }
    W.hits++
    W.stall = 0.28
    W.path.push([...W.c] as V3)
    if (W.path.length > 14) W.path.shift()
  }
}

function drawElectron(ctx: CanvasRenderingContext2D, w: number, h: number, W: Walk, t: number, dt: number) {
  ctx.clearRect(0, 0, w, h)
  const P = camera(w, h, 0.5 + t * 0.1, 0.38, Math.min(w / 3.3, h / 2.3), 6)
  // bonds (nearest neighbours at √3/4)
  ctx.lineWidth = 1
  ctx.strokeStyle = 'rgba(233,229,220,0.13)'
  const A = W.atoms
  for (let i = 0; i < A.length; i++) for (let j = i + 1; j < A.length; j++) {
    const d = Math.hypot(A[i].p[0] - A[j].p[0], A[i].p[1] - A[j].p[1], A[i].p[2] - A[j].p[2])
    if (Math.abs(d - 0.433) < 0.02) { const a = P(A[i].p), b = P(A[j].p); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke() }
  }
  // depth-sorted atoms + the packet
  type D = { z: number; draw: () => void }
  const list: D[] = []
  for (const a of A) {
    a.heat *= Math.pow(0.35, dt)
    const q = P(a.p)
    const jig = a.heat * 3
    list.push({ z: q.z, draw: () => {
      const x = q.x + Math.sin(t * 40 + a.p[0] * 9) * jig, y = q.y + Math.cos(t * 33 + a.p[2] * 7) * jig
      const r = (a.defect ? 10 : 7.5) * q.f
      const g = ctx.createRadialGradient(x - r * 0.35, y - r * 0.35, 0, x, y, r)
      const hot = a.heat
      const base = a.defect ? [120, 116, 110] : [150, 146, 138]
      g.addColorStop(0, `rgba(${Math.round(base[0] + hot * 105)},${Math.round(base[1] + hot * 20)},${Math.round(base[2] - hot * 60)},${0.55 + 0.4 * q.f / 1.3})`)
      g.addColorStop(1, `rgba(${Math.round(40 + hot * 180)},${Math.round(38 + hot * 40)},${Math.round(36)},0.6)`)
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill()
      if (hot > 0.05) {
        const gl = ctx.createRadialGradient(x, y, 0, x, y, 26 * hot + 6)
        gl.addColorStop(0, `rgba(255,120,40,${0.45 * hot})`); gl.addColorStop(1, 'rgba(255,120,40,0)')
        ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(x, y, 26 * hot + 6, 0, Math.PI * 2); ctx.fill()
      }
    } })
  }
  const c = P(W.c)
  list.push({ z: c.z, draw: () => {
    // wave packet: points in a Gaussian cloud, coloured by the phase of e^{ik·r} along the momentum
    const sig = 0.09 + 0.1 * W.spread
    for (let n = 0; n < 160; n++) {
      const u = (Math.sin(n * 12.9898) * 43758.5453) % 1, v = (Math.sin(n * 78.233) * 12543.1) % 1, q2 = (Math.sin(n * 39.42) * 9871.7) % 1
      const off: V3 = [u * sig * 1.8, v * sig * 1.8, q2 * sig * 1.8]
      const along = off[0] * W.dir[0] + off[1] * W.dir[1] + off[2] * W.dir[2]
      const ph = Math.cos(along * 38 - t * 18)
      const e = Math.exp(-(off[0] ** 2 + off[1] ** 2 + off[2] ** 2) / (2 * sig * sig))
      const p = P([W.c[0] + off[0], W.c[1] + off[1], W.c[2] + off[2]])
      const [r, g, b] = mixc((ph + 1) / 2)
      ctx.fillStyle = `rgba(${r},${g},${b},${0.25 + 0.7 * e})`
      ctx.beginPath(); ctx.arc(p.x, p.y, 1.3 + 2.8 * e * p.f, 0, Math.PI * 2); ctx.fill()
    }
  } })
  list.sort((a, b) => b.z - a.z).forEach((d) => d.draw())
  // saccade path
  ctx.strokeStyle = 'rgba(140,190,255,0.85)'
  ctx.lineWidth = 1.5
  ctx.setLineDash([3, 3])
  ctx.beginPath()
  ;[...W.path, W.c].forEach((p, i) => { const q = P(p); i ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y) })
  ctx.stroke()
  ctx.setLineDash([])
  for (const p of W.path.slice(1)) { const q = P(p); ctx.fillStyle = 'rgba(255,138,42,0.9)'; ctx.fillRect(q.x - 2, q.y - 2, 4, 4) }
}

export function Carriers() {
  const a = useRef<HTMLCanvasElement>(null)
  const b = useRef<HTMLCanvasElement>(null)
  const hits = useRef<HTMLElement>(null)
  useEffect(() => {
    const ca = a.current!, cb = b.current!
    const xa = ca.getContext('2d')!, xb = cb.getContext('2d')!
    let seed = 7
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)
    const W: Walk = { atoms: lattice(), c: [-1.15, 0.1, 0], dir: [1, 0, 0], seg: 0, stall: 0, spread: 0, path: [[-1.15, 0.1, 0]], hits: 0, last: -1 }
    let raf = 0, visible = false, last = performance.now(), t = 0
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
    io.observe(ca)
    const size = (c: HTMLCanvasElement, x: CanvasRenderingContext2D) => {
      const d = Math.min(devicePixelRatio || 1, 2)
      if (c.width !== Math.round(c.clientWidth * d)) { c.width = Math.round(c.clientWidth * d); c.height = Math.round(c.clientHeight * d); x.setTransform(d, 0, 0, d, 0, 0) }
    }
    let first = true
    const loop = (now: number) => {
      raf = requestAnimationFrame(loop)
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      if (!visible && !first) return
      first = false
      const d = reduced ? 0 : dt
      t += d
      size(ca, xa); size(cb, xb)
      drawPhoton(xa, ca.clientWidth, ca.clientHeight, t + 1.2)
      stepElectron(W, d, rnd)
      drawElectron(xb, cb.clientWidth, cb.clientHeight, W, t, d)
      if (hits.current) hits.current.textContent = String(W.hits).padStart(4, '0')
    }
    raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); io.disconnect() }
  }, [])
  return (
    <div className={s.pair}>
      <figure>
        <canvas ref={a} aria-hidden="true" />
        <figcaption><span>Photon · in free space</span><span>Moves at c. Loses nothing.</span></figcaption>
      </figure>
      <figure>
        <canvas ref={b} aria-hidden="true" />
        <figcaption><span>Electron · in silicon</span><span>Stops and turns → heat: <b ref={hits}>0000</b></span></figcaption>
      </figure>
    </div>
  )
}
