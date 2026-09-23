'use client'
/**
 * Hero visual. 64 × 64 points are, at the same time, the weights of a digital 64 × 64 layer and the pixels of the PHASER
 * SLM plane. Digital: each weight is fetched from memory and multiplied in turn. PHASER: the whole plane is transformed
 * at once by one round trip of light. The field heights/colours are the actual simulated circulating field of the
 * Experiment 15 reservoir configuration (A_preset), one frame per round trip, with an input injected every 10 trips.
 */
import { Canvas, advance, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { heroState, BASE } from '@/lib/heroState'

const G = 64
const S = 0.052 // point spacing (world units)
const ATLAS_W = 1024, ATLAS_H = 640, COLS = 16
const LAP = 1.15 // seconds per displayed round trip

const vert = /* glsl */ `
attribute vec2 aIJ;
attribute float aW;
uniform float uMorph, uMix, uScan, uPix, uHas, uInject;
uniform sampler2D uField;
uniform vec2 uTileA, uTileB;
varying vec3 vColor;
varying float vA;
vec4 frame(vec2 tile) { return texture2D(uField, tile + (aIJ + 0.5) / vec2(${ATLAS_W}.0, ${ATLAS_H}.0)); }
void main() {
  float i = aIJ.x, j = aIJ.y;
  // staggered morph: rows sweep over from the top
  float m = smoothstep(0.0, 1.0, clamp(uMorph * 1.7 - (1.0 - j / 63.0) * 0.7, 0.0, 1.0));
  vec4 fa = frame(uTileA), fb = frame(uTileB);
  float I = pow(mix(fa.r, fb.r, uMix), 0.7) * uHas; // amplitude, gently compressed for display
  float ph = fb.g * 6.2831853;

  // digital: tilted weight matrix
  vec3 p0 = vec3((i - 31.5) * ${S}, (j - 31.5) * ${S}, 0.0);
  float c = cos(-1.05), s = sin(-1.05);
  p0 = vec3(p0.x, p0.y * c, p0.y * s);
  float row = abs(j - floor(uScan));
  float done = step(i, fract(uScan) * 64.0);
  float onRow = 1.0 - step(0.5, row);
  p0.y += onRow * 0.05 * done;

  // PHASER: SLM plane, height = field amplitude
  // the SLM plane faces the viewer; the ring closes behind it
  vec3 e1 = vec3(1.0, 0.0, 0.0);
  vec3 nrm = vec3(0.0, 0.0, 1.0);
  vec3 p1 = (i - 31.5) * ${S} * e1 + vec3(0.0, (j - 31.5) * ${S}, 0.0) + I * 0.95 * nrm;
  vec3 pos = mix(p0, p1, m);

  vec3 warm = vec3(1.0, 0.616, 0.36);
  vec3 cyan = vec3(0.373, 0.89, 0.94);
  vec3 violet = vec3(0.616, 0.55, 1.0);
  vec3 cd = vec3(0.92, 0.92, 0.9) * (0.10 + 0.34 * aW) + onRow * done * warm * 0.9 + onRow * (1.0 - done) * warm * 0.18;
  vec3 cp = mix(violet, cyan, 0.5 + 0.5 * cos(ph)) * (0.06 + 2.1 * I) + vec3(0.05) + uInject * warm * 0.25 * I;
  vColor = mix(cd, cp, m);
  vA = 1.0;

  vec4 mv = modelViewMatrix * vec4(pos, 1.0);
  gl_Position = projectionMatrix * mv;
  float sz = mix(1.35 + onRow * done * 1.4, 1.3 + 3.2 * I, m);
  gl_PointSize = uPix * sz * (6.0 / -mv.z);
}`

const frag = /* glsl */ `
varying vec3 vColor;
varying float vA;
void main() {
  float d = length(gl_PointCoord - 0.5);
  float a = smoothstep(0.5, 0.18, d) * vA;
  if (a < 0.01) discard;
  gl_FragColor = vec4(vColor * a, a);
}`

function useFieldTexture() {
  const tex = useMemo(() => {
    const t = new THREE.DataTexture(new Uint8Array(ATLAS_W * ATLAS_H * 4), ATLAS_W, ATLAS_H, THREE.RGBAFormat)
    t.minFilter = t.magFilter = THREE.NearestFilter
    t.needsUpdate = true
    return t
  }, [])
  const info = useRef({ trips: 0, loaded: false })
  useEffect(() => {
    let dead = false
    fetch(`${BASE}/field-apre.bin`)
      .then((r) => r.arrayBuffer())
      .then((buf) => {
        if (dead) return
        const src = new Uint8Array(buf)
        const trips = src.length / (G * G * 2)
        const dst = tex.image.data as Uint8Array
        for (let t = 0; t < trips; t++) {
          const tc = t % COLS, tr = Math.floor(t / COLS)
          for (let j = 0; j < G; j++) for (let i = 0; i < G; i++) {
            const k = 2 * (t * G * G + j * G + i)
            const o = 4 * ((tr * G + j) * ATLAS_W + tc * G + i)
            dst[o] = src[k]; dst[o + 1] = src[k + 1]; dst[o + 3] = 255
          }
        }
        tex.needsUpdate = true
        info.current = { trips, loaded: true }
      })
      .catch(() => {})
    return () => { dead = true }
  }, [tex])
  return { tex, info }
}

const tile = (t: number) => new THREE.Vector2(((t % COLS) * G) / ATLAS_W, (Math.floor(t / COLS) * G) / ATLAS_H)

/** Schematic ring (not to scale): SLM → lens → fold → out-coupler → lens → gain → in-coupler → SLM. */
const RING: [number, number, number][] = [
  [0, 0, 0], [1.9, 0, -1.9], [0, 0, -3.8], [-1.9, 0, -1.9], [0, 0, 0],
]
const ELEMENTS: { name: string; at: number }[] = [
  { name: 'lens', at: 0.1 }, { name: 'fold', at: 0.2 }, { name: 'out', at: 0.3 },
  { name: 'lens', at: 0.5 }, { name: 'gain', at: 0.83 }, { name: 'in', at: 0.92 },
]
function ringPoint(u: number, out: THREE.Vector3) {
  const segs = RING.length - 1
  const lens = RING.slice(0, -1).map((p, k) => Math.hypot(RING[k + 1][0] - p[0], RING[k + 1][2] - p[2]))
  const total = lens.reduce((a, b) => a + b, 0)
  let d = (((u % 1) + 1) % 1) * total
  for (let k = 0; k < segs; k++) {
    if (d <= lens[k]) {
      const f = d / lens[k]
      return out.set(RING[k][0] + (RING[k + 1][0] - RING[k][0]) * f, 0, RING[k][2] + (RING[k + 1][2] - RING[k][2]) * f)
    }
    d -= lens[k]
  }
  return out.set(0, 0, 0)
}

function label(text: string, color = '#b4b6ba') {
  const c = document.createElement('canvas')
  const px = 44
  const ctx = c.getContext('2d')!
  ctx.font = `500 ${px}px ui-monospace, "JetBrains Mono", monospace`
  const w = Math.ceil(ctx.measureText(text).width) + 16
  c.width = w; c.height = px + 16
  ctx.font = `500 ${px}px ui-monospace, "JetBrains Mono", monospace`
  ctx.fillStyle = color
  ctx.textBaseline = 'middle'
  ctx.fillText(text, 8, c.height / 2)
  const t = new THREE.CanvasTexture(c)
  t.colorSpace = THREE.SRGBColorSpace
  const m = new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false, opacity: 0 })
  const sp = new THREE.Sprite(m)
  const h = 0.1
  sp.scale.set((h * c.width) / c.height, h, 1)
  return sp
}

function Scene() {
  const { tex, info } = useFieldTexture()
  const gl = useThree((s) => s.gl)
  const camera = useThree((s) => s.camera)
  const pointer = useRef(new THREE.Vector2())
  const phaser = useRef<THREE.Group>(null)
  const ringMat = useRef<THREE.LineBasicMaterial>(null)
  const bankMat = useRef<THREE.PointsMaterial>(null)
  const streamRef = useRef<THREE.Points>(null)
  const trailRef = useRef<THREE.Points>(null)

  const { geo, mat } = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    const ij = new Float32Array(G * G * 2), w = new Float32Array(G * G), pos = new Float32Array(G * G * 3)
    let seed = 7
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)
    for (let j = 0; j < G; j++) for (let i = 0; i < G; i++) {
      const k = j * G + i
      ij[2 * k] = i; ij[2 * k + 1] = j
      w[k] = Math.abs(rnd() + rnd() + rnd() - 1.5) / 1.5
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    geo.setAttribute('aIJ', new THREE.BufferAttribute(ij, 2))
    geo.setAttribute('aW', new THREE.BufferAttribute(w, 1))
    geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 10)
    const mat = new THREE.ShaderMaterial({
      vertexShader: vert, fragmentShader: frag, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: {
        uMorph: { value: 0 }, uMix: { value: 1 }, uScan: { value: 0 }, uPix: { value: 1 }, uHas: { value: 0 }, uInject: { value: 0 },
        uField: { value: tex }, uTileA: { value: tile(0) }, uTileB: { value: tile(0) },
      },
    })
    return { geo, mat }
  }, [tex])

  // ring line + element labels
  const ring = useMemo(() => {
    const pts: THREE.Vector3[] = []
    const v = new THREE.Vector3()
    for (let k = 0; k <= 240; k++) pts.push(ringPoint(k / 240, v).clone())
    const g = new THREE.BufferGeometry().setFromPoints(pts)
    const ticks = ELEMENTS.map((e) => {
      const p = ringPoint(e.at, new THREE.Vector3())
      const sp = label(e.name)
      const ox = p.x, oz = p.z + 1.9, L = Math.hypot(ox, oz) || 1
      sp.position.set(p.x + (ox / L) * 0.3, 0.12, p.z + (oz / L) * 0.3)
      return { sp, p, e }
    })
    const tickGeo = new THREE.BufferGeometry()
    const tp: number[] = []
    for (const t of ticks) tp.push(t.p.x, -0.09, t.p.z, t.p.x, 0.09, t.p.z)
    tickGeo.setAttribute('position', new THREE.Float32BufferAttribute(tp, 3))
    return { g, ticks, tickGeo }
  }, [])

  // digital memory bank and weight stream
  const stream = useMemo(() => {
    const n = 140
    const g = new THREE.BufferGeometry()
    const p = new Float32Array(n * 3)
    const seedT = new Float32Array(n)
    for (let k = 0; k < n; k++) seedT[k] = Math.random()
    g.setAttribute('position', new THREE.BufferAttribute(p, 3))
    const bank = new THREE.BufferGeometry()
    const bp: number[] = []
    for (let j = 0; j < 64; j++) for (let c = 0; c < 6; c++) bp.push(-2.3 - c * 0.05, (j - 31.5) * S * Math.cos(-1.05), (j - 31.5) * S * Math.sin(-1.05))
    bank.setAttribute('position', new THREE.Float32BufferAttribute(bp, 3))
    return { g, seedT, n, bank }
  }, [])

  const trail = useMemo(() => {
    const n = 36
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3))
    const col = new Float32Array(n * 3)
    for (let k = 0; k < n; k++) { const a = (1 - k / n) ** 2; col[3 * k] = 0.37 * a + 0.2 * a; col[3 * k + 1] = 0.89 * a; col[3 * k + 2] = 0.94 * a }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3))
    return { g, n }
  }, [])

  useEffect(() => {
    const mv = (e: PointerEvent) => pointer.current.set((e.clientX / window.innerWidth) * 2 - 1, (e.clientY / window.innerHeight) * 2 - 1)
    window.addEventListener('pointermove', mv, { passive: true })
    return () => window.removeEventListener('pointermove', mv)
  }, [])

  const look = useRef(new THREE.Vector3(-0.3, -0.25, 0))
  const clock = useRef({ lap: 0, trip: 0, scan: 0, lastTrip: -1, shownTrip: 0, mixT: 1 })
  const v = useMemo(() => new THREE.Vector3(), [])

  useFrame((state, dtRaw) => {
    const dt = Math.min(dtRaw, 0.05)
    const m = heroState.morph
    const u = mat.uniforms
    const ck = clock.current
    u.uPix.value = gl.getPixelRatio() * (state.size.width < 700 ? 1.6 : 2.2)
    u.uMorph.value = m
    u.uHas.value = info.current.loaded ? 1 : 0

    // digital clock: one row of MACs per 60 ms
    if (m < 0.98 && heroState.running) {
      ck.scan = (ck.scan + dt * 12) % 64
      heroState.macs += dt * 12 * 64
      heroState.bytes += dt * 12 * 64 * 2
    }
    u.uScan.value = ck.scan

    // PHASER clock: one displayed round trip per LAP seconds
    if (m > 0.35 && heroState.running) ck.lap += dt / LAP
    if (heroState.forceLap !== null) ck.lap = heroState.forceLap
    const trips = info.current.trips || 1
    const t = Math.floor(ck.lap)
    if (t !== ck.lastTrip) {
      ck.lastTrip = t
      const shown = t % trips
      u.uTileA.value = tile(ck.shownTrip)
      u.uTileB.value = tile(shown)
      ck.shownTrip = shown
      ck.mixT = 0
      heroState.trips = t
      heroState.inputs = Math.floor(t / 10) + 1
    }
    ck.mixT = Math.min(1, ck.mixT + dt * 6)
    u.uMix.value = 1 - (1 - ck.mixT) ** 3
    const inPhase = (ck.lap % 1)
    u.uInject.value = ck.lastTrip % 10 === 0 ? Math.max(0, 1 - ck.mixT) : 0

    // ring + labels + pulse fade in with the morph
    const rv = THREE.MathUtils.smoothstep(m, 0.45, 0.85)
    if (ringMat.current) ringMat.current.opacity = 0.38 * rv
    for (const tk of ring.ticks) (tk.sp.material as THREE.SpriteMaterial).opacity = 0.9 * rv
    const tp = trail.g.attributes.position as THREE.BufferAttribute
    for (let k = 0; k < trail.n; k++) {
      ringPoint(inPhase - k * 0.004, v)
      tp.setXYZ(k, v.x, v.y, v.z)
    }
    tp.needsUpdate = true
    if (trailRef.current) (trailRef.current.material as THREE.PointsMaterial).opacity = rv

    // weight stream fades out with the morph
    const dv = 1 - THREE.MathUtils.smoothstep(m, 0.0, 0.4)
    if (bankMat.current) bankMat.current.opacity = 0.5 * dv
    const sp = stream.g.attributes.position as THREE.BufferAttribute
    const rowY = (Math.floor(ck.scan) - 31.5) * S
    const cc = Math.cos(-1.05), ss = Math.sin(-1.05)
    for (let k = 0; k < stream.n; k++) {
      const f = (stream.seedT[k] + state.clock.elapsedTime * 0.9) % 1
      // weights leave the memory bank and run along the active row to their multiplier
      const x0 = -2.3, x1 = (((stream.seedT[k] * 997) % 1) * 64 - 31.5) * S
      const y = rowY + 0.012
      sp.setXYZ(k, x0 + (x1 - x0) * f, y * cc + 0.02, y * ss)
    }
    sp.needsUpdate = true
    if (streamRef.current) (streamRef.current.material as THREE.PointsMaterial).opacity = 0.75 * dv

    // camera: from the tilted matrix view to a 3/4 view of the SLM plane and ring, with pointer parallax
    const wide = state.size.width > 860
    const shift = wide ? -1.25 : 0
    const cx = THREE.MathUtils.lerp(shift + 0.2, 2.2 + shift, m) + pointer.current.x * 0.25
    const cy = THREE.MathUtils.lerp(2.6, 0.75, m) - pointer.current.y * 0.18
    const cz = THREE.MathUtils.lerp(wide ? 8.2 : 10.5, wide ? 5.4 : 7.4, m)
    camera.position.lerp(v.set(cx, cy, cz), 0.08)
    look.current.lerp(v.set(THREE.MathUtils.lerp(shift - 0.1, shift - 0.15, m), THREE.MathUtils.lerp(-0.3, -0.05, m), THREE.MathUtils.lerp(0, -1.1, m)), 0.08)
    camera.lookAt(look.current)
  })

  return (
    <group>
      <points geometry={geo} material={mat} frustumCulled={false} />
      <group ref={phaser}>
        <lineLoop geometry={ring.g}>
          <lineBasicMaterial ref={ringMat} color="#9d8cff" transparent opacity={0} depthWrite={false} />
        </lineLoop>
        <lineSegments geometry={ring.tickGeo}>
          <lineBasicMaterial color="#ecebe6" transparent opacity={0.35} depthWrite={false} />
        </lineSegments>
        {ring.ticks.map((t, k) => <primitive key={k} object={t.sp} />)}
        <points ref={trailRef} geometry={trail.g} frustumCulled={false}>
          <pointsMaterial size={0.07} vertexColors transparent opacity={0} depthWrite={false} blending={THREE.AdditiveBlending} sizeAttenuation />
        </points>
      </group>
      <points geometry={stream.bank}>
        <pointsMaterial ref={bankMat} size={0.022} color="#ecebe6" transparent opacity={0.5} depthWrite={false} sizeAttenuation />
      </points>
      <points ref={streamRef} geometry={stream.g} frustumCulled={false}>
        <pointsMaterial size={0.03} color="#ff9d5c" transparent opacity={0.7} depthWrite={false} blending={THREE.AdditiveBlending} sizeAttenuation />
      </points>
    </group>
  )
}

export default function HeroScene({ active }: { active: boolean }) {
  useEffect(() => {
    // headless verification hook: /?debug exposes the state and a manual frame advance (hidden tabs do not animate)
    if (!location.search.includes('debug')) return
    const w = window as unknown as Record<string, unknown>
    w.__hero = heroState
    w.__advance = (n = 1) => { for (let i = 0; i < n; i++) advance(performance.now() + i * 16) }
  }, [])
  return (
    <Canvas
      frameloop={active ? 'always' : 'never'}
      dpr={[1, 1.75]}
      camera={{ position: [0, 1.1, 4.4], fov: 38, near: 0.05, far: 60 }}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      style={{ position: 'absolute', inset: 0 }}
    >
      <Scene />
    </Canvas>
  )
}
