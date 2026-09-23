import { Timeline } from '../timeline/Timeline'
import { Branches } from './Branches'
import { Evidence } from '../Evidence'
import { REPO, REPORT } from '@/data/evidence'
import s from './Unlocks.module.css'

export function Unlocks() {
  return (
    <section className={s.section} aria-labelledby="speed-title">
      <div className={s.head}>
        <p className="eyebrow">03 · latent speed</p>
        <h2 id="speed-title" className={`serif ${s.h2}`}>The edge that holds up is time.</h2>
        <p className={s.lede}>
          The simulations show one clear advantage: latency. A recurrent step takes 6.7 ns<Evidence id="inputRate" />, the state never
          leaves the loop, and nothing waits on memory. The digital lanes below are stated assumptions for an equal-quality
          digital reservoir, not measurements.
        </p>
      </div>
      <Timeline />
      <div className={s.head2}>
        <p className="eyebrow">what one substrate supports today</p>
        <p className={s.lede2}>
          The same static cavity, with a different program or gain medium, is five different machines. Only the branches the
          simulations support are drawn, and the one that ends is part of the result.
        </p>
      </div>
      <Branches />
      <div className={s.close}>
        <p className={`serif ${s.statement}`}>
          The program is the geometry.<br />
          The clock is one lap of light.<br />
          <span>What it cannot do yet is written down too.</span>
        </p>
        <div className={s.ctas}>
          <a className={s.primary} href={REPORT} target="_blank" rel="noreferrer">read the research <span>↗</span></a>
          <a className={s.secondary} href={REPO} target="_blank" rel="noreferrer">explore the source <span>↗</span></a>
        </div>
      </div>
    </section>
  )
}
