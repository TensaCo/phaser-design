'use client'
import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { EV, LEVEL_LABEL, type EvidenceId, type EvidenceLevel } from '@/data/evidence'
import s from './Evidence.module.css'

const ORDER = Object.keys(EV) as EvidenceId[]
export const LEVEL_COLOR: Record<EvidenceLevel, string> = { measured: 'var(--cyan)', modeled: 'var(--violet)', theoretical: 'var(--fg-2)', target: 'var(--warm)' }

export function LevelTag({ level }: { level: EvidenceLevel }) {
  return (
    <span className={s.tag} data-level={level} style={{ color: LEVEL_COLOR[level] }}>
      <i className={s.glyph} data-level={level} />
      {LEVEL_LABEL[level]}
    </span>
  )
}

/** Superscript source marker. Hover, focus or tap opens the derivation and a link to the exact source lines. */
export function Evidence({ id, children }: { id: EvidenceId; children?: React.ReactNode }) {
  const ev = EV[id]
  const n = ORDER.indexOf(id) + 1
  const [open, setOpen] = useState(false)
  const [shift, setShift] = useState(0)
  const pop = useRef<HTMLSpanElement>(null)
  const root = useRef<HTMLSpanElement>(null)
  const pid = useId()
  const hideT = useRef<number>(0)

  useLayoutEffect(() => {
    if (!open || !pop.current) return
    const r = pop.current.getBoundingClientRect()
    const vw = document.documentElement.clientWidth
    if (r.right > vw - 12) setShift((x) => x - (r.right - vw + 12))
    else if (r.left < 12) setShift((x) => x + (12 - r.left))
  }, [open])
  useEffect(() => {
    if (!open) { setShift(0); return }
    const close = (e: PointerEvent) => { if (root.current && !root.current.contains(e.target as Node)) setOpen(false) }
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('pointerdown', close)
    document.addEventListener('keydown', esc)
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', esc) }
  }, [open])

  const show = () => { window.clearTimeout(hideT.current); setOpen(true) }
  const hide = () => { hideT.current = window.setTimeout(() => setOpen(false), 120) }

  return (
    <span ref={root} className={s.root} onMouseEnter={show} onMouseLeave={hide}>
      {children}
      <button
        className={s.mark}
        style={{ color: LEVEL_COLOR[ev.level] }}
        aria-expanded={open}
        aria-describedby={open ? pid : undefined}
        aria-label={`Source ${n}: ${ev.label} (${LEVEL_LABEL[ev.level]})`}
        onClick={() => setOpen((o) => !o)}
        onFocus={show}
        onBlur={hide}
      >
        <sup>{n}</sup>
      </button>
      {open && (
        <span ref={pop} id={pid} role="tooltip" className={s.pop} style={{ transform: `translateX(${shift}px)` }} onMouseEnter={show} onMouseLeave={hide}>
          <span className={s.head}>
            <LevelTag level={ev.level} />
            <span className={s.ref}>{ev.ref}</span>
          </span>
          <span className={s.value}>
            {ev.value}
            {ev.unit && <span className={s.unit}> {ev.unit}</span>}
          </span>
          <span className={s.label}>{ev.label}</span>
          <span className={s.deriv}>{ev.derivation}</span>
          <a className={s.src} href={ev.source} target="_blank" rel="noreferrer" onFocus={show} onBlur={hide}>
            view source ↗
          </a>
        </span>
      )}
    </span>
  )
}
