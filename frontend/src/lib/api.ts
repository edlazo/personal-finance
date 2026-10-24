/** Cliente de la API. El access token vive solo en memoria; el refresh, en una cookie httpOnly. */

const BASE = '/api'

/** Error con el formato problem+json (RFC 9457) que devuelve la API. */
export class ApiError extends Error {
  readonly status: number

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
  }
}

let accessToken: string | null = null
let refreshing: Promise<boolean> | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}

async function toApiError(response: Response): Promise<ApiError> {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null
  return new ApiError(response.status, body?.detail ?? 'Error inesperado')
}

/**
 * Renueva el access token con la cookie del refresh. Los pedidos simultáneos comparten una
 * sola renovación: el refresh rota, y un segundo intento con la cookie vieja cerraría la sesión.
 */
export function refreshSession(): Promise<boolean> {
  refreshing ??= fetch(`${BASE}/auth/refresh`, { method: 'POST' })
    .then(async (response) => {
      setAccessToken(
        response.ok ? ((await response.json()) as { access_token: string }).access_token : null,
      )
      return response.ok
    })
    .finally(() => {
      refreshing = null
    })
  return refreshing
}

/** Pedido autenticado; ante un 401 renueva la sesión una vez y reintenta. */
export async function api<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers)
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (init.body) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${BASE}${path}`, { ...init, headers })
  if (response.status === 401 && retry && (await refreshSession())) {
    return api<T>(path, init, false)
  }
  if (!response.ok) throw await toApiError(response)
  return (response.status === 204 ? undefined : await response.json()) as T
}
