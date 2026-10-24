import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'

import App from './App'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
const TOKENS = { access_token: 'a', token_type: 'bearer', expires_in: 900 }
const ANA = {
  id: '1',
  email: 'ana@example.com',
  name: 'Ana',
  preferences: { default_rate_type: 'MEP' },
}
// Cada Response se puede leer una sola vez: una nueva por pedido.
const noSession = () => json(401, { detail: 'Token inválido o vencido' })

let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
}

test('sin sesión, el dashboard redirige al login y al entrar vuelve al dashboard', async () => {
  fetchMock.mockResolvedValueOnce(noSession())
  renderAt('/')
  expect(await screen.findByRole('heading', { name: 'Iniciar sesión' })).toBeInTheDocument()

  fetchMock.mockResolvedValueOnce(json(200, TOKENS)).mockResolvedValueOnce(json(200, ANA))
  fill('Email', 'ana@example.com')
  fill('Contraseña', 'clave-larga-123')
  fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

  expect(await screen.findByRole('navigation', { name: 'Principal' })).toBeInTheDocument()
  // El header usa el usuario de GET /me, no uno de ejemplo.
  expect(screen.getByRole('heading', { name: 'Hola, Ana' })).toBeInTheDocument()
})

test('el login muestra el error de la API', async () => {
  fetchMock
    .mockResolvedValueOnce(noSession())
    .mockResolvedValueOnce(json(401, { detail: 'Email o contraseña incorrectos' }))
  renderAt('/login')
  await screen.findByRole('heading', { name: 'Iniciar sesión' })

  fill('Email', 'ana@example.com')
  fill('Contraseña', 'otra-clave')
  fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

  expect(await screen.findByRole('alert')).toHaveTextContent('Email o contraseña incorrectos')
})

test('el registro valida la contraseña en el navegador y muestra el 409 de la API', async () => {
  fetchMock
    .mockResolvedValueOnce(noSession())
    .mockResolvedValueOnce(json(409, { detail: 'El email ya está registrado' }))
  renderAt('/registro')
  await screen.findByRole('heading', { name: 'Crear cuenta' })

  expect(screen.getByLabelText('Contraseña')).toHaveAttribute('minLength', '10')
  fill('Nombre', 'Ana')
  fill('Email', 'ana@example.com')
  fill('Contraseña', 'clave-larga-123')
  fireEvent.click(screen.getByRole('button', { name: 'Registrarme' }))

  expect(await screen.findByRole('alert')).toHaveTextContent('El email ya está registrado')
})
