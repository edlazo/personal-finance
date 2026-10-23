import type { Money } from '@/lib/money'

export type Kpi = { current: Money; previous: Money }

/** Patrimonio de fin de mes en ambas monedas; `month` en formato YYYY-MM. */
export type NetWorthPoint = { month: string; ars: string; usd: string }

// Forma esperada de `GET /dashboard/summary` (Reportes); hasta entonces, datos de ejemplo.
export type DashboardSummary = {
  netWorth: Kpi
  monthIncome: Kpi
  monthExpenses: Kpi
  mepRate: Kpi
  netWorthHistory: NetWorthPoint[]
  budget: { spent: Money; limit: Money }
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
}
