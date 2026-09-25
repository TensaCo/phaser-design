# Generation settings

Every request, with its full prompt, inputs and fal request id, is in `generation-log.jsonl`. The prompt sources are
`src/prompts_chars.py`, `src/prompts_scenes.py`, `src/prompts_video.py`, `src/script.py`.

| Stage | Model (fal endpoint) | Settings |
|---|---|---|
| Character sheets | `fal-ai/nano-banana-pro` | 16:9, 2K, three views on neutral grey |
| Scene stills | `fal-ai/nano-banana-pro/edit` | 16:9, 2K; reference images: PHASER render(s) (`assets/ref/phaser-ref-*.jpg`), character sheet, garage master plate |
| World stills (no people identity) | `fal-ai/nano-banana-pro` | 16:9, 2K |
| Motion | `fal-ai/kling-video/v2.5-turbo/pro/image-to-video` | 5 s (10 s for interviews), cfg 0.5, shared negative prompt (morphing, extra fingers, identity change, text, logos, neon, flares, fast moves) |
| Lip-sync | `fal-ai/sync-lipsync/v2` | `cut_off`; audio padded 0.3 s at head, 0.5 s tail |
| Voices | `fal-ai/elevenlabs/tts/eleven-v3` | stability 0.5; audio tags `[laughs]`, `[short pause]`; every line verified by transcription (whisper-1) |
| Product renders | the site's three.js scene (`harness/`) | headless Chromium on the GB10 GPU (ANGLE/OpenGL), 1920×1080, 24 fps, deterministic seed |
| Visualization | numpy (`src/viz_electrons.py`) | 1920×1080, 24 fps, seed 7 |

Shared prompt suffix (people/places): "Documentary film still, shot on a cinema camera, natural skin texture … no text, no
logos, no brand names, no readable writing anywhere. No neon, no cyberpunk, no blue or teal grading, no holograms, no
smoke, no lens flares."

QC passes applied to generated stills: plate count (exactly four), readable/branded text, hands, identity drift; rejected
shots are listed in `CONTINUITY.md`.
