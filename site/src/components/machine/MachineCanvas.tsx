'use client'
import { useEffect, useRef } from 'react'
import type { Machine } from './engine'

export interface MachineCanvasProps {
  frameX?: number
  frameY?: number
  distance?: number
  className?: string
  /** called every drawn frame with the live machine (e.g. to place annotation leaders) */
  onFrame?: (m: Machine) => void
  /** expose as window.__machine (the hero plate reads it) */
  global?: boolean
}

export default function MachineCanvas({ frameX, frameY, distance, className, onFrame, global = false }: MachineCanvasProps) {
  const cb = useRef(onFrame)
  cb.current = onFrame
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    let m: Machine | null = null
    let raf = 0
    let alive = true
    let last = performance.now()
    let visible = true
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
    io.observe(canvas)
    import('./engine').then(({ Machine }) => {
      if (!alive) return
      const box = canvas.getBoundingClientRect()
      const dpr = Math.min(window.devicePixelRatio || 1, 1.75)
      try {
        m = new Machine({ canvas, width: box.width, height: box.height, dpr, frameX, frameY, distance })
      } catch {
        // no WebGL2 / float render targets: show the poster frame instead
        canvas.parentElement?.setAttribute('data-fallback', '')
        canvas.style.display = 'none'
        return
      }
      if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
        // one still frame, mid-flight
        for (let i = 0; i < 90; i++) m.frame(1 / 60)
        return
      }
      if (global) (window as unknown as { __machine: Machine }).__machine = m
      const loop = (now: number) => {
        raf = requestAnimationFrame(loop)
        const dt = (now - last) / 1000
        last = now
        if (visible && m) { m.frame(dt); cb.current?.(m) }
      }
      raf = requestAnimationFrame(loop)
    })
    const onResize = () => {
      if (!m) return
      const box = canvas.getBoundingClientRect()
      m.resize(box.width, box.height, Math.min(window.devicePixelRatio || 1, 2))
    }
    const onMove = (e: PointerEvent) => m?.setPointer((e.clientX / window.innerWidth) * 2 - 1, (e.clientY / window.innerHeight) * 2 - 1)
    window.addEventListener('resize', onResize)
    window.addEventListener('pointermove', onMove)
    return () => {
      alive = false
      cancelAnimationFrame(raf)
      io.disconnect()
      window.removeEventListener('resize', onResize)
      window.removeEventListener('pointermove', onMove)
      m?.dispose()
    }
  }, [frameX, frameY, distance, global])
  return <canvas ref={ref} className={className} style={{ width: '100%', height: '100%', display: 'block' }} />
}
