'use client'
import { useEffect, useRef } from 'react'
import { animate, useInView, useReducedMotion } from 'framer-motion'

/** Number that eases into place once, when first visible. Renders the final value on the server and for reduced motion. */
export function CountUp({ to, decimals = 0, from = 0, duration = 1.6 }: { to: number; decimals?: number; from?: number; duration?: number }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, margin: '-10% 0px' })
  const reduced = useReducedMotion()
  useEffect(() => {
    if (!inView || reduced || !ref.current) return
    const el = ref.current
    const c = animate(from, to, { duration, ease: [0.16, 1, 0.3, 1], onUpdate: (v) => { el.textContent = v.toFixed(decimals) } })
    return () => c.stop()
  }, [inView, reduced, to, from, decimals, duration])
  return <span ref={ref}>{to.toFixed(decimals)}</span>
}
