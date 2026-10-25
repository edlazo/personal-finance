import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router'

import { AuthCard } from '@/components/auth/AuthCard'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

export function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (auth.status === 'authenticated') return <Navigate to={from} replace />

  const submit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await auth.login(email, password)
      void navigate(from, { replace: true })
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'No se pudo conectar con el servidor')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthCard
      title="Iniciar sesión"
      submitLabel="Entrar"
      submitting={submitting}
      error={error}
      onSubmit={submit}
      footer={
        <>
          ¿No tenés cuenta?{' '}
          <Link to="/registro" className="font-medium text-primary hover:underline">
            Registrate
          </Link>
        </>
      }
    >
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">Contraseña</Label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
    </AuthCard>
  )
}
