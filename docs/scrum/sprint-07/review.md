# Sprint 7: Review

- **Fecha:** 2026-10-25
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Comprar o vender dólares al tipo de cambio real y seguir la cartera de inversiones con posiciones y resultados. → **Cumplido ✅**
- **Nota:** se completó antes de su inicio previsto (2026-10-26). Por la regla de cadencia, se cierra y el Sprint 8 toma sus fechas.

## Historias y tareas
| Key Jira | Ítem | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-90 | Build de la imagen Docker en cada PR (acción A1) | — | Done | #73 | ✅ |
| PF-89 | Pautas de trabajo en CLAUDE.md | — | Done | #72 | ✅ |
| PF-37 | Compra y venta de dólares | 3 | Done | #74 | ✅ |
| PF-43 | Catálogo de instrumentos | 3 | Done | #76, #77 | ✅ |
| PF-44 | Registrar compra y venta de instrumentos | 5 | Done | #78, #79, #80 | ✅ |
| PF-45 | Posiciones y resultados | 5 | Done | #81 | ✅ |
| — | Fix: el worker no guardaba las cotizaciones (bug de la v0.1.0) | — | Done | #75 | ✅ |

- **Comprometido:** 16 SP · **Completado:** 16 SP

## Demo
- Compra/venta de USD: `POST /transfers` entre ARS y USD con `to_amount`; devuelve el tipo de cambio efectivo y registra la comisión como gasto en "Comisiones".
- Inversiones: catálogo propio de instrumentos (`/instruments`), `POST /trades` desde una comitente o wallet de la misma moneda, que debita o acredita la cuenta en la misma transacción, y `GET /positions` con costo promedio ponderado, P&L realizado y no realizado y valuación en ARS y USD.
- La app completa (API, frontend y cotizaciones reales) se levantó en local contra Postgres; ahí apareció el bug del worker, ya corregido.

## Cambios al Product Backlog
- **Decisiones del PO aplicadas:** la comisión es un gasto aparte en el origen; "Comisiones" se suma a las categorías por defecto; al editar una compra de USD cambia solo la pata editada; el catálogo de instrumentos es de cada usuario; las operaciones mueven la cuenta con un movimiento ligado (`trade_id`) por un contrato en `app.shared`; tenencia y posiciones por cuenta; misma moneda entre cuenta e instrumento; precio actual = última operación hasta US-029; las comisiones entran en costo y resultado.
- **Sprint 8:** suma PF-86 (US-062, saldo no negativo) y queda en 16 SP.
- **v0.1.1:** no se publica; el fix del worker sale con la v0.2.0 (decisión del PO).

## Release
- [x] Sin release este sprint (v0.2.0 al cierre del Sprint 9).
