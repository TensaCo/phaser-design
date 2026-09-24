import { Carriers } from './Carriers'
import s from './Close.module.css'

const REPO = 'https://github.com/JacobFV/phaser-design'

export function Close() {
  return (
    <section className={s.sec} id="light" aria-labelledby="close-h">
      <div className="wrap">
        <p className="eyebrow">03 / Light</p>
        <h2 id="close-h" className={s.h}>
          <span>Intelligence runs on electrons.</span>
          <span className={s.dim}>Every one of them is paid for in heat.</span>
          <span className={s.red}>PHASER runs it on light.</span>
        </h2>
        <Carriers />
        <p className={s.body}>
          Pushing charge through a wire costs energy every time. Light passing through glass doesn’t: it interferes with itself on the
          way through, and that interference is the arithmetic. PHASER only pays to keep the light going.
        </p>
        <div className={s.cta}>
          <a href={`${REPO}/blob/main/research/2026-09-14/REPORT.md`}>Read the research <span>↗</span></a>
          <a href={`${REPO}/tree/main/research/2026-09-14/out/29`}>See the energy model <span>↗</span></a>
        </div>
      </div>
    </section>
  )
}

export function Receipts() {
  const R = [
    <>Modeled, not built (Exp. 29, research/2026-09-14). One step of a 135,000-neuron dense layer: a GPU at 2 pJ per multiply–accumulate uses 36.6 mJ, and PHASER on one 1080p modulator at 32 optical modes per neuron uses 0.037 mJ, about 1,000× less. Across 4–32 modes per neuron and layer sizes that fit one modulator, the modeled gap is 490× to 31,000×. At today&apos;s simulated scale (4,096 modes) PHASER only matches an equally good digital system, and it has no advantage over sparse layers.</>,
    <>Simulated: one step is 10 round trips of 0.667 ns, which is 6.7 ns and about 150 million steps per second. The weights are fixed patterns in the modulators, so no weights move through memory.</>,
    <>Wood Mackenzie (Aug 2025): power-transformer lead times of about 128 weeks in Q2 2025.</>,
    <>Lawrence Berkeley National Laboratory, <em>Queued Up</em> (2026 edition): the median time from grid-interconnection request to operation is over 5 years.</>,
    <>IEA, <em>Energy and AI</em> (Apr 2025) and its 16 Apr 2026 update: the five largest tech companies spent over $400 B in 2025.</>,
    <>The photographs on this page are AI-generated illustrations, not documentary images.</>,
  ]

  return (
    <footer className={s.receipts}>
      <div className="wrap">
        <p className="label">Receipts</p>
        <ol>{R.map((r, i) => <li key={i} id={`r${i + 1}`}>{r}</li>)}</ol>
        <div className={s.foot}><span>PHASER · optical compute research</span><span>λ 650 nm</span></div>
      </div>
    </footer>
  )
}
