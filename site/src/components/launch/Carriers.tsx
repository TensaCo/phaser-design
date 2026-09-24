'use client'
import { useRef } from 'react'
import X from '@/data/exp29.json'
import { FieldVolume } from './FieldVolume'
import s from './Carriers.module.css'

// Exp. 29 scaling model, one step of a 135,000-neuron dense layer: energy per multiply–accumulate
const N = X.N as number[]
const I = N.findIndex((n) => n >= 135000)
const MACS = N[I] * N[I]
const GPU_PJ = ((X.series.digital_dense_gpu as number[])[I] / MACS) * 1e12
const LIGHT_PJ = ((X.series.optical_modeled_32 as number[])[I] / MACS) * 1e12

export function Carriers() {
  const hits = useRef<HTMLElement>(null)
  return (
    <div className={s.pair}>
      <figure>
        <div className={s.vol}><FieldVolume kind="electron" onEvent={(n) => { if (hits.current) hits.current.textContent = String(n).padStart(4, '0') }} /></div>
        <figcaption>
          <span className={s.big}>{GPU_PJ.toFixed(1)}<small>pJ</small></span>
          <span className={s.what}>per multiply in silicon, all of it heat. The electron scatters, stalls, and turns again: <b ref={hits}>0000</b></span>
        </figcaption>
      </figure>
      <figure>
        <div className={s.vol}><FieldVolume kind="photon" /></div>
        <figcaption>
          <span className={`${s.big} ${s.red}`}>{LIGHT_PJ.toFixed(3)}<small>pJ</small></span>
          <span className={s.what}>per multiply in PHASER, modeled. Light crosses the glass at c and loses nothing on the way.</span>
        </figcaption>
      </figure>
    </div>
  )
}
