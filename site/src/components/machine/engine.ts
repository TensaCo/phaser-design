/**
 * The hero machine: a scalar-wave simulation of the cavity, rendered as a 3-D instrument.
 *
 * Physics (2-D FDTD, leapfrog, on the GPU): a pinhole in the flat bottom mirror injects short 650 nm-like pulses; seven
 * phase-plate SLMs (slabs with a pixelated refractive-index profile) sit between it and a concave top mirror whose centre of
 * curvature is the pinhole, so every round trip spreads the light out and re-focuses it onto the pinhole (the readout).
 * The (x, z) field is symmetric in x and is revolved about the optical axis to draw the 3-D volume.
 */
import * as THREE from 'three'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'

// ---- simulation grid (cells) ----------------------------------------------------------------------------------------
const W = 320 // x: −160 … 160
const H = 800 // z: 0 (below bottom mirror) … 800
const R_CELLS = 128 // disc radius
const Z_BOT = 40 // bottom mirror surface
const Z_TOP = 760 // top mirror vertex
const L = Z_TOP - Z_BOT
const MIRROR_T = 10
const PIN_HALF = 4 // pinhole half-width
const C0 = 0.5 // courant number in vacuum
const LAMBDA = 12 // cells
const OMEGA = (2 * Math.PI * C0) / LAMBDA
const N_SLM = 7
const SLM_T = 10
export const SLM_Z = Array.from({ length: N_SLM }, (_, i) => Z_BOT + (L * (i + 1)) / (N_SLM + 1))
const ROUND_TRIP_STEPS = (2 * L) / C0
// synchronous pumping: a new pulse leaves the pinhole just as the previous one returns to it (slabs add group delay)
export const PULSE_PERIOD = Math.round(ROUND_TRIP_STEPS + (2 * N_SLM * SLM_T * 0.14) / C0)

// world units: disc radius = 1
const S = 1 / R_CELLS
export const WORLD = {
  radius: 1,
  zBot: Z_BOT * S,
  zTop: Z_TOP * S,
  height: H * S,
  halfWidth: (W / 2) * S,
  slmZ: SLM_Z.map((z) => z * S),
  slmT: SLM_T * S,
  mirrorT: MIRROR_T * S,
}

function hash(n: number) {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453
  return s - Math.floor(s)
}

/** refractive-index profile of SLM k at radius r (cells), pixelated */
function slmIndex(k: number, r: number) {
  const pix = 5
  const p = Math.floor(r / pix)
  const rc = (p + 0.5) * pix
  // mix of a weak lens term (alternating sign), concentric rings and per-pixel phase noise
  const lens = (k % 2 ? 1 : -1) * 0.35 * (rc / R_CELLS) ** 2
  const rings = 0.18 * Math.sin(rc * (0.035 + 0.011 * k) + k * 1.7)
  const noise = 0.1 * (hash(p * 13 + k * 101) - 0.5)
  const phase = lens + rings + noise // arbitrary units → Δn
  return 1.14 + 0.13 * Math.tanh(phase * 1.6)
}

function buildMedium() {
  const d = new Float32Array(W * H * 4)
  for (let j = 0; j < H; j++) {
    for (let i = 0; i < W; i++) {
      const x = i - W / 2 + 0.5
      const r = Math.abs(x)
      let n = 1
      let mask = 1
      let sponge = 0
      // side sponge: light spilling past the aperture is lost
      const edge = r - (R_CELLS + 12)
      if (edge > 0) sponge = Math.min(0.2, 0.0006 * edge * edge)
      // bottom sponge (fibre below the pinhole carries the readout away)
      if (j < 18) sponge = Math.max(sponge, 0.004 * (18 - j) ** 2 * 0.1)
      // bottom mirror (flat) with the pinhole
      if (j >= Z_BOT - MIRROR_T && j < Z_BOT && r <= R_CELLS + 4 && r > PIN_HALF) mask = 0
      // top mirror (concave, centre of curvature at the pinhole)
      const zs = Z_BOT + Math.sqrt(Math.max(0, L * L - x * x))
      if (j >= zs && j < zs + MIRROR_T + 2 && r <= R_CELLS + 4) mask = 0
      if (j >= zs + MIRROR_T + 2) sponge = 0.2
      // SLM slabs
      for (let k = 0; k < N_SLM; k++) {
        if (r <= R_CELLS && Math.abs(j - SLM_Z[k]) < SLM_T / 2) n = slmIndex(k, r)
      }
      const c = C0 / n
      const o = (j * W + i) * 4
      d[o] = c * c
      d[o + 1] = mask
      d[o + 2] = sponge
      d[o + 3] = n
    }
  }
  const t = new THREE.DataTexture(d, W, H, THREE.RGBAFormat, THREE.FloatType)
  t.needsUpdate = true
  return t
}

const quadVert = /* glsl */ `
out vec2 vUv;
void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`

const stepFrag = /* glsl */ `
precision highp float;
in vec2 vUv;
out vec4 o;
uniform sampler2D uState, uMedium;
uniform vec2 uTexel;
uniform float uSrc; // source amplitude this step
void main() {
  vec4 s = texture(uState, vUv);
  vec4 m = texture(uMedium, vUv);
  float u = s.r, up = s.g;
  float lap = texture(uState, vUv + vec2(uTexel.x, 0.)).r + texture(uState, vUv - vec2(uTexel.x, 0.)).r
            + texture(uState, vUv + vec2(0., uTexel.y)).r + texture(uState, vUv - vec2(0., uTexel.y)).r - 4. * u;
  float sg = m.b;
  float un = (2. * u - (1. - sg) * up + m.r * lap) / (1. + sg);
  un *= 0.99975; // bulk + mirror loss
  // soft source inside the fibre, just below the pinhole
  vec2 px = vUv / uTexel;
  float x = px.x - ${W / 2}.0;
  float z = px.y;
  un += uSrc * exp(-x * x / 6.0) * exp(-(z - ${Z_BOT - MIRROR_T - 4}.0) * (z - ${Z_BOT - MIRROR_T - 4}.0) / 4.0);
  un *= m.g;
  // energy accumulator: slow running mean of u²
  float e = s.b * 0.9992 + un * un * 0.004;
  o = vec4(un, u, e, 0.);
}`

// ---- 3-D rendering ------------------------------------------------------------------------------------------------
const volumeVert = /* glsl */ `
out vec3 vObj;
out vec3 vCamObj;
uniform vec3 uCamObj;
void main() {
  vObj = position;
  vCamObj = uCamObj;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`

const colorRamp = /* glsl */ `
vec3 ramp(float I) {
  // 650 nm on film: deep red → saturated red → orange → white core
  vec3 c = vec3(0.0);
  c += vec3(1.0, 0.035, 0.012) * (1.0 - exp(-I * 1.1));
  c += vec3(1.0, 0.28, 0.08) * (1.0 - exp(-I * 0.07));
  c += vec3(1.0, 0.86, 0.74) * (1.0 - exp(-I * 0.022));
  return c;
}`

const volumeFrag = /* glsl */ `
precision highp float;
in vec3 vObj;
in vec3 vCamObj;
out vec4 o;
uniform sampler2D uState;
uniform float uGain, uShell, uCut, uAcc;
uniform vec3 uCutN;
${colorRamp}
vec2 simUv(float r, float y) {
  return vec2((${W / 2}.0 + r * ${R_CELLS}.0) / ${W}.0, y * ${R_CELLS}.0 / ${H}.0);
}
vec4 samp(vec3 p) {
  float r = length(p.xz);
  return texture(uState, simUv(r, p.y));
}
void main() {
  vec3 ro = vCamObj;
  vec3 rd = normalize(vObj - vCamObj);
  // ray / cylinder (radius 1, y in [yb, yt])
  float a = dot(rd.xz, rd.xz), b = dot(ro.xz, rd.xz), c = dot(ro.xz, ro.xz) - 1.0;
  float h = b * b - a * c;
  if (h < 0.0) discard;
  h = sqrt(h);
  float t0 = (-b - h) / a, t1 = (-b + h) / a;
  float yb = ${(Z_BOT * S).toFixed(5)}, yt = ${(Z_TOP * S).toFixed(5)};
  float ty0 = (yb - ro.y) / rd.y, ty1 = (yt - ro.y) / rd.y;
  if (ty0 > ty1) { float tmp = ty0; ty0 = ty1; ty1 = tmp; }
  t0 = max(max(t0, ty0), 0.0);
  t1 = min(t1, ty1);
  // cutaway: keep the half-space dot(p, uCutN) < 0
  float cutSurface = 0.0;
  if (uCut > 0.5) {
    float dn = dot(rd, uCutN), pn = dot(ro, uCutN);
    float tc = -pn / dn;
    if (dn < 0.0) { if (tc > t0) { t0 = tc; cutSurface = 1.0; } }
    else { t1 = min(t1, tc); }
  }
  if (t1 <= t0) discard;
  const int N = 110;
  float dt = (t1 - t0) / float(N);
  vec3 acc = vec3(0.0);
  float jitter = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  for (int i = 0; i < N; i++) {
    vec3 p = ro + rd * (t0 + (float(i) + jitter) * dt);
    vec4 s = samp(p);
    float I = s.r * s.r * uShell; I = I * I / (I + 0.35) + s.b * uAcc;
    acc += ramp(I * uGain) * dt;
  }
  vec3 col = acc * 0.9;
  if (cutSurface > 0.5) {
    vec3 p = ro + rd * t0;
    vec4 s = samp(p);
    float I = s.r * s.r * uShell * 1.5 + s.b * uAcc * 2.0;
    col += ramp(I * uGain) * 0.5;
  }
  o = vec4(col, 1.0);
}`

const partVert = /* glsl */ `
out vec3 vN;
out vec3 vW;
out vec3 vObj;
void main() {
  vObj = position;
  vec4 w = modelMatrix * vec4(position, 1.0);
  vW = w.xyz;
  vN = normalize(mat3(modelMatrix) * normal);
  gl_Position = projectionMatrix * viewMatrix * w;
}`

/** machined parts: anodised rims, polished mirrors, SLM glass faces lit by the field that crosses them */
const partFrag = /* glsl */ `
precision highp float;
in vec3 vN;
in vec3 vW;
in vec3 vObj;
out vec4 o;
uniform sampler2D uState;
uniform float uKind; // 0 = SLM, 1 = mirror, 2 = rod / hardware
uniform float uY;    // world height of the part centre
uniform float uGain;
uniform vec3 uCam;
${colorRamp}
vec4 fieldAt(float r, float y) {
  return texture(uState, vec2((${W / 2}.0 + r * ${R_CELLS}.0) / ${W}.0, clamp(y, 0.01, ${(H * S - 0.01).toFixed(4)}) * ${R_CELLS}.0 / ${H}.0));
}
void main() {
  vec3 n = normalize(vN);
  vec3 v = normalize(uCam - vW);
  vec3 L1 = normalize(vec3(-0.6, 0.9, 0.35)); // soft studio strip, upper left
  float diff = max(dot(n, L1), 0.0);
  vec3 hlf = normalize(L1 + v);
  float fres = pow(1.0 - max(dot(n, v), 0.0), 4.0);
  float r = length(vW.xz);
  bool face = abs(n.y) > 0.9;
  // light arriving at this height, near the axis and at the rim
  vec4 fc = fieldAt(min(r, 0.99), vW.y);
  float eLocal = fc.b * 1.4 + fc.r * fc.r * 0.6;
  vec4 fr = fieldAt(0.35, vW.y);
  float eBand = fr.b * 1.4;
  vec3 col;
  float alpha = 1.0;
  if (uKind < 0.5) {
    if (face) {
      // SLM face: pixel grid over glass, lit by the wavefront crossing it
      vec2 g = abs(fract(vW.xz * 42.0) - 0.5);
      float grid = smoothstep(0.46, 0.5, max(g.x, g.y));
      float ringPhase = fract(r * 20.0);
      vec3 glass = vec3(0.006) + vec3(0.09) * pow(max(dot(n, hlf), 0.0), 80.0);
      col = glass * (1.0 - grid * 0.5) + ramp(eLocal * uGain) * (0.9 + 0.4 * grid);
      col += vec3(0.05) * fres;
      alpha = 0.22 + 0.5 * fres;
      // outer ring (clear aperture border)
      col += vec3(0.12) * smoothstep(0.985, 0.995, r) * (1.0 - smoothstep(0.995, 1.0, r));
    } else {
      // anodised rim: dark, fine lathe highlight, red bounce from the light inside
      float spec = pow(max(dot(n, hlf), 0.0), 24.0);
      col = vec3(0.012) + vec3(0.025) * diff + vec3(0.22) * spec + vec3(0.06) * fres;
      col += ramp(eBand * uGain) * 0.22;
    }
  } else if (uKind < 1.5) {
    if (face) {
      // polished mirror face: bright, takes the colour of the light on it
      float lathe = 0.5 + 0.5 * sin(r * 520.0);
      float spec = pow(max(dot(n, hlf), 0.0), 260.0) * (0.5 + 0.5 * lathe);
      col = vec3(0.012) + vec3(1.2) * spec + vec3(0.06) * fres + ramp(eLocal * uGain) * 1.6;
      // pinhole
      float ph = smoothstep(0.045, 0.03, r);
      col = mix(col, vec3(0.0), ph * step(uY, 1.0));
    } else {
      float spec = pow(max(dot(n, hlf), 0.0), 40.0);
      col = vec3(0.022) + vec3(0.04) * diff + vec3(0.8) * pow(max(dot(n, hlf), 0.0), 60.0) + vec3(0.08) * fres + ramp(eBand * uGain) * 0.25;
    }
  } else {
    // steel cage rod / fibre ferrule
    float spec = pow(max(dot(n, hlf), 0.0), 50.0);
    vec4 fy = fieldAt(0.9, vW.y);
    col = vec3(0.015) + vec3(0.03) * diff + vec3(0.5) * spec + vec3(0.05) * fres + ramp(fy.b * 1.4 * uGain) * 0.05;
  }
  o = vec4(col, alpha);
}`

const gradeFrag = /* glsl */ `
uniform sampler2D tDiffuse;
uniform float uTime;
uniform vec2 uRes;
varying vec2 vUv;
void main() {
  vec3 c = texture2D(tDiffuse, vUv).rgb;
  // vignette + grain (darkroom print)
  vec2 q = vUv - 0.5;
  q.x *= uRes.x / uRes.y;
  c *= 1.0 - 0.55 * smoothstep(0.35, 1.05, length(q));
  float g = fract(sin(dot(vUv * uRes + fract(uTime) * 91.7, vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
  c += g * 0.014;
  gl_FragColor = vec4(c, 1.0);
}`

export interface MachineOptions {
  canvas: HTMLCanvasElement
  /** css pixels */
  width: number
  height: number
  dpr: number
  /** horizontal placement of the stack in the frame: −1 left … 1 right */
  frameX?: number
  cutaway?: boolean
}

export class Machine {
  renderer: THREE.WebGLRenderer
  scene = new THREE.Scene()
  camera: THREE.PerspectiveCamera
  composer: EffectComposer
  private simScene = new THREE.Scene()
  private simCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1)
  private rt: THREE.WebGLRenderTarget[]
  private stepMat: THREE.ShaderMaterial
  private volMat: THREE.ShaderMaterial
  private partMats: THREE.ShaderMaterial[] = []
  private grade: ShaderPass
  private bloom: UnrealBloomPass
  private rig = new THREE.Group()
  private glint!: THREE.Sprite
  private stepN = 0
  private cur = 0
  private t = 0
  private pointer = new THREE.Vector2()
  private pointerS = new THREE.Vector2()
  opts: MachineOptions
  /** pulses injected so far */
  pulses = 0
  stepsPerSecond = 1700
  get tripSeconds() { return PULSE_PERIOD / this.stepsPerSecond }

  constructor(opts: MachineOptions) {
    this.opts = opts
    const r = new THREE.WebGLRenderer({ canvas: opts.canvas, antialias: true, powerPreference: 'high-performance' })
    r.setPixelRatio(opts.dpr)
    r.setSize(opts.width, opts.height, false)
    r.setClearColor(0x070606, 1)
    this.renderer = r
    if (!r.capabilities.isWebGL2 || !r.extensions.has('EXT_color_buffer_float')) {
      r.dispose()
      throw new Error('float render targets unavailable')
    }

    // ---- simulation ----
    const rtOpts = { type: THREE.FloatType, format: THREE.RGBAFormat, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: false, wrapS: THREE.ClampToEdgeWrapping, wrapT: THREE.ClampToEdgeWrapping }
    this.rt = [new THREE.WebGLRenderTarget(W, H, rtOpts), new THREE.WebGLRenderTarget(W, H, rtOpts)]
    const medium = buildMedium()
    medium.minFilter = medium.magFilter = THREE.NearestFilter
    this.stepMat = new THREE.ShaderMaterial({
      glslVersion: THREE.GLSL3,
      vertexShader: quadVert,
      fragmentShader: stepFrag,
      uniforms: { uState: { value: null }, uMedium: { value: medium }, uTexel: { value: new THREE.Vector2(1 / W, 1 / H) }, uSrc: { value: 0 } },
    })
    this.simScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.stepMat))
    r.setClearColor(0x000000, 0)
    for (const t of this.rt) { r.setRenderTarget(t); r.clear() }
    r.setRenderTarget(null)
    r.setClearColor(0x070606, 1)

    // ---- scene ----
    this.camera = new THREE.PerspectiveCamera(22, opts.width / opts.height, 0.1, 100)
    this.scene.add(this.rig)
    const yMid = (WORLD.zBot + WORLD.zTop) / 2
    this.rig.position.y = -yMid

    this.volMat = new THREE.ShaderMaterial({
      glslVersion: THREE.GLSL3,
      vertexShader: volumeVert,
      fragmentShader: volumeFrag,
      uniforms: { uState: { value: null }, uCamObj: { value: new THREE.Vector3() }, uGain: { value: 2.2 }, uShell: { value: 110 }, uAcc: { value: 0.12 }, uCut: { value: opts.cutaway ? 1 : 0 }, uCutN: { value: new THREE.Vector3(0, 0, 1) } },
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.BackSide,
    })
    const vol = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, WORLD.zTop - WORLD.zBot, 64, 1, false), this.volMat)
    vol.position.y = yMid
    vol.geometry.translate(0, 0, 0)
    // the volume shader works in rig-object space (y from 0); bake the offset into the geometry instead
    vol.position.y = 0
    vol.geometry.translate(0, yMid, 0)
    vol.renderOrder = 2
    this.rig.add(vol)

    const mkMat = (kind: number, y: number, transparent = false) => {
      const m = new THREE.ShaderMaterial({
        glslVersion: THREE.GLSL3,
        vertexShader: partVert,
        fragmentShader: partFrag,
        uniforms: { uState: { value: null }, uKind: { value: kind }, uY: { value: y }, uGain: { value: 1 }, uCam: { value: new THREE.Vector3() } },
        transparent,
        depthWrite: !transparent,
      })
      this.partMats.push(m)
      return m
    }
    // SLMs: glass disc + anodised ring
    for (const z of WORLD.slmZ) {
      const glass = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, WORLD.slmT, 128, 1, false), mkMat(0, z, true))
      glass.position.y = z
      glass.renderOrder = 3
      this.rig.add(glass)
      const ring = new THREE.Mesh(ringGeometry(1.0, 1.05, WORLD.slmT * 1.5), mkMat(0, z))
      ring.position.y = z
      this.rig.add(ring)
    }
    // mirrors
    const mb = new THREE.Mesh(ringGeometry(0.0, 1.1, WORLD.mirrorT * 2.8, 0.034), mkMat(1, WORLD.zBot))
    mb.position.y = WORLD.zBot - WORLD.mirrorT * 1.4
    this.rig.add(mb)
    const mt = new THREE.Mesh(ringGeometry(0.0, 1.1, WORLD.mirrorT * 2.8), mkMat(1, WORLD.zTop))
    mt.position.y = WORLD.zTop + WORLD.mirrorT * 1.4
    this.rig.add(mt)
    // cage rods
    const rodLen = WORLD.zTop - WORLD.zBot + 0.9
    for (let k = 0; k < 4; k++) {
      // square cage, turned so that no rod crosses the optical axis from the default camera azimuth (0.55 rad)
      const a = Math.PI / 4 - 0.55 + (k * Math.PI) / 2
      const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, rodLen, 16), mkMat(2, 0))
      rod.position.set(Math.cos(a) * 1.16, yMid, Math.sin(a) * 1.16)
      this.rig.add(rod)
    }
    // fibre ferrule under the pinhole
    const fer = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.7, 24), mkMat(2, 0))
    fer.position.y = WORLD.zBot - WORLD.mirrorT * 2.4 - 0.35
    this.rig.add(fer)
    const fib = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 3, 12), mkMat(2, 0))
    fib.position.y = WORLD.zBot - WORLD.mirrorT * 2.4 - 2.0
    this.rig.add(fib)

    // injector / readout glint at the pinhole
    const gc = document.createElement('canvas')
    gc.width = gc.height = 64
    const g2 = gc.getContext('2d')!
    const grad = g2.createRadialGradient(32, 32, 0, 32, 32, 32)
    grad.addColorStop(0, 'rgba(255,240,230,1)')
    grad.addColorStop(0.12, 'rgba(255,60,30,0.9)')
    grad.addColorStop(0.4, 'rgba(255,30,10,0.18)')
    grad.addColorStop(1, 'rgba(255,20,0,0)')
    g2.fillStyle = grad
    g2.fillRect(0, 0, 64, 64)
    this.glint = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(gc), blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, transparent: true }))
    this.glint.position.set(0, WORLD.zBot + 0.005, 0)
    this.glint.scale.setScalar(0.22)
    this.glint.renderOrder = 5
    this.rig.add(this.glint)

    // ---- post ----
    this.composer = new EffectComposer(r, new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType }))
    this.composer.setPixelRatio(opts.dpr)
    this.composer.setSize(opts.width, opts.height)
    this.composer.addPass(new RenderPass(this.scene, this.camera))
    this.bloom = new UnrealBloomPass(new THREE.Vector2(opts.width, opts.height), 0.7, 0.12, 0.6)
    // keep the glow tight: the wide mips wash the whole frame when a pulse is large
    ;(this.bloom as unknown as { compositeMaterial: THREE.ShaderMaterial }).compositeMaterial.uniforms.bloomFactors.value = [1.0, 0.75, 0.32, 0.1, 0.03]
    this.composer.addPass(this.bloom)
    this.grade = new ShaderPass({ uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uRes: { value: new THREE.Vector2(opts.width * opts.dpr, opts.height * opts.dpr) } }, vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }', fragmentShader: gradeFrag })
    this.composer.addPass(this.grade)
    this.composer.addPass(new OutputPass())
    this.layout()
  }

  setPointer(x: number, y: number) { this.pointer.set(x, y) }

  resize(width: number, height: number, dpr: number) {
    this.opts = { ...this.opts, width, height, dpr }
    this.renderer.setPixelRatio(dpr)
    this.renderer.setSize(width, height, false)
    this.composer.setPixelRatio(dpr)
    this.composer.setSize(width, height)
    ;(this.grade.uniforms.uRes.value as THREE.Vector2).set(width * dpr, height * dpr)
    this.layout()
  }

  private layout() {
    const { width, height } = this.opts
    this.camera.aspect = width / height
    this.camera.updateProjectionMatrix()
  }

  private wave(n: number) {
    // a pulse every 2 round trips; each pulse has its own amplitude (the "input")
    const period = PULSE_PERIOD
    const k = Math.floor(n / period)
    const tt = n - k * period - 130
    const env = tt < -200 || tt > 200 ? 0 : Math.exp(-(tt * tt) / (2 * 24 * 24))
    const amp = 0.45 + 0.35 * hash(k * 7.1)
    return { k, v: amp * env * Math.sin(OMEGA * tt) }
  }

  private sourceAt(n: number) {
    // inject the discrete time-derivative so the net injected displacement is exactly zero (no DC mode)
    const a = this.wave(n)
    this.pulses = a.k + 1
    return 3.2 * (a.v - this.wave(n - 1).v)
  }

  private step(count: number) {
    const r = this.renderer
    for (let i = 0; i < count; i++) {
      const src = this.rt[this.cur]
      const dst = this.rt[1 - this.cur]
      this.stepMat.uniforms.uState.value = src.texture
      this.stepMat.uniforms.uSrc.value = this.sourceAt(this.stepN)
      r.setRenderTarget(dst)
      r.render(this.simScene, this.simCam)
      this.cur = 1 - this.cur
      this.stepN++
    }
    r.setRenderTarget(null)
  }

  /** advance by dt seconds and draw */
  frame(dt: number) {
    dt = Math.min(dt, 1 / 20)
    this.t += dt
    const n = Math.max(1, Math.round(this.stepsPerSecond * dt))
    this.step(n)
    const w = Math.abs(this.wave(this.stepN).v)
    this.glint.material.opacity = 0.45 + Math.min(1, w * 2.5)
    this.glint.scale.setScalar(0.18 + 0.25 * Math.min(1, w * 2))

    // camera: long lens, slightly above, very slow drift + pointer parallax
    this.pointerS.lerp(this.pointer, 0.04)
    const az = 0.55 + Math.sin(this.t * 0.07) * 0.08 + this.pointerS.x * 0.06
    const el = 0.15 + this.pointerS.y * 0.03
    const { width: vw, height: vh } = this.opts
    const aspect = vw / vh
    // desktop: stack right of centre, filling ~88 % of the height; portrait: centred, raised above the copy
    const wide = aspect > 1.05
    const dist = wide ? 19.5 : 18.5 / Math.min(1, aspect * 1.25)
    const fx = this.opts.frameX ?? (wide ? 0.2 : 0)
    const fy = wide ? 0 : 0.17
    const target = new THREE.Vector3(0, -0.15, 0)
    this.camera.position.set(Math.sin(az) * Math.cos(el) * dist, Math.sin(el) * dist, Math.cos(az) * Math.cos(el) * dist)
    this.camera.lookAt(target)
    this.camera.setViewOffset(vw, vh, -fx * vw, fy * vh, vw, vh)

    const tex = this.rt[this.cur].texture
    const camObj = this.rig.worldToLocal(this.camera.position.clone())
    this.volMat.uniforms.uState.value = tex
    ;(this.volMat.uniforms.uCamObj.value as THREE.Vector3).copy(camObj)
    const cn = new THREE.Vector3(camObj.x, 0, camObj.z).normalize()
    ;(this.volMat.uniforms.uCutN.value as THREE.Vector3).copy(cn)
    for (const m of this.partMats) {
      m.uniforms.uState.value = tex
      ;(m.uniforms.uCam.value as THREE.Vector3).copy(this.camera.position)
    }
    this.grade.uniforms.uTime.value = this.t
    this.composer.render()
  }

  dispose() {
    this.rt.forEach((t) => t.dispose())
    this.composer.dispose()
    this.renderer.dispose()
  }
}

/** a turned ring (or solid disc when inner = 0) with flat faces, as a lathe profile */
function ringGeometry(inner: number, outer: number, thickness: number, hole = 0) {
  const h = thickness / 2
  const ch = Math.min(0.012, h * 0.3) // chamfer
  const i0 = Math.max(inner, hole)
  const pts = [
    new THREE.Vector2(i0, -h),
    new THREE.Vector2(outer - ch, -h),
    new THREE.Vector2(outer, -h + ch),
    new THREE.Vector2(outer, h - ch),
    new THREE.Vector2(outer - ch, h),
    new THREE.Vector2(i0, h),
  ]
  if (i0 > 0) pts.push(new THREE.Vector2(i0, -h))
  const g = new THREE.LatheGeometry(pts, 128)
  g.computeVertexNormals()
  return g
}
