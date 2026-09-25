'use client'
import dynamic from 'next/dynamic'
import s from './Hero.module.css'

const MachineCanvas = dynamic(() => import('../machine/MachineCanvas'), { ssr: false, loading: () => null })

export function Hero() {
  return (
    <header className={s.hero}>
      <div className={s.canvas} aria-hidden="true" style={{ ['--poster' as string]: `url(${process.env.NEXT_PUBLIC_BASE_PATH ?? ''}/og.jpg)` }}><MachineCanvas global /></div>
      <div className={s.top}>
        <span className={s.mark}>PHASER</span>
        <nav className={s.nav} aria-label="Sections">
          <a href="#light">01 The light</a>
          <a href="#machine">02 The machine</a>
          <a href="#world">03 The world</a>
        </nav>
      </div>
      <div className={s.claim}>
        <p className={s.brand}>PHASER</p>
        <h1 className={s.h1}>
          <span>The fastest thing</span>
          <span>in the universe,</span>
          <span className={s.red}>put to work.</span>
        </h1>
        <p className={s.sub}>PHASER computes with light instead of electricity, so AI can keep growing without burning through the grid.</p>
      </div>
      <a className={s.scroll} href="#light"><span className="label">Why it matters</span><i /></a>
    </header>
  )
}
