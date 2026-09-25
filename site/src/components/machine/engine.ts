/**
 * The hero machine: a 3-D scalar-wave simulation of the cavity, rendered as an instrument.
 *
 * Physics (3-D FDTD, leapfrog, on the GPU): a pinhole in the flat bottom mirror injects short pulses; seven phase-plate
 * SLMs (slabs whose refractive index is a 2-D pixel pattern) sit between it and a concave top mirror whose centre of
 * curvature is the pinhole, so each round trip spreads the light and re-focuses it onto the pinhole (the readout).
 * Pulses are injected three times per round trip, so three wavefronts are in flight at once (time multiplexing).
 *
 * The volume is an NX × NX × NZ grid stored as a 2-D atlas of NZ tiles (TC tiles per row). The renderer ray-marches the
 * field and draws each wave crest it crosses as a lit, translucent sheet.
 */
import * as THREE from 'three'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'

// ---- simulation grid (cells) ----------------------------------------------------------------------------------------
const NX = 96 // horizontal cells (x and z)
const NZ = 240 // vertical cells
const TC = 16 // atlas tiles per row
const TR = Math.ceil(NZ / TC)
const AW = NX * TC
const AH = NX * TR
const R_CELLS = 40 // disc radius
const Z_BOT = 14 // bottom mirror surface
const Z_TOP = 226 // top mirror vertex
const L = Z_TOP - Z_BOT
const MIRROR_T = 4
const PIN_HALF = 2.2 // pinhole radius
const C0 = 0.5 // courant number in vacuum (3-D limit 0.577)
const LAMBDA = 7 // cells
const OMEGA = (2 * Math.PI * C0) / LAMBDA
const N_SLM = 7
const SLM_T = 4
const SLM_Z = Array.from({ length: N_SLM }, (_, i) => Z_BOT + (L * (i + 1)) / (N_SLM + 1))
/** steps for one round trip (vacuum path plus the slabs' extra optical path) */
export const ROUND_TRIP_STEPS = Math.round((2 * L) / C0 + (2 * N_SLM * SLM_T * 0.14) / C0)
/** wavefronts in flight at once */
export const IN_FLIGHT = 3
const PULSE_PERIOD = Math.round(ROUND_TRIP_STEPS / IN_FLIGHT)

// world units: disc radius = 1
const S = 1 / R_CELLS
export const WORLD = {
  radius: 1,
  zBot: Z_BOT * S,
  zTop: Z_TOP * S,
  slmZ: SLM_Z.map((z) => z * S),
  slmT: SLM_T * S,
  mirrorT: MIRROR_T * S,
}

function hash(n: number) {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453
  return s - Math.floor(s)
}

/** refractive index of SLM k at pixel-centre (x, y) in cells from the axis: a weak lens, rings, a 3-fold term, pixel noise */
function slmIndex(k: number, x: number, y: number) {
  const pix = 3
  const px = Math.floor(x / pix), py = Math.floor(y / pix)
  const cx = (px + 0.5) * pix, cy = (py + 0.5) * pix
  const r = Math.hypot(cx, cy) / R_CELLS
  const phi = Math.atan2(cy, cx)
  const lens = (k % 2 ? 1 : -1) * 0.35 * r * r
  const rings = 0.18 * Math.sin(r * R_CELLS * (0.12 + 0.025 * k) + k)
  const lobes = 0.25 * r * Math.sin(3 * phi + k * 1.3)
  const noise = 0.14 * (hash(px * 57.3 + py * 13.1 + k * 101) - 0.5)
  return 1.14 + 0.14 * Math.tanh(1.6 * (lens + rings + lobes + noise))
}

/** static medium, one RGBA8 texel per cell: r = (n − 1) / 0.5, g = conductor mask, b = sponge / 0.25 */
function buildMedium() {
  const d = new Uint8Array(AW * AH * 4)
  for (let k = 0; k < NZ; k++) {
    const ox = (k % TC) * NX, oy = Math.floor(k / TC) * NX
    for (let j = 0; j < NX; j++) {
      for (let i = 0; i < NX; i++) {
        const x = i - NX / 2 + 0.5, y = j - NX / 2 + 0.5
        const r = Math.hypot(x, y)
        let n = 1, mask = 1, sponge = 0
        const edge = r - (R_CELLS + 3)
        if (edge > 0) sponge = Math.min(0.25, 0.012 * edge * edge)
        if (k < 6) sponge = Math.max(sponge, 0.03 * (6 - k))
        if (k >= Z_BOT - MIRROR_T && k < Z_BOT && r <= R_CELLS + 2 && r > PIN_HALF) mask = 0
        const zs = Z_BOT + Math.sqrt(Math.max(0, L * L - r * r))
        if (k >= zs && k < zs + MIRROR_T && r <= R_CELLS + 2) mask = 0
        if (k >= zs + MIRROR_T) sponge = 0.25
        for (let s = 0; s < N_SLM; s++) if (r <= R_CELLS && Math.abs(k + 0.5 - SLM_Z[s]) < SLM_T / 2) n = slmIndex(s, x, y)
        const o = ((oy + j) * AW + ox + i) * 4
        d[o] = Math.round(((n - 1) / 0.5) * 255)
        d[o + 1] = mask * 255
        d[o + 2] = Math.round((sponge / 0.25) * 255)
        d[o + 3] = 255
      }
    }
  }
  const t = new THREE.DataTexture(d, AW, AH, THREE.RGBAFormat, THREE.UnsignedByteType)
  t.minFilter = t.magFilter = THREE.NearestFilter
  t.needsUpdate = true
  return t
}

const quadVert = /* glsl */ `
out vec2 vUv;
void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`

const stepFrag = /* glsl */ `
precision highp float;
precision highp int;
out vec4 o;
uniform sampler2D uState, uMedium;
uniform float uSrc;
const int NX = ${NX}, NZ = ${NZ}, TC = ${TC};
ivec2 at(int i, int j, int k) { return ivec2((k % TC) * NX + i, (k / TC) * NX + j); }
float U(int i, int j, int k) {
  if (i < 0 || j < 0 || k < 0 || i >= NX || j >= NX || k >= NZ) return 0.0;
  return texelFetch(uState, at(i, j, k), 0).r;
}
void main() {
  ivec2 p = ivec2(gl_FragCoord.xy);
  int tx = p.x / NX, ty = p.y / NX;
  int k = ty * TC + tx;
  if (k >= NZ) { o = vec4(0.0); return; }
  int i = p.x - tx * NX, j = p.y - ty * NX;
  vec2 s = texelFetch(uState, p, 0).rg;
  vec4 m = texelFetch(uMedium, p, 0);
  float n = 1.0 + m.r * 0.5;
  float c2 = ${(C0 * C0).toFixed(4)} / (n * n);
  float sg = m.b * 0.25;
  float lap = U(i + 1, j, k) + U(i - 1, j, k) + U(i, j + 1, k) + U(i, j - 1, k) + U(i, j, k + 1) + U(i, j, k - 1) - 6.0 * s.r;
  float un = (2.0 * s.r - (1.0 - sg) * s.g + c2 * lap) / (1.0 + sg);
  un *= 0.99965; // bulk + mirror loss
  // point source inside the fibre, just below the pinhole
  vec3 q = vec3(float(i) - ${(NX / 2 - 0.5).toFixed(1)}, float(j) - ${(NX / 2 - 0.5).toFixed(1)}, float(k) - ${(Z_BOT - MIRROR_T - 2).toFixed(1)});
  un += uSrc * exp(-dot(q, q) / 1.6);
  un *= m.g;
  o = vec4(un, s.r, 0.0, 0.0);
}`

// ---- 3-D rendering ------------------------------------------------------------------------------------------------
const colorRamp = /* glsl */ `
vec3 ramp(float I) {
  // 650 nm on film: deep red → saturated red → orange → white core
  vec3 c = vec3(0.0);
  c += vec3(1.0, 0.035, 0.012) * (1.0 - exp(-I * 1.1));
  c += vec3(1.0, 0.28, 0.08) * (1.0 - exp(-I * 0.07));
  c += vec3(1.0, 0.86, 0.74) * (1.0 - exp(-I * 0.022));
  return c;
}`

/** trilinear field lookup in rig-object space (y up); returns (u, u_prev) */
const fieldLookup = /* glsl */ `
uniform sampler2D uState;
vec2 tileUv(float k, vec2 g) {
  g = clamp(g, vec2(0.5), vec2(${NX}.0 - 1.5));
  return (vec2(mod(k, ${TC}.0), floor(k / ${TC}.0)) * ${NX}.0 + g + 0.5) / vec2(${AW}.0, ${AH}.0);
}
vec2 field(vec3 p) {
  vec3 g = vec3(p.x * ${R_CELLS}.0 + ${NX / 2}.0, p.z * ${R_CELLS}.0 + ${NX / 2}.0, p.y * ${R_CELLS}.0) - 0.5;
  float kz = clamp(g.z, 0.0, ${NZ}.0 - 1.001);
  float k0 = floor(kz);
  return mix(texture(uState, tileUv(k0, g.xy)).rg, texture(uState, tileUv(k0 + 1.0, g.xy)).rg, kz - k0);
}`

const volumeVert = /* glsl */ `
out vec3 vObj;
void main() {
  vObj = position;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`

const volumeFrag = /* glsl */ `
precision highp float;
in vec3 vObj;
out vec4 o;
uniform vec3 uCamObj;
uniform vec3 uLight;
uniform float uSheetGain, uGlowGain, uGlow;
${colorRamp}
${fieldLookup}
void main() {
  vec3 ro = uCamObj;
  vec3 rd = normalize(vObj - uCamObj);
  float a = dot(rd.xz, rd.xz), b = dot(ro.xz, rd.xz), c = dot(ro.xz, ro.xz) - 1.0;
  float h = b * b - a * c;
  if (h < 0.0) discard;
  h = sqrt(h);
  float t0 = (-b - h) / a, t1 = (-b + h) / a;
  float yb = ${(Z_BOT * S).toFixed(5)}, yt = ${((Z_TOP + 2) * S).toFixed(5)};
  float ty0 = (yb - ro.y) / rd.y, ty1 = (yt - ro.y) / rd.y;
  if (ty0 > ty1) { float tmp = ty0; ty0 = ty1; ty1 = tmp; }
  t0 = max(max(t0, ty0), 0.0);
  t1 = min(t1, ty1);
  if (t1 <= t0) discard;
  const int N = 150;
  float dt = (t1 - t0) / float(N);
  float jitter = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  vec3 col = vec3(0.0);
  float A = 0.0;
  float prev = 0.0;
  float eps = ${(1 / R_CELLS).toFixed(5)};
  for (int i = 0; i < N; i++) {
    vec3 p = ro + rd * (t0 + (float(i) + jitter) * dt);
    vec2 f = field(p);
    float u = f.x;
    // faint volumetric fill from the local intensity
    float I = (u * u + (u - f.y) * (u - f.y) * ${(1 / (OMEGA * OMEGA)).toFixed(3)}) * uGlowGain;
    col += (1.0 - A) * ramp(I) * uGlow * dt;
    // wavefront sheets: surfaces of constant phase, where the ray crosses u = 0 upward
    if (i > 0 && prev < 0.0 && u >= 0.0) {
      vec3 gr = vec3(field(p + vec3(eps, 0, 0)).x - field(p - vec3(eps, 0, 0)).x,
                     field(p + vec3(0, eps, 0)).x - field(p - vec3(0, eps, 0)).x,
                     field(p + vec3(0, 0, eps)).x - field(p - vec3(0, 0, eps)).x);
      float gl = length(gr);
      vec3 n = gr / max(gl, 1e-6);
      if (dot(n, rd) > 0.0) n = -n;
      float amp = gl * ${(LAMBDA / (2 * Math.PI)).toFixed(3)} * 0.5; // |∇u|/k ≈ local amplitude
      float diff = 0.35 + 0.65 * max(dot(n, uLight), 0.0);
      float fres = pow(1.0 - abs(dot(n, rd)), 2.0);
      float spec = pow(max(dot(reflect(-uLight, n), -rd), 0.0), 24.0);
      float sI = pow(min(amp, 0.06) * uSheetGain, 0.8);
      vec3 sc = ramp(sI * 1.6) * (0.55 + 0.45 * diff + 1.3 * fres) + vec3(1.0, 0.8, 0.7) * spec * 0.35 * min(1.0, sI);
      float al = smoothstep(0.003, 0.03, amp) * 0.42 * (0.45 + 0.55 * fres) * smoothstep(${(Z_BOT * S).toFixed(4)}, ${((Z_BOT + 5) * S).toFixed(4)}, p.y);
      col += (1.0 - A) * sc * al;
      A += (1.0 - A) * al;
      if (A > 0.97) break;
    }
    prev = u;
  }
  // light doesn't hide what's behind it: mostly additive, with a little occlusion for depth
  o = vec4(col, A * 0.2);
}`

const partVert = /* glsl */ `
out vec3 vN;
out vec3 vW;
out vec3 vObj;
void main() {
  vObj = (modelMatrix * vec4(position, 1.0)).xyz;
  vec4 w = modelMatrix * vec4(position, 1.0);
  vW = w.xyz;
  vN = normalize(mat3(modelMatrix) * normal);
  gl_Position = projectionMatrix * viewMatrix * w;
}`

/** machined parts: anodised rims, polished mirrors, SLM glass faces showing the field that crosses them */
const partFrag = /* glsl */ `
precision highp float;
in vec3 vN;
in vec3 vW;
in vec3 vObj;
out vec4 o;
uniform float uKind; // 0 = SLM, 1 = mirror, 2 = rod / hardware
uniform float uY;
uniform float uGain;
uniform vec3 uCam;
uniform mat4 uToRig; // world → rig-object
${colorRamp}
${fieldLookup}
float energyAt(vec3 pw) {
  vec3 p = (uToRig * vec4(pw, 1.0)).xyz;
  p.y = clamp(p.y, ${(1 * S).toFixed(4)}, ${((NZ - 2) * S).toFixed(4)});
  vec2 f = field(p);
  return f.x * f.x + (f.x - f.y) * (f.x - f.y) * ${(1 / (OMEGA * OMEGA)).toFixed(3)};
}
void main() {
  vec3 n = normalize(vN);
  vec3 v = normalize(uCam - vW);
  vec3 L1 = normalize(vec3(-0.6, 0.9, 0.35));
  float diff = max(dot(n, L1), 0.0);
  vec3 hlf = normalize(L1 + v);
  float fres = pow(1.0 - max(dot(n, v), 0.0), 4.0);
  vec3 pr = (uToRig * vec4(vW, 1.0)).xyz;
  float r = length(pr.xz);
  bool face = abs(n.y) > 0.9;
  float eLocal = energyAt(vW) * 900.0;
  vec3 col;
  float alpha = 1.0;
  if (uKind < 0.5) {
    if (face) {
      vec2 g = abs(fract(pr.xz * ${(R_CELLS / 3).toFixed(3)}) - 0.5);
      float grid = smoothstep(0.44, 0.5, max(g.x, g.y));
      vec3 glass = vec3(0.006) + vec3(0.09) * pow(max(dot(n, hlf), 0.0), 80.0);
      col = glass * (1.0 - grid * 0.5) + ramp(eLocal * uGain) * (0.9 + 0.4 * grid);
      col += vec3(0.05) * fres;
      alpha = 0.22 + 0.5 * fres;
      col += vec3(0.12) * smoothstep(0.985, 0.995, r) * (1.0 - smoothstep(0.995, 1.0, r));
    } else {
      float spec = pow(max(dot(n, hlf), 0.0), 24.0);
      col = vec3(0.012) + vec3(0.025) * diff + vec3(0.22) * spec + vec3(0.06) * fres;
      col += ramp(eLocal * uGain) * 0.22;
    }
  } else if (uKind < 1.5) {
    if (face) {
      float lathe = 0.5 + 0.5 * sin(r * 520.0);
      float spec = pow(max(dot(n, hlf), 0.0), 260.0) * (0.5 + 0.5 * lathe);
      col = vec3(0.012) + vec3(1.2) * spec + vec3(0.06) * fres + ramp(eLocal * uGain) * 1.6;
      float ph = smoothstep(0.075, 0.05, r);
      col = mix(col, vec3(0.0), ph * step(uY, 1.0));
    } else {
      col = vec3(0.022) + vec3(0.04) * diff + vec3(0.8) * pow(max(dot(n, hlf), 0.0), 60.0) + vec3(0.08) * fres + ramp(eLocal * uGain) * 0.25;
    }
  } else {
    float spec = pow(max(dot(n, hlf), 0.0), 50.0);
    col = vec3(0.015) + vec3(0.03) * diff + vec3(0.5) * spec + vec3(0.05) * fres;
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
  /** vertical placement: fraction of the height to raise the stack by */
  frameY?: number
  /** camera distance override (smaller = larger stack) */
  distance?: number
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
  private glint: THREE.Sprite
  private stepN = 0
  private cur = 0
  private t = 0
  private spin = 0.9
  private pointer = new THREE.Vector2()
  private pointerS = new THREE.Vector2()
  opts: MachineOptions
  /** pulses injected so far */
  pulses = 0
  stepsPerSecond = 480
  get tripSeconds() { return ROUND_TRIP_STEPS / this.stepsPerSecond }

  constructor(opts: MachineOptions) {
    this.opts = opts
    const r = new THREE.WebGLRenderer({ canvas: opts.canvas, antialias: true, powerPreference: 'high-performance' })
    r.setPixelRatio(opts.dpr)
    r.setSize(opts.width, opts.height, false)
    this.renderer = r
    if (!r.capabilities.isWebGL2 || !r.extensions.has('EXT_color_buffer_float') || !r.extensions.has('OES_texture_float_linear')) {
      r.dispose()
      throw new Error('float render targets unavailable')
    }

    // ---- simulation ----
    const rtOpts = { type: THREE.FloatType, format: THREE.RGFormat, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: false, wrapS: THREE.ClampToEdgeWrapping, wrapT: THREE.ClampToEdgeWrapping }
    this.rt = [new THREE.WebGLRenderTarget(AW, AH, rtOpts), new THREE.WebGLRenderTarget(AW, AH, rtOpts)]
    this.stepMat = new THREE.ShaderMaterial({
      glslVersion: THREE.GLSL3,
      vertexShader: quadVert,
      fragmentShader: stepFrag,
      uniforms: { uState: { value: null }, uMedium: { value: buildMedium() }, uSrc: { value: 0 } },
    })
    this.simScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.stepMat))
    r.setClearColor(0x000000, 0)
    for (const t of this.rt) { r.setRenderTarget(t); r.clear() }
    r.setRenderTarget(null)
    r.setClearColor(0x0a0908, 1)

    // ---- scene ----
    this.camera = new THREE.PerspectiveCamera(22, opts.width / opts.height, 0.1, 100)
    this.scene.add(this.rig)
    const yMid = (WORLD.zBot + WORLD.zTop) / 2
    this.rig.position.y = -yMid

    this.volMat = new THREE.ShaderMaterial({
      glslVersion: THREE.GLSL3,
      vertexShader: volumeVert,
      fragmentShader: volumeFrag,
      uniforms: {
        uState: { value: null }, uCamObj: { value: new THREE.Vector3() }, uLight: { value: new THREE.Vector3(-0.5, 0.8, 0.4).normalize() },
        uSheetGain: { value: 70 }, uGlowGain: { value: 900 }, uGlow: { value: 0.3 },
      },
      transparent: true,
      blending: THREE.CustomBlending,
      blendSrc: THREE.OneFactor,
      blendDst: THREE.OneMinusSrcAlphaFactor,
      depthWrite: false,
      side: THREE.BackSide,
    })
    // proxy for the ray-march: slightly inside the mirrors so its caps never z-fight with the mirror faces
    const y0 = WORLD.zBot + 0.012, y1 = WORLD.zTop - 0.012
    const vol = new THREE.Mesh(new THREE.CylinderGeometry(1.01, 1.01, y1 - y0, 64, 1, false), this.volMat)
    // the volume shader works in rig-object space (y from 0): bake the offset into the geometry
    vol.geometry.translate(0, (y0 + y1) / 2, 0)
    vol.renderOrder = 2
    this.rig.add(vol)

    const mkMat = (kind: number, y: number, transparent = false) => {
      const m = new THREE.ShaderMaterial({
        glslVersion: THREE.GLSL3,
        vertexShader: partVert,
        fragmentShader: partFrag,
        uniforms: { uState: { value: null }, uKind: { value: kind }, uY: { value: y }, uGain: { value: 1 }, uCam: { value: new THREE.Vector3() }, uToRig: { value: new THREE.Matrix4() } },
        transparent,
        depthWrite: !transparent,
      })
      this.partMats.push(m)
      return m
    }
    for (const z of WORLD.slmZ) {
      const glass = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, WORLD.slmT, 128, 1, false), mkMat(0, z, true))
      glass.position.y = z
      glass.renderOrder = 3
      this.rig.add(glass)
      const ring = new THREE.Mesh(ringGeometry(1.0, 1.05, WORLD.slmT * 1.5), mkMat(0, z))
      ring.position.y = z
      this.rig.add(ring)
    }
    const mb = new THREE.Mesh(ringGeometry(0.0, 1.1, WORLD.mirrorT * 2.2, 0.06), mkMat(1, WORLD.zBot))
    mb.position.y = WORLD.zBot - WORLD.mirrorT * 1.1
    this.rig.add(mb)
    const mt = new THREE.Mesh(ringGeometry(0.0, 1.1, WORLD.mirrorT * 2.2), mkMat(1, WORLD.zTop))
    mt.position.y = WORLD.zTop + WORLD.mirrorT * 1.1
    this.rig.add(mt)
    const rodLen = WORLD.zTop - WORLD.zBot + 0.9
    for (let k = 0; k < 4; k++) {
      const a = Math.PI / 4 + (k * Math.PI) / 2
      const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, rodLen, 16), mkMat(2, 0))
      rod.position.set(Math.cos(a) * 1.16, yMid, Math.sin(a) * 1.16)
      this.rig.add(rod)
    }
    const fer = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.7, 24), mkMat(2, 0))
    fer.position.y = WORLD.zBot - WORLD.mirrorT * 2.2 - 0.35
    this.rig.add(fer)
    const fib = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 3, 12), mkMat(2, 0))
    fib.position.y = WORLD.zBot - WORLD.mirrorT * 2.2 - 2.0
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
    // pre-warm: run two round trips before the first frame so the cavity is already full of wavefronts
    this.step(2 * ROUND_TRIP_STEPS)
  }

  setPointer(x: number, y: number) { this.pointer.set(x, y) }

  /** css-pixel positions of named parts, for annotation drawn over the canvas */
  anchors() {
    const P = (v3: THREE.Vector3) => {
      const v = v3.project(this.camera)
      return { x: (v.x * 0.5 + 0.5) * this.opts.width, y: (-v.y * 0.5 + 0.5) * this.opts.height }
    }
    const rigP = (x: number, y: number, z: number) => this.rig.localToWorld(new THREE.Vector3(x, y, z))
    // a measuring line beside the stack, on the side facing the camera's left, outside the cage
    const side = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), this.camera.position.clone().setY(0).normalize()).multiplyScalar(-1.55)
    const top = rigP(0, WORLD.zTop, 0).add(side), bot = rigP(0, WORLD.zBot, 0).add(side)
    const zMid = (WORLD.zBot + WORLD.zTop) / 2
    return {
      beam: P(rigP(0, zMid + 0.9, 0)),
      pinhole: P(rigP(0, WORLD.zBot - 0.02, 0)),
      mirrorTop: P(top),
      mirrorBot: P(bot),
    }
  }

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
    // a pulse every third of a round trip; each pulse has its own amplitude (the "input")
    const k = Math.floor(n / PULSE_PERIOD)
    const tt = n - k * PULSE_PERIOD - 60
    const env = tt < -60 || tt > 60 ? 0 : Math.exp(-(tt * tt) / (2 * 14 * 14))
    const amp = 0.55 + 0.45 * hash(k * 7.1)
    return { k, v: amp * env * Math.sin(OMEGA * tt) }
  }

  private sourceAt(n: number) {
    // inject the discrete time-derivative so the net injected displacement is exactly zero (no DC mode)
    const a = this.wave(n)
    this.pulses = a.k + 1
    return 2.4 * (a.v - this.wave(n - 1).v)
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
    this.step(Math.max(1, Math.round(this.stepsPerSecond * dt)))
    const w = Math.abs(this.wave(this.stepN).v)
    this.glint.material.opacity = 0.45 + Math.min(1, w * 2.5)
    this.glint.scale.setScalar(0.18 + 0.25 * Math.min(1, w * 2))

    // slow turntable on the whole instrument; camera: long lens, above, pointer parallax only
    this.spin += dt * 0.06
    this.rig.rotation.y = this.spin
    this.pointerS.lerp(this.pointer, 0.04)
    const az = 0.55 + this.pointerS.x * 0.06
    const el = 0.3 + this.pointerS.y * 0.03
    const { width: vw, height: vh } = this.opts
    const aspect = vw / vh
    const wide = aspect > 1.05
    const dist = this.opts.distance ?? (wide ? 19.5 : 18.5 / Math.min(1, aspect * 1.25))
    const fx = this.opts.frameX ?? (wide ? 0.2 : 0)
    const fy = this.opts.frameY ?? (wide ? 0 : 0.17)
    this.camera.position.set(Math.sin(az) * Math.cos(el) * dist, Math.sin(el) * dist, Math.cos(az) * Math.cos(el) * dist)
    this.camera.lookAt(0, -0.25, 0)
    this.camera.setViewOffset(vw, vh, -fx * vw, fy * vh, vw, vh)
    this.camera.updateMatrixWorld()
    this.rig.updateMatrixWorld()

    const tex = this.rt[this.cur].texture
    const toRig = this.rig.matrixWorld.clone().invert()
    ;(this.volMat.uniforms.uCamObj.value as THREE.Vector3).copy(this.camera.position).applyMatrix4(toRig)
    ;(this.volMat.uniforms.uLight.value as THREE.Vector3).set(-0.5, 0.8, 0.4).transformDirection(toRig)
    this.volMat.uniforms.uState.value = tex
    for (const m of this.partMats) {
      m.uniforms.uState.value = tex
      ;(m.uniforms.uToRig.value as THREE.Matrix4).copy(toRig)
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
