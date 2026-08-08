const DASH = '—'

export function fmtNum(v: number | null | undefined, digits = 2): string {
  return v == null ? DASH : v.toFixed(digits)
}

export function fmtRatio(v: number | null | undefined): string {
  return v == null ? DASH : `${(v * 100).toFixed(2)}%`
}

export function fmtPct(v: number | null | undefined): string {
  return v == null ? DASH : `${(v * 100).toFixed(1)}%`
}

export function fmtDate(v: string | null | undefined): string {
  return v ?? DASH
}

export function fmtSigned(v: number | null | undefined, digits = 2): string {
  if (v == null) return DASH
  const s = v > 0 ? '+' : ''
  return `${s}${v.toFixed(digits)}`
}

export function fmtDays(v: number | null | undefined): string {
  return v == null ? DASH : String(v)
}
