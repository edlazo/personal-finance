import { fireEvent, render, screen, within } from '@testing-library/react'
import { expect, test } from 'vitest'

import { formatMoney, type Money } from '@/lib/money'
import { mockDashboard } from '@/mocks/dashboard'

import { Dashboard } from './Dashboard'

test('los KPIs muestran el monto en es-AR y la variación con el color según si es bueno o malo', () => {
  render(<Dashboard />)

  expect(screen.getByText(/18\.450\.000,00/)).toBeInTheDocument()
  // Los ingresos subieron: es bueno, va en verde.
  expect(screen.getByText('+6,8% vs el mes anterior')).toHaveClass('text-primary')
  // Los gastos subieron: es malo, va en rojo.
  expect(screen.getByText('+6,5% vs el mes anterior')).toHaveClass('text-destructive')
})

test('el gráfico cambia de moneda con los botones ARS/USD', () => {
  render(<Dashboard />)
  const ars = screen.getByRole('button', { name: 'ARS' })
  const usd = screen.getByRole('button', { name: 'USD' })

  expect(ars).toHaveAttribute('aria-pressed', 'true')
  fireEvent.click(usd)
  expect(usd).toHaveAttribute('aria-pressed', 'true')
  expect(ars).toHaveAttribute('aria-pressed', 'false')
})

test('la dona muestra el porcentaje usado y lo pasado de presupuesto', () => {
  const over = {
    ...mockDashboard,
    budget: {
      spent: { amount: '1600000', currency: 'ARS' as const },
      limit: mockDashboard.budget.limit,
    },
  }
  const { unmount } = render(<Dashboard />)
  expect(screen.getByText('68,9%')).toBeInTheDocument()
  unmount()

  render(<Dashboard summary={over} />)
  expect(screen.getByText('108,1%')).toBeInTheDocument()
})

const ars = (amount: string): Money => ({ amount, currency: 'ARS' })
// Testing Library normaliza el texto del DOM (espacio duro → espacio) pero no lo que se busca.
const shown = (money: Money, signed = false) => formatMoney(money, signed).replace(/ /g, ' ')

test('el perfil y la tarjeta de crédito muestran los datos del usuario', () => {
  render(<Dashboard />)

  expect(screen.getByText('elias@example.com')).toBeInTheDocument()
  expect(screen.getByRole('img', { name: 'VISA terminada en 4821' })).toBeInTheDocument()
  expect(screen.getByText(shown(ars('1650000')))).toBeInTheDocument()
  expect(screen.getByText('Cierra 29 oct · vence 10 nov')).toBeInTheDocument()
})

test('los últimos movimientos muestran el signo según el tipo y linkean a Movimientos', () => {
  render(<Dashboard />)

  expect(screen.getByText(shown(ars('2350000'), true))).toHaveClass('text-primary')
  expect(screen.getByText(shown(ars('-84500'), true))).toBeInTheDocument()
  // Las transferencias entre cuentas no suman ni restan: van sin signo.
  expect(screen.getByText(shown(ars('300000')))).toHaveClass('text-muted-foreground')
  expect(screen.getByRole('link', { name: 'Ver todos' })).toHaveAttribute('href', '/movimientos')
})

test('seguridad avisa si la verificación en dos pasos está desactivada', () => {
  render(<Dashboard />)

  expect(screen.getByText('Desactivada: te recomendamos activarla')).toBeInTheDocument()
  expect(screen.getByText('2')).toBeInTheDocument()
})

test('los gastos por categoría van de mayor a menor con su porcentaje', () => {
  render(<Dashboard />)
  const list = within(screen.getByRole('list', { name: 'Gastos por categoría' }))
  const items = list.getAllByRole('listitem')

  expect(items[0]).toHaveTextContent('Vivienda')
  expect(items[0]).toHaveTextContent('41,9%')
  expect(items.at(-1)).toHaveTextContent('Ocio')
})

test('inversiones muestra el valor de la cartera y el resultado en verde si es positivo', () => {
  render(<Dashboard />)
  const pnl = screen.getByText(/de resultado/)

  expect(pnl).toHaveTextContent(`${shown(ars('800000'), true)} (+14,8%) de resultado`)
  expect(pnl).toHaveClass('text-primary')
})
