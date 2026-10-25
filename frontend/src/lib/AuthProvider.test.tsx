import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'

import { useAuth } from './auth-context'
import { AuthProvider } from './AuthProvider'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

const ANA = {
  id: '1',
  email: 'ana@example.com',
  name: 'Ana',
  preferences: { default_rate_type: 'MEP' },
}

let fetchMock: ReturnType<typeof vi.fn>

function Probe() {
  const auth = useAuth()
  return (
    <>
      <p>{auth.status === 'authenticated' ? auth.user?.name : auth.status}</p>
      <button onClick={() => void auth.login('ana@example.com', 'clave-larga-123')}>Entrar</button>
      <button onClick={() => void auth.logout()}>Salir</button>
    </>
  )
}

beforeEach(() => {
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

test('sin cookie de refresh queda anónimo; el login carga el perfil y el logout lo saca', async () => {
  fetchMock.mockResolvedValueOnce(json(401, { detail: 'Token inválido o vencido' }))
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
  expect(await screen.findByText('anonymous')).toBeInTheDocument()

  fetchMock
    .mockResolvedValueOnce(json(200, { access_token: 'a', token_type: 'bearer', expires_in: 900 }))
    .mockResolvedValueOnce(json(200, ANA))
  fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))
  expect(await screen.findByText('Ana')).toBeInTheDocument()

  fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }))
  fireEvent.click(screen.getByRole('button', { name: 'Salir' }))
  expect(await screen.findByText('anonymous')).toBeInTheDocument()
})

test('con la cookie vigente la sesión continúa al recargar', async () => {
  fetchMock
    .mockResolvedValueOnce(json(200, { access_token: 'a', token_type: 'bearer', expires_in: 900 }))
    .mockResolvedValueOnce(json(200, ANA))

  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )

  expect(await screen.findByText('Ana')).toBeInTheDocument()
})
