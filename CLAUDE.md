# CLAUDE.md

PHASER research: the optical-cavity simulator (`src/`, `docs/ARCHITECTURE.md`, `tests/`, `examples/`) and the dated
research sprints under `research/`.

## Git workflow

- Work and commit directly on `main`. Don't create feature branches or PRs unless asked.
- The repository is `TensaCo/phaser-design`.

## The website lives elsewhere

- The PHASER site (https://phaser.tensaco.ai) is `apps/phaser` in the `TensaCo/tensaco.ai` repository, next to the TensaCo
  parent site (https://tensaco.ai). It moved out of this repo's `site/` on 2026-09-24; its history before that is here.
- `jacobfv.github.io/phaser-design` is a redirect-only GitHub Pages stub (repo `JacobFV/phaser-design`) pointing at
  https://phaser.tensaco.ai.
- Open items for the websites (deploy token, email sending) are tracked in `STATUS.md` in TensaCo/tensaco.ai.
- Energy claims on the site are *modeled* (Exp. 29): always pair them with that caveat, and never quote 1e6×.
