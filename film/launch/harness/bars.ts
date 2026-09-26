// The stack-up: energy per multiply, to scale. H100 (INT8, 0.71 pJ) and TPU v4 (1.24 pJ) at chip level, and PHASER
// (<= 0.001 pJ, modeled at a million optical modes; phaser.tensaco.ai footnote 2). Heights are linear, so PHASER is a sliver.
import * as THREE from 'three'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
const W = Number(new URLSearchParams(location.search).get('w') ?? 1920), H = Number(new URLSearchParams(location.search).get('h') ?? 1080)
const canvas = document.createElement('canvas'); canvas.width = W; canvas.height = H; document.body.style.margin = '0'; document.body.appendChild(canvas)
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setSize(W, H, false); renderer.setClearColor(0x000000, 1)
renderer.toneMapping = THREE.ACESFilmicToneMapping
const scene = new THREE.Scene()
scene.fog = new THREE.Fog(0x000000, 14, 34)
const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.55
const camera = new THREE.PerspectiveCamera(35, W / H, 0.01, 200)
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js'
const RoundedBox = (w: number, h: number, d: number) => new RoundedBoxGeometry(w, h, d, 4, Math.min(0.06, h / 2.2))
const S = 8 / 1.24 // world units per pJ: TPU v4 is 8 units tall
const bars = [['H100', 0.71, -3.2], ['TPU v4', 1.24, 0], ['PHASER', 0.001, 3.2]] as const
const graphite = new THREE.MeshStandardMaterial({ color: 0x4a4744, roughness: 0.22, metalness: 0.92 })
const red = new THREE.MeshStandardMaterial({ color: 0xff2a12, emissive: 0xff2a12, emissiveIntensity: 0.55 })
const floor = new THREE.Mesh(new THREE.PlaneGeometry(80, 80).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 0.12, metalness: 0.7 }))
scene.add(floor)
const label = (text: string, x: number, col: string) => {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 256; const g = c.getContext('2d')!
  g.fillStyle = col; g.font = '600 120px "Archivo", "Helvetica Neue", Arial'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, 512, 128)
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = THREE.RepeatWrapping; t.repeat.x = 1
  const m = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 0.65).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: t, transparent: true }))
  m.position.set(x, 0.01, 1.9); scene.add(m)
}
for (const [name, pj, x] of bars) {
  const h = Math.max(pj * S, 0.02)
  const m = new THREE.Mesh(RoundedBox(1.8, h, 1.8), name === 'PHASER' ? red : graphite)
  m.position.set(x, h / 2, 0); scene.add(m)
  label(name, x, name === 'PHASER' ? '#ff2a12' : '#e9e5dc')
}
const glow = new THREE.PointLight(0xff2a12, 2.5, 5, 2); glow.position.set(3.2, 0.3, 0.6); scene.add(glow)
scene.add(new THREE.HemisphereLight(0xffffff, 0x080808, 0.15))
const key = new THREE.DirectionalLight(0xffffff, 1.2); key.position.set(-6, 12, 8); scene.add(key)
const rim = new THREE.DirectionalLight(0xffffff, 3.0); rim.position.set(6, 6, -10); scene.add(rim)
;(window as any).ready = true
;(window as any).info = () => ({ renderer: 'bars' })
;(window as any).shot = (f: { cam: { pos: number[]; target: number[]; fov: number } }) => {
  camera.position.set(...(f.cam.pos as [number, number, number])); camera.lookAt(new THREE.Vector3(...(f.cam.target as [number, number, number])))
  camera.fov = f.cam.fov; camera.updateProjectionMatrix(); renderer.render(scene, camera); return canvas.toDataURL('image/png')
}
