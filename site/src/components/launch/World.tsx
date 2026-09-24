'use client'
import { useEffect, useRef, useState } from 'react'
import CLIPS from '@/data/broll.json'
import s from './World.module.css'

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? ''
const HOLD = 6500

/** real b-roll; licences and credits in src/data/broll.json and public/video/broll/credits.json */
const REEL = CLIPS as { slug: string }[]

export function World() {
  const [i, setI] = useState(0)
  const vids = useRef<(HTMLVideoElement | null)[]>([])
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const t = setInterval(() => setI((v) => (v + 1) % REEL.length), HOLD)
    return () => clearInterval(t)
  }, [])
  useEffect(() => {
    vids.current.forEach((v, n) => {
      if (!v) return
      if (n === i) { v.currentTime = 0; v.play().catch(() => {}) } else if (n !== (i + REEL.length - 1) % REEL.length) v.pause()
    })
  }, [i])

  return (
    <section className={s.sec} id="world" aria-labelledby="world-h">
      <div className={s.stage}>
        <div className={s.reel} aria-hidden="true">
          {REEL.map((c, n) => {
            const cls = n === i ? s.live : n === (i + REEL.length - 1) % REEL.length ? s.prev : ''
            const near = n === i || n === (i + 1) % REEL.length || n === (i + REEL.length - 1) % REEL.length
            return (
              // src is set only for the current and neighbouring clips; setting it later starts the load
              <video key={c.slug} ref={(el) => { vids.current[n] = el }} className={cls} muted playsInline loop autoPlay={n === 0}
                preload={near ? 'auto' : 'none'} poster={`${BASE}/video/broll/${c.slug}.jpg`}
                src={near ? `${BASE}/video/broll/${c.slug}.mp4` : undefined} />
            )
          })}
        </div>
        <div className={`wrap ${s.over}`}>
          <div>
            <p className="eyebrow">03 / The world</p>
            <h2 id="world-h" className={s.h}>AI is running out of electricity.</h2>
          </div>
          <div className={s.friction}>
            <div><span className="num">128<small>weeks</small></span><p>to get a large power transformer.</p></div>
            <div><span className="num">5<small>years+</small></span><p>typical wait to connect a new power plant to the US grid.</p></div>
            <div><span className="num">$400<small>B+</small></span><p>spent on AI infrastructure by five companies in 2025 alone.</p></div>
          </div>
        </div>
      </div>
    </section>
  )
}
