import { describe, expect, test } from 'vitest'

import { formatMoney, formatPercent, variation, type Money } from './money'

const ars = (amount: string): Money => ({ amount, currency: 'ARS' })

// Intl usa espacios duros (U+00A0) entre el símbolo y el número.
const plain = (text: string) => text.replace(/ /g, ' ')

describe('formatMoney', () => {
  test('usa el formato es-AR con la moneda explícita', () => {
    expect(plain(formatMoney(ars('1234567.5')))).toBe('$ 1.234.567,50')
    expect(plain(formatMoney({ amount: '14350', currency: 'USD' }))).toBe('US$ 14.350,00')
  })
})

describe('variation', () => {
  test('calcula la variación relativa', () => {
    expect(variation(ars('110'), ars('100'))).toBeCloseTo(0.1)
    expect(variation(ars('90'), ars('100'))).toBeCloseTo(-0.1)
  })

  test('devuelve null si la base es cero y falla si las monedas difieren', () => {
    expect(variation(ars('50'), ars('0'))).toBeNull()
    expect(() => variation(ars('1'), { amount: '1', currency: 'USD' })).toThrow()
  })
})

test('formatPercent muestra el signo solo cuando se pide', () => {
  expect(plain(formatPercent(0.0307, true))).toBe('+3,1%')
  expect(plain(formatPercent(0.69))).toBe('69%')
})
