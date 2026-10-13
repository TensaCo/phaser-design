#!/bin/bash
# push code (not outputs, not the film) to the compute peer; pull a results dir back: sync.sh [pull <relative dir>]
cd "$(dirname "$0")/../.."
if [ "$1" = pull ]; then rsync -a "gb10-direct:phaser/$2/" "$2/"; exit; fi
rsync -a --exclude film --exclude .git --exclude 'research/2026-09-14/out' --exclude 'research/2026-10-12/out' ./ gb10-direct:phaser/
