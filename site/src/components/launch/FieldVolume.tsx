'use client'
/**
 * Volumetric renderings of a photon and an electron as complex fields, ray-marched through a fine voxel grid.
 * Brightness is the density |ψ|² (for light, |E|²); colour is the phase arg ψ, mapped blue ↔ orange.
 *
 * Photon: a stream of Gaussian light packets in vacuum, E ∝ exp(−(x−ct)²/2σ² − ρ²/w²) · e^{i(kx−ωt)}. They move rigidly
 * at c and keep their norm: nothing in free space takes energy from them.
 * Electrons: Bloch wave packets (envelope × e^{ik·r} × a lattice-periodic factor) in a diamond-cubic crystal. Each flies to
 * an atom and is absorbed; the atom heats up (red) and rings out a spherical wavelet, then emits a new electron toward the
 * next atom.
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
  // a continuous stream of identical light packets, evenly spaced, all moving at c
  float sx = 0.34, w = 0.42, k = 22.0, span = 5.6, gap = 1.4;
  float rho = exp(-dot(p.yz, p.yz) / (w * w));
  vec3 col = vec3(0.0);
  float dens = 0.0;
  for (int n = 0; n < 4; n++) {
    float x0 = mod(uX0 + float(n) * gap + span * 0.5, span) - span * 0.5;
    float dx = p.x - x0;
    float env = exp(-dx * dx / (2.0 * sx * sx)) * rho;
    float ph = k * dx; // the phase rides with the packet: in vacuum phase and group velocity are both c
    float c2 = cos(ph) * cos(ph);
    // raw field: energy density of the real field E·E as thin crest sheets; colour = sign of E
    float d = env * env * (c2 * c2 * 1.8 + 0.04);
    col += phaseColor(ph) * d;
    dens += d;
  }
  return vec4(col, dens);
}
`

const ELECTRON = COMMON + `
uniform vec4 uE[4];           // electrons: xyz = centre, w = 1 when in flight
uniform vec3 uEk[4];          // their wave vectors
uniform vec4 uEv[10];         // absorption events: xyz = atom, w = time (−1 = none)
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
  vec3 col = vec3(0.0);
  float dens = 0.0;
  for (int i = 0; i < 4; i++) {
    if (uE[i].w < 0.5) continue;
    vec3 r = p - uE[i].xyz;
    float env = exp(-dot(r, r) / (2.0 * 0.15 * 0.15));
    if (env < 1e-3) continue;
    // Bloch packet: envelope × plane wave × (smooth + lattice-periodic part), drawn through Re ψ
    float ph = dot(uEk[i], r) - uT * 14.0;
    float cc = cos(ph) * cos(ph);
    float d = env * env * (0.8 + 0.5 * u) * (0.08 + 1.7 * cc * cc);
    col += phaseColor(ph) * d;
    dens += d;
  }
  float heat = 0.0;
  for (int i = 0; i < 10; i++) {
    if (uEv[i].w < 0.0) continue;
    float age = uT - uEv[i].w;
    vec3 q = p - uEv[i].xyz;
    float dd = length(q);
    // the absorbing atom rings out a spherical wavelet ...
    float shell = exp(-pow(dd - 1.2 * age, 2.0) / (2.0 * 0.04 * 0.04)) * exp(-age * 3.0) / (1.0 + 6.0 * dd);
    float phs = 26.0 * dd - uT * 14.0;
    float cs = cos(phs) * cos(phs);
    float ds = shell * shell * 1.6 * (0.1 + 1.6 * cs * cs);
    col += phaseColor(phs) * ds;
    dens += ds;
    // ... and heats up
    heat += (0.3 + u) * exp(-dd * dd / 0.012) * exp(-age * 0.9);
  }
  // the crystal itself: faint grey density at the atom sites; heat turns it red
  float lat = u * 0.3;
  col += vec3(0.62, 0.6, 0.57) * lat + vec3(1.0, 0.14, 0.06) * heat * 2.4;
  return vec4(col, dens + lat + heat * 2.4);
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

    // electrons hop atom to atom: fly to a target atom, get absorbed (the atom heats up), and a moment later a new
    // electron leaves that atom for the next target
    let seed = 11
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)
    const LA = 0.5
    const BASIS: V3[] = [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5], [0.25, 0.25, 0.25], [0.75, 0.75, 0.25], [0.75, 0.25, 0.75], [0.25, 0.75, 0.75]]
    const atoms: V3[] = []
    for (let i = -4; i <= 4; i++) for (let j = -2; j <= 2; j++) for (let k = -2; k <= 2; k++) for (const b of BASIS) {
      const q: V3 = [(i + b[0]) * LA, (j + b[1]) * LA, (k + b[2]) * LA]
      if (Math.abs(q[0]) < 1.85 && Math.abs(q[1]) < 0.8 && Math.abs(q[2]) < 0.8) atoms.push(q)
    }
    const pick = (from: V3): V3 => {
      // next target: an atom ahead (the applied field pushes +x), a short hop away
      const c = atoms.filter((q) => q[0] - from[0] > 0.15 && q[0] - from[0] < 0.9 && Math.hypot(q[1] - from[1], q[2] - from[2]) < 0.7)
      return c.length ? c[Math.floor(rnd() * c.length)] : atoms[Math.floor(rnd() * atoms.length)]
    }
    type E = { p: V3; to: V3; dir: V3; state: 'fly' | 'hot'; timer: number }
    const spawn = (): E => { const p: V3 = [-1.95, (rnd() - 0.5) * 1.2, (rnd() - 0.5) * 1.2]; const to = pick(p); return { p, to, dir: norm([to[0] - p[0], to[1] - p[1], to[2] - p[2]]), state: 'fly', timer: 0 } }
    const el: E[] = Array.from({ length: 4 }, spawn)
    const events: [number, number, number, number][] = []
    let hits = 0
    const stepE = (d: number, now: number) => {
      for (let n = 0; n < el.length; n++) {
        const e = el[n]
        if (e.state === 'fly') {
          const v = 2.4 * d
          const dx = e.to[0] - e.p[0], dy = e.to[1] - e.p[1], dz = e.to[2] - e.p[2]
          const dist = Math.hypot(dx, dy, dz)
          if (dist <= v) {
            e.p = [...e.to] as V3
            e.state = 'hot'
            e.timer = 0.3 + rnd() * 0.25
            events.push([e.to[0], e.to[1], e.to[2], now])
            if (events.length > 10) events.shift()
            hits++
          } else e.p = [e.p[0] + (dx / dist) * v, e.p[1] + (dy / dist) * v, e.p[2] + (dz / dist) * v]
        } else {
          e.timer -= d
          if (e.timer <= 0) {
            if (e.p[0] > 1.35) { el[n] = spawn(); continue }
            e.to = pick(e.p)
            e.dir = norm([e.to[0] - e.p[0], e.to[1] - e.p[1], e.to[2] - e.p[2]])
            e.state = 'fly'
          }
        }
      }
    }
    // start in equilibrium: stagger the electrons across the crystal and let them run for a few seconds
    el.forEach((e, n) => { e.p = [-1.8 + n * 0.9, e.p[1], e.p[2]]; e.to = pick(e.p); e.dir = norm([e.to[0] - e.p[0], e.to[1] - e.p[1], e.to[2] - e.p[2]]) })
    let tPre = 0
    for (let i = 0; i < 240; i++) { tPre += 1 / 60; stepE(1 / 60, tPre) }

    let raf = 0, visible = false, last = performance.now(), t = tPre, first = true
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
        gl.uniform1f(U('uX0'), (t * 1.1) % span)
      } else {
        stepE(d, t)
        cb.current?.(hits)
        const E = new Float32Array(16), K = new Float32Array(12)
        el.forEach((e, n) => { E.set([e.p[0], e.p[1], e.p[2], e.state === 'fly' ? 1 : 0], n * 4); K.set([e.dir[0] * 24, e.dir[1] * 24, e.dir[2] * 24], n * 3) })
        gl.uniform4fv(U('uE'), E)
        gl.uniform3fv(U('uEk'), K)
        const ev = new Float32Array(40).fill(-1)
        events.forEach((e, i) => ev.set(e, i * 4))
        gl.uniform4fv(U('uEv'), ev)
      }
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
    }
    raf = requestAnimationFrame(loop)
    return () => { cancelAnimationFrame(raf); io.disconnect() }
  }, [kind])
  return <canvas ref={ref} aria-hidden="true" style={{ display: 'block', width: '100%', height: '100%' }} />
}
