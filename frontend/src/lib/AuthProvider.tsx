import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { api, refreshSession, setAccessToken } from './api'
import { AuthContext, type Auth, type Profile } from './auth-context'

type State = Pick<Auth, 'status' | 'user'>

const ANONYMOUS: State = { status: 'anonymous', user: null }

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>({ status: 'loading', user: null })

  const loadUser = useCallback(async () => {
    setState({ status: 'authenticated', user: await api<Profile>('/me') })
  }, [])

  // Al cargar la app: si la cookie del refresh sigue vigente, la sesión continúa.
  useEffect(() => {
    refreshSession()
      .then((ok) => (ok ? loadUser() : setState(ANONYMOUS)))
      .catch(() => setState(ANONYMOUS))
  }, [loadUser])

  const login = useCallback(
    async (email: string, password: string) => {
      // retry=false: un 401 acá son credenciales incorrectas, no una sesión vencida.
      const body = JSON.stringify({ email, password })
      const tokens = await api<{ access_token: string }>(
        '/auth/login',
        { method: 'POST', body },
        false,
      )
      setAccessToken(tokens.access_token)
      await loadUser()
    },
    [loadUser],
  )

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      const body = JSON.stringify({ name, email, password })
      await api('/auth/register', { method: 'POST', body }, false)
      await login(email, password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    try {
      await api('/auth/logout', { method: 'POST' }, false)
    } finally {
      setAccessToken(null)
      setState(ANONYMOUS)
    }
  }, [])

  const auth = useMemo(
    () => ({ ...state, login, register, logout }),
    [state, login, register, logout],
  )
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}
