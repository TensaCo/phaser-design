// Film harness: the site's own PHASER scene (StackScene + hardware.ts + the live simulator), driven frame by frame
// with a scripted camera so every product shot in the film is the same machine the site draws.
import * as THREE from 'three'
import { StackScene, yAt } from '@/components/machine/StackScene'

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
  crestMat.uniforms.uGain.value = 0.55 * f.beamGain
  s.frame(f.dt)
  return canvas.toDataURL('image/png')
}
;(window as any).ready = true
