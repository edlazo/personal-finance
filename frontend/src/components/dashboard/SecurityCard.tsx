import { ShieldAlert, ShieldCheck } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { SecurityStatus } from '@/mocks/dashboard'

export function SecurityCard({ security }: { security: SecurityStatus }) {
  const { twoFactorEnabled, activeSessions } = security
  const Icon = twoFactorEnabled ? ShieldCheck : ShieldAlert

  return (
    <Card className="rounded-3xl">
      <CardHeader>
        <CardTitle>Seguridad</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex items-center gap-3">
          <Icon
            aria-hidden
            className={cn('size-8', twoFactorEnabled ? 'text-primary' : 'text-destructive')}
          />
          <div>
            <p className="font-medium">Verificación en dos pasos</p>
            <p className="text-muted-foreground">
              {twoFactorEnabled ? 'Activada' : 'Desactivada: te recomendamos activarla'}
            </p>
          </div>
        </div>
        <p>
          Sesiones activas: <span className="font-semibold tabular-nums">{activeSessions}</span>
        </p>
      </CardContent>
    </Card>
  )
}
