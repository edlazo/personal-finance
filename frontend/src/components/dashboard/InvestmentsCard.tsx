import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatMoney, formatPercent, variation } from '@/lib/money'
import { cn } from '@/lib/utils'
import type { InvestmentsSummary } from '@/mocks/dashboard'

export function InvestmentsCard({ investments }: { investments: InvestmentsSummary }) {
  const { value, cost, pnl } = investments
  const ratio = variation(value, cost)
  const pnlAmount = Number(pnl.amount)

  return (
    <Card className="rounded-3xl">
      <CardHeader>
        <CardTitle>Inversiones</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-sm text-muted-foreground">Valor de la cartera</p>
        <p className="text-2xl font-semibold tabular-nums">{formatMoney(value)}</p>
        <p
          className={cn(
            'text-sm font-medium tabular-nums',
            pnlAmount > 0 && 'text-primary',
            pnlAmount < 0 && 'text-destructive',
          )}
        >
          {formatMoney(pnl, true)}
          {ratio !== null && ` (${formatPercent(ratio, true)})`} de resultado
        </p>
      </CardContent>
    </Card>
  )
}
