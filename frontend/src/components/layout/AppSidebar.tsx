import {
  ArrowLeftRight,
  ChartColumn,
  CreditCard,
  LayoutDashboard,
  LogOut,
  Settings,
  TrendingUp,
  Wallet,
  type LucideIcon,
} from 'lucide-react'

import { cn } from '@/lib/utils'

type NavItem = { label: string; href: string; icon: LucideIcon }

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'Cuentas', href: '/cuentas', icon: Wallet },
  { label: 'Movimientos', href: '/movimientos', icon: ArrowLeftRight },
  { label: 'Inversiones', href: '/inversiones', icon: TrendingUp },
  { label: 'Tarjetas', href: '/tarjetas', icon: CreditCard },
  { label: 'Reportes', href: '/reportes', icon: ChartColumn },
  { label: 'Configuración', href: '/configuracion', icon: Settings },
]

const itemClass =
  'flex size-11 shrink-0 items-center justify-center rounded-xl text-muted-foreground outline-none transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50'

export function AppSidebar({ currentPath = '/' }: { currentPath?: string }) {
  return (
    <nav
      aria-label="Principal"
      className="flex gap-2 overflow-x-auto rounded-3xl bg-card p-2 md:sticky md:top-4 md:h-[calc(100svh-2rem)] md:flex-col"
    >
      {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
        const current = href === currentPath
        return (
          <a
            key={href}
            href={href}
            title={label}
            aria-current={current ? 'page' : undefined}
            className={cn(
              itemClass,
              current && 'bg-primary text-primary-foreground hover:bg-primary/90',
            )}
          >
            <Icon aria-hidden className="size-5" />
            <span className="sr-only">{label}</span>
          </a>
        )
      })}
      {/* El cierre de sesión real llega con Identity (Sprint 3). */}
      <button type="button" title="Salir" className={cn(itemClass, 'md:mt-auto')}>
        <LogOut aria-hidden className="size-5" />
        <span className="sr-only">Salir</span>
      </button>
    </nav>
  )
}
