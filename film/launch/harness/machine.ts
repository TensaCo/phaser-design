// Film harness: the site's own PHASER scene (StackScene + hardware.ts + the live simulator), driven frame by frame
// with a scripted camera so every product shot in the film is the same machine the site draws.
import * as THREE from 'three'
import { StackScene, yAt } from './site_machine/StackScene'

type Cam = { pos: [number, number, number]; target: [number, number, number]; fov: number }
type FrameSpec = {
  dt: number              // display seconds to advance
  cam: Cam
  light: number           // 0..1 scales every light and the environment (reveal from darkness)
  hardware: number        // 0..1: hardware opacity-ish (0 hides the assembly entirely)
  packets: number | null  // show only the first n packets (null = all)
  beamGain: number        // brightness of the wavefronts
  plates: boolean         // show the plate panels
  follow?: number         // 0..1: blend camera and target height toward the leading wavefront (y = yAt(clock))
  explode?: number        // 0..1: exploded view — parts separate along the optical axis (and the pump sideways)
  studio?: number         // 0..1: white studio (white cyclorama, contact shadow, brighter light) instead of the darkroom
  depth?: boolean         // also return a depth pass (RGBA-packed) for depth of field
}

const W = Number(new URLSearchParams(location.search).get('w') ?? 1920)
const H = Number(new URLSearchParams(location.search).get('h') ?? 1080)
const canvas = document.createElement('canvas')
canvas.width = W; canvas.height = H
canvas.style.width = W + 'px'; canvas.style.height = H + 'px'
document.body.style.margin = '0'
document.body.appendChild(canvas)

const s = new StackScene({ canvas, width: W, height: H, dpr: 1, tripSeconds: 3.2, framing: 'hero' }) as any
const lights: { l: THREE.Light; i: number }[] = []
s.scene.traverse((o: any) => { if (o.isLight) lights.push({ l: o, i: o.intensity }) })
const env0 = s.scene.environmentIntensity
const groups = s.scene.children.filter((o: any) => o.type === 'Group')
const panels = s.scene.children.filter((o: any) => o.isMesh && o.material?.uniforms?.uMap)
const crestMat = s.crests.material as THREE.ShaderMaterial

s.renderer.setClearColor(0x000000, 1)
let spec: FrameSpec | null = null

// ── exploded view ────────────────────────────────────────────────────────────────────────────────────────────────────
// Parts are merged by material in hardware.ts, so the explode is a vertex displacement chosen by where a vertex sits:
// board, camera, pump block, each plate cell, end mirror. The two cage rods and the standoffs stay put, so the parts
// slide off them along the axis. Wires stretch between their ends (they are flexible).
const uExplode = { value: 0 }
const EXPLODE_GLSL = /* glsl */ `
  uniform float uExplode;
  attribute vec3 aPart;
  vec3 explodeOffset(vec3 c) {
    // c: the part's centre (mm). Zones along the axis; the pump block slides sideways.
    float y = c.y, dy = 0.0, dx = 0.0;
    if (y >= 22.6) dy = 46.0;
    else if (y >= 17.4) dy = 34.0;
    else if (y >= 12.4) dy = 25.0;
    else if (y >= 7.4) dy = 16.0;
    else if (y >= 2.4) dy = 8.0;
    else if (y >= -17.0) { if (c.x > 3.2) dx = 16.0; }
    else if (y >= -27.0) dy = -13.0;
    else dy = -28.0;
    return uExplode * vec3(dx, dy, 0.0);
  }
`
const patched = new Set<THREE.Material>()
function patchExplode(root: THREE.Object3D) {
  root.traverse((o: any) => {
    if (!o.isMesh) return
    for (const m of (Array.isArray(o.material) ? o.material : [o.material]) as THREE.Material[]) patchMaterial(m)
  })
}
function patchMaterial(m: THREE.Material) {
    {
      if (patched.has(m)) return
      patched.add(m)
      const prev = m.onBeforeCompile
      m.onBeforeCompile = (sh, r) => {
        prev?.call(m, sh, r)
        sh.uniforms.uExplode = uExplode
        sh.vertexShader = EXPLODE_GLSL + sh.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
          #ifdef USE_INSTANCING
            vec3 pc = (modelMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
            // the offset is in world space; instances can be rotated (fillets under the board are flipped)
            transformed += inverse(mat3(modelMatrix) * mat3(instanceMatrix)) * explodeOffset(pc);
          #else
            transformed += inverse(mat3(modelMatrix)) * explodeOffset(aPart);
          #endif`)
      }
      m.customProgramCacheKey = () => 'explode'
      m.needsUpdate = true
    }
}
for (const g of groups) patchExplode(g)
const PLATE_DY = [8, 16, 25, 34]

// ── white studio: cyclorama floor with a soft contact shadow ─────────────────────────────────────────────────────────
const shadowTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 512
  const x = c.getContext('2d')!
  const g = x.createRadialGradient(256, 256, 10, 256, 256, 256)
  g.addColorStop(0, 'rgba(0,0,0,0.55)'); g.addColorStop(0.35, 'rgba(0,0,0,0.25)'); g.addColorStop(1, 'rgba(0,0,0,0)')
  x.fillStyle = g; x.fillRect(0, 0, 512, 512)
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t
})()
const floor = new THREE.Mesh(new THREE.PlaneGeometry(4000, 4000).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xf1efea, toneMapped: false }))
floor.position.y = -34.8; floor.visible = false; s.scene.add(floor)
const shadow = new THREE.Mesh(new THREE.PlaneGeometry(70, 110).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false, toneMapped: false }))
shadow.position.set(2, -34.7, 4); shadow.visible = false; s.scene.add(shadow)
const studioKey = new THREE.DirectionalLight(0xffffff, 0); studioKey.position.set(-60, 120, 90); s.scene.add(studioKey)
const studioFill = new THREE.HemisphereLight(0xffffff, 0xe8e4dc, 0); s.scene.add(studioFill)
const depthMat = new THREE.MeshDepthMaterial({ depthPacking: THREE.BasicDepthPacking })
patchMaterial(depthMat)
const origPlace = s.placeCamera.bind(s)
s.placeCamera = () => {
  if (!spec) return origPlace()
  const c = spec.cam
  const k = spec.follow ?? 0
  const dy = k ? k * (yAt(s.clock) - c.target[1]) : 0
  s.camera.clearViewOffset()
  s.camera.fov = c.fov
  s.camera.aspect = W / H
  s.camera.position.set(c.pos[0], c.pos[1] + dy, c.pos[2])
  s.camera.lookAt(new THREE.Vector3(c.target[0], c.target[1] + dy, c.target[2]))
  s.camera.updateProjectionMatrix()
}
const origLayout = s.layoutCrests.bind(s)
s.layoutCrests = () => {
  origLayout()
  if (spec && spec.packets !== null) {
    for (let k = 0; k < 36; k++) if (k >= spec.packets) for (let c = 0; c < 3; c++) s.aWeight.setX(k * 3 + c, 0)
    s.aWeight.needsUpdate = true
  }
}

;(window as any).info = () => {
  const gl = s.renderer.getContext(), dbg = gl.getExtension('WEBGL_debug_renderer_info')
  return { renderer: String(dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : ''), bounds: s.bounds, trip: s.live.cav.trip }
}
;(window as any).shot = (f: FrameSpec) => {
  spec = f
  for (const { l, i } of lights) l.intensity = i * f.light
  s.scene.environmentIntensity = env0 * f.light
  for (const g of groups) g.visible = f.hardware > 0
  for (const p of panels) p.visible = f.plates
  const ex = f.explode ?? 0, st = f.studio ?? 0
  uExplode.value = ex
  panels.forEach((p: any, k: number) => { p.userData.y0 ??= p.position.y; p.position.y = p.userData.y0 + ex * PLATE_DY[k] })
  floor.visible = shadow.visible = st > 0
  floor.position.y = -34.8 - 28 * ex; shadow.position.y = -34.7 - 28 * ex
  ;(shadow.material as THREE.MeshBasicMaterial).opacity = st * (1 - 0.6 * ex)
  s.renderer.setClearColor(new THREE.Color(0x000000).lerp(new THREE.Color(0xf1efea), st), 1)
  ;(floor.material as THREE.MeshBasicMaterial).color.set(0x000000).lerp(new THREE.Color(0xf1efea), st)
  studioKey.intensity = 2.2 * st; studioFill.intensity = 1.1 * st
  s.scene.environmentIntensity = env0 * f.light * (1 + 2.5 * st)
  crestMat.uniforms.uGain.value = 0.55 * f.beamGain
  s.frame(f.dt)
  const color = canvas.toDataURL('image/png')
  if (!f.depth) return color
  // depth pass: every opaque surface, no wavefronts, no floor
  const vis = [s.crests.visible, floor.visible, shadow.visible]
  s.crests.visible = false; floor.visible = false; shadow.visible = false
  const cc = s.renderer.getClearColor(new THREE.Color()), tm = s.renderer.toneMapping
  s.renderer.setClearColor(0xffffff, 1); s.renderer.toneMapping = THREE.NoToneMapping
  // an 8-bit depth pass is enough for depth of field once near/far hug the subject (about 1 mm per level)
  const dist = s.camera.position.distanceTo(new THREE.Vector3(...f.cam.target))
  const n0 = s.camera.near, f0 = s.camera.far
  s.camera.near = Math.max(1, dist - 140); s.camera.far = dist + 140; s.camera.updateProjectionMatrix()
  s.scene.overrideMaterial = depthMat
  s.renderer.render(s.scene, s.camera)
  const depth = canvas.toDataURL('image/png')
  const nf = s.camera.near + ',' + s.camera.far + ',' + dist
  s.camera.near = n0; s.camera.far = f0; s.camera.updateProjectionMatrix()
  s.scene.overrideMaterial = null; s.renderer.toneMapping = tm; s.renderer.setClearColor(cc, 1)
  ;[s.crests.visible, floor.visible, shadow.visible] = vis
  return color + '|' + depth + '|' + nf
}
;(window as any).S = s
;(window as any).ready = true
