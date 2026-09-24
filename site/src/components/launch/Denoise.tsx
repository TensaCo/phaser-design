'use client'
/**
 * Cross-sections of the light before and after one pass, where the pass is programmed as one denoising step of a
 * diffusion model whose data is a single smiley face. With a perfect denoiser for that data, the deterministic (DDIM)
 * step is x_{t-1} = x0 + (σ_{t-1} / σ_t)(x_t − x0): the same noise, scaled down. Each pass of the machine advances t.
 */
import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import s from './Denoise.module.css'

const G = 44
const SIGMAS = [1.3, 0.95, 0.68, 0.48, 0.32, 0.2, 0.11, 0.04]

function smiley() {
  const a = new Float32Array(G * G)
  for (let j = 0; j < G; j++) for (let i = 0; i < G; i++) {
    const x = (i + 0.5) / G * 2 - 1, y = (j + 0.5) / G * 2 - 1
    const r = Math.hypot(x, y)
    let v = 0
    if (Math.abs(r - 0.8) < 0.09) v = 1 // face outline
    if (Math.hypot(x + 0.3, y + 0.3) < 0.15 || Math.hypot(x - 0.3, y + 0.3) < 0.15) v = 1 // eyes
    const mr = Math.hypot(x, y + 0.05)
    if (Math.abs(mr - 0.45) < 0.09 && y > 0.12) v = 1 // mouth
    a[j * G + i] = v
  }
  return a
}

function gauss(seed: number) {
  let s0 = seed * 9301 + 49297
  const rnd = () => ((s0 = (s0 * 9301 + 49297) % 233280) / 233280)
  const n = new Float32Array(G * G)
  for (let i = 0; i < n.length; i++) {
    const u = Math.max(1e-6, rnd()), v = rnd()
    n[i] = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v)
  }
  return n
}

function paint(c: HTMLCanvasElement, x0: Float32Array, noise: Float32Array, sigma: number) {
  const ctx = c.getContext('2d')!
  const img = ctx.createImageData(G, G)
  for (let j = 0; j < G; j++) for (let i = 0; i < G; i++) {
    const k = j * G + i
    const x = (i + 0.5) / G * 2 - 1, y = (j + 0.5) / G * 2 - 1
    const inside = Math.hypot(x, y) < 0.98 ? 1 : 0
    const v = Math.max(0, Math.min(1.4, x0[k] * (1 - 0.25 * Math.min(1, sigma)) + sigma * noise[k] * 0.5)) * inside
    // light on film: red → orange → white
    img.data[k * 4] = Math.min(255, 40 + v * 300)
    img.data[k * 4 + 1] = Math.min(255, v * v * 120)
    img.data[k * 4 + 2] = Math.min(255, v * v * v * 60)
    img.data[k * 4 + 3] = inside ? 255 : 0
  }
  ctx.putImageData(img, 0, 0)
}

export interface DenoiseHandle { pass(): void }

export const Denoise = forwardRef<DenoiseHandle>(function Denoise(_, ref) {
  const a = useRef<HTMLCanvasElement>(null)
  const b = useRef<HTMLCanvasElement>(null)
  const la = useRef<HTMLSpanElement>(null)
  const lb = useRef<HTMLSpanElement>(null)
  const st = useRef({ t: 0, seed: 1, x0: null as Float32Array | null, noise: null as Float32Array | null })
  const draw = () => {
    const S = st.current
    if (!S.x0) S.x0 = smiley()
    if (!S.noise) S.noise = gauss(S.seed)
    paint(a.current!, S.x0, S.noise, SIGMAS[S.t])
    paint(b.current!, S.x0, S.noise, SIGMAS[S.t + 1])
    if (la.current) la.current.textContent = `noise ${SIGMAS[S.t].toFixed(2)}`
    if (lb.current) lb.current.textContent = `noise ${SIGMAS[S.t + 1].toFixed(2)}`
  }
  useEffect(draw, [])
  useImperativeHandle(ref, () => ({
    pass() {
      const S = st.current
      S.t++
      if (S.t >= SIGMAS.length - 1) { S.t = 0; S.seed++; S.noise = null }
      draw()
    },
  }))
  return (
    <div className={s.pair}>
      <div className={s.disc}>
        <canvas ref={a} width={G} height={G} />
        <span className={s.lbl}>Light in · <span ref={la} /></span>
      </div>
      <span className={s.arrow} aria-hidden="true">→</span>
      <div className={s.disc}>
        <canvas ref={b} width={G} height={G} />
        <span className={s.lbl}>Out, one pass later · <span ref={lb} /></span>
      </div>
    </div>
  )
})
