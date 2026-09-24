'use client'
import { useMemo, useRef, useState } from 'react'
import { scaleLog } from 'd3-scale'
import { area, line } from 'd3-shape'
import X from '@/data/exp29.json'
import s from './Economics.module.css'

// Experiment 29 scaling model (research/2026-09-14/out/29): joules per step vs equivalent neurons in one dense layer
const N = X.N as number[]
const GPU = X.series.digital_dense_gpu as number[]
const LO = X.series.optical_modeled_4 as number[] // 4 optical modes worth one neuron (optimistic)
const HI = X.series.optical_modeled_32 as number[] // 32 modes per neuron (pessimistic)
const N_MIN = 64, N_MAX = 1.2e6
const idx = N.map((n, i) => i).filter((i) => N[i] >= N_MIN && N[i] <= N_MAX)
const SLM = [(1920 * 1080) / 32, (1920 * 1080) / 4] // one 1080p modulator, in equivalent neurons
const BRACKET_N = 135224 // inside the 1080p range, at the pessimistic 32 modes/neuron

const VW = 1100, VH = 470, M = { l: 56, r: 150, t: 28, b: 44 }
const x = scaleLog().domain([N_MIN, N_MAX]).range([M.l, VW - M.r])
const y = scaleLog().domain([1e-8, 3]).range([VH - M.b, M.t])

function joules(v: number) {
  const u: [number, string][] = [[1, 'J'], [1e-3, 'mJ'], [1e-6, 'µJ'], [1e-9, 'nJ']]
  const [k, name] = u.find(([k]) => v >= k) ?? [1e-9, 'nJ']
  const n = v / k
  return `${n >= 100 || Number.isInteger(n) ? n.toFixed(0) : n >= 10 ? n.toFixed(1) : n.toFixed(2)} ${name}`
}
const neurons = (n: number) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${Math.round(n / 1e3)}k` : `${Math.round(n)}`)

export function Economics() {
  const [hover, setHover] = useState<number | null>(null)
  const svg = useRef<SVGSVGElement>(null)
  const paths = useMemo(() => {
    const pts = idx.map((i) => ({ n: N[i], g: GPU[i], lo: LO[i], hi: HI[i] }))
    return {
      gpu: line<(typeof pts)[0]>().x((d) => x(d.n)).y((d) => y(d.g))(pts)!,
      hi: line<(typeof pts)[0]>().x((d) => x(d.n)).y((d) => y(d.hi))(pts)!,
      lo: line<(typeof pts)[0]>().x((d) => x(d.n)).y((d) => y(d.lo))(pts)!,
      band: area<(typeof pts)[0]>().x((d) => x(d.n)).y0((d) => y(d.lo)).y1((d) => y(d.hi))(pts)!,
      last: pts[pts.length - 1],
    }
  }, [])
  const bi = N.findIndex((n) => n >= BRACKET_N)
  const bx = x(N[bi])
  const ratio = GPU[bi] / HI[bi]

  const onMove = (e: React.PointerEvent) => {
    const r = svg.current!.getBoundingClientRect()
    const px = ((e.clientX - r.left) / r.width) * VW
    const n = x.invert(Math.min(Math.max(px, M.l), VW - M.r))
    let best = idx[0]
    for (const i of idx) if (Math.abs(Math.log(N[i] / n)) < Math.abs(Math.log(N[best] / n))) best = i
    setHover(best)
  }

  return (
    <section className={s.sec} id="economics" aria-labelledby="econ-h">
      <div className="wrap">
        <div className={s.head}>
          <p className={`label ${s.eyebrow}`}>01 · The economics</p>
          <h2 id="econ-h" className={s.h}>
            <span>Make the model 10× bigger.</span>
            <span>A GPU pays 100× the energy.</span>
            <span className={s.red}>Light pays 10×.<sup className="fn"><a href="#r2">2</a></sup></span>
          </h2>
          <p className={s.body}>
            In a GPU every connection is a multiplication, and every multiplication is paid for in electricity. Widen a layer and the
            bill grows with the <em>square</em>. In PHASER the connections happen inside the glass, so you pay only for the light.
          </p>
        </div>

        <figure className={s.fig}>
          <div className={s.legend} aria-hidden="true">
            <span><i className={s.swGpu} />GPU</span>
            <span><i className={s.swLight} />PHASER, modeled</span>
            <span className={s.legendNote}>Energy for one step of one dense layer · log–log</span>
          </div>
          <div className={s.scroller} ref={(el) => { if (el && el.scrollWidth > el.clientWidth) el.scrollLeft = el.scrollWidth }}>
          <svg ref={svg} viewBox={`0 0 ${VW} ${VH}`} className={s.svg} role="img"
            aria-label={`Energy per step against layer width. The GPU line rises with the square of width; PHASER rises linearly. At ${neurons(N[bi])} neurons the GPU uses about ${Math.round(ratio / 10) * 10} times more energy.`}
            onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
            <defs>
              <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(10,9,8,.09)" strokeWidth="1" />
              </pattern>
            </defs>
            {/* one 1080p modulator */}
            <rect x={x(SLM[0])} y={M.t} width={x(SLM[1]) - x(SLM[0])} height={VH - M.t - M.b} fill="url(#hatch)" />
            <text x={x(SLM[0]) + 8} y={M.t + 16} className={s.zone}>ONE 1080p MODULATOR</text>
            {/* grid */}
            {[1e-6, 1e-3, 1].map((v) => (
              <g key={v}>
                <line x1={M.l} x2={VW - M.r} y1={y(v)} y2={y(v)} className={s.grid} />
                <text x={M.l - 10} y={y(v) + 4} className={s.tick} textAnchor="end">{joules(v)}</text>
              </g>
            ))}
            {[100, 1e3, 1e4, 1e5, 1e6].map((v) => (
              <g key={v}>
                <line x1={x(v)} x2={x(v)} y1={VH - M.b} y2={VH - M.b + 5} className={s.axis} />
                <text x={x(v)} y={VH - M.b + 22} className={s.tick} textAnchor="middle">{neurons(v)}</text>
              </g>
            ))}
            <line x1={M.l} x2={VW - M.r} y1={VH - M.b} y2={VH - M.b} className={s.axis} />
            <text x={VW - M.r} y={VH - 4} className={s.tick} textAnchor="end">NEURONS IN THE LAYER →</text>
            {/* series */}
            <path d={paths.band} className={s.band} />
            <path d={paths.hi} className={s.lightEdge} />
            <path d={paths.lo} className={s.lightEdge} />
            <path d={paths.gpu} className={s.gpu} />
            {/* the gap */}
            <line x1={bx} x2={bx} y1={y(GPU[bi]) + 6} y2={y(HI[bi]) - 6} className={s.bracket} />
            <line x1={bx - 6} x2={bx + 6} y1={y(GPU[bi]) + 6} y2={y(GPU[bi]) + 6} className={s.bracket} />
            <line x1={bx - 6} x2={bx + 6} y1={y(HI[bi]) - 6} y2={y(HI[bi]) - 6} className={s.bracket} />
            <text x={bx + 16} y={y(GPU[bi]) + 58} className={s.gap}>~{Math.round(ratio / 100) * 100 >= 1000 ? '1,000' : Math.round(ratio)}×</text>
            <text x={bx + 18} y={y(GPU[bi]) + 80} className={s.gapNote}>LESS ENERGY PER STEP</text>
            {/* direct labels */}
            <text x={VW - M.r + 10} y={y(paths.last.g) + 4} className={s.dl}>GPU</text>
            <text x={VW - M.r + 10} y={y(paths.last.g) + 20} className={s.dlSub}>grows with width²</text>
            <text x={VW - M.r + 10} y={y(paths.last.hi) + 4} className={`${s.dl} ${s.dlRed}`}>PHASER</text>
            <text x={VW - M.r + 10} y={y(paths.last.hi) + 20} className={s.dlSub}>grows with width</text>
            {hover !== null && (
              <g pointerEvents="none">
                <line x1={x(N[hover])} x2={x(N[hover])} y1={M.t} y2={VH - M.b} className={s.cross} />
                <circle cx={x(N[hover])} cy={y(GPU[hover])} r={4.5} className={s.dotGpu} />
                <circle cx={x(N[hover])} cy={y(HI[hover])} r={4.5} className={s.dotLight} />
                <circle cx={x(N[hover])} cy={y(LO[hover])} r={4.5} className={s.dotLight} />
              </g>
            )}
          </svg>
          </div>
          {hover !== null && (
            <div className={s.tip} style={{ left: `${(x(N[hover]) / VW) * 100}%` }}>
              <div className={s.tipH}>{neurons(N[hover])} neurons</div>
              <div><i className={s.swGpu} />GPU <b>{joules(GPU[hover])}</b></div>
              <div><i className={s.swLight} />PHASER <b>{joules(LO[hover])} – {joules(HI[hover])}</b></div>
              <div className={s.tipR}>{GPU[hover] / HI[hover] >= 1 ? `${Math.round(GPU[hover] / HI[hover]).toLocaleString('en-US')}–${Math.round(GPU[hover] / LO[hover]).toLocaleString('en-US')}× less` : 'GPU cheaper at this size'}</div>
            </div>
          )}
          <figcaption className={s.cap}>
            Modeled, not measured: energy per step for one dense layer. PHASER’s band spans 4 to 32 optical modes per neuron.
            <details className={s.data}>
              <summary>Data</summary>
              <table>
                <thead><tr><th>Neurons</th><th>GPU</th><th>PHASER</th><th>Ratio</th></tr></thead>
                <tbody>
                  {[1e3, 1e4, 1e5, 1e6].map((n) => { const i = N.findIndex((v) => v >= n); return (
                    <tr key={n}><td>{neurons(N[i])}</td><td>{joules(GPU[i])}</td><td>{joules(LO[i])} – {joules(HI[i])}</td><td>{Math.round(GPU[i] / HI[i]).toLocaleString('en-US')}–{Math.round(GPU[i] / LO[i]).toLocaleString('en-US')}×</td></tr>
                  ) })}
                </tbody>
              </table>
            </details>
          </figcaption>
        </figure>

        <div className={s.stats}>
          <div><span className="num">6.7<small>ns</small></span><p>One step. Light crosses the stack and the answer is already there.<sup className="fn"><a href="#r3">3</a></sup></p></div>
          <div><span className="num">0<small>bytes</small></span><p>Weights fetched from memory per step. The weights are the glass.</p></div>
          <div><span className="num">150<small>M</small></span><p>Steps per second, from one stack, with no batching.<sup className="fn"><a href="#r3">3</a></sup></p></div>
        </div>
      </div>
    </section>
  )
}
