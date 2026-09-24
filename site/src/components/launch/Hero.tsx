'use client'
import dynamic from 'next/dynamic'
import { useEffect, useRef, useState } from 'react'
import s from './Hero.module.css'

const MachineCanvas = dynamic(() => import('../machine/MachineCanvas'), { ssr: false, loading: () => null })

/** real round trip of the modeled cavity (research/2026-09-14, Exp. 29: 6.7 ns per step = 10 trips) */
const REAL_TRIP_S = 0.667e-9

export function Hero() {
  const [slow, setSlow] = useState<string | null>(null)
  const steps = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    let raf = 0
    const tick = () => {
      raf = requestAnimationFrame(tick)
      const m = (window as unknown as { __machine?: { pulses: number; tripSeconds: number } }).__machine
      if (!m) return
      if (steps.current) steps.current.textContent = String(m.pulses).padStart(4, '0')
      if (!slow) setSlow(new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(m.tripSeconds / REAL_TRIP_S))
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [slow])

  return (
    <header className={s.hero}>
      <div className={s.canvas} aria-hidden="true" style={{ ['--poster' as string]: `url(${process.env.NEXT_PUBLIC_BASE_PATH ?? ''}/og.jpg)` }}><MachineCanvas /></div>
      <div className={s.top}>
        <span className={s.mark}>PHASER</span>
        <nav className={s.nav} aria-label="Sections">
          <a href="#economics">01 Economics</a>
          <a href="#world">02 The world</a>
          <a href="#light">03 Light</a>
        </nav>
      </div>
      <div className={s.claim}>
        <h1>
          <span className={`num ${s.big}`}>1,000×</span>
          <span className={s.line}>less energy per step than a GPU.<sup className="fn"><a href="#r1">1</a></sup></span>
        </h1>
        <p className={s.sub}>Every bounce of light is a computation.</p>
        <p className={s.note}>Modeled at one megapixel of optics · not yet built</p>
      </div>
      <div className={s.plate} aria-hidden="true">
        <div><span>Fig. 1</span><span>λ 650 nm</span></div>
        <div><span>Passes</span><span ref={steps}>0000</span></div>
        <div><span>Playback</span><span>{slow ? `${slow}× slower` : '—'}</span></div>
      </div>
      <a className={s.scroll} href="#economics"><span className="label">Why it matters</span><i /></a>
    </header>
  )
}
