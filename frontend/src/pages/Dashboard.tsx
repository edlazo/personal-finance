import { BudgetDonut } from '@/components/dashboard/BudgetDonut'
import { CreditCardWidget } from '@/components/dashboard/CreditCardWidget'
import { ExpensesByCategory } from '@/components/dashboard/ExpensesByCategory'
import { InvestmentsCard } from '@/components/dashboard/InvestmentsCard'
import { KpiCard } from '@/components/dashboard/KpiCard'
import { NetWorthChart } from '@/components/dashboard/NetWorthChart'
import { ProfileCard } from '@/components/dashboard/ProfileCard'
import { RecentTransactions } from '@/components/dashboard/RecentTransactions'
import { SecurityCard } from '@/components/dashboard/SecurityCard'
import { mockDashboard, type DashboardSummary } from '@/mocks/dashboard'
import type { Profile } from '@/lib/auth-context'

type Props = { summary?: DashboardSummary; user: Profile }

export function Dashboard({ summary = mockDashboard, user }: Props) {
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
      <SecurityCard security={summary.security} />
      <ExpensesByCategory expenses={summary.expensesByCategory} />
      <InvestmentsCard investments={summary.investments} />
    </section>
  )
}
