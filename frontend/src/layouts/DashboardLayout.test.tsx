import { fireEvent, render, screen, within } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import { AuthContext, type Auth } from '@/lib/auth-context'

import { DashboardLayout } from './DashboardLayout'

function renderLayout(logout = vi.fn()) {
  const auth: Auth = {
    status: 'authenticated',
    user: {
      id: '1',
      email: 'elias@example.com',
      name: 'Elias Lazo',
      preferences: { default_rate_type: 'MEP' },
    },
    login: vi.fn(),
    register: vi.fn(),
    logout,
  }
  render(
    <AuthContext.Provider value={auth}>
      <DashboardLayout />
    </AuthContext.Provider>,
  )
}

test('la sidebar tiene todas las secciones y marca el dashboard como actual', () => {
  renderLayout()
  const nav = within(screen.getByRole('navigation', { name: 'Principal' }))

  for (const name of ['Cuentas', 'Movimientos', 'Inversiones', 'Tarjetas', 'Reportes']) {
    expect(nav.getByRole('link', { name })).toBeInTheDocument()
  }
  expect(nav.getByRole('link', { name: 'Configuración' })).toBeInTheDocument()
  expect(nav.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('aria-current', 'page')
  expect(nav.getByRole('button', { name: 'Salir' })).toBeInTheDocument()
})

test('el header saluda al usuario y tiene búsqueda, notificaciones y avatar', () => {
  renderLayout()

  expect(screen.getByRole('heading', { name: 'Hola, Elias' })).toBeInTheDocument()
  expect(screen.getByRole('searchbox', { name: 'Buscar' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Notificaciones' })).toBeInTheDocument()
  expect(within(screen.getByRole('banner')).getByText('EL')).toBeInTheDocument()
})

test('hay un atajo al contenido y el dashboard ya no tiene módulos pendientes', () => {
  renderLayout()

  expect(screen.getByRole('link', { name: 'Ir al contenido' })).toHaveAttribute(
    'href',
    '#contenido',
  )
  const resumen = within(screen.getByRole('region', { name: 'Resumen' }))
  expect(resumen.queryByText('Próximamente')).not.toBeInTheDocument()
})

test('Salir cierra la sesión', () => {
  const logout = vi.fn().mockResolvedValue(undefined)
  renderLayout(logout)

  fireEvent.click(screen.getByRole('button', { name: 'Salir' }))

  expect(logout).toHaveBeenCalledOnce()
})
