export { cn } from 'cn'

/** Iniciales de las dos primeras palabras: "Elias Lazo" → "EL". */
export function initials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}
