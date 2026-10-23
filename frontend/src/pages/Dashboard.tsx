import { BudgetDonut } from '@/components/dashboard/BudgetDonut'
import { CreditCardWidget } from '@/components/dashboard/CreditCardWidget'
import { KpiCard } from '@/components/dashboard/KpiCard'
import { NetWorthChart } from '@/components/dashboard/NetWorthChart'
import { ProfileCard } from '@/components/dashboard/ProfileCard'
import { RecentTransactions } from '@/components/dashboard/RecentTransactions'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { mockDashboard, type DashboardSummary } from '@/mocks/dashboard'
import { mockUser, type User } from '@/mocks/user'

// Módulos de PF-79, todavía sin contenido.
const PENDING_MODULES = ['Seguridad', 'Gastos por categoría', 'Inversiones']

type Props = { summary?: DashboardSummary; user?: User }

export function Dashboard({ summary = mockDashboard, user = mockUser }: Props) {
  return (
    <section aria-label="Resumen" className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div className="grid gap-4 md:col-span-2 md:grid-cols-2 lg:col-span-3 xl:grid-cols-4">
        <KpiCard title="Patrimonio neto" kpi={summary.netWorth} higherIsBetter />
        <KpiCard title="Ingresos del mes" kpi={summary.monthIncome} higherIsBetter />
        <KpiCard title="Gastos del mes" kpi={summary.monthExpenses} higherIsBetter={false} />
        <KpiCard title="Dólar MEP (venta)" kpi={summary.mepRate} highlighted />
      </div>
      <NetWorthChart history={summary.netWorthHistory} />
      <BudgetDonut spent={summary.budget.spent} limit={summary.budget.limit} />
      <ProfileCard user={user} />
      <CreditCardWidget card={summary.creditCard} />
      <RecentTransactions transactions={summary.recentTransactions} />
      {PENDING_MODULES.map((title) => (
        <Card key={title} className="rounded-3xl">
          <CardHeader>
            <CardTitle>{title}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">Próximamente</CardContent>
        </Card>
      ))}
    </section>
  )
}
