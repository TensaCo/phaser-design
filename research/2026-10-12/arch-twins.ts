// Twin configurations for the 2026-10-12 sprint (Exps. 36+). Each entry is a slmRing option set; the same object is stored in every
// design spec (`arch`) and rebuilt by verify.ts, so the JS check runs exactly the geometry the GPU twin was dumped from.
import type { RingOptions } from '../2026-09-14/arch'

const BIST = { gain: { G0: 2.2, sat: { kind: 'local' as const, saturationIntensity: 1 } }, nl: { amplitude: { kind: 'saturable' as const, strength: -0.6, saturationIntensity: 0.05 }, phase: { kind: 'kerr' as const, coefficient: 0.1 } } }
const A64 = { n: 64, spp: 1, roof: true, inputFirst: true, maxStep: 10e-3, ...BIST } satisfies RingOptions
const A128 = { ...A64, n: 128, lensAperture: 2.4e-3 } satisfies RingOptions // Exp. 39: twice the window, relay aperture scaled with it (as Exp. 31)

/** geometry only: gain/nl parameters and masks are overridden per design (twin.set_active / verify.ts). */
export const ARCHS: Record<string, RingOptions> = {
  A64s_amp: { ...A64, ampMask: { dark: 0 } },
  // Exp. 37: gain sheet z mm downstream of the image plane (physical cross-gain), absorber stays in the image plane
  ...Object.fromEntries([0.5, 1, 2, 3, 5, 8, 12].map((z) => [`A64s_amp_go${z}`, { ...A64, ampMask: { dark: 0 }, gainOffset: z * 1e-3 }])),
  A128s_amp: { ...A128, ampMask: { dark: 0 } },
}
