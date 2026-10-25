# Sprint 7: Planning

- **Fecha:** 2026-10-25
- **Fechas del sprint:** 2026-10-26 → 2026-11-06 (toma las fechas que tenía el Sprint 6)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 14,3 SP (promedio de los Sprints 4 a 6)

## Sprint Goal
> Comprar o vender dólares al tipo de cambio real y seguir la cartera de inversiones con posiciones y resultados.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 0 | — | — | Build de la imagen Docker en los checks de PR | — | Acción A1 de la Retro del Sprint 6 |
| 1 | PF-37 | US-020 | Compra y venta de dólares | 3 | Transferencia entre monedas con el tipo de cambio efectivo; comisión como gasto |
| 2 | PF-43 | US-026 | Catálogo de instrumentos | 3 | Módulo nuevo `investments` |
| 3 | PF-44 | US-027 | Registrar compra y venta de instrumentos | 5 | Depende de PF-43; debita o acredita la cuenta comitente |
| 4 | PF-45 | US-028 | Posiciones y resultados | 5 | Depende de PF-44 |

**Total comprometido:** 16 SP

## Decisiones
- Se mantienen las 4 historias aunque superan la velocity (decisión del PO): el objetivo queda completo.
- PF-86 y PF-87 siguen sin sprint asignado.

## Riesgos
- **Arquitectura:** las operaciones (investments) mueven el saldo de cuentas de ledger. Se resuelve con un contrato en `app.shared`, como la conversión (A4 del Sprint 5).
- **Precio actual:** la valuación de PF-45 necesita un precio y la carga de precios (US-029) es del Sprint 8. Se decide con el PO al arrancar PF-45 (acción A5).
- **Alcance:** 16 SP con velocity de 14,3; si aprieta, PF-45 es la candidata a pasar al Sprint 8.
