// Planet-scale shot: NASA Black Marble 2016 night lights (public domain) on a sphere, a thin atmosphere rim, and a
// scripted camera. Every frame is a pure function of the frame spec.
import * as THREE from 'three'
const W = Number(new URLSearchParams(location.search).get('w') ?? 1920)
const H = Number(new URLSearchParams(location.search).get('h') ?? 1080)
const canvas = document.createElement('canvas'); canvas.width = W; canvas.height = H
document.body.style.margin = '0'; document.body.appendChild(canvas)
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
renderer.setSize(W, H, false); renderer.setClearColor(0x000000, 1)
const scene = new THREE.Scene()
const camera = new THREE.PerspectiveCamera(35, W / H, 0.0005, 100)
const R = 1
const tex = new THREE.TextureLoader().load('blackmarble-8k.jpg', () => { (window as any).ready = true })
tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 16
const earth = new THREE.Mesh(new THREE.SphereGeometry(R, 256, 128), new THREE.ShaderMaterial({
  uniforms: { uMap: { value: tex }, uGain: { value: 1.0 } },
  vertexShader: `varying vec2 vUv; varying vec3 vN; varying vec3 vP; void main(){ vUv=uv; vN=normalize(normalMatrix*normal); vec4 p=modelViewMatrix*vec4(position,1.); vP=p.xyz; gl_Position=projectionMatrix*p; }`,
  fragmentShader: `uniform sampler2D uMap; uniform float uGain; varying vec2 vUv; varying vec3 vN; varying vec3 vP;
    void main(){ vec3 c = texture2D(uMap, vUv).rgb; c = pow(c, vec3(1.12)) * 2.5 * uGain; // keep the faint land, lift the lights
      float rim = pow(1.0 - max(dot(normalize(-vP), vN), 0.0), 3.0);
      gl_FragColor = vec4(c + vec3(0.10, 0.11, 0.13) * rim * 0.6, 1.0); }`,
}))
scene.add(earth)
const atmo = new THREE.Mesh(new THREE.SphereGeometry(R * 1.006, 256, 128), new THREE.ShaderMaterial({
  vertexShader: `varying vec3 vN; varying vec3 vP; void main(){ vN=normalize(normalMatrix*normal); vec4 p=modelViewMatrix*vec4(position,1.); vP=p.xyz; gl_Position=projectionMatrix*p; }`,
  fragmentShader: `varying vec3 vN; varying vec3 vP; void main(){ float f = pow(1.0 - abs(dot(normalize(-vP), vN)), 9.0); gl_FragColor = vec4(vec3(0.62, 0.6, 0.58) * f * 0.28, f * 0.3); }`,
  transparent: true, side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false,
}))
scene.add(atmo)
/** lat/lon (deg) → point on the sphere, matching SphereGeometry's UVs */
const ll = (lat: number, lon: number, r = R) => {
  const phi = (lon + 180) * Math.PI / 180, th = (90 - lat) * Math.PI / 180
  return new THREE.Vector3(-r * Math.cos(phi) * Math.sin(th), r * Math.cos(th), r * Math.sin(phi) * Math.sin(th))
}
;(window as any).shot = (f: { cam: { lat: number; lon: number; alt: number }; look: { lat: number; lon: number; alt: number }; fov: number; gain?: number }) => {
  const p = ll(f.cam.lat, f.cam.lon, R + f.cam.alt), q = ll(f.look.lat, f.look.lon, R + f.look.alt)
  camera.position.copy(p); camera.up.copy(p.clone().normalize()); camera.lookAt(q)
  camera.fov = f.fov; camera.updateProjectionMatrix()
  ;(earth.material as THREE.ShaderMaterial).uniforms.uGain.value = f.gain ?? 1
  renderer.render(scene, camera)
  return canvas.toDataURL('image/png')
}
;(window as any).info = () => ({ renderer: 'globe' })
