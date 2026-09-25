// Experiment 33: per-trip loss budget of the ring and of the linear stack, including bulk glass absorption and residual
// surface reflectance of every transmissive element (core `slab` element), at 650 nm. For each scenario: element-by-element
// passive power transmission (uniform illumination), the product, and the simulated passive retention of the dominant
// cavity mode (power iteration, 1500 trips); their ratio is the aperture/diffraction loss (lens stops, absorbing window).
// Component values and sources are in C below (see research/notes/energy-per-multiply.md for the references).
// usage: npx vite-node 33-loss.ts → out/33/loss_budget.json
import { AssetStore } from '../../src/core/physics/assets'
import type { RunContext } from '../../src/core/physics/elements/element'
import type { OpticalElementSpec } from '../../src/core/physics/elements/types'
import { createField } from '../../src/core/physics/field/grid'
import { CompiledSystem, type PhysicsConfig } from '../../src/core/physics/system'
import { mulberry32, gaussian } from '../../src/core/common/random'
import { slmRing, stackCavity } from './arch'
import { OUT, writeJson } from './util'

/** Component values at 650 nm. [value, source]. "est." = engineering estimate, not a datasheet value. */
const C = {
  bk7_alpha: [0.21, 'SCHOTT N-BK7 datasheet: τi = 0.998 per 10 mm at 620–700 nm ⇒ α ≈ 0.2 /m (power)'],
  fs_alpha: [0.01, 'fused silica (Corning 7980): transmittance ≈ 100 % in the visible; 0.01 /m is an upper-bound est.'],
  host_alpha: [0.3, 'gain-crystal host passive loss 0.3 %/cm (est.; Pr:YLF passive loss not found in a datasheet)'],
  ar_vcoat: [0.0025, 'Thorlabs V-coat R < 0.25 % at the design wavelength'],
  ar_broad: [0.005, 'Thorlabs A-coat R_avg < 0.5 % (350–700 nm)'],
  ar_ibs: [0.001, 'ion-beam-sputtered V-coat R ≈ 0.1 % (vendor claims; est.)'],
  lcos_al: [0.79, 'Hamamatsu X15213-01 light utilisation 79 % at 633 nm (Holoeye PLUTO-2 VIS-014: 65 %; Meadowlark Al: 76–91 %)'],
  lcos_diel: [0.95, 'dielectric-mirror LCOS: Holoeye PLUTO-2 VIS-130 94 %; Meadowlark dielectric 92–98 % zeroth order'],
  plate_refl: [0.99, 'fabricated reflective phase plate (etched fused silica, HR back coating ≥ 99.5 %, AR front 0.1 %; est.)'],
  mirror_diel: [0.995, 'dielectric laser-line mirror > 99.5 % (EKSMA); 99.9 % for IBS mirrors (est.)'],
  mirror_ibs: [0.999, 'IBS dielectric mirror 99.9 % (est.)'],
  lc_ff_today: [0.55, 'Holoeye LC 2012 transmissive panel fill factor 55 % (black matrix absorbs the rest)'],
  lc_ff_best: [0.85, 'high-aperture transmissive LC panel fill factor 0.85 (est.)'],
  ito_pass: [0.98, 'two ITO electrodes, ≈ 1 % absorption each per pass (est.; ITO films 89–92 % T incl. reflection)'],
  lc_internal: [0.005, 'residual reflection at the internal glass/ITO/LC interfaces per pass (est.)'],
} as const
const v = (k: keyof typeof C) => C[k][0] as number

const slab = (id: string, t: number, alpha: number, R: number, n = 1.515, ng = 1.534): OpticalElementSpec =>
  ({ kind: 'slab', id, thickness: t, medium: { kind: 'custom', label: 'glass', refractiveIndex: n, groupIndex: ng, attenuationPerM: alpha }, surfaceReflectance: { front: R, back: R } })
const glassIds = (cfg: PhysicsConfig) => new Set(cfg.elements.filter((e) => e.kind === 'slab').map((e) => e.id))

type Cat = 'glass' | 'modulator' | 'mirrors' | 'input coupler' | 'output tap' | 'air'
function category(label: string, glass: Set<string>): Cat {
  const id = label.split(' ')[0]
  if (glass.has(id)) return 'glass'
  if (id === 'slm' || /^p\d/.test(id) || id === 'amp') return 'modulator'
  if (id === 'in') return 'input coupler'
  if (id === 'out') return 'output tap'
  if (id === 'propagate') return 'air'
  return 'mirrors' // fold, roof, end, lens curvature (transmission 1 unless given)
}

function analyse(name: string, cfg: PhysicsConfig, tapIds: string[], note: string) {
  const sys = new CompiledSystem(cfg, new AssetStore())
  const glass = glassIds(cfg)
  const budget = sys.powerBudget()
  const byCat: Record<string, number> = {}
  let prod = 1
  const kind = new Map(cfg.elements.map((e) => [e.id, e]))
  for (const b of budget) {
    const el = kind.get(b.label.split(' ')[0])
    // a lens's budget entry includes its stop (clear aperture vs window) under uniform light: keep only the spec
    // transmission (glass + coating) here; the stop is part of the simulated aperture/diffraction term
    if (el?.kind === 'slab') { // split bulk absorption from surface (coating) loss
      const bulk = Math.exp(-(el.medium.kind === 'custom' ? el.medium.attenuationPerM : 0) * el.thickness)
      byCat['glass bulk'] = (byCat['glass bulk'] ?? 1) * bulk
      byCat['glass surfaces'] = (byCat['glass surfaces'] ?? 1) * b.transmission / bulk
      prod *= b.transmission; continue
    }
    const t = el?.kind === 'lens' ? el.transmission.front : b.transmission
    const c = el?.kind === 'lens' ? 'glass surfaces' : category(b.label, glass)
    byCat[c] = (byCat[c] ?? 1) * t; prod *= t
  }
  // the stack's start coupler is both input port and output tap: count its loss as the tap
  if (tapIds.includes('in')) { byCat['output tap'] = byCat['input coupler']; delete byCat['input coupler'] }
  const ctx: RunContext = { cycle: 0, inputs: { take: () => null }, taps: { record: () => {} } }
  const r = mulberry32(5), f = createField(sys.grid)
  for (let i = 0; i < f.re.length; i++) { f.re[i] = gaussian(r); f.im[i] = gaussian(r) }
  let ret = 0
  for (let t = 0; t < 1500; t++) {
    let p0 = 0; for (let i = 0; i < f.re.length; i++) p0 += f.re[i] ** 2 + f.im[i] ** 2
    sys.roundTrip(f, ctx)
    let p1 = 0; for (let i = 0; i < f.re.length; i++) p1 += f.re[i] ** 2 + f.im[i] ** 2
    ret = p1 / p0; const s = 1 / Math.sqrt(p1); for (let i = 0; i < f.re.length; i++) { f.re[i] *= s; f.im[i] *= s }
  }
  // loss shares: −ln T_c / −ln R_total (additive in log space)
  const aperture = ret / prod
  const cats = { ...byCat, 'aperture/diffraction (simulated)': aperture }
  const L = -Math.log(ret)
  const share = Object.fromEntries(Object.entries(cats).map(([k, t]) => [k, -Math.log(t) / L]))
  const tap = 1 - (byCat['output tap'] ?? 1)
  const out = { name, note, retention: ret, loss: 1 - ret, elementProduct: prod, transmissionByCategory: cats, lossShare: share, tap,
    pumpOverhead: (1 - ret) / tap, t_rt: sys.timing().roundTripTime, budget }
  console.log(`${name.padEnd(34)} R ${ret.toFixed(4)}  loss ${(1 - ret).toFixed(4)}  tap ${tap.toFixed(3)}  (L/T ${((1 - ret) / tap).toFixed(2)})  t_rt ${(sys.timing().roundTripTime * 1e9).toFixed(3)} ns  ` +
    Object.entries(share).map(([k, s]) => `${k} ${(100 * s).toFixed(1)}%`).join(', '))
  return out
}

const RAND = { kind: 'random' as const, seed: 3, depth: 0.1 }
const ringBase = { n: 64, spp: 1, focal: 40e-3, inputFirst: true, mask: RAND }
const ringGlass = (ar: number, lensT = 4e-3) => [
  { spec: slab('gL1', lensT, v('bk7_alpha'), ar), after: 'lensR' },
  { spec: slab('gL2', lensT, v('bk7_alpha'), ar), after: 'lensL' },
  { spec: slab('gGain', 5e-3, v('host_alpha'), ar, 1.45, 1.47), after: 'slm' },
]
const results = [
  analyse('ring: as modelled (Exp. 15/29)', slmRing(ringBase), ['out'], 'arch.ts defaults: SLM 0.75, lenses 0.995, mirrors 0.995, in 2 %, tap 5 %; no explicit glass'),
  analyse('ring: today (Al LCOS, V-coat glass)', slmRing({ ...ringBase, losses: { slmR: v('lcos_al'), lensT: 1, foldR: v('mirror_diel') }, extra: ringGlass(v('ar_vcoat')) }), ['out'],
    'LCOS 79 % (incl. its cover glass), N-BK7 lenses 4 mm + gain host 5 mm with V-coat AR, dielectric folds 99.5 %'),
  analyse('ring: today, broadband AR 0.5 %', slmRing({ ...ringBase, losses: { slmR: v('lcos_al'), lensT: 1, foldR: v('mirror_diel') }, extra: ringGlass(v('ar_broad')) }), ['out'], 'as above with A-coat 0.5 %/surface'),
  analyse('ring: dielectric LCOS + IBS AR', slmRing({ ...ringBase, losses: { slmR: v('lcos_diel'), slmDead: v('lcos_diel'), lensT: 1, foldR: v('mirror_ibs'), inR: 0.99 }, extra: ringGlass(v('ar_ibs')) }), ['out'],
    'LCOS 95 %, AR 0.1 %, mirrors 99.9 %, input coupler 1 %'),
  analyse('ring: static reflective plate + IBS', slmRing({ ...ringBase, losses: { slmR: v('plate_refl'), slmDead: v('plate_refl'), lensT: 1, foldR: v('mirror_ibs'), inR: 0.99 }, extra: ringGlass(v('ar_ibs')) }), ['out'],
    'fabricated reflective phase plate 99 % instead of the powered SLM'),
]
// linear stack, 4 planes, 5 mm apart; the start coupler is input and output (tap 5 %); gain host passed twice per round trip
const lcdLoss = (ff: number) => ({ lcdT: ff * v('ito_pass'), lcdSurf: v('lc_internal') })
const lcdGlass = (ar: number) => (k: number) => slab(`g${k}`, 1.4e-3, v('bk7_alpha'), ar)
const gainHost = (ar: number) => slab('gGain', 10e-3, v('host_alpha'), 1 - (1 - ar) ** 2, 1.45, 1.47)
const stackBase = { n: 64, spp: 1, planes: 4 }
results.push(
  analyse('stack: as modelled (Exp. 30)', stackCavity(stackBase), ['in'], 'arch.ts stackCavity defaults: LC 0.97 + 0.25 % surface per pass, end 0.995, coupler 5 %'),
  analyse('stack: LC panels today (FF 0.55)', stackCavity({ ...stackBase, loss: { ...lcdLoss(v('lc_ff_today')), endR: v('mirror_diel') }, glass: lcdGlass(v('ar_vcoat')), gainGlass: gainHost(v('ar_vcoat')) }), ['in'],
    'transmissive LC panels: fill factor 0.55 (black matrix), 2 ITO, internal reflections, 2 × 0.7 mm substrates with V-coat, passed twice'),
  analyse('stack: LC panels, FF 0.85 (est.)', stackCavity({ ...stackBase, loss: { ...lcdLoss(v('lc_ff_best')), endR: v('mirror_diel') }, glass: lcdGlass(v('ar_vcoat')), gainGlass: gainHost(v('ar_vcoat')) }), ['in'], 'as above, fill factor 0.85'),
  analyse('stack: fabricated plates (IBS AR)', stackCavity({ ...stackBase, planeKind: 'plate', plateT: 1, loss: { endR: v('mirror_ibs') }, glass: (k) => slab(`g${k}`, 1e-3, v('fs_alpha'), v('ar_ibs'), 1.457, 1.47), gainGlass: gainHost(v('ar_ibs')) }), ['in'],
    'static etched fused-silica phase plates 1 mm, AR 0.1 %, IBS end mirror 99.9 %'),
  analyse('stack: plates + dielectric LCOS end', stackCavity({ ...stackBase, planeKind: 'plate', plateT: 1, loss: { endR: v('lcos_diel') }, glass: (k) => slab(`g${k}`, 1e-3, v('fs_alpha'), v('ar_ibs'), 1.457, 1.47), gainGlass: gainHost(v('ar_ibs')) }), ['in'],
    'as above with one programmable dielectric LCOS (95 %) as the end mirror'),
  analyse('stack: plates, 2× window (128²)', stackCavity({ ...stackBase, n: 128, planeKind: 'plate', plateT: 1, loss: { endR: v('mirror_ibs') }, glass: (k) => slab(`g${k}`, 1e-3, v('fs_alpha'), v('ar_ibs'), 1.457, 1.47), gainGlass: gainHost(v('ar_ibs')) }), ['in'],
    'as "fabricated plates" on a 2.56 mm window: how much of the aperture/diffraction loss is the finite simulated window'),
  analyse('stack: 8 fabricated plates', stackCavity({ ...stackBase, planes: 8, planeKind: 'plate', plateT: 1, loss: { endR: v('mirror_ibs') }, glass: (k) => slab(`g${k}`, 1e-3, v('fs_alpha'), v('ar_ibs'), 1.457, 1.47), gainGlass: gainHost(v('ar_ibs')) }), ['in'], '8 plates'),
)
writeJson(`${OUT}33/loss_budget.json`, { components: C, results })
