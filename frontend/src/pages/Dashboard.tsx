import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

// Lugares de los módulos; PF-78 y PF-79 los reemplazan por el contenido real.
const MODULES = [
  'Patrimonio neto',
  'Ingresos del mes',
  'Gastos del mes',
  'Dólar MEP',
  'Evolución del patrimonio',
  'Presupuesto del mes',
  'Perfil',
  'Tarjeta de crédito',
  'Últimos movimientos',
  'Seguridad',
  'Gastos por categoría',
  'Inversiones',
]

export function Dashboard() {
  return (
    <section aria-label="Resumen" className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {MODULES.map((title) => (
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
