# Continuity bible

## 1. The machine (locked)

The canonical PHASER is the bench assembly that phaser.tensaco.ai draws: `apps/phaser/src/components/machine/hardware.ts` and
`StackScene.ts` in TensaCo/tensaco.ai, driven by the site's own simulator (`src/lib/phaser-sim.ts`, validated bit-for-bit
against the research simulator). Every product shot in the film is rendered **from that code**, through
`harness/machine.ts` (a scripted camera over the unmodified scene). The product therefore cannot redesign itself between
shots, and it is the same object investors see on the site.

| Part | Spec (mm, true scale) |
|---|---|
| Optical axis | vertical (+y); beam on x = z = 0 |
| Input mirror / coupler | y = 0: top face of the gain crystal (3 × 3 × 10 mm), 5 % coupling |
| Phase plates | **exactly four**, y = 5, 10, 15, 20; etched fused silica 5 × 5 × 1 mm, 64 × 64 px at 20 µm, AR coated, in slim black-anodised cells on cantilever arms |
| End mirror | y = 25: Ø6.35 mm concave (R 120 mm) dielectric mirror in a 25.4 mm kinematic mount, two black knurled M3 adjusters on top |
| Cage | two Ø4 mm stainless rods on 16 mm centres, at the back (cavity open to view) |
| Pump | TO-56 laser diode in a copper heatsink, leads twisted by hand in white heat-shrink |
| Readout | OV3660 camera module (M8 lens barrel) below the coupler, FPC to an ESP32-S3-DevKitC-1 |
| Wear | handling nicks, hairline scratches, a thumbprint; nothing looks new |
| Light | 650 nm; the only saturated red in the film, drawn as crest sheets whose cross-section is the simulated |E|² |

Scale cue for generated shots: about 8 cm tall, the size of a coffee mug.

References: `assets/ref/png/*.png` (renders), `assets/ref/phaser-ref-{0,1,3}.jpg` (the images given to the image model).

### Generated shots that contain the machine
Generated with the render as a reference image (`nano-banana-pro/edit`) and checked by counting plate cells.
Rejected and regenerated: `g-e2-adjuster` (wrong stack), `g-e5-inspect` (5+ plates), `g-e10-switch` (6 plates).
Known residual drift: in `g-e1-interview`, `g-b1-desk` and `g-e6-monitor` the machine is small and soft and reads as the same
object, but the plate count isn't countable; `g-e9-notebook` still shows extra cells and is **not used** in the cut.
`v-e10` (switch-on) shows the red glow brighter between the cells than the physics would give; used for 3.4 s.

## 2. People (dramatized, AI-generated)

| Role | Look (locked) | Reference | Voice |
|---|---|---|---|
| Optical engineer | South Asian woman, early 30s; dark hair tied back loosely; thin black-framed glasses; charcoal crewneck, sleeves pushed up; plain steel watch, left wrist | `gen/char/eng.png` | ElevenLabs v3 "Jessica" |
| Head of inference, AI company | Black man, mid 40s; close-cropped greying hair; short beard; navy overshirt over grey T-shirt | `gen/char/b1.png` | ElevenLabs v3 "Eric" |
| Infrastructure lead, datacenter operator | White woman, mid 50s; grey chin-length bob; reading glasses on head; green quarter-zip fleece over light-blue shirt | `gen/char/b2.png` | ElevenLabs v3 "Matilda" |

Every shot of a person is generated from its character sheet as a reference image, so faces and clothes are held within
each sequence. None of them is a real employee, customer or endorser; each first appearance carries a lower third
"dramatized role · AI-generated".

## 3. Places

- **Garage lab** (`gen/stills/g-garage-master.png`): two-car garage at night; worn wooden bench; black optical breadboard;
  pegboard; grey steel shelving with clear bins and blank masking-tape labels; unbranded boxes; small oscilloscope;
  3D-printed fixtures and older prototypes; whiteboard with a hand-drawn vertical cavity with four lines (the real
  architecture); warm 3200 K task lamp, neutral monitor spill. Every garage shot uses this plate as a reference.
- **AI company office**: open-plan, overcast daylight, glass-walled meeting room.
- **Operations room**: ordinary fluorescent ops room, no video wall.

## 4. Camera grammar

| Section | Movement | Lens (equiv.) |
|---|---|---|
| Product (renders) | mechanically perfect: slow push, crane, orbit | 16–34° vertical FOV (≈ 40–85 mm) |
| Science layer (renders, hardware hidden) | locked or slow push | ≈ 70 mm |
| Garage, office | handheld, 1–2 cm drift | 35–50 mm, 85–100 mm macro |
| Infrastructure, human systems | locked-off or slow dolly | 28–50 mm |

## 5. Colour

- Studio grade: true black, red bloom only from the beam, 0.28 vignette, fine grain.
- Documentary grade: 10 % desaturation, lifted blacks (0.018), slight warmth, grain 0.022, never teal–orange.
- World grade: 20 % desaturation, neutral, grain 0.02.
- Red (#ff2a12, 650 nm) appears only where light is: the beam, the numbers about light, aviation lights.

## 6. Typography

- Display: Archivo (variable), weight 500–700, width 75 for numerals (the site's face).
- Captions, qualifiers, labels: IBM Plex Mono Medium/SemiBold, uppercase, +0.12–0.16 em tracking.
- Two scales only: huge and tiny. Qualifiers ("MODELED") are always present and legible, one step subordinate.
- Centre label on every frame of every version: `PLANNED FUTURE PRODUCT LAUNCH VIDEO`, Plex Mono SemiBold 34 px (1080p),
  paper on 50 % black with a hairline box.
