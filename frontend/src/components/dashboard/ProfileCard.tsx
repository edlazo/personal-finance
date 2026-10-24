import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { initials } from '@/lib/utils'
import type { Profile } from '@/lib/auth-context'

export function ProfileCard({ user }: { user: Profile }) {
  return (
    <Card className="rounded-3xl">
      <CardHeader>
        <CardTitle>Perfil</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-2 text-center">
        <Avatar className="size-16 text-lg">
          <AvatarFallback>{initials(user.name)}</AvatarFallback>
        </Avatar>
        <p className="font-semibold">{user.name}</p>
        <p className="text-sm text-muted-foreground">{user.email}</p>
      </CardContent>
    </Card>
  )
}
