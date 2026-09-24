import { Carriers } from './Carriers'
import CLIPS from '@/data/broll.json'
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

export function Footer() {
  return (
    <footer className={s.footer}>
      <div className="wrap">
        <div className={s.foot}><span>PHASER · optical compute</span><a href={`${process.env.NEXT_PUBLIC_BASE_PATH ?? ''}/notes/`}>Methods &amp; sources</a></div>
      </div>
    </footer>
  )
}

export function Receipts() {
  const R = [
    <><b>1,000× less energy per step.</b> Modeled, not built (Exp. 29, research/2026-09-14). One step of a 135,000-neuron dense layer: a GPU at 2 pJ per multiply–accumulate uses 36.6 mJ; PHASER on one 1080p modulator at 32 optical modes per neuron uses 0.037 mJ. Across 4–32 modes per neuron and layer sizes that fit one modulator the modeled gap is 490× to 31,000×. At today&apos;s simulated scale (4,096 modes) PHASER only matches an equally good digital system, and it has no advantage over sparse layers.</>,
    <><b>6.7 ns per step.</b> Simulated: the modeled ring has a 200 mm round-trip path (0.667 ns), drawn here folded between two mirrors 10 cm apart; one step is 10 round trips.</>,
    <><b>10 B steps per second.</b> Modeled: each wavefront completes a step every 6.7 ns (≈150 M steps/s). With 100 GHz modulators and detectors, wavefronts can be spaced 10 ps apart, so 0.667 ns / 10 ps ≈ 67 are in flight at once; 67 × 150 M ≈ 10 B steps/s. Assumes the gain medium and detectors keep up and that wavefronts do not cross-talk.</>,
    <><b>Denoising pass.</b> Illustration of a programmed pass: one deterministic diffusion step, x<sub>t−1</sub> = x<sub>0</sub> + (σ<sub>t−1</sub>/σ<sub>t</sub>)(x<sub>t</sub> − x<sub>0</sub>), for a model whose data is a single image. It shows what a pass computes; it is not a simulation of the optics.</>,
    <><b>128 weeks.</b> Wood Mackenzie (Aug 2025): power-transformer lead times of about 128 weeks in Q2 2025.</>,
    <><b>5 years+.</b> Lawrence Berkeley National Laboratory, <em>Queued Up</em> (2026 edition): the median time from grid-interconnection request to operation is over 5 years.</>,
    <><b>$400 B+.</b> IEA, <em>Energy and AI</em> (Apr 2025) and its 16 Apr 2026 update: the five largest tech companies spent over $400 B in 2025.</>,
    <><b>Footage.</b> Real b-roll from Pexels (Pexels License), Mixkit (free licence) and the US Senate Committee on Energy and Natural Resources (public domain). {(CLIPS as { attribution: string }[]).filter((c) => c.attribution).map((c) => c.attribution).join(' ')}</>,
    <><b>The machine.</b> The hero is a live 3-D wave simulation (FDTD) of a pinhole-fed cavity with seven phase-plate modulators, slowed about 2.7 billion times.</>,
  ]

  return (
    <main className={s.receipts}>
      <div className="wrap">
        <p className="eyebrow">Methods &amp; sources</p>
        <ol>{R.map((r, i) => <li key={i} id={`r${i + 1}`}>{r}</li>)}</ol>
        <div className={s.foot}><a href={`${process.env.NEXT_PUBLIC_BASE_PATH ?? ''}/`}>← PHASER</a><span>λ 650 nm</span></div>
      </div>
    </main>
  )
}
