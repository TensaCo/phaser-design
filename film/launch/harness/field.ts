// The explainer's wavefront: a complex field E(x, y) drawn as a surface. Height = |E| (brightness), colour = arg E (phase:
// where the wave is in its cycle, red ↔ pale). The etched plate is 64 × 64 columns (height = etch depth) rising beneath.
// Frames come from src/field_v4.py (angular-spectrum propagation on the site's plate program). Pure function of the spec.
import * as THREE from 'three'
const W = Number(new URLSearchParams(location.search).get('w') ?? 1920), H = Number(new URLSearchParams(location.search).get('h') ?? 1080)
const canvas = document.createElement('canvas'); canvas.width = W; canvas.height = H; document.body.style.margin = '0'; document.body.appendChild(canvas)
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setSize(W, H, false); renderer.setClearColor(0x000000, 1)
const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(40, W / H, 0.01, 100)
let meta: any, data: Float32Array, S = 128
const amp = new THREE.DataTexture(new Float32Array(S * S), S, S, THREE.RedFormat, THREE.FloatType)
const pha = new THREE.DataTexture(new Float32Array(S * S), S, S, THREE.RedFormat, THREE.FloatType)
for (const t of [amp, pha]) { t.magFilter = t.minFilter = THREE.LinearFilter; t.needsUpdate = true }
const L = 1.6
const surf = new THREE.Mesh(new THREE.PlaneGeometry(L, L, 255, 255).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({
  uniforms: { uAmp: { value: amp }, uPha: { value: pha }, uH: { value: 0.32 } },
  vertexShader: `uniform sampler2D uAmp; uniform float uH; varying vec2 vUv; varying float vA; varying vec3 vN; varying vec3 vP;
    float h(vec2 uv){ return texture2D(uAmp, uv).r * uH; }
    void main(){ vUv = uv; float e = 1.0/255.0; float a = h(uv); vA = texture2D(uAmp, uv).r;
      vec3 p = position + vec3(0.0, a, 0.0);
      vec3 dx = vec3(2.0*e*${L}, h(uv+vec2(e,0.))-h(uv-vec2(e,0.)), 0.0), dz = vec3(0.0, h(uv+vec2(0.,e))-h(uv-vec2(0.,e)), 2.0*e*${L});
      vN = normalize(normalMatrix * normalize(cross(dz, dx))); vec4 mv = modelViewMatrix * vec4(p, 1.0); vP = mv.xyz; gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `uniform sampler2D uPha; varying vec2 vUv; varying float vA; varying vec3 vN; varying vec3 vP;
    void main(){ float ph = texture2D(uPha, vUv).r; float c = 0.5 + 0.5 * cos(ph);
      vec3 red = vec3(1.0, 0.16, 0.07), pale = vec3(0.95, 0.9, 0.86);
      vec3 col = mix(pale * 0.55, red, c);
      float diff = 0.35 + 0.65 * max(dot(vN, normalize(vec3(-0.4, 0.9, 0.3))), 0.0);
      float rim = pow(1.0 - max(dot(vN, normalize(-vP)), 0.0), 3.0);
      vec2 g = abs(fract(vUv * 64.0) - 0.5); float grid = smoothstep(0.47, 0.5, max(g.x, g.y)) * 0.12;
      gl_FragColor = vec4(col * (0.12 + 1.25 * vA) * diff + rim * 0.15 * red + grid, 1.0); }`,
  side: THREE.DoubleSide,
}))
scene.add(surf)
// the etched plate: 64 x 64 columns, graphite, lit from above
const P = 64, cell = L / P
const pillars = new THREE.InstancedMesh(new THREE.BoxGeometry(cell * 0.94, 1, cell * 0.94), new THREE.MeshStandardMaterial({ color: 0x3a3836, roughness: 0.45, metalness: 0.6 }), P * P)
scene.add(pillars)
scene.add(new THREE.HemisphereLight(0xffffff, 0x111111, 1.2)); const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(-1, 2, 1); scene.add(key)
const sweepLine = new THREE.Mesh(new THREE.BoxGeometry(0.004, 0.22, L), new THREE.MeshBasicMaterial({ color: 0xff2a12, transparent: true, opacity: 0.35, depthWrite: false }))
scene.add(sweepLine)
const o = new THREE.Object3D()
;(async () => {
  meta = await (await fetch('field-meta.json')).json(); S = meta.size
  data = new Float32Array(await (await fetch('field-frames.bin')).arrayBuffer())
  ;(window as any).ready = true
})()
;(window as any).info = () => ({ renderer: 'field', frames: meta?.n })
;(window as any).shot = (f: { i: number; cam: { pos: number[]; target: number[]; fov: number } }) => {
  const i = Math.min(meta.n - 1, Math.max(0, f.i)), sc = meta.script[i], off = i * 2 * S * S
  ;(amp.image.data as Float32Array).set(data.subarray(off, off + S * S)); (pha.image.data as Float32Array).set(data.subarray(off + S * S, off + 2 * S * S))
  amp.needsUpdate = pha.needsUpdate = true
  const pl = sc.plate ?? 0
  pillars.visible = pl > 0.01
  for (let y = 0; y < P; y++) for (let x = 0; x < P; x++) {
    const h = 0.02 + meta.plate[y][x] * 0.035
    o.position.set(-L / 2 + (x + 0.5) * cell, -0.34 + (pl - 1) * 0.5 - h / 2 + 0.02, -L / 2 + (y + 0.5) * cell); o.scale.set(1, h, 1); o.updateMatrix(); pillars.setMatrixAt(y * P + x, o.matrix)
  }
  pillars.instanceMatrix.needsUpdate = true
  sweepLine.visible = sc.part === 'B' && sc.sweep > 0 && sc.sweep < 1
  sweepLine.position.set(-L / 2 + (sc.sweep ?? 0) * L, 0.02, 0)
  camera.position.set(...(f.cam.pos as [number, number, number])); camera.lookAt(new THREE.Vector3(...(f.cam.target as [number, number, number])))
  camera.fov = f.cam.fov; camera.updateProjectionMatrix()
  renderer.render(scene, camera)
  return canvas.toDataURL('image/png')
}
