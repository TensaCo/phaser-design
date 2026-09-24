import { Carriers } from './Carriers'
import s from './Close.module.css'

export function Light() {
  return (
    <section className={s.sec} id="light" aria-labelledby="light-h">
      <div className="wrap">
        <p className="eyebrow">01 / The light</p>
        <h2 id="light-h" className={s.h}>
          <span>Intelligence runs on electrons.</span>
          <span className={s.dim}>Every one of them is paid for in heat.</span>
          <span className={s.red}>PHASER runs it on light.</span>
        </h2>
        <Carriers />
      </div>
    </section>
  )
}
