import { fireEvent, render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'

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
