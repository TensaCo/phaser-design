'use client'
/**
 * A still photograph that breathes: the steam plume drifts (flow-noise displacement masked to bright sky) and the red
 * aviation lights blink in sync. Deterministic, a few hundred bytes of shader; falls back to the plain <img>.
 */
import { useEffect, useRef } from 'react'

const VS = `#version 300 es
in vec2 p; out vec2 uv;
uniform vec2 uCover; // uv scale for object-fit: cover
uniform float uZoom;
void main() { uv = (p * 0.5 + 0.5 - 0.5) * uCover / uZoom + 0.5; uv.y = 1.0 - uv.y; gl_Position = vec4(p, 0.0, 1.0); }`

const FS = `#version 300 es
precision highp float;
in vec2 uv; out vec4 o;
uniform sampler2D uImg; uniform float uT;
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * n(p); p *= 2.03; a *= 0.5; } return s; }
void main() {
  vec3 base = texture(uImg, uv).rgb;
  float lum = dot(base, vec3(0.3, 0.59, 0.11));
  // steam: bright, soft, above the tower tops (image y < 0.82), right half
  float sky = smoothstep(0.84, 0.78, uv.y) * smoothstep(0.42, 0.55, uv.x);
  float steam = sky * smoothstep(0.08, 0.35, lum);
  vec2 q = uv * vec2(3.0, 5.0) + vec2(-uT * 0.035, uT * 0.012);
  vec2 d = vec2(fbm(q), fbm(q + 7.3)) - 0.5;
  vec3 c = mix(base, texture(uImg, uv + d * 0.018 * steam + vec2(-0.004, 0.0) * steam * sin(uT * 0.2)).rgb, steam);
  // aviation lights: blink ~40/min, soft on/off
  float red = smoothstep(0.18, 0.4, base.r - max(base.g, base.b));
  float blink = 0.25 + 0.75 * smoothstep(0.0, 0.08, sin(uT * 4.2)) ;
  c = mix(c, c * vec3(0.35 + 0.65 * blink, 0.4 + 0.6 * blink, 0.4 + 0.6 * blink), red);
  o = vec4(c, 1.0);
}`

export function LivingPhoto({ src, alt, className }: { src: string; alt: string; className?: string }) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const img = useRef<HTMLImageElement>(null)
  useEffect(() => {
    const cv = canvas.current!, im = img.current!
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const gl = cv.getContext('webgl2', { antialias: false, premultipliedAlpha: false })
    if (!gl) return
    let raf = 0, alive = true, visible = false
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
    io.observe(cv)
    const start = () => {
      if (!alive) return
      const sh = (t: number, s: string) => { const x = gl.createShader(t)!; gl.shaderSource(x, s); gl.compileShader(x); return x }
      const pr = gl.createProgram()!
      gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr)
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return
      gl.useProgram(pr)
      const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b)
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)
      const loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)
      const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex)
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, im)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
      const uT = gl.getUniformLocation(pr, 'uT'), uCover = gl.getUniformLocation(pr, 'uCover'), uZoom = gl.getUniformLocation(pr, 'uZoom')
      cv.style.opacity = '1'
      const t0 = performance.now()
      const loop = () => {
        raf = requestAnimationFrame(loop)
        if (!visible) return
        const dpr = Math.min(devicePixelRatio || 1, 1.5)
        const w = Math.round(cv.clientWidth * dpr), hh = Math.round(cv.clientHeight * dpr)
        if (cv.width !== w || cv.height !== hh) { cv.width = w; cv.height = hh }
        gl.viewport(0, 0, w, hh)
        const ia = im.naturalWidth / im.naturalHeight, ca = w / hh
        gl.uniform2f(uCover, ca > ia ? 1 : ca / ia, ca > ia ? ia / ca : 1)
        const t = (performance.now() - t0) / 1000
        gl.uniform1f(uT, t)
        gl.uniform1f(uZoom, 1 + 0.035 * (1 - Math.cos(Math.min(t / 40, 1) * Math.PI)) / 2)
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
      }
      loop()
    }
    if (im.complete && im.naturalWidth) start(); else im.addEventListener('load', start, { once: true })
    return () => { alive = false; cancelAnimationFrame(raf); io.disconnect() }
  }, [src])
  return (
    <div className={className} style={{ position: 'relative' }}>
      <img ref={img} src={src} alt={alt} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
      <canvas ref={canvas} aria-hidden="true" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0, transition: 'opacity .6s' }} />
    </div>
  )
}
