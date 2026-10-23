import { render, screen, within } from '@testing-library/react'
import { expect, test } from 'vitest'

import App from './App'

test('la sidebar tiene todas las secciones y marca el dashboard como actual', () => {
  render(<App />)
  const nav = within(screen.getByRole('navigation', { name: 'Principal' }))

  for (const name of ['Cuentas', 'Movimientos', 'Inversiones', 'Tarjetas', 'Reportes']) {
    expect(nav.getByRole('link', { name })).toBeInTheDocument()
  }
  expect(nav.getByRole('link', { name: 'Configuración' })).toBeInTheDocument()
  expect(nav.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('aria-current', 'page')
  expect(nav.getByRole('button', { name: 'Salir' })).toBeInTheDocument()
})

test('el header saluda al usuario y tiene búsqueda, notificaciones y avatar', () => {
  render(<App />)

  expect(screen.getByRole('heading', { name: 'Hola, Elias' })).toBeInTheDocument()
  expect(screen.getByRole('searchbox', { name: 'Buscar' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Notificaciones' })).toBeInTheDocument()
  expect(screen.getByText('EL')).toBeInTheDocument()
})

test('hay un atajo al contenido y el dashboard muestra los 12 módulos', () => {
  render(<App />)

  expect(screen.getByRole('link', { name: 'Ir al contenido' })).toHaveAttribute(
    'href',
    '#contenido',
  )
  const resumen = within(screen.getByRole('region', { name: 'Resumen' }))
  expect(resumen.getAllByText('Próximamente')).toHaveLength(12)
})
