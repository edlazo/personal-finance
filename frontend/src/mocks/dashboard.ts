import type { Money } from '@/lib/money'

export type Kpi = { current: Money; previous: Money }

/** Patrimonio de fin de mes en ambas monedas; `month` en formato YYYY-MM. */
export type NetWorthPoint = { month: string; ars: string; usd: string }

export type CreditCardSummary = {
  brand: 'VISA' | 'Mastercard' | 'AMEX'
  last4: string
  holder: string
  available: Money
  limit: Money
  /** Fechas en formato YYYY-MM-DD. */
  nextStatement: { closingDate: string; dueDate: string; amount: Money }
}

/** El monto siempre es positivo; `kind` define si suma, resta o es un movimiento entre cuentas. */
export type Transaction = {
  id: string
  date: string
  description: string
  category: string
  kind: 'income' | 'expense' | 'transfer'
  amount: Money
}

// Forma esperada de `GET /dashboard/summary` (Reportes); hasta entonces, datos de ejemplo.
export type DashboardSummary = {
  netWorth: Kpi
  monthIncome: Kpi
  monthExpenses: Kpi
  mepRate: Kpi
  netWorthHistory: NetWorthPoint[]
  budget: { spent: Money; limit: Money }
  creditCard: CreditCardSummary
  recentTransactions: Transaction[]
}

const ars = (amount: string): Money => ({ amount, currency: 'ARS' })

export const mockDashboard: DashboardSummary = {
  netWorth: { current: ars('18450000.00'), previous: ars('17900000.00') },
  monthIncome: { current: ars('2350000.00'), previous: ars('2200000.00') },
  monthExpenses: { current: ars('1480000.00'), previous: ars('1390000.00') },
  mepRate: { current: ars('1285.50'), previous: ars('1240.00') },
  netWorthHistory: [
    { month: '2025-11', ars: '11200000.00', usd: '9800.00' },
    { month: '2025-12', ars: '11900000.00', usd: '10150.00' },
    { month: '2026-01', ars: '12400000.00', usd: '10400.00' },
    { month: '2026-02', ars: '12100000.00', usd: '10050.00' },
    { month: '2026-03', ars: '13300000.00', usd: '10900.00' },
    { month: '2026-04', ars: '14000000.00', usd: '11350.00' },
    { month: '2026-05', ars: '14800000.00', usd: '11900.00' },
    { month: '2026-06', ars: '15200000.00', usd: '12100.00' },
    { month: '2026-07', ars: '16100000.00', usd: '12800.00' },
    { month: '2026-08', ars: '16900000.00', usd: '13400.00' },
    { month: '2026-09', ars: '17900000.00', usd: '14100.00' },
    { month: '2026-10', ars: '18450000.00', usd: '14350.00' },
  ],
  budget: { spent: ars('1020000.00'), limit: ars('1480000.00') },
  creditCard: {
    brand: 'VISA',
    last4: '4821',
    holder: 'ELIAS LAZO',
    available: ars('1650000.00'),
    limit: ars('2500000.00'),
    nextStatement: { closingDate: '2026-10-29', dueDate: '2026-11-10', amount: ars('850000.00') },
  },
  recentTransactions: [
    {
      id: 't5',
      date: '2026-10-22',
      description: 'Supermercado',
      category: 'Comida',
      kind: 'expense',
      amount: ars('84500.00'),
    },
    {
      id: 't4',
      date: '2026-10-21',
      description: 'Compra de dólares MEP',
      category: 'Transferencia',
      kind: 'transfer',
      amount: ars('300000.00'),
    },
    {
      id: 't3',
      date: '2026-10-20',
      description: 'Sueldo',
      category: 'Ingresos',
      kind: 'income',
      amount: ars('2350000.00'),
    },
    {
      id: 't2',
      date: '2026-10-18',
      description: 'Alquiler',
      category: 'Vivienda',
      kind: 'expense',
      amount: ars('620000.00'),
    },
    {
      id: 't1',
      date: '2026-10-15',
      description: 'Internet',
      category: 'Servicios',
      kind: 'expense',
      amount: ars('32000.00'),
    },
  ],
}
