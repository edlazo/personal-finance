import { render, screen, within } from '@testing-library/react'
import { expect, test } from 'vitest'

import { DashboardLayout } from './DashboardLayout'

test('la sidebar tiene todas las secciones y marca el dashboard como actual', () => {
  render(<DashboardLayout />)
  const nav = within(screen.getByRole('navigation', { name: 'Principal' }))

  for (const name of ['Cuentas', 'Movimientos', 'Inversiones', 'Tarjetas', 'Reportes']) {
    expect(nav.getByRole('link', { name })).toBeInTheDocument()
  }
  expect(nav.getByRole('link', { name: 'Configuración' })).toBeInTheDocument()
  expect(nav.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('aria-current', 'page')
  expect(nav.getByRole('button', { name: 'Salir' })).toBeInTheDocument()
})

test('el header saluda al usuario y tiene búsqueda, notificaciones y avatar', () => {
  render(<DashboardLayout />)

  expect(screen.getByRole('heading', { name: 'Hola, Elias' })).toBeInTheDocument()
  expect(screen.getByRole('searchbox', { name: 'Buscar' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Notificaciones' })).toBeInTheDocument()
  expect(within(screen.getByRole('banner')).getByText('EL')).toBeInTheDocument()
})

test('hay un atajo al contenido y el dashboard ya no tiene módulos pendientes', () => {
  render(<DashboardLayout />)

  expect(screen.getByRole('link', { name: 'Ir al contenido' })).toHaveAttribute(
    'href',
    '#contenido',
  )
  const resumen = within(screen.getByRole('region', { name: 'Resumen' }))
  expect(resumen.queryByText('Próximamente')).not.toBeInTheDocument()
})
