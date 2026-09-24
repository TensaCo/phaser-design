# CLAUDE.md

## Git workflow

- Work and commit directly on `main`. Don't create feature branches or PRs unless asked.
- Pushing `main` with changes under `site/` deploys the launch page to GitHub Pages (`.github/workflows/pages.yml`).

## Launch site (`site/`)

- Next.js static export. Run it with `npm run dev` in `site/`, then open http://localhost:3217/phaser-design/.
- Art direction and claim rules live in `site/VISUAL_BIBLE.md`. Energy claims are *modeled*: always pair them with that
  caveat and a receipt, and never quote 1e6×.
