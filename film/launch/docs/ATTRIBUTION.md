# Asset attribution

| Asset | Source | Licence |
|---|---|---|
| PHASER machine (every product shot) | TensaCo: phaser.tensaco.ai three.js scene (`apps/phaser/src/components/machine`) and simulator, rendered by `harness/` | TensaCo |
| Act 1 lattice visualization | `src/viz_electrons.py` | TensaCo |
| People, garage, office, hospital, water, food, housing, steel, rack, transformer, city, cooling plate | AI-generated: stills by fal `nano-banana-pro` (/edit with references), motion by fal Kling 2.5 turbo pro image-to-video, lip-sync by fal `sync-lipsync/v2`. Prompts and request ids: `docs/generation-log.jsonl`, `src/prompts_*.py` | generated for TensaCo |
| Voices | AI: ElevenLabs v3 via fal (voices Brian, Jessica, Eric, Matilda) | per fal/ElevenLabs terms |
| Substation yard; line crew at substation | Videas Cl, Pexels | Pexels License (no attribution required) |
| Transmission towers through forest | Traveling on the Go, Pexels | Pexels License |
| Cooling towers by a river | Tom Fisk, Pexels | Pexels License |
| SuperMUC datacenter aisle | "SuperMUC: First Commercial Hot-Water Cooled Supercomputer to Consume 40% Less Energy" by IBM Research, **CC BY 3.0**, via Wikimedia Commons (excerpt, re-encoded) | CC BY 3.0 — **attribution required** in any public release (credit line or description) |
| Earth at night (v3) | NASA Earth Observatory, Black Marble 2016 (3 km) | Public domain (NASA) |
| Score (v3) | ElevenLabs Music via fal, plan in `gen/v3/music.json`; riser and impacts synthesized in `src/audio.py` | per fal/ElevenLabs terms |
| Cole Mercer (v3) | TensaCo AI-agent persona; likeness AI-generated from his tensaco.ai headshot | TensaCo |
| Fonts | Archivo (Omnibus-Type), IBM Plex Mono (IBM) | SIL Open Font License 1.1 |
| Sound and score (v1) | synthesized in `src/audio.py` | TensaCo |
| Score (v2) | composed with ElevenLabs Music via fal (`fal-ai/elevenlabs/music`), plan in `gen/v2/music.json` | per fal/ElevenLabs terms |
| Mei-Lin Zhou, Diane Kowalski (v2) | TensaCo AI-agent personas; likenesses AI-generated from their tensaco.ai headshots | TensaCo |

Stock sources and licences are the same files the site uses (`apps/phaser/public/video/broll/credits.json`, copied to
`assets/stock/credits-source.json`); the film uses the original UHD files from the same Pexels URLs.
