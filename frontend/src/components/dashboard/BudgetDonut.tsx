import { Pie, PieChart } from 'recharts'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartContainer, type ChartConfig } from '@/components/ui/chart'
import { formatMoney, formatPercent, type Money } from '@/lib/money'

const config = {
  spent: { label: 'Usado', color: 'var(--primary)' },
  left: { label: 'Disponible', color: 'var(--muted)' },
} satisfies ChartConfig

export function BudgetDonut({ spent, limit }: { spent: Money; limit: Money }) {
  const used = Number(spent.amount)
  const total = Number(limit.amount)
  const ratio = total > 0 ? used / total : 0
  const data = [
    { name: 'spent', value: used, fill: 'var(--color-spent)' },
    { name: 'left', value: Math.max(total - used, 0), fill: 'var(--color-left)' },
  ]

  return (
    <Card className="rounded-3xl">
      <CardHeader>
        <CardTitle>Presupuesto del mes</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-2">
        <div className="relative size-44">
          <ChartContainer config={config} className="aspect-square size-44" aria-hidden>
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                innerRadius={58}
                outerRadius={80}
                startAngle={90}
                endAngle={-270}
                stroke="none"
              />
            </PieChart>
          </ChartContainer>
          <p className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-semibold tabular-nums">{formatPercent(ratio)}</span>
            <span className="text-xs text-muted-foreground">usado</span>
          </p>
        </div>
        <p className="text-sm text-muted-foreground">
          {formatMoney(spent)} de {formatMoney(limit)}
        </p>
      </CardContent>
    </Card>
  )
}
