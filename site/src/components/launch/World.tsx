'use client'
import { useEffect, useState } from 'react'
import s from './World.module.css'

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? ''
const SLIDES = [
  ['grid', 'Transmission tower and cooling towers at night'],
  ['nuclear', 'Nuclear power station with cooling towers'],
  ['lines', 'Transmission lines crossing a landscape in fog'],
  ['substation', 'High-voltage substation at night'],
  ['transformer', 'A power transformer on a heavy-haul trailer'],
  ['stacks', 'Gas power plant smokestacks'],
  ['turbine', 'Turbine hall of a power plant'],
  ['datacenter', 'Hot aisle of a data center'],
  ['hearing', 'An empty government hearing room'],
] as const
const HOLD = 4200

export function World() {
  const [i, setI] = useState(0)
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const t = setInterval(() => setI((v) => (v + 1) % SLIDES.length), HOLD)
    return () => clearInterval(t)
  }, [])
  return (
    <section className={s.sec} id="world" aria-labelledby="world-h">
      <div className="wrap">
        <p className="eyebrow">02 / The world</p>
        <h2 id="world-h" className={s.h}>AI is running out of electricity.</h2>
      </div>

      <div className={s.reel} aria-label="Power stations, transmission lines, transformers, data centers and a hearing room" role="img">
        {SLIDES.map(([k], n) => (
          <img key={k} src={`${BASE}/img/broll/${k}.jpg`} alt="" loading={n < 2 ? 'eager' : 'lazy'} decoding="async"
            className={n === i ? s.live : n === (i + SLIDES.length - 1) % SLIDES.length ? s.prev : ''} />
        ))}
      </div>

      <div className="wrap">
        <div className={s.friction}>
          <div><span className="num">128<small>weeks</small></span><p>to get a large power transformer.<sup className="fn"><a href="#r3">3</a></sup></p></div>
          <div><span className="num">5<small>years+</small></span><p>typical wait to connect a new power plant to the US grid.<sup className="fn"><a href="#r4">4</a></sup></p></div>
          <div><span className="num">$400<small>B+</small></span><p>spent on AI infrastructure by five companies in 2025 alone.<sup className="fn"><a href="#r5">5</a></sup></p></div>
        </div>
      </div>
    </section>
  )
}
