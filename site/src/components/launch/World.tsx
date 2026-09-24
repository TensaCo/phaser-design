import { LivingPhoto } from './LivingPhoto'
import s from './World.module.css'

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? ''
// IEA, Energy and AI (2025) + 2026 update: global data-centre electricity, TWh / yr (2030, 2035: base case)
const TWH = [
  { y: '2020', v: 269 },
  { y: '2024', v: 415 },
  { y: '2030', v: 945 },
  { y: '2035', v: 1193 },
]

export function World() {
  return (
    <section className={s.sec} id="world" aria-labelledby="world-h">
      <div className="wrap">
        <p className="eyebrow">02 / The world</p>
        <h2 id="world-h" className={s.h}>
          <span>AI isn’t running out of chips.</span>
          <span>It’s running out of electricity.</span>
        </h2>
        <figure className={s.plate}>
          <LivingPhoto src={`${BASE}/img/grid-night.jpg`} alt="A transmission tower and power-station cooling towers at night; the only colour is the red aviation lights." className={s.img} />
          <figcaption><span>Fig. 2</span><span>The grid at night. Its only red light is a warning.</span></figcaption>
        </figure>

        <div className={s.scale} role="img" aria-label="Data-centre electricity use: 269 TWh in 2020, 415 in 2024, 945 projected for 2030 and 1,193 for 2035.">
          {TWH.map((d) => (
            <div key={d.y} className={s.col} style={{ ['--v' as string]: d.v / 1193 }}>
              <span className={`num ${s.v}`}>{d.v.toLocaleString('en-US')}</span>
              <span className={s.y}>{d.y}{+d.y > 2025 ? ' · projected' : ''}</span>
            </div>
          ))}
        </div>
        <p className={s.scaleCap}>
          <span>Terawatt-hours a year used by the world’s data centres.<sup className="fn"><a href="#r4">4</a></sup></span>
          <span className={s.japan}>By 2030 that is more electricity than all of Japan uses.</span>
        </p>

        <div className={s.friction}>
          <div><span className="num">128<small>weeks</small></span><p>to get a large power transformer.<sup className="fn"><a href="#r5">5</a></sup></p></div>
          <div><span className="num">5<small>years+</small></span><p>typical wait to connect a new power plant to the US grid.<sup className="fn"><a href="#r6">6</a></sup></p></div>
          <div><span className="num">$400<small>B+</small></span><p>spent on AI infrastructure by five companies in 2025 alone.<sup className="fn"><a href="#r4">4</a></sup></p></div>
        </div>

        <p className={s.turn}>
          Every one of those watts ends as heat. Then more power is spent pumping the heat away.
          <span> The fix isn’t a bigger grid. It’s a cheaper step.</span>
        </p>
      </div>
    </section>
  )
}
