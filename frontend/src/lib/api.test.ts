import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { api, ApiError, refreshSession, setAccessToken } from './api'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  setAccessToken(null)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

const authHeader = (call: number) =>
  new Headers((fetchMock.mock.calls[call][1] as RequestInit).headers).get('Authorization')

describe('api', () => {
  test('manda el access token y ante un 401 renueva la sesión una vez y reintenta', async () => {
    setAccessToken('viejo')
    fetchMock
      .mockResolvedValueOnce(json(401, { detail: 'Token inválido o vencido' }))
      .mockResolvedValueOnce(json(200, { access_token: 'nuevo' }))
      .mockResolvedValueOnce(json(200, { name: 'Ana' }))

    await expect(api('/me')).resolves.toEqual({ name: 'Ana' })

    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      '/api/me',
      '/api/auth/refresh',
      '/api/me',
    ])
    expect(authHeader(0)).toBe('Bearer viejo')
    expect(authHeader(2)).toBe('Bearer nuevo')
  })

  test('si la renovación falla, devuelve el error de la API (problem+json)', async () => {
    fetchMock
      .mockResolvedValueOnce(json(401, { detail: 'Token inválido o vencido' }))
      .mockResolvedValueOnce(json(401, { detail: 'Token inválido o vencido' }))

    const error = await api('/me').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 401, message: 'Token inválido o vencido' })
  })

  test('204 no tiene cuerpo', async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }))

    await expect(api('/auth/logout', { method: 'POST' })).resolves.toBeUndefined()
  })
})

test('las renovaciones simultáneas comparten un solo pedido', async () => {
  fetchMock.mockResolvedValue(json(200, { access_token: 'nuevo' }))

  const results = await Promise.all([refreshSession(), refreshSession(), refreshSession()])

  expect(results).toEqual([true, true, true])
  expect(fetchMock).toHaveBeenCalledTimes(1)
})
