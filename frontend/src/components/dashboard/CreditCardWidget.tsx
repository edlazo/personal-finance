import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDay } from '@/lib/dates'
import { formatMoney } from '@/lib/money'
import type { CreditCardSummary } from '@/mocks/dashboard'

export function CreditCardWidget({ card }: { card: CreditCardSummary }) {
  const { nextStatement } = card
  return (
    <Card className="rounded-3xl">
      <CardHeader>
        <CardTitle>Tarjeta de crédito</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          role="img"
          aria-label={`${card.brand} terminada en ${card.last4}`}
          className="flex aspect-[1.6] flex-col justify-between rounded-2xl bg-gradient-to-br from-primary to-primary/70 p-5 text-primary-foreground"
        >
          <span className="self-end text-sm font-semibold tracking-wide">{card.brand}</span>
          <span className="font-mono text-lg tracking-widest">•••• •••• •••• {card.last4}</span>
          <span className="text-xs tracking-wide">{card.holder}</span>
        </div>
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-muted-foreground">Disponible</dt>
            <dd className="font-semibold tabular-nums">{formatMoney(card.available)}</dd>
            <dd className="text-xs text-muted-foreground">de {formatMoney(card.limit)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Próximo resumen</dt>
            <dd className="font-semibold tabular-nums">{formatMoney(nextStatement.amount)}</dd>
            <dd className="text-xs text-muted-foreground">
              Cierra {formatDay(nextStatement.closingDate)} · vence{' '}
              {formatDay(nextStatement.dueDate)}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  )
}
