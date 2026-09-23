import { LevelTag } from './Evidence'
import { REPO } from '@/data/evidence'
import s from './Footer.module.css'

export function Footer() {
  return (
    <footer className={s.footer}>
      <div className={s.levels}>
        <LevelTag level="measured" /><span>from the PHASER simulator (scalar wave optics, thin elements, TypeScript). There is no hardware yet.</span>
        <LevelTag level="modeled" /><span>computed from stated device or workload assumptions.</span>
        <LevelTag level="theoretical" /><span>physical bounds with ideal devices.</span>
        <LevelTag level="target" /><span>not supported by current evidence; shown for reference.</span>
      </div>
      <p className={s.meta}>
        Research sprint 2026-09-14 → 2026-09-23 · every number links to the lines it came from ·{' '}
        <a href={REPO} target="_blank" rel="noreferrer">github.com/JacobFV/phaser-design</a>
      </p>
    </footer>
  )
}
