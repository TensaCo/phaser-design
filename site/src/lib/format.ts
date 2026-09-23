const SUP = '⁰¹²³⁴⁵⁶⁷⁸⁹'
export const sup = (e: number) => String(Math.round(e)).split('').map((c) => (c === '-' ? '⁻' : SUP[Number(c)])).join('')

export function sci(v: number, digits = 2) {
  if (!isFinite(v)) return '—'
  if (v === 0) return '0'
  const e = Math.floor(Math.log10(Math.abs(v)))
  if (e >= -2 && e <= 3) return Number(v.toPrecision(digits)).toString()
  const m = v / 10 ** e
  return `${m.toFixed(Math.max(0, digits - 1))}×10${sup(e)}`
}

function scaled(v: number, table: [number, string][], unit: string) {
  if (!isFinite(v)) return '—'
  for (const [f, u] of table) if (Math.abs(v) >= f) return `${Number((v / f).toPrecision(3))} ${u}`
  return `${sci(v)} ${unit}`
}
export const joules = (v: number) => scaled(v, [[1e3, 'kJ'], [1, 'J'], [1e-3, 'mJ'], [1e-6, 'µJ'], [1e-9, 'nJ'], [1e-12, 'pJ'], [1e-15, 'fJ']], 'J')
export const watts = (v: number) => scaled(v, [[1e9, 'GW'], [1e6, 'MW'], [1e3, 'kW'], [1, 'W'], [1e-3, 'mW'], [1e-6, 'µW']], 'W')
export const units = (v: number) => {
  if (!isFinite(v)) return '—'
  if (v >= 1e9) return `${Number((v / 1e9).toPrecision(2))} G`
  if (v >= 1e6) return `${Number((v / 1e6).toPrecision(2))} M`
  if (v >= 1e4) return `${Number((v / 1e3).toPrecision(3))}k`
  if (v >= 1e3) return `${Number((v / 1e3).toPrecision(2))}k`
  return `${Math.round(v)}`
}
