import { useState } from 'react'
import { Area, AreaChart, CartesianGrid, XAxis } from 'recharts'

import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import { formatMoney, type Currency } from '@/lib/money'
import type { NetWorthPoint } from '@/mocks/dashboard'

const config = { value: { label: 'Patrimonio', color: 'var(--primary)' } } satisfies ChartConfig

const monthLabel = (month: string) =>
  new Date(`${month}-01T00:00`).toLocaleDateString('es-AR', { month: 'short' })

export function NetWorthChart({ history }: { history: NetWorthPoint[] }) {
  const [currency, setCurrency] = useState<Currency>('ARS')
  const data = history.map((point) => ({
    month: point.month,
    value: Number(currency === 'ARS' ? point.ars : point.usd),
  }))

  return (
    <Card className="rounded-3xl md:col-span-2">
      <CardHeader>
        <CardTitle>Evolución del patrimonio</CardTitle>
        <CardAction>
          <div role="group" aria-label="Moneda del gráfico" className="flex gap-1">
            {(['ARS', 'USD'] as const).map((option) => (
              <Button
                key={option}
                size="sm"
                variant={option === currency ? 'default' : 'outline'}
                aria-pressed={option === currency}
                onClick={() => setCurrency(option)}
              >
                {option}
              </Button>
            ))}
          </div>
        </CardAction>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="aspect-auto h-56 w-full">
          <AreaChart data={data} margin={{ left: 8, right: 8 }}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="month" tickFormatter={monthLabel} tickLine={false} axisLine={false} />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  labelFormatter={(month) => monthLabel(String(month))}
                  formatter={(value) => formatMoney({ amount: String(value), currency })}
                />
              }
            />
            <Area
              dataKey="value"
              type="monotone"
              stroke="var(--color-value)"
              fill="var(--color-value)"
              fillOpacity={0.15}
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
