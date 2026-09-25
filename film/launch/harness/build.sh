#!/bin/sh
cd "$(dirname "$0")"
SITE=$HOME/Documents/tensaco.ai/apps/phaser/src
$HOME/Documents/tensaco.ai/node_modules/.bin/esbuild machine.ts --bundle --format=esm --alias:@=$SITE \
  --outfile=dist/machine.js --log-level=warning
echo '<!doctype html><html><body style="margin:0;background:#0a0908"><script type="module" src="machine.js"></script></body></html>' > dist/index.html
