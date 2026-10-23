import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatMoney, formatPercent } from '@/lib/money'
import type { CategoryExpense } from '@/mocks/dashboard'

export function ExpensesByCategory({ expenses }: { expenses: CategoryExpense[] }) {
  const total = expenses.reduce((sum, e) => sum + Number(e.amount.amount), 0)
  const sorted = [...expenses].sort((a, b) => Number(b.amount.amount) - Number(a.amount.amount))

  return (
    <Card className="rounded-3xl">
      <CardHeader>
        <CardTitle>Gastos por categoría</CardTitle>
      </CardHeader>
      <CardContent>
        <ul aria-label="Gastos por categoría" className="space-y-3">
          {sorted.map(({ category, amount }) => {
            const share = total > 0 ? Number(amount.amount) / total : 0
            return (
              <li key={category} className="space-y-1 text-sm">
                <div className="flex justify-between gap-2">
                  <span>{category}</span>
                  <span className="tabular-nums text-muted-foreground">
                    {formatMoney(amount)} · {formatPercent(share)}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-muted" aria-hidden>
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${share * 100}%` }}
                  />
                </div>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}
