export type Currency = 'ARS' | 'USD'

// La API manda los importes como string decimal (Decimal de Python), nunca como float.
export type Money = { amount: string; currency: Currency }

// shortcut: Number() solo para mostrar; exacto hasta ~15 dígitos, pasar a un decimal si se calcula con montos.
export function formatMoney({ amount, currency }: Money): string {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency }).format(Number(amount))
}

/** Variación relativa entre dos montos de la misma moneda; null si no hay base para comparar. */
export function variation(current: Money, previous: Money): number | null {
  if (current.currency !== previous.currency) {
    throw new Error(`No se comparan ${current.currency} y ${previous.currency} sin convertir`)
  }
  const base = Number(previous.amount)
  return base === 0 ? null : (Number(current.amount) - base) / Math.abs(base)
}

export function formatPercent(ratio: number, signed = false): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'percent',
    maximumFractionDigits: 1,
    signDisplay: signed ? 'exceptZero' : 'auto',
  }).format(ratio)
}
