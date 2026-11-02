# Sprint 11: Planning

- **Fecha:** 2026-11-02
- **Fechas del sprint:** 2026-11-02 → 2026-11-06 (toma los días que le quedaban al Sprint 10)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 15 SP (promedio de los Sprints 8 a 10)

## Sprint Goal
> Que los movimientos recurrentes se registren solos y ver mi patrimonio neto y mi flujo de fondos.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 0 | PF-100 | — | Segunda tanda de Dependabot (#119 a #128) | — | Primera tarea del sprint (decisión del PO) |
| 1 | PF-60 | US-043 | Reglas de movimientos recurrentes | 3 | Si va en un módulo nuevo o dentro de ledger se decide al arrancar |
| 2 | PF-61 | US-044 | Generación automática de recurrentes | 3 | Job diario e idempotente en el worker |
| 3 | PF-64 | US-047 | Patrimonio neto | 5 | Lee cuentas, inversiones, tarjetas y deudas: contratos de lectura en `app.shared`; un PR por capa (acción A1) |
| 4 | PF-65 | US-048 | Flujo de fondos mensual | 3 | Excluye transferencias y movimientos sin categoría (operaciones, pagos de tarjeta y de deuda) |

**Total comprometido:** 14 SP

## Decisiones
- US-047 y US-048 se adelantan desde el Sprint 12 y los presupuestos (US-045 y US-046) pasan a ese sprint (decisión del PO).
- Release **v0.3.0** al cierre del sprint: tarjetas, deudas, recurrentes, patrimonio neto y flujo de fondos.

## Riesgos
- **Patrimonio neto:** es la primera historia que lee de cinco módulos. Al arrancar PF-64 se define qué cuenta como pasivo de una tarjeta (el resumen abierto o todas las cuotas que faltan) y con qué cotización se convierte.
- **Recurrentes:** el job no tiene que duplicar movimientos si corre dos veces el mismo día ni si estuvo caído varios días.
- **Dependabot:** la tanda anterior rompió dos tests (httpx2 2.16); puede pasar de nuevo.
- El Postgres local se cae entre sesiones y Docker sigue sin arrancar.
