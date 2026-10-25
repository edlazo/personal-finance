import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatMoney, formatPercent, variation } from '@/lib/money'
import { cn } from '@/lib/utils'
import type { Kpi } from '@/mocks/dashboard'

type Props = {
  title: string
  kpi: Kpi
  /** true: subir es bueno (ingresos); false: subir es malo (gastos); sin valor: neutro. */
  higherIsBetter?: boolean
  highlighted?: boolean
}

export function KpiCard({ title, kpi, higherIsBetter, highlighted = false }: Props) {
  const change = variation(kpi.current, kpi.previous)
  const tone =
    highlighted || change === null || change === 0 || higherIsBetter === undefined
      ? 'neutral'
      : change > 0 === higherIsBetter
        ? 'good'
        : 'bad'

  return (
    <Card className={cn('rounded-3xl', highlighted && 'bg-primary text-primary-foreground')}>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        <p className="text-2xl font-semibold tabular-nums">{formatMoney(kpi.current)}</p>
        {change !== null && (
          <p
            className={cn(
              'text-xs',
              tone === 'good' && 'text-primary',
              tone === 'bad' && 'text-destructive',
              tone === 'neutral' &&
                (highlighted ? 'text-primary-foreground/85' : 'text-muted-foreground'),
            )}
          >
            {formatPercent(change, true)} vs el mes anterior
          </p>
        )}
      </CardContent>
    </Card>
  )
}
