import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'

import { AuthCard } from '@/components/auth/AuthCard'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

// Mismas reglas que la API (MIN/MAX_PASSWORD_LENGTH): el navegador avisa antes de enviar.
const MIN_PASSWORD = 10
const MAX_PASSWORD = 128

export function RegisterPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (auth.status === 'authenticated') return <Navigate to="/" replace />

  const submit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await auth.register(name, email, password)
      void navigate('/', { replace: true })
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'No se pudo conectar con el servidor')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthCard
      title="Crear cuenta"
      submitLabel="Registrarme"
      submitting={submitting}
      error={error}
      onSubmit={submit}
      footer={
        <>
          ¿Ya tenés cuenta?{' '}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Iniciá sesión
          </Link>
        </>
      }
    >
      <div className="space-y-2">
        <Label htmlFor="name">Nombre</Label>
        <Input
          id="name"
          autoComplete="name"
          required
          maxLength={100}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
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
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD}
          maxLength={MAX_PASSWORD}
          aria-describedby="password-hint"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <p id="password-hint" className="text-xs text-muted-foreground">
          Al menos {MIN_PASSWORD} caracteres.
        </p>
      </div>
    </AuthCard>
  )
}
