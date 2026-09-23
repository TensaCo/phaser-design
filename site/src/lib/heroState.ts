/** Mutable state shared between the scroll driver, the WebGL loop and DOM counters (no React re-renders per frame). */
export const heroState = {
  morph: 0, // 0 = digital layer, 1 = PHASER cavity
  macs: 0,
  bytes: 0,
  trips: 0,
  inputs: 0,
  running: true,
  reduced: false,
  /** debug only (?debug in the URL): force the displayed round trip */
  forceLap: null as number | null,
}
export const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? ''
