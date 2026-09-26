# Factual-claim source sheet

**Read this first.** This is a *planned future product launch video*. It is set on **14 November 2026**, after the pre-seed
round, and it depicts PHASER as built, launched and in use. **As of this film's production (25 September 2026), none of that
has happened yet:** every PHASER performance number is *modeled* in simulation, no PHASER hardware has been built or
measured, and there are no users or customers. The persistent centre label (PLANNED FUTURE PRODUCT LAUNCH VIDEO) and the
per-shot "dramatization / AI-generated" tags exist so that nobody mistakes the film for a record of events. When the film is
shown to investors, present it as the launch film we plan to release, not as evidence of traction.

Categories used below:
- **Modeled**: computed by the PHASER research simulator (TensaCo/phaser-design); not measured on hardware.
- **Projected**: extrapolated beyond what was simulated.
- **External**: a published third-party figure.
- **Depicted (future)**: something the film shows as having happened by 14 Nov 2026; true today only as a plan.
- **Dramatized**: a fictional person or statement.

## On-screen numbers

| On screen | Category | What it means | Source |
|---|---|---|---|
| **0.26 ns** per input step: one round trip up the stack and back · MODELED | Modeled | Optical round trip of the linear stack (25 mm between mirrors, four 1 mm fused-silica plates), glass included; one round trip per input (K = 1). | phaser.tensaco.ai "The machine" (footnote 5); research/2026-09-14 Exps. 30, 33 |
| **10 billion** input steps per second, with light pulses in flight · MODELED | Modeled | Time-slot multiplexing: about 3 pulses in flight in the stack (3.9 × 10⁹ steps/s per stream); per-stream quality held to 80 pulses in simulation. | Site footnote 3; Exps. 32, 34 |
| **≤ 0.001 pJ** per equivalent multiply, at a million optical modes · MODELED | Modeled + projected | 0.06–1 fJ per *equivalent* multiply, modeled at 10⁶ optical modes; the simulation measured scaling to 65k modes, so 10⁶ is extrapolated. | Site footnote 2; research/notes/energy-per-multiply.md |
| today's AI chips: **~1 pJ** per multiply-accumulate | External | 0.7–2 pJ/MAC at chip level (H100 INT8 ≈ 0.71 pJ, TPU v4 ≈ 1.24 pJ, H100 BF16 ≈ 2 pJ). | Site footnote 2 |
| **200–3,000×** less energy per step than an equally capable dense recurrent network · MODELED at a million optical modes | Modeled + projected | Versus a dense echo-state network on an 8-bit chip at 0.2 pJ/MAC; PHASER extrapolated to 10⁶ modes. At today's simulated sizes PHASER is at parity (1.5–1.9 nJ/step). **Never quote 10⁶×.** | Site footnote 1; REPORT.md Exps. 31, 34, 35 |
| **128 weeks** to get a large power transformer · Wood Mackenzie, 2025 | External | Power-transformer lead times of about 128 weeks in Q2 2025. | Wood Mackenzie (Aug 2025), cited on phaser.tensaco.ai (footnote 7) |
| Tagline: "A neural accelerator that runs at the speed of light." | Positioning | The site's own tagline. | phaser.tensaco.ai hero |
| "PHASER runs it on light." / "Intelligence runs on electrons." | Positioning | The site's own section copy. | phaser.tensaco.ai "01 / The light" |
| "Now live · phaser.tensaco.ai" | Depicted (future) | The website is live today; the *product* is not. In the film's 14 Nov 2026 setting, "now live" refers to the product launch. | — |

Numbers checked against the live site (https://phaser.tensaco.ai) on 2026-09-25. The site also states 79 % of light kept per
round trip (modeled) and 1.28 mm × 25 mm cavity geometry; the film shows the geometry but does not put those numbers on screen.

## Spoken claims

| Line | Speaker | Category | Note |
|---|---|---|---|
| "The math was the easy part." … "four pieces of glass in a cavity" … "a few microns" | Engineer | Dramatized; architecture is real (4 plates, cavity) | The engineering difficulties named (alignment tolerance, error compounding over recurrent passes) are real properties of the design, from the research. The anecdotes are invented. |
| "Before the pre-seed, half of this was 3D-printed. Now it's, like… a third." | Engineer | Dramatized, depicted (future) | Refers to the pre-seed round the film assumes has closed by 14 Nov 2026. |
| "the camera image finally matched what the simulator said" | Engineer | Depicted (future) | No hardware measurement exists yet. The simulator itself is real and runs on the site. |
| "I didn't care that it was optical. I cared that it was fast." / "thought the dashboard was broken" / "that's our energy bill?" / "how often do we want to?" / "waiting 200 milliseconds felt broken" / "You start arguing about transformers." | Business roles | Dramatized | No customers, workloads, dashboards or bills exist. On screen during the energy-bill line: "Dramatization. PHASER energy figures are modeled." |
| "eventually, the software problem becomes a power problem" / "the bottleneck stops being algorithms" | Narrator | Argument | Supported by the external grid-constraint figures on the site (transformer lead times, 5+ year interconnection queues, IEA). |
| "PHASER changes the slope of that curve." / "It makes computation ask for less of it." | Narrator | Modeled | Rests on the modeled energy-per-step result above. The film does not claim PHASER eliminates datacenter energy use, or solves hospital, food or water problems; Act 6 only says energy is shared by all of them. |

## What the film deliberately does not say
- No "measured" anything; no benchmark, customer, deployment, saving, volume, certification or approval.
- No 10⁶× figure (the research found that would need ≥ 7.5 × 10⁸ modes).
- No claim that PHASER solves energy scarcity, hunger, or healthcare.

## v3 additions
| On screen / spoken | Category | Source / note |
|---|---|---|
| **~945 TWh**: data-centre electricity use by 2030, more than Japan uses today · IEA, Energy and AI (2025) · projection | External projection | IEA *Energy and AI* (Apr 2025): data-centre demand reaches ~945 TWh in 2030, slightly more than Japan's total electricity consumption today. The PHASER site cites the same comparison. |
| Cole: "Most of the energy in a chip goes into pushing charge through wire… and then pulling the heat back out of the room. Light crossing glass barely loses anything." | Physics framing | Matches the site's copy ("Pushing charge through a wire costs energy every time. Light crossing glass barely loses any…"). PHASER still loses 10–30 % per round trip to mirrors and coatings and pays for gain and readout (Exps. 33–34); the film does not claim zero loss. |
| Customer (head of platform): "thought the dashboard was broken" / "that's our energy bill?" | Dramatized; depicted future | No customers exist. On screen: "Dramatization. PHASER energy figures are modeled." |
| Globe: NASA Black Marble 2016 night lights | Real imagery | Public domain (NASA Earth Observatory). |
| Cold open CRT | Prop | A generic, unbranded industrial CRT terminal (an Apple Macintosh the model first produced was replaced). |

## v4 additions
| Spoken / on screen | Category | Derivation |
|---|---|---|
| "Two hundred and sixty picoseconds" / **0.26 ns** | Modeled | One round trip of the linear stack (site footnote 5). |
| "Seven hundred times less energy than NVIDIA's H100" / **700×** | Modeled + projected vs external | PHASER ≤ 0.001 pJ (0.06–1 fJ) per *equivalent* multiply, modeled and extrapolated to 10⁶ optical modes; NVIDIA H100 INT8 ≈ 0.71 pJ per MAC at chip level (site footnote 2). 0.71 pJ / 1 fJ = 710× at PHASER's worst modeled case; the film rounds down to 700×. |
| "Twelve hundred times less than Google's TPU v4" / **1,200×** | Same | TPU v4 ≈ 1.24 pJ per MAC at chip level; 1.24 pJ / 1 fJ = 1,240×, rounded down to 1,200×. |
| 3D stack-up: H100, TPU v4, PHASER bars to linear scale | Same numbers | Heights 0.71 : 1.24 : 0.001. |
| "Each plate is fused silica, etched with 4,096 pixels of phase, each twenty microns across" | Design | 64 × 64 px at 20 µm (site, VISUAL_BIBLE). |
| "One step of a recurrent neural network, done by physics" | Architecture | The linear stack is one recurrent step per round trip (Exps. 30, 33). |
| Ignition story ("the cavity ignited") | Depicted future | Lasing threshold, when gain exceeds loss with the cavity aligned, is the physical meaning; no hardware has been built. |
| Cole: "…when thinking stops costing the Earth" | Rhetoric | Vision statement, no quantitative claim. |

Not said, deliberately: "world's fastest", or any speed multiple over a named chip. The 0.26 ns step is a modeled
optical round trip, not comparable to a GPU clock cycle, and no source ranks PHASER against every computing system.
The density argument (≈10¹⁸ equivalent multiplies/s in a few cm³ at 10⁶ modes and 10 GHz) stacks extrapolations and
ignores the readout (≈10¹⁶ samples/s of detector bandwidth), which the research lists as the open bottleneck.
