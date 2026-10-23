import { Button } from '@/components/ui/button'

// El dashboard llega en PF-77/PF-78; esto solo prueba que Tailwind y shadcn/ui funcionan.
export default function App() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-semibold">Personal Finance</h1>
      <Button>Empezar</Button>
    </main>
  )
}
