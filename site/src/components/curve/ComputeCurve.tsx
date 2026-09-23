'use client'
import { useEffect, useMemo, useRef, useState } from 'react'
import { scaleLinear, scaleLog } from 'd3-scale'
import { area, curveMonotoneX, line } from 'd3-shape'
import { motion, useInView, useReducedMotion } from 'framer-motion'
import { ENERGY, EXP29_DATA, type EnergySeries } from '@/data/energy'
import { LEVEL_LABEL, type EvidenceLevel } from '@/data/evidence'
import { Evidence, LEVEL_COLOR, LevelTag } from '../Evidence'
import { joules, sci, sup, units, watts } from '@/lib/format'
import s from './ComputeCurve.module.css'

const LEVELS: EvidenceLevel[] = ['measured', 'modeled', 'theoretical']
const COLOR: Record<string, string> = {
  'digital-dense-gpu': 'var(--warm)', 'digital-dense-asic': 'var(--warm)', 'digital-sparse-asic': 'var(--warm)',
  'optical-4': 'var(--cyan)', 'optical-32': 'var(--cyan)', 'photon-floor': 'var(--violet)',
}
const DASH: Record<string, string | undefined> = { 'digital-dense-gpu': '6 4', 'digital-sparse-asic': '1.5 3.5', 'photon-floor': '3 4' }
const LADDER = [1, 10, 100, 1000, 1e6]

function useSize<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [size, set] = useState({ w: 960, h: 520 })
  useEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => set({ w: Math.round(e.contentRect.width), h: Math.round(e.contentRect.height) }))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [])
  return [ref, size] as const
}

/** nearest index in a sorted log grid */
const nearest = (arr: number[], v: number) => {
  let best = 0, bd = Infinity
  arr.forEach((a, i) => { const d = Math.abs(Math.log(a) - Math.log(v)); if (d < bd) { bd = d; best = i } })
  return best
}
const at = (sr: EnergySeries | undefined, i: number) => (sr ? sr.joulesPerStep[i] : NaN)

export function ComputeCurve() {
  const [level, setLevel] = useState<EvidenceLevel>('modeled')
  const [idx, setIdx] = useState(() => nearest(ENERGY.N, 1024))
  const [pIdx, setPIdx] = useState(() => ENERGY.quality.sweep.findIndex((p) => p.photons === ENERGY.quality.operatingPhotons))
  const [boxRef, { w, h }] = useSize<HTMLDivElement>()
  const inView = useInView(boxRef, { once: true, margin: '-15% 0px' })
  const reduced = useReducedMotion() ?? false

  return (
    <section className={s.section} aria-labelledby="curve-title">
      <div className={s.head}>
        <p className="eyebrow">02 · the compute curve</p>
        <h2 id="curve-title" className={`serif ${s.h2}`}>Parity today. An advantage only at scale.</h2>
        <p className={s.lede}>
          At the simulated size, one optical step costs about what an equal-quality digital reservoir costs
          <Evidence id="parity" />. Optical cost grows linearly with modes, while a dense digital recurrence grows as N². The gap
          opens only in that regime, and only if the optical modes keep their worth as the system grows.
        </p>
      </div>

      <div className={s.controls}>
        <div className={s.levels} role="radiogroup" aria-label="Evidence category">
          {LEVELS.map((l) => (
            <button key={l} role="radio" aria-checked={level === l} onClick={() => setLevel(l)} style={{ ['--c' as string]: LEVEL_COLOR[l] }}>
              [ {LEVEL_LABEL[l]} ]
            </button>
          ))}
        </div>
        <p className={s.levelNote}>
          {level === 'measured' && 'Simulated: reservoir quality vs photon budget, with loop and detector noise. No energy assumptions.'}
          {level === 'modeled' && 'Modeled: energy per input step from stated device assumptions. The quality anchors were simulated; nothing here is hardware.'}
          {level === 'theoretical' && 'Theoretical: shot-noise photon floor with perfect devices, and the switching energy of an optical logic cell.'}
        </p>
      </div>

      <div ref={boxRef} className={s.chart}>
        {level === 'modeled' && <ModeledChart w={w} h={h} idx={idx} setIdx={setIdx} inView={inView} reduced={reduced} />}
        {level === 'measured' && <QualityChart w={w} h={h} idx={pIdx} setIdx={setPIdx} inView={inView} reduced={reduced} />}
        {level === 'theoretical' && <FloorChart w={w} h={h} idx={idx} setIdx={setIdx} inView={inView} reduced={reduced} />}
      </div>

      {level === 'modeled' && <ModeledInspector idx={idx} setIdx={setIdx} />}
      {level === 'measured' && <QualityInspector idx={pIdx} />}
      {level === 'theoretical' && <FloorInspector idx={idx} />}
    </section>
  )
}

type ChartProps = { w: number; h: number; idx: number; setIdx: (i: number) => void; inView: boolean; reduced: boolean }

function useFrameScales(w: number, h: number, yDomain: [number, number], xDomain: [number, number]) {
  const narrow = w < 640
  const m = { l: narrow ? 44 : 62, r: narrow ? 12 : 200, t: 16, b: 44 }
  const x = scaleLog().domain(xDomain).range([m.l, w - m.r])
  const y = scaleLog().domain(yDomain).range([h - m.b, m.t]).clamp(true)
  return { m, x, y, narrow }
}

function DecadeGrid({ x, y, m, w, h, xLabel, yLabel, xFmt }: {
  x: ReturnType<typeof scaleLog<number>>; y: ReturnType<typeof scaleLog<number>>; m: { l: number; r: number; t: number; b: number }
  w: number; h: number; xLabel: string; yLabel: string; xFmt?: (v: number) => string
}) {
  const [x0, x1] = x.domain(), [y0, y1] = y.domain()
  const xs: number[] = [], ys: number[] = []
  for (let e = Math.ceil(Math.log10(x0)); e <= Math.floor(Math.log10(x1)); e++) xs.push(10 ** e)
  for (let e = Math.ceil(Math.log10(y0)); e <= Math.floor(Math.log10(y1)); e++) ys.push(10 ** e)
  const every = Math.ceil(ys.length / (h < 420 ? 6 : 9))
  return (
    <g>
      {ys.map((v, k) => (
        <g key={v}>
          <line x1={m.l} x2={w - m.r} y1={y(v)} y2={y(v)} className={s.gridline} />
          {k % every === 0 && <text x={m.l - 8} y={y(v)} className={s.tick} textAnchor="end" dominantBaseline="middle">10{sup(Math.log10(v))}</text>}
        </g>
      ))}
      {xs.map((v) => (
        <g key={v}>
          <line x1={x(v)} x2={x(v)} y1={m.t} y2={h - m.b} className={s.gridline} />
          <text x={x(v)} y={h - m.b + 17} className={s.tick} textAnchor="middle">{xFmt ? xFmt(v) : `10${sup(Math.log10(v))}`}</text>
        </g>
      ))}
      <text x={w - m.r} y={h - 8} className={s.axis} textAnchor="end">{xLabel}</text>
      <text x={m.l + 6} y={m.t + 12} className={s.axis}>{yLabel}</text>
    </g>
  )
}

function Draw({ d, color, width = 1.5, dash, delay = 0, inView, reduced }: { d: string; color: string; width?: number; dash?: string; delay?: number; inView: boolean; reduced: boolean }) {
  if (dash) return <motion.path d={d} fill="none" stroke={color} strokeWidth={width} strokeDasharray={dash} initial={{ opacity: 0 }} animate={{ opacity: inView ? 1 : 0 }} transition={{ duration: reduced ? 0 : 1, delay: reduced ? 0 : delay }} />
  return (
    <motion.path d={d} fill="none" stroke={color} strokeWidth={width}
      initial={{ pathLength: reduced ? 1 : 0 }} animate={{ pathLength: inView || reduced ? 1 : 0 }}
      transition={{ duration: reduced ? 0 : 1.8, delay: reduced ? 0 : delay, ease: [0.3, 0, 0.2, 1] }} />
  )
}

function ModeledChart({ w, h, idx, setIdx, inView, reduced }: ChartProps) {
  const N = ENERGY.N
  const { m, x, y, narrow } = useFrameScales(w, h, [1e-10, 1e7], [N[0], N[N.length - 1]])
  const ser = ENERGY.series.filter((z) => z.level === 'modeled')
  const get = (id: string) => ser.find((z) => z.id === id)!
  const asic = get('digital-dense-asic'), o4 = get('optical-4'), o32 = get('optical-32')
  const path = (v: number[]) => line<number>().defined((q) => isFinite(q) && q > 0).x((_, i) => x(N[i])).y((q) => y(q)).curve(curveMonotoneX)(v) ?? ''
  const wall = area<number>().x((_, i) => x(N[i])).y0(h - m.b).y1((q) => y(q)).curve(curveMonotoneX)(asic.joulesPerStep) ?? ''
  const band = area<number>().x((_, i) => x(N[i])).y0((_, i) => y(o32.joulesPerStep[i])).y1((q) => y(q)).curve(curveMonotoneX)(o4.joulesPerStep) ?? ''

  const target = ENERGY.nForRatio.find((r) => r.ratio === 1e6)!
  const slm = ENERGY.hardware[1], today = ENERGY.hardware[0]
  const ra = at(asic, idx), r4 = ra / at(o4, idx), r32 = ra / at(o32, idx)
  const cx = x(N[idx])

  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    setIdx(nearest(N, x.invert(Math.min(Math.max(e.clientX - r.left, m.l), w - m.r))))
  }

  return (
    <svg width={w} height={h} onPointerMove={onMove} role="img" aria-label="Modeled joules per input step versus equivalent digital reservoir units">
      <defs>
        <pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse">
          <line x1="0" y1="0" x2="0" y2="4" stroke="var(--warm)" strokeWidth="0.55" strokeOpacity="0.28" />
        </pattern>
      </defs>
      <DecadeGrid x={x} y={y} m={m} w={w} h={h} xLabel="equivalent digital reservoir units N (log)" yLabel="joules per input step (log)" />

      {/* hardware scale */}
      <rect x={x(today.N[0])} width={x(today.N[1]) - x(today.N[0])} y={m.t} height={h - m.t - m.b} className={s.hwToday} />
      <rect x={x(slm.N[0])} width={x(slm.N[1]) - x(slm.N[0])} y={m.t} height={h - m.t - m.b} className={s.hwSlm} />
      {!narrow && <text x={x(today.N[0]) + 4} y={h - m.b - 8} className={s.hwLabel}>simulated today</text>}
      {!narrow && <text x={x(slm.N[0]) + 4} y={h - m.b - 8} className={s.hwLabel}>a 1080p SLM</text>}

      <motion.path d={wall} fill="url(#hatch)" initial={{ opacity: 0 }} animate={{ opacity: inView || reduced ? 1 : 0 }} transition={{ duration: reduced ? 0 : 1.4, delay: reduced ? 0 : 1 }} />
      <motion.path d={band} fill="var(--cyan)" initial={{ opacity: 0 }} animate={{ opacity: inView || reduced ? 0.13 : 0 }} transition={{ duration: reduced ? 0 : 1.2, delay: reduced ? 0 : 1.3 }} />
      {ser.map((z, k) => (
        <Draw key={z.id} d={path(z.joulesPerStep)} color={COLOR[z.id]} dash={DASH[z.id]} width={z.id === 'digital-dense-asic' || z.id === 'optical-4' ? 1.7 : 1.1} delay={0.15 + k * 0.18} inView={inView} reduced={reduced} />
      ))}
      {!narrow && ser.map((z) => {
        const yy = y(z.joulesPerStep[z.joulesPerStep.length - 1])
        return <text key={z.id} x={w - m.r + 10} y={yy + (z.id === 'optical-32' ? -7 : z.id === 'optical-4' ? 7 : 0)} className={s.slabel} fill={COLOR[z.id]} dominantBaseline="middle">{z.label}</text>
      })}

      {/* anchors: modeled energy of simulated-quality systems */}
      {ENERGY.anchors.map((a) => {
        const xa = x(Math.sqrt(a.N[0] * a.N[1]))
        const c = a.kind === 'optical' ? 'var(--cyan)' : 'var(--warm)'
        return (
          <g key={a.id} className={s.anchor}>
            {a.N[1] > a.N[0] && <line x1={x(a.N[0])} x2={x(a.N[1])} y1={y(a.J.nominal)} y2={y(a.J.nominal)} stroke={c} />}
            <line x1={xa} x2={xa} y1={y(a.J.low)} y2={y(a.J.high)} stroke={c} />
            <rect x={xa - 3.5} y={y(a.J.nominal) - 3.5} width={7} height={7} fill="var(--bg)" stroke={c} transform={`rotate(45 ${xa} ${y(a.J.nominal)})`} />
          </g>
        )
      })}

      {/* the 10⁶× requirement */}
      {target.optimistic && (
        <g className={s.target}>
          <line x1={x(target.optimistic)} x2={x(target.optimistic)} y1={m.t} y2={h - m.b} />
          <circle cx={x(target.optimistic)} cy={y(at(o4, nearest(N, target.optimistic)))} r={4} />
          {!narrow && (
            <text x={x(target.optimistic) - 6} y={m.t + 30} textAnchor="end">
              <tspan x={x(target.optimistic) - 6}>10⁶× would need</tspan>
              <tspan x={x(target.optimistic) - 6} dy={14}>{sci(target.optimistic, 2)} units</tspan>
              <tspan x={x(target.optimistic) - 6} dy={14}>≥ 7.5×10⁸ modes</tspan>
            </text>
          )}
        </g>
      )}

      {/* inspection + ratio bracket */}
      <line x1={cx} x2={cx} y1={m.t} y2={h - m.b} className={s.cross} />
      {isFinite(r4) && (
        <g className={s.ratio}>
          <line x1={cx + 9} x2={cx + 9} y1={y(at(o4, idx))} y2={y(ra)} />
          <line x1={cx + 5} x2={cx + 13} y1={y(ra)} y2={y(ra)} />
          <line x1={cx + 5} x2={cx + 13} y1={y(at(o4, idx))} y2={y(at(o4, idx))} />
          <line x1={cx + 5} x2={cx + 13} y1={y(at(o32, idx))} y2={y(at(o32, idx))} strokeDasharray="2 2" />
          <text x={cx > (w - m.r) * 0.55 ? cx - 8 : cx + 17} textAnchor={cx > (w - m.r) * 0.55 ? 'end' : 'start'} y={(y(at(o4, idx)) + y(ra)) / 2} dominantBaseline="middle">{ratioText(r32, r4)}</text>
        </g>
      )}
    </svg>
  )
}

/** lo/hi = digital ÷ optical energy under the pessimistic / optimistic optical assumption, phrased from the optics' side */
export function ratioText(lo: number, hi: number) {
  const f = (r: number) => (r >= 1 ? `${sci(r, 2)}× cheaper` : `${sci(1 / r, 2)}× costlier`)
  if (lo >= 1 || hi < 1) {
    const a = lo >= 1 ? lo : 1 / lo, b = hi >= 1 ? hi : 1 / hi
    return `optics ${sci(Math.min(a, b), 2)}–${sci(Math.max(a, b), 2)}× ${lo >= 1 ? 'cheaper' : 'costlier'}`
  }
  return `optics ${f(lo)} … ${f(hi)}`
}

function ModeledInspector({ idx, setIdx }: { idx: number; setIdx: (i: number) => void }) {
  const N = ENERGY.N[idx]
  const rate = ENERGY.inputRateHz
  const ser = ENERGY.series.filter((z) => z.level === 'modeled')
  const asic = ser.find((z) => z.id === 'digital-dense-asic')
  const maxC = Math.max(...ENERGY.components.map((c) => c.high))
  const cx = scaleLog().domain([1e-13, maxC]).range([0, 100]).clamp(true)
  return (
    <div className={s.inspector}>
      <div className={s.icol}>
        <p className="eyebrow">inspecting</p>
        <p className={`mono ${s.ibig}`}>N ≈ {units(N)}</p>
        <LevelTag level="modeled" />
        <p className={s.small}>equivalent digital units; optical modes = 4…32 × N. Power at the {sci(rate / 1e6, 3)} MHz input rate (10 trips per input).</p>
        <p className="eyebrow" style={{ marginTop: 22 }}>what would it take?</p>
        <ul className={s.ladder}>
          <li><button onClick={() => setIdx(nearest(ENERGY.N, Math.sqrt(ENERGY.crossover.optimistic * ENERGY.crossover.pessimistic)))}>
            <b>1×</b><span>{units(ENERGY.crossover.optimistic)}–{units(ENERGY.crossover.pessimistic)}</span></button>
          </li>
          {ENERGY.nForRatio.map((r) => (
            <li key={r.ratio} data-target={r.ratio >= 1e6 || undefined}>
              <button onClick={() => r.optimistic && setIdx(nearest(ENERGY.N, r.optimistic))}>
                <b>{r.ratio >= 1e6 ? '10⁶×' : `${r.ratio}×`}</b>
                <span>{r.optimistic ? units(r.optimistic) : '—'}{r.pessimistic ? `–${units(r.pessimistic)}` : r.ratio >= 1e6 ? ' (only at 4 modes/unit)' : ''}</span>
              </button>
            </li>
          ))}
        </ul>
        <p className={s.small}>vs a dense 8-bit ASIC reservoir <Evidence id="crossover" />. The 10⁶× row is a <Evidence id="target1e6">target, not a result</Evidence>. Against a sparse digital reservoir the optics never wins<Evidence id="sparse" />.</p>
      </div>
      <div className={s.tables}>
        <table className={s.table}>
          <thead><tr><th /><th>J / step</th><th>power</th><th>PHASER vs this</th></tr></thead>
          <tbody>
            {ser.map((z) => {
              const v = at(z, idx)
              const o4 = at(ser.find((q) => q.id === 'optical-4'), idx), o32 = at(ser.find((q) => q.id === 'optical-32'), idx)
              return (
                <tr key={z.id} title={z.assumptions.join(' · ')}>
                  <th style={{ color: COLOR[z.id] }}>{z.label}</th>
                  <td>{joules(v)}</td>
                  <td>{watts(v * rate)}</td>
                  <td>{z.kind === 'digital' ? ratioText(v / o32, v / o4) : ''}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        <p className="eyebrow" style={{ marginTop: 26 }}>where the optical joules go · 4096-mode operating point</p>
        <div className={s.bars}>
          {ENERGY.components.map((c) => (
            <div key={c.id} className={s.bar}>
              <span className={s.blabel}>{c.label}</span>
              <span className={s.btrack}>
                <i style={{ left: `${cx(c.low)}%`, width: `${Math.max(0.6, cx(c.high) - cx(c.low))}%` }} />
                <b style={{ left: `${cx(c.nominal)}%` }} />
              </span>
              <span className={`mono ${s.bval}`}>{joules(c.nominal)}</span>
            </div>
          ))}
        </div>
        <p className={s.small}>
          Bars: low–high device assumptions, tick = nominal, log scale. Total {joules(ENERGY.anchors[0].J.nominal)} (range {joules(ENERGY.anchors[0].J.low)}–{joules(ENERGY.anchors[0].J.high)}).
          The pump dominates: power ∝ round-trip loss, so raising retention from 0.684 to 0.98 would cut it 16×. {asic && ''}
          <a href={EXP29_DATA} target="_blank" rel="noreferrer"> data ↗</a>
        </p>
      </div>
    </div>
  )
}

function QualityChart({ w, h, idx, setIdx, inView, reduced }: ChartProps) {
  const sw = ENERGY.quality.sweep
  const narrow = w < 640
  const m = { l: narrow ? 44 : 62, r: narrow ? 40 : 170, t: 16, b: 44 }
  const x = scaleLog().domain([sw[0].photons, sw[sw.length - 1].photons]).range([m.l, w - m.r])
  const yN = scaleLinear().domain([0, 1.2]).range([h - m.b, m.t])
  const yM = scaleLinear().domain([0, 40]).range([h - m.b, m.t])
  const ln = (f: (p: (typeof sw)[number]) => number, sc: (v: number) => number) => line<(typeof sw)[number]>().x((p) => x(p.photons)).y((p) => sc(f(p))).curve(curveMonotoneX)(sw) ?? ''
  const op = ENERGY.quality.operatingPhotons
  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    setIdx(nearest(sw.map((p) => p.photons), x.invert(Math.min(Math.max(e.clientX - r.left, m.l), w - m.r))))
  }
  const xs: number[] = []
  for (let e = 2; e <= 12; e++) xs.push(10 ** e)
  return (
    <svg width={w} height={h} onPointerMove={onMove} role="img" aria-label="Simulated reservoir quality versus circulating photons">
      {[0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2].map((v) => (
        <g key={v}>
          <line x1={m.l} x2={w - m.r} y1={yN(v)} y2={yN(v)} className={s.gridline} />
          <text x={m.l - 8} y={yN(v)} className={s.tick} textAnchor="end" dominantBaseline="middle" fill="var(--warm)">{v.toFixed(1)}</text>
        </g>
      ))}
      {[0, 10, 20, 30, 40].map((v) => <text key={v} x={w - m.r + 8} y={yM(v)} className={s.tick} dominantBaseline="middle" fill="var(--cyan)">{v}</text>)}
      {xs.map((v) => (
        <g key={v}>
          <line x1={x(v)} x2={x(v)} y1={m.t} y2={h - m.b} className={s.gridline} />
          <text x={x(v)} y={h - m.b + 17} className={s.tick} textAnchor="middle">10{sup(Math.log10(v))}</text>
        </g>
      ))}
      <text x={w - m.r} y={h - 8} className={s.axis} textAnchor="end">mean photons circulating in the loop (log)</text>
      <text x={m.l + 6} y={m.t + 12} className={s.axis} fill="var(--warm)">NARMA10 error (NMSE, lower is better)</text>
      {!narrow && <text x={w - m.r + 8} y={m.t - 2} className={s.axis} fill="var(--cyan)">memory capacity</text>}
      <line x1={m.l} x2={w - m.r} y1={yN(ENERGY.quality.clean.narma10)} y2={yN(ENERGY.quality.clean.narma10)} stroke="var(--warm)" strokeOpacity={0.35} strokeDasharray="2 4" />
      <line x1={m.l} x2={w - m.r} y1={yM(ENERGY.quality.clean.memoryCapacity)} y2={yM(ENERGY.quality.clean.memoryCapacity)} stroke="var(--cyan)" strokeOpacity={0.35} strokeDasharray="2 4" />
      {!narrow && <text x={w - m.r - 4} y={yM(ENERGY.quality.clean.memoryCapacity) - 6} className={s.hwLabel} textAnchor="end">noise-free</text>}
      <Draw d={ln((p) => p.narma10, yN)} color="var(--warm)" inView={inView} reduced={reduced} />
      <Draw d={ln((p) => p.memoryCapacity, yM)} color="var(--cyan)" delay={0.3} inView={inView} reduced={reduced} />
      {sw.map((p, i) => (
        <g key={p.photons}>
          <circle cx={x(p.photons)} cy={yN(p.narma10)} r={i === idx ? 3.4 : 1.8} fill="var(--warm)" />
          <circle cx={x(p.photons)} cy={yM(p.memoryCapacity)} r={i === idx ? 3.4 : 1.8} fill="var(--cyan)" />
        </g>
      ))}
      <g className={s.target} style={{ ['--tc' as string]: 'var(--fg-2)' }}>
        <line x1={x(op)} x2={x(op)} y1={m.t} y2={h - m.b} />
        {!narrow && <text x={x(op) - 8} y={m.t + 30} textAnchor="end"><tspan x={x(op) - 8}>operating point</tspan><tspan x={x(op) - 8} dy={14}>≈ 4.6 W circulating</tspan></text>}
      </g>
      <line x1={x(sw[idx].photons)} x2={x(sw[idx].photons)} y1={m.t} y2={h - m.b} className={s.cross} />
    </svg>
  )
}

function QualityInspector({ idx }: { idx: number }) {
  const p = ENERGY.quality.sweep[idx]
  const hv = 3.056e-19
  const circW = (p.photons * hv) / 6.673e-10
  return (
    <div className={s.inspector}>
      <div className={s.icol}>
        <p className="eyebrow">inspecting</p>
        <p className={`mono ${s.ibig}`}>10{sup(Math.round(Math.log10(p.photons)))} photons</p>
        <LevelTag level="measured" />
        <p className={s.small}>Simulated in the loop: amplified spontaneous emission every trip, shot and read noise at a 256-bin detector<Evidence id="photons" />.</p>
      </div>
      <div className={s.tables}>
        <table className={s.table}>
          <tbody>
            <tr><th>memory capacity</th><td>{p.memoryCapacity.toFixed(1)}</td><td className={s.dimcell}>noise-free {ENERGY.quality.clean.memoryCapacity.toFixed(1)}</td></tr>
            <tr><th>NARMA10 error</th><td>{p.narma10.toFixed(3)}</td><td className={s.dimcell}>noise-free {ENERGY.quality.clean.narma10.toFixed(3)}</td></tr>
            <tr><th>delayed XOR accuracy</th><td>{p.xor.toFixed(3)}</td><td className={s.dimcell}>noise-free {ENERGY.quality.clean.xor.toFixed(3)}</td></tr>
            <tr><th>photons detected per step</th><td>{sci(p.detectedPerStep, 2)}</td><td /></tr>
            <tr><th>circulating optical power</th><td>{watts(circW)}</td><td className={s.dimcell}>photons × hν ÷ 0.667 ns</td></tr>
          </tbody>
        </table>
        <p className={s.small}>
          Why so many photons: the input from 30 steps back survives only as a small, decayed part of the field, and resolving it
          takes a high signal-to-noise ratio. Tasks that need a shorter memory need orders of magnitude fewer photons.
        </p>
      </div>
    </div>
  )
}

function FloorChart({ w, h, idx, setIdx, inView, reduced }: ChartProps) {
  const N = ENERGY.N
  const { m, x, y } = useFrameScales(w, h, [1e-10, 1e-1], [N[0], N[N.length - 1]])
  const fl = ENERGY.series.find((z) => z.id === 'photon-floor')!
  const d = line<number>().x((_, i) => x(N[i])).y((q) => y(q)).curve(curveMonotoneX)(fl.joulesPerStep) ?? ''
  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    setIdx(nearest(N, x.invert(Math.min(Math.max(e.clientX - r.left, m.l), w - m.r))))
  }
  return (
    <svg width={w} height={h} onPointerMove={onMove} role="img" aria-label="Theoretical photon floor per input step">
      <DecadeGrid x={x} y={y} m={m} w={w} h={h} xLabel="equivalent digital units N (4 modes per unit, log)" yLabel="joules per input step (log)" />
      <Draw d={d} color="var(--violet)" inView={inView} reduced={reduced} />
      {w >= 640 && <text x={w - m.r + 10} y={y(fl.joulesPerStep[fl.joulesPerStep.length - 1])} className={s.slabel} fill="var(--violet)" dominantBaseline="middle">{fl.label}</text>}
      <line x1={x(N[idx])} x2={x(N[idx])} y1={m.t} y2={h - m.b} className={s.cross} />
      <circle cx={x(N[idx])} cy={y(fl.joulesPerStep[idx])} r={3.4} fill="var(--violet)" />
    </svg>
  )
}

function FloorInspector({ idx }: { idx: number }) {
  const fl = ENERGY.series.find((z) => z.id === 'photon-floor')!
  const r = ENERGY.nForRatio
  return (
    <div className={s.inspector}>
      <div className={s.icol}>
        <p className="eyebrow">inspecting</p>
        <p className={`mono ${s.ibig}`}>N ≈ {units(ENERGY.N[idx])}</p>
        <LevelTag level="theoretical" />
        <p className={`mono ${s.ibig}`} style={{ marginTop: 14 }}>{joules(fl.joulesPerStep[idx])}</p>
        <p className={s.small}>{fl.assumptions.join(' · ')}</p>
      </div>
      <div className={s.tables}>
        <p className={s.prose}>
          Even with perfect devices, only photons, the floor meets a dense 8-bit ASIC reservoir (modeled) at 10× near{' '}
          {units(r.find((q) => q.ratio === 10)?.floor ?? NaN)} units and at 10⁶× only near {units(r.find((q) => q.ratio === 1e6)?.floor ?? NaN)} units.
        </p>
        <p className={s.prose}>
          Persistent optical logic is not an energy path either. A saturable-gain cell 120 µm across switches at about{' '}
          <Evidence id="logicEnergy">14 nJ</Evidence>, where a CMOS gate needs ~10⁻¹⁶ J.
        </p>
      </div>
    </div>
  )
}
