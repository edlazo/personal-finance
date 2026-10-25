# Sprint 5: Review

- **Fecha:** 2026-10-24
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Registrar ingresos, gastos y transferencias en la misma moneda, con el saldo de cada cuenta calculado a partir de sus movimientos. → **Cumplido ✅**
- **Nota:** se completó antes de su inicio previsto (2026-10-26). Por la regla de cadencia, se cierra y el Sprint 6 toma sus fechas.

## Historias
| Key Jira | Historia | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-33 | Registrar ingreso o gasto | 3 | Done | #54, #55, #56 | ✅ |
| PF-30 | Saldo de cuenta derivado | 3 | Done | #57, #58 (fix) | ✅ |
| PF-34 | Listar movimientos con filtros | 3 | Done | #59 | ✅ |
| PF-36 | Transferencia entre cuentas de la misma moneda | 3 | Done | #60 | ✅ |
| PF-35 | Editar y eliminar movimiento | 2 | Done | #61 | ✅ |

- **Comprometido:** 14 SP · **Completado:** 14 SP

## Demo
- Movimientos: `POST /transactions` con categoría del mismo tipo y cuenta no archivada; una cuenta con movimientos ya no cambia de moneda.
- Saldo: no se guarda; es el saldo inicial más ingresos menos gastos. `GET /accounts` y `GET /accounts/{id}` lo devuelven, también a una fecha con `as_of`.
- Listado: `GET /transactions` con filtros por fechas, cuenta, categoría (con sus subcategorías), tipo, texto y montos; paginación con `limit`/`offset` y total; del más reciente al más viejo.
- Transferencias: `POST /transfers` genera un gasto en el origen y un ingreso en el destino ligados por `transfer_group_id`, sin categoría. Cuentas distintas, propias, de la misma moneda y no archivadas.
- Edición y borrado: `PATCH` y `DELETE /transactions/{id}`; en una transferencia cambian o se borran las dos patas.

## Cambios al Product Backlog
- **Decisiones del PO aplicadas:** el módulo accounts se une a ledger (PF-33); el filtro por categoría incluye las subcategorías; el borrado de movimientos es definitivo; en una transferencia solo se editan monto, fecha y descripción.
- **Historias nuevas (surgieron en PF-36):** US-062 → PF-86 *Gastos y transferencias sin saldo negativo* (3 SP) y US-063 → PF-87 *Filtro por tipo de movimiento sin transferencias* (1 SP). Sin sprint asignado.
- **Sprint 6:** US-020 (compra/venta de USD) pasa al Sprint 7; el Sprint 6 queda con las cotizaciones (15 SP).
- **Cambio de API:** en `GET /transactions`, `category_id` puede ser `null` (transferencias) y aparece `transfer_group_id`.

## Release
- [x] Sin release este sprint (v0.1.0 al cierre del Sprint 6).
