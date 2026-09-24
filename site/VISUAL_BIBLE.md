# PHASER launch — visual bible

## Thesis the page must leave behind

1. **~1,000× less energy per step** than a GPU, modeled at one megapixel of optics. Every repeat of this number carries "modeled".
2. **10× bigger model: a GPU pays 100×, light pays 10×.** Dense electronics pay for every connection; light pays for every pixel.
3. **AI is running out of electricity, not chips.** Data centres pass Japan's total electricity use by 2030 (IEA).
4. **Close:** intelligence runs on electrons, which turn into heat. PHASER moves it to light.

Every section answers "why should I care?". Anything that only explains the mechanism is cut.

## Direction: "darkroom instrument"

Monochrome scientific-instrument photography. One saturated colour: **650 nm red, the actual wavelength of the modeled
device.** Red appears **only where light physically exists**: the beam, the wavefront, the red number that is about light,
and the aviation warning lights on the grid. Everything else is ink, paper and graphite.

References and what each contributes:
- Thomas Ruff, *expériences lumineuses*: light as the only subject, drawn as geometry on a dead ground.
- Hiroshi Sugimoto, *Lightning Fields*: full-bleed black with one electrical event.
- Ryoji Ikeda, *data-verse*: tiny monospaced numbers against huge emptiness, motion cut to a beat.
- Burtynsky and the Bechers: industry photographed flat, frontal and without drama. Used for the grid section.
- Teenage Engineering and Nothing: spec plates, tiny labels, one indicator colour.
- NASA schlieren: invisible physics made visible, and everything looks measurable.
- Tokyo TDC editorial: huge numerals beside 10 px captions, vertical side labels, generous margin.

## Palette (tokens)

| token | hex | use |
|---|---|---|
| `--ink` | `#0a0908` | darkroom ground |
| `--ink-2` | `#141210` | raised plates on dark |
| `--paper` | `#e9e5dc` | the one light section (the chart) |
| `--graphite` | `#8a857c` | captions, hairlines on dark |
| `--rule` | `rgba(233,229,220,.12)` | hairlines |
| `--red` | `#ff2a12` | 650 nm on dark |
| `--red-paper` | `#d8200a` | 650 nm on paper (contrast-safe) |

No blue, no gradients, no glass, no glow outside the beam itself.

## Type

- **Archivo** (variable width): display numerals and headlines. Condensed 62–75 width, 600–800 weight, tight tracking.
  Numerals are the page's graphic elements, sized 18–30 vw.
- **IBM Plex Mono**: captions, spec plates, footnotes. 10–12 px, uppercase with +0.12 em tracking for labels.
- Only two scales: huge and tiny. Body copy is rare, 17–19 px Archivo at normal width.

## Motion

- The machine carries the motion. It runs as a real FDTD wave simulation: a pinhole source, 7 phase-plate SLMs and a
  concave mirror that refocuses light onto the pinhole. Pulses are synchronous with the round trip, so one coherent
  wavefront bounces continuously and builds up.
- The camera is a long lens (22°), almost frontal, with a slow 15-second drift and faint pointer parallax. There are no cuts
  inside the hero.
- Page motion is discrete: numbers count once, rules draw once, and nothing floats. Reduced motion shows a still frame.

## Composition rules

1. At least 60 % of every viewport is black or paper.
2. Each section has exactly one hero element: the machine, the chart, the photograph, or the closing line.
3. Hairline spec plates (fig. no., λ = 650 nm, scale) replace labels on imagery.
4. Every number sits next to a footnote marker; the receipts live at the bottom, not inline.
5. Every frame must hold up as a screenshot on its own.

## Generated assets

- **fal `flux-2-max`**: a monochrome night photograph of grid infrastructure (a transmission tower and cooling towers) where
  the only colour is red aviation lights. It rhymes with the beam: the world's red light means *warning*, ours means *compute*.
- **Seedance 2.5 image-to-video** was planned for slow steam and blinking aviation lights. fal's media CDN
  (`*.fal.media`) is unreachable from the build machine, so no video could be downloaded. The same shot is done in WebGL instead
  (`LivingPhoto.tsx`), which is deterministic, a few KB, and loops forever: flow-noise displacement masked to the plume, and
  synced blinking on the red pixels. Stills come through fal's `sync_mode` (inline data URI).
- **Procedural** (three.js and GLSL): the machine. It is never generated video.
