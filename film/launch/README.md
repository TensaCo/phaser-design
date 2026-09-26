# PHASER launch film — planned future product launch video

A 3:39 launch film for PHASER, set on **14 November 2026** (after the pre-seed), for investor pitches.
**Every frame of every version carries the centred label `PLANNED FUTURE PRODUCT LAUNCH VIDEO`.**
PHASER is depicted as built and launched; today every PHASER number is *modeled*, nothing is built, and every person
is an AI-generated dramatized role. Read `docs/CLAIMS.md` before showing it.

## v2

The current cut is **v2** (3:32): white-studio interviews with Mei-Lin Zhou and Diane Kowalski, an exploded-view reveal,
a composed three-movement score and photographic camera behaviour. See `docs/V2.md`. Every v2 file ends in `-v2`
(`out/PHASER-launch-film-master-1080p-v2.mp4` etc.); build with `bash src/run_v2.sh` (generation) then
`python src/compose.py master --edl=edl_v2` and `bash src/finalize_v2.sh`.

## Deliverables (`out/`)

| File | What |
|---|---|
| `PHASER-launch-film-master-1080p.mp4` | master, 16:9, 1920×1080, 24 fps, H.264 CRF 16, AAC 256k, −16 LUFS |
| `PHASER-launch-film-share-1080p.mp4` | the same master at CRF 24 (110 MB), for sending |
| `PHASER-launch-film-master-2160p.mp4` | 4K master: **Lanczos upscale** of the 1080p master (the renders and generated video are native 1080p) |
| `PHASER-launch-film-9x16.mp4` | social, 1080×1920, per-shot reframed, typography re-laid out |
| `PHASER-launch-60s.mp4`, `-30s` (product cut), `PHASER-reveal-15s.mp4`, and `…-9x16.mp4` of each | cut-downs |
| `PHASER-launch-film-clean-no-narration.mp4` | master picture, no narrator (interviews kept) |
| `PHASER-launch-film-clean-no-typography.mp4` | no titles, numbers or lower thirds (the label and the AI tags stay) |
| `stems/` | dialogue, narration, music, effects-ambience (48 kHz) |
| `keyframes/` | one still per shot |

## Documents (`docs/`)
`CLAIMS.md` (measured / modeled / projected / depicted-future / dramatized), `SHOT-LIST.md` (second by second, generated
from the EDL), `TRANSCRIPT.md`, `TRANSCRIPT-engineer.md`, `TRANSCRIPT-business.md`, `NARRATION.md`, `TYPOGRAPHY.md`,
`CONTINUITY.md` (the bible), `SOUND.md`, `ATTRIBUTION.md`, `GENERATION.md` (models and settings),
`generation-log.jsonl` (every fal request: prompt, inputs, request id).

## Source (editable project)

| Path | Role |
|---|---|
| `src/edl.py` | **the edit**: every shot, timing, text, voice placement, sound; the cut-downs |
| `src/script.py` | every spoken line and voice |
| `src/prompts_chars.py`, `src/prompts_scenes.py`, `src/prompts_video.py` | every generation prompt |
| `src/renders.py` + `harness/` | camera moves for product shots, rendered through the site's own three.js scene |
| `src/viz_electrons.py` | Act 1 lattice visualization |
| `src/compose.py`, `src/audio.py` | compositor (grade, type, label) and sound (synthesized beds, effects, score, mix, stems) |
| `src/jobs.py` | fal job runner (skips finished outputs) |
| `src/docs.py` | regenerates the shot list, transcripts and typography sheet from the EDL |

Rebuild: `python src/renders.py && for s in gen/render/*.json; do node harness/render.mjs $s ${s%.json}; done`, then
`python src/compose.py master` (or `vertical`, `nonarr`, `notype`, `cut60`, `cut30`, `cut15`, `cut60v`, `cut30v`, `cut15v`).
Generated media (`gen/`, ~2 GB) and renders are not committed; the prompts and log regenerate them.
Needs: the TensaCo/tensaco.ai checkout (for the scene), `FAL_KEY`, Python with numpy/scipy/Pillow/imageio-ffmpeg, Node + Playwright.
