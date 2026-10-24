import type { FormEvent, ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

type Props = {
  title: string
  submitLabel: string
  submitting: boolean
  error: string | null
  onSubmit: () => Promise<void>
  footer: ReactNode
  children: ReactNode
}

/** Tarjeta común de login y registro: formulario, error de la API y botón. */
export function AuthCard({
  title,
  submitLabel,
  submitting,
  error,
  onSubmit,
  footer,
  children,
}: Props) {
  const submit = (event: FormEvent) => {
    event.preventDefault()
    void onSubmit()
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm rounded-3xl">
        <CardHeader>
          <CardTitle>
            <h1 className="text-xl">{title}</h1>
          </CardTitle>
        </CardHeader>
        <form onSubmit={submit}>
          <CardContent className="space-y-4">
            {children}
            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}
          </CardContent>
          <CardFooter className="mt-4 flex-col gap-3">
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? 'Un momento…' : submitLabel}
            </Button>
            <p className="text-sm text-muted-foreground">{footer}</p>
          </CardFooter>
        </form>
      </Card>
    </main>
  )
}
