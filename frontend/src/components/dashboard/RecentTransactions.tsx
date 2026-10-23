import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDay } from '@/lib/dates'
import { formatMoney } from '@/lib/money'
import { cn } from '@/lib/utils'
import type { Transaction } from '@/mocks/dashboard'

function signedAmount({ kind, amount }: Transaction): string {
  if (kind === 'transfer') return formatMoney(amount)
  return formatMoney(kind === 'expense' ? { ...amount, amount: `-${amount.amount}` } : amount, true)
}

export function RecentTransactions({ transactions }: { transactions: Transaction[] }) {
  return (
    <Card className="rounded-3xl">
      <CardHeader>
        <CardTitle>Últimos movimientos</CardTitle>
        <CardAction>
          <a href="/movimientos" className="text-sm font-medium text-primary hover:underline">
            Ver todos
          </a>
        </CardAction>
      </CardHeader>
      <CardContent>
        <ul className="divide-y">
          {transactions.slice(0, 5).map((tx) => (
            <li key={tx.id} className="flex items-center justify-between gap-3 py-2.5">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{tx.description}</p>
                <p className="text-xs text-muted-foreground">
                  {formatDay(tx.date)} · {tx.category}
                </p>
              </div>
              <span
                className={cn(
                  'shrink-0 text-sm font-semibold tabular-nums',
                  tx.kind === 'income' && 'text-primary',
                  tx.kind === 'transfer' && 'text-muted-foreground',
                )}
              >
                {signedAmount(tx)}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
