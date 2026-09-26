#!/bin/sh
# Bundles the film harness against the site's own scene. The machine folder is copied and one function is patched:
# mergeByMaterial stamps each part's centre onto its vertices (aPart) so the exploded view can move parts rigidly.
# The site repo itself is never modified.
set -e
cd "$(dirname "$0")"
SITE=$HOME/Documents/tensaco.ai/apps/phaser/src
rm -rf site_machine && cp -r $SITE/components/machine site_machine
python3 - <<'PY'
p = 'site_machine/hardware.ts'; s = open(p).read()
old = "    for (const k of Object.keys(geo.attributes)) if (!['position', 'normal', 'uv'].includes(k)) geo.deleteAttribute(k)"
assert old in s
s = s.replace(old, old + """
    let top: THREE.Object3D = m; while (top.parent && top.parent !== root) top = top.parent
    if (!partCentre.has(top)) partCentre.set(top, new THREE.Box3().setFromObject(top).getCenter(new THREE.Vector3()))
    const pc = partCentre.get(top)!
    geo.setAttribute('aPart', new THREE.Float32BufferAttribute(new Float32Array(geo.attributes.position.count * 3).map((_, i) => [pc.x, pc.y, pc.z][i % 3]), 3))""")
s = s.replace("  const keep: THREE.Object3D[] = []", "  const keep: THREE.Object3D[] = []\n  const partCentre = new Map<THREE.Object3D, THREE.Vector3>()")
s = s.replace("if (!['position', 'normal', 'uv'].includes(k))", "if (!['position', 'normal', 'uv', 'aPart'].includes(k))")
open(p, 'w').write(s)
PY
$HOME/Documents/tensaco.ai/node_modules/.bin/esbuild machine.ts --bundle --format=esm --alias:@=$SITE \
  --outfile=dist/machine.js --log-level=warning
echo '<!doctype html><html><body style="margin:0;background:#000"><script type="module" src="machine.js"></script></body></html>' > dist/index.html
$HOME/Documents/tensaco.ai/node_modules/.bin/esbuild globe.ts --bundle --format=esm --outfile=dist/globe.js --log-level=warning
echo '<!doctype html><html><body style="margin:0;background:#000"><script type="module" src="globe.js"></script></body></html>' > dist/globe.html
cp blackmarble-8k.jpg dist/ 2>/dev/null || true
