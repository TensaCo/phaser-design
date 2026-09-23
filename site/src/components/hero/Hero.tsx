'use client'
import dynamic from 'next/dynamic'
import { useEffect, useRef, useState } from 'react'
import { motion, useMotionValueEvent, useScroll, useTransform, useReducedMotion } from 'framer-motion'
import { heroState } from '@/lib/heroState'
import { Evidence } from '../Evidence'
import { REPO } from '@/data/evidence'
import { CountUp } from '../CountUp'
import s from './Hero.module.css'

const HeroScene = dynamic(() => import('./HeroScene'), { ssr: false, loading: () => null })

const fmt = new Intl.NumberFormat('en-US')

function useCounters() {
  const macs = useRef<HTMLSpanElement>(null)
  const bytes = useRef<HTMLSpanElement>(null)
  const trips = useRef<HTMLSpanElement>(null)
  const time = useRef<HTMLSpanElement>(null)
  const inputs = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    let raf = 0
    const tick = () => {
      if (macs.current) macs.current.textContent = fmt.format(Math.floor(heroState.macs))
      if (bytes.current) bytes.current.textContent = (heroState.bytes / 1024).toFixed(1)
      if (trips.current) trips.current.textContent = fmt.format(heroState.trips)
      if (time.current) time.current.textContent = (heroState.trips * 0.6673).toFixed(2)
      if (inputs.current) inputs.current.textContent = fmt.format(heroState.inputs)
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])
  return { macs, bytes, trips, time, inputs }
}

export function Hero() {
  const ref = useRef<HTMLElement>(null)
  const reduced = useReducedMotion() ?? false
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] })
  const [stage, setStage] = useState(0)
  const [active, setActive] = useState(true)
  const [manual, setManual] = useState<number | null>(null)
  const c = useCounters()

  useMotionValueEvent(scrollYProgress, 'change', (p) => {
    if (reduced || manual !== null) return
    const m = Math.min(1, Math.max(0, (p - 0.14) / 0.46))
    heroState.morph = m
    setStage(m < 0.05 ? 0 : m < 0.95 ? 1 : 2)
  })
  useEffect(() => {
    heroState.reduced = reduced
    heroState.running = !reduced
    if (reduced) { heroState.morph = 1; heroState.forceLap = 37; setStage(2) }
  }, [reduced])
  useEffect(() => {
    if (manual === null) return
    heroState.morph = manual
    setStage(manual < 0.5 ? 0 : 2)
  }, [manual])
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(([e]) => setActive(e.isIntersecting), { rootMargin: '100px' })
    io.observe(el)
    return () => io.disconnect()
  }, [])

  const factsOpacity = useTransform(scrollYProgress, [0.55, 0.72], [0, 1])
  const titleOpacity = useTransform(scrollYProgress, [0.0, 0.1, 0.62, 0.78], [1, 1, 1, 0.0])

  return (
    <section ref={ref} className={s.hero} data-reduced={reduced || undefined} aria-label="The mechanism">
      <div className={s.stage}>
        <div className={s.canvas} aria-hidden>
          <HeroScene active={active} />
        </div>
        <div className={s.grid} aria-hidden />

        <header className={s.bar}>
          <span className={s.mark}>PHASER</span>
          <span className="eyebrow">research preview · all results simulated</span>
          <a className={s.src} href={REPO} target="_blank" rel="noreferrer">view source ↗</a>
        </header>

        <motion.div className={s.copy} style={reduced ? undefined : { opacity: titleOpacity }}>
          <p className="eyebrow">A recurrent optical cavity</p>
          <h1 className={`serif ${s.h1}`}>
            The multiply is done<br />by light crossing a gap.
          </h1>
          <p className={s.lede}>
            PHASER is a loop of free-space optics. Every round trip
            <Evidence id="tripTime"> (0.667 ns)</Evidence>, diffraction and interference mix every pixel with every other,
            a static phase program on a spatial light modulator shapes the mix, and saturable gain supplies the nonlinearity.
            One lap of light is one compute step. No weights are fetched. The program is the geometry.
          </p>
        </motion.div>

        <div className={s.captions} aria-live="polite">
          <Caption on={stage === 0} k="01" title="Digital layer">
            64 × 64 weights. Each is fetched from memory and multiplied, one multiply-accumulate at a time.
            <span className={s.counter}>
              <b ref={c.macs}>0</b> MACs · <b ref={c.bytes}>0</b> KiB moved <i>(illustrative)</i>
            </span>
          </Caption>
          <Caption on={stage === 1} k="02" title="Same plane, different physics">
            The weight grid becomes the modulator's pixel grid. Propagation couples every pixel to every other at once. It is
            a structured transform set by one phase per pixel<Evidence id="structured" />, not an arbitrary matrix.
          </Caption>
          <Caption on={stage === 2} k="03" title="One round trip = one step">
            Heights are the simulated circulating field of the Exp. 15 reservoir, one frame per trip; an input is injected
            every 10 trips<Evidence id="inputRate" />.
            <span className={s.counter}>
              trip <b ref={c.trips}>0</b> · <b ref={c.time}>0.00</b> ns simulated · input <b ref={c.inputs}>0</b> · shown 1.7 × 10⁹× slower
            </span>
          </Caption>
        </div>

        <div className={s.toggle} role="group" aria-label="View">
          <button aria-pressed={stage === 0} onClick={() => setManual(0)}>digital</button>
          <button aria-pressed={stage === 2} onClick={() => setManual(1)}>PHASER</button>
          {manual !== null && !reduced && <button className={s.follow} onClick={() => setManual(null)}>follow scroll</button>}
        </div>

        <motion.dl className={s.facts} style={reduced ? undefined : { opacity: factsOpacity }}>
          <Fact id="tripTime" big={<CountUp to={0.667} decimals={3} />} unit="ns" label="per compute step (one round trip, 1.5 GHz)" />
          <Fact id="inputRate" big={<CountUp to={6.7} decimals={1} />} unit="ns" label="per input at 10 trips/input — 150 MHz streaming" />
          <Fact id="memory1e6" big={<>10<sup>6</sup></>} unit="trips" label="bits held, zero errors, in a static program" />
          <Fact id="nand" big={<>10<sup>5</sup></>} unit="trips" label="persistent NAND, checked every trip" />
        </motion.dl>

        <div className={s.scrollHint} aria-hidden>scroll</div>
      </div>
    </section>
  )
}

function Caption({ on, k, title, children }: { on: boolean; k: string; title: string; children: React.ReactNode }) {
  return (
    <div className={s.caption} data-on={on || undefined}>
      <span className={`mono ${s.k}`}>{k}</span>
      <div>
        <p className={s.ctitle}>{title}</p>
        <p className={s.cbody}>{children}</p>
      </div>
    </div>
  )
}

function Fact({ id, big, unit, label }: { id: Parameters<typeof Evidence>[0]['id']; big: React.ReactNode; unit: string; label: string }) {
  return (
    <div className={s.fact}>
      <dt className={`mono ${s.big}`}>
        <Evidence id={id}>
          {big}
          <span className={s.unit}>{unit}</span>
        </Evidence>
      </dt>
      <dd className={s.flabel}>{label}</dd>
    </div>
  )
}
