/** "2026-10-22" → "22 oct". La fecha se interpreta en hora local, sin corrimiento por zona horaria. */
export function formatDay(isoDate: string): string {
  return new Date(`${isoDate}T00:00`).toLocaleDateString('es-AR', {
    day: 'numeric',
    month: 'short',
  })
}
