import { AppHeader } from '@/components/layout/AppHeader'
import { AppSidebar } from '@/components/layout/AppSidebar'
import { mockUser } from '@/mocks/user'
import { Dashboard } from '@/pages/Dashboard'

export function DashboardLayout() {
  return (
    <div className="flex min-h-svh flex-col gap-4 p-4 md:flex-row">
      <a
        href="#contenido"
        className="sr-only rounded-xl bg-card px-4 py-2 focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-10"
      >
        Ir al contenido
      </a>
      <AppSidebar />
      <div className="flex flex-1 flex-col gap-6">
        <AppHeader user={mockUser} />
        <main id="contenido">
          <Dashboard />
        </main>
      </div>
    </div>
  )
}
