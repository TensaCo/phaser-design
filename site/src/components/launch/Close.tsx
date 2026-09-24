import s from './Close.module.css'

const REPO = 'https://github.com/JacobFV/phaser-design'

export function Close() {
  return (
    <section className={s.sec} aria-labelledby="close-h">
      <div className={s.beam} aria-hidden="true"><i className={s.m} /><i className={s.pulse} /><i className={`${s.m} ${s.mr}`} /></div>
      <div className="wrap">
        <h2 id="close-h" className={s.h}>
          <span>Intelligence runs on electrons.</span>
          <span className={s.dim}>Every one of them is paid for in heat.</span>
          <span className={s.red}>PHASER runs it on light.</span>
        </h2>
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
    <>Modeled, not built (Exp. 29, research/2026-09-14). One dense recurrent layer: a GPU at 2 pJ per multiply–accumulate, against PHASER on one 1080p modulator (2.07 M pixels, which is 65 k–518 k neurons at 32 to 4 optical modes per neuron). The modeled gap is 490× to 31,000×. At 135 k neurons and 32 modes per neuron it is about 1,000×. At today’s simulated scale (4,096 modes) PHASER only matches an equally good digital system, and it has no advantage over sparse layers.</>,
    <>Same model. Dense digital energy grows with the square of the width. PHASER’s grows with the number of optical modes, plus a fixed 2.7 nJ per step, so at large widths 10× the width costs about 10× the energy.</>,
    <>Simulated: one step is 10 round trips of 0.667 ns, which is 6.7 ns and about 150 million steps per second. The weights are fixed patterns in the modulators, so no weights move through memory.</>,
    <>IEA, <em>Energy and AI</em> (Apr 2025) and its 16 Apr 2026 update. 269 TWh in 2020 and 415 TWh in 2024; base case 945 TWh in 2030 (&quot;slightly more than Japan’s total electricity consumption today&quot;) and 1,193 TWh in 2035. The five largest tech companies spent over $400 B in 2025.</>,
    <>Wood Mackenzie (Aug 2025): power-transformer lead times of about 128 weeks in Q2 2025.</>,
    <>Lawrence Berkeley National Laboratory, <em>Queued Up</em> (2026 edition): the median time from grid-interconnection request to operation is over 5 years.</>,
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
