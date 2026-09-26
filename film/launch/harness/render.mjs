// node render.mjs <frames.json> <outdir> [w h]  — renders each frame spec through the site's scene, writes PNGs
import { createRequire } from 'module'
import fs from 'fs'
import http from 'http'
import path from 'path'
const require = createRequire(import.meta.url)
const { chromium } = require(process.env.HOME + '/Documents/my-little-brain/node_modules/playwright')
const [, , framesFile, outDir, w = '1920', h = '1080'] = process.argv
const frames = JSON.parse(fs.readFileSync(framesFile, 'utf8'))
fs.mkdirSync(outDir, { recursive: true })
const dist = path.join(path.dirname(new URL(import.meta.url).pathname), 'dist')
const srv = http.createServer((q, r) => {
  const f = path.join(dist, q.url.split('?')[0] === '/' ? 'index.html' : q.url.split('?')[0])
  r.writeHead(200, { 'content-type': f.endsWith('.js') ? 'text/javascript' : f.endsWith('.jpg') ? 'image/jpeg' : f.endsWith('.json') ? 'application/json' : f.endsWith('.bin') ? 'application/octet-stream' : 'text/html' }); r.end(fs.readFileSync(f))
}).listen(0)
const port = srv.address().port
const browser = await chromium.launch({ args: ['--use-angle=gl', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'] })
const page = await browser.newPage({ viewport: { width: +w, height: +h } })
page.on('console', (m) => { if (m.type() === 'error') console.error('page:', m.text()) })
page.on('pageerror', (e) => console.error('pageerror:', e.message))
await page.goto(`http://localhost:${port}/${process.env.PAGE ?? ''}?w=${w}&h=${h}`)
await page.waitForFunction('window.ready === true', null, { timeout: 120000 })
console.log(JSON.stringify(await page.evaluate('info()')))
const t0 = Date.now()
for (let i = 0; i < frames.length; i++) {
  const out = path.join(outDir, String(i).padStart(5, '0') + '.png')
  if (fs.existsSync(out) && !frames[i].force) { await page.evaluate((f) => shot(f), { ...frames[i], dt: frames[i].dt }); continue }
  const url = await page.evaluate((f) => shot(f), frames[i])
  const [color, depth, nf] = url.split('|')
  fs.writeFileSync(out, Buffer.from(color.split(',')[1], 'base64'))
  if (depth) { fs.writeFileSync(out.replace('.png', '.depth.png'), Buffer.from(depth.split(',')[1], 'base64')); fs.writeFileSync(out.replace('.png', '.depth.txt'), nf) }
  if (i % 24 === 0) console.log(`${i}/${frames.length} ${((Date.now() - t0) / 1000 / (i + 1)).toFixed(2)} s/frame`)
}
await browser.close(); srv.close()
