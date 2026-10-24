import { createContext, useContext } from 'react'

/** Forma de `GET /me`. */
export type Profile = {
  id: string
  email: string
  name: string
  preferences: { default_rate_type: string }
}

export type Auth = {
  status: 'loading' | 'authenticated' | 'anonymous'
  user: Profile | null
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<Auth | null>(null)

export function useAuth(): Auth {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth necesita un <AuthProvider>')
  return auth
}
