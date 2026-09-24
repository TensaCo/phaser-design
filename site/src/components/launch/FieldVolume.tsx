'use client'
/**
 * Volumetric renderings of a photon and an electron as complex fields, ray-marched through a fine voxel grid.
 * Brightness is the density |ψ|² (for light, |E|²); colour is the phase arg ψ, mapped blue ↔ orange.
 *
 * Photon: a Gaussian wave packet of light in vacuum, E ∝ exp(−(x−ct)²/2σ² − ρ²/w²) · e^{i(kx−ωt)}. It moves rigidly at c
 * and keeps its norm: nothing in free space takes energy from it.
 * Electron: a Bloch wave packet, envelope × e^{ik·r} × a lattice-periodic factor on a diamond-cubic crystal. It drifts,
 * scatters (stalls, spreads, emits a spherical scattered wavelet) and leaves on a new heading; each event deposits heat
 * (red) into the lattice around the site.
 */
import { useEffect, useRef } from 'react'

const VS = `#version 300 es
in vec2 p; out vec2 uv;
void main() { uv = p; gl_Position = vec4(p, 0.0, 1.0); }`

const COMMON = `#version 300 es
precision highp float;
in vec2 uv; out vec4 o;
uniform float uT, uAspect, uAbs, uGain;
uniform vec3 uEye, uRight, uUp, uFwd;
const vec3 BOX = vec3(2.0, 1.0, 1.0);
const float VOX = 1.0 / 72.0; // voxel pitch: fine enough to vanish at a glance
vec3 phaseColor(float ph) {
  float t = 0.5 + 0.5 * cos(ph);
  return mix(vec3(0.29, 0.56, 1.0), vec3(1.0, 0.54, 0.16), t);
}
bool box(vec3 ro, vec3 rd, out float t0, out float t1) {
  vec3 inv = 1.0 / rd;
  vec3 a = (-BOX - ro) * inv, b = (BOX - ro) * inv;
  vec3 lo = min(a, b), hi = max(a, b);
  t0 = max(max(lo.x, lo.y), lo.z); t1 = min(min(hi.x, hi.y), hi.z);
  return t1 > max(t0, 0.0);
}
`

const PHOTON = COMMON + `
uniform float uX0;
vec4 sampleField(vec3 p) {
  float sx = 0.55, w = 0.5, k = 22.0;
  float dx = p.x - uX0;
  float env = exp(-dx * dx / (2.0 * sx * sx) - dot(p.yz, p.yz) / (w * w));
  float ph = k * dx; // the phase rides with the packet: in vacuum phase and group velocity are both c
  float re = env * cos(ph);
  // raw field: energy density of the real field, E·E, as thin crest sheets; colour = sign of E
  float c2 = cos(ph) * cos(ph);
  float dens = env * env * (c2 * c2 * 1.8 + 0.04);
  return vec4(phaseColor(ph) * dens, dens);
}
`

const ELECTRON = COMMON + `
uniform vec3 uC, uK;          // packet centre and wave vector
uniform float uSig;           // envelope width (grows while scattering)
uniform vec4 uEv[6];          // scattering events: xyz = site, w = birth time (−1 = none)
const float A = 0.5;           // lattice constant
float lattice(vec3 p) {
  // diamond cubic density: distance to the nearest of the 8 basis atoms in the unit cell
  vec3 c = fract(p / A) * A;
  float d = 1e9;
  vec3 B[8] = vec3[8](vec3(0), vec3(0.5, 0.5, 0), vec3(0.5, 0, 0.5), vec3(0, 0.5, 0.5),
                      vec3(0.25), vec3(0.75, 0.75, 0.25), vec3(0.75, 0.25, 0.75), vec3(0.25, 0.75, 0.75));
  for (int i = 0; i < 8; i++) {
    vec3 q = c - B[i] * A;
    q -= A * round(q / A);
    d = min(d, dot(q, q));
  }
  return exp(-d / (0.0011 * A * A * 4.0));
}
vec4 sampleField(vec3 p) {
  float u = lattice(p);
  vec3 r = p - uC;
  float env = exp(-dot(r, r) / (2.0 * uSig * uSig));
  // Bloch packet: envelope × plane wave × (smooth + lattice-periodic part)
  float amp = env * (0.8 + 0.5 * u);
  float ph = dot(uK, r) - uT * 9.0;
  vec2 psi = amp * vec2(cos(ph), sin(ph));
  float heat = 0.0;
  for (int i = 0; i < 6; i++) {
    if (uEv[i].w < 0.0) continue;
    float age = uT - uEv[i].w;
    vec3 q = p - uEv[i].xyz;
    float d = length(q);
    // outgoing spherical scattered wavelet
    float shell = exp(-pow(d - 0.9 * age, 2.0) / (2.0 * 0.05 * 0.05)) * exp(-age * 1.6) / (1.0 + 5.0 * d);
    float phs = 22.0 * d - uT * 9.0;
    psi += 1.4 * shell * vec2(cos(phs), sin(phs));
    // heat left in the lattice around the site
    heat += (0.25 + u) * exp(-d * d / 0.02) * exp(-age * 0.5);
  }
  float ph2 = atan(psi.y, psi.x);
  // probability cloud |ψ|², drawn through its real part so the phase fronts show as sheets
  float cc = cos(ph2) * cos(ph2);
  float dens = dot(psi, psi) * (0.08 + 1.7 * cc * cc);
  vec3 col = phaseColor(ph2);
  // the crystal itself: faint grey density at the atom sites; heat turns it red
  float lat = u * 0.3;
  vec3 c = col * dens + vec3(0.62, 0.6, 0.57) * lat + vec3(1.0, 0.14, 0.06) * heat * 2.0;
  return vec4(c, dens + lat + heat * 2.0);
}
`

const MARCH = `
void main() {
  vec3 rd = normalize(uFwd * 2.6 + uRight * uv.x * uAspect + uUp * uv.y);
  vec3 ro = uEye;
  float t0, t1;
  vec3 bg = vec3(0.039, 0.035, 0.031);
  if (!box(ro, rd, t0, t1)) { o = vec4(bg, 1.0); return; }
  t0 = max(t0, 0.0);
  const int N = 220;
  float dt = (t1 - t0) / float(N);
  float j = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  vec3 acc = vec3(0.0);
  float T = 1.0;
  for (int i = 0; i < N; i++) {
    vec3 p = ro + rd * (t0 + (float(i) + j) * dt);
    p = (floor(p / VOX) + 0.5) * VOX; // voxel grid
    vec4 s = sampleField(p);
    // emission–absorption: each voxel glows in its phase colour and hides a little of what is behind it
    float a = 1.0 - exp(-s.a * dt * uAbs);
    acc += T * a * (s.rgb / max(s.a, 1e-5));
    T *= 1.0 - a;
    if (T < 0.01) break;
  }
  vec3 c = 1.0 - exp(-acc * uGain);
  o = vec4(bg * T + c, 1.0);
}
`

type Kind = 'photon' | 'electron'
type V3 = [number, number, number]
const norm = (v: V3): V3 => { const l = Math.hypot(...v) || 1; return [v[0] / l, v[1] / l, v[2] / l] }
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]

export function FieldVolume({ kind, onEvent }: { kind: Kind; onEvent?: (n: number) => void }) {
  const ref = useRef<HTMLCanvasElement>(null)
  const cb = useRef(onEvent)
  cb.current = onEvent
  useEffect(() => {
    const cv = ref.current!
    const gl = cv.getContext('webgl2', { antialias: false, premultipliedAlpha: false })
    if (!gl) return
    const sh = (type: number, src: string) => { const x = gl.createShader(type)!; gl.shaderSource(x, src); gl.compileShader(x); if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(x)); return x }
    const pr = gl.createProgram()!
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS))
    gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, (kind === 'photon' ? PHOTON : ELECTRON) + MARCH))
    gl.linkProgram(pr)
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { console.error(gl.getProgramInfoLog(pr)); return }
    gl.useProgram(pr)
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)
    const loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)
    const U = (n: string) => gl.getUniformLocation(pr, n)

    // electron walk state
    let seed = 11
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)
    const W = { c: [-1.7, 0, 0] as V3, dir: [1, 0, 0] as V3, seg: 0, free: 0.5, stall: 0, sig: 0.34, events: [] as [number, number, number, number][], hits: 0 }
    const newDir = (): V3 => norm([0.8 + rnd() * 0.7, (rnd() - 0.5) * 1.8, (rnd() - 0.5) * 1.8])

    let raf = 0, visible = false, last = performance.now(), t = 0, first = true
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
    io.observe(cv)
    const loop = (now: number) => {
      raf = requestAnimationFrame(loop)
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      if (!visible && !first) return
      first = false
      const d = reduced ? 0 : dt
      t += d
      const dpr = Math.min(devicePixelRatio || 1, 1.25)
      const w = Math.round(cv.clientWidth * dpr), h = Math.round(cv.clientHeight * dpr)
      if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h }
      gl.viewport(0, 0, w, h)
      // slow orbit
      // mostly side-on to the motion (x), so wavefronts are seen edge-on
      const yaw = -0.3 + 0.16 * Math.sin(t * 0.13), pitch = 0.36, R = kind === 'photon' ? 4.9 : 4.4
      const eye: V3 = [Math.sin(yaw) * Math.cos(pitch) * R, Math.sin(pitch) * R, Math.cos(yaw) * Math.cos(pitch) * R]
      const fwd = norm([-eye[0], -eye[1], -eye[2]])
      const right = norm(cross(fwd, [0, 1, 0]))
      const up = cross(right, fwd)
      gl.uniform1f(U('uT'), t)
      gl.uniform1f(U('uAspect'), w / h)
      gl.uniform1f(U('uAbs'), kind === 'photon' ? 9 : 6)
      gl.uniform1f(U('uGain'), kind === 'photon' ? 1.5 : 1.4)
      gl.uniform3fv(U('uEye'), eye); gl.uniform3fv(U('uRight'), right); gl.uniform3fv(U('uUp'), up); gl.uniform3fv(U('uFwd'), fwd)
      if (kind === 'photon') {
        const span = 5.2
        gl.uniform1f(U('uX0'), ((t * 1.1) % span) - span / 2)
      } else {
        if (W.stall > 0) {
          W.stall -= d
          W.sig = Math.min(0.5, W.sig + d * 0.5)
          if (W.stall <= 0) { W.dir = newDir(); W.seg = 0; W.free = 0.3 + rnd() * 0.45 }
        } else {
          W.sig = Math.max(0.32, W.sig - d * 0.35)
          const v = 0.55
          W.c = [W.c[0] + W.dir[0] * v * d, W.c[1] + W.dir[1] * v * d, W.c[2] + W.dir[2] * v * d]
          W.seg += v * d
          for (const ax of [1, 2] as const) if (Math.abs(W.c[ax]) > 0.62) { W.dir[ax] *= -1; W.c[ax] = Math.sign(W.c[ax]) * 0.62 }
          if (W.c[0] > 1.75) { W.c = [-1.75, (rnd() - 0.5) * 0.6, (rnd() - 0.5) * 0.6]; W.dir = [1, 0, 0] }
          if (W.seg > W.free) {
            W.stall = 0.45
            W.events.push([W.c[0], W.c[1], W.c[2], t])
            if (W.events.length > 6) W.events.shift()
            W.hits++
            cb.current?.(W.hits)
          }
        }
        gl.uniform3fv(U('uC'), W.c)
        const k = W.stall > 0 ? 9 : 22
        gl.uniform3fv(U('uK'), [W.dir[0] * k, W.dir[1] * k, W.dir[2] * k])
        gl.uniform1f(U('uSig'), W.sig)
        const ev = new Float32Array(24).fill(-1)
        W.events.forEach((e, i) => ev.set(e, i * 4))
        gl.uniform4fv(U('uEv'), ev)
      }
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
    }
    raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); io.disconnect() }
  }, [kind])
  return <canvas ref={ref} aria-hidden="true" style={{ display: 'block', width: '100%', height: '100%' }} />
}
