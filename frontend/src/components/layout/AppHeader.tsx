import { Bell, Search } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { initials } from '@/lib/utils'
import type { User } from '@/mocks/user'

export function AppHeader({ user }: { user: User }) {
  return (
    <header className="flex flex-wrap items-center gap-3">
      <div className="mr-auto">
        <h1 className="text-2xl font-semibold">Hola, {user.name.split(' ')[0]}</h1>
        <p className="text-sm text-muted-foreground">Este es el resumen de tus finanzas</p>
      </div>
      <div className="relative w-full sm:w-64">
        <Search
          aria-hidden
          className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          type="search"
          aria-label="Buscar"
          placeholder="Buscar"
          className="rounded-full bg-card pl-9"
        />
      </div>
      <Button variant="outline" size="icon" aria-label="Notificaciones" className="rounded-full">
        <Bell aria-hidden />
      </Button>
      <Avatar title={user.name}>
        <AvatarFallback>{initials(user.name)}</AvatarFallback>
      </Avatar>
    </header>
  )
}
