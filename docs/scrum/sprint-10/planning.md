# Sprint 10: Planning

- **Fecha:** 2026-10-27
- **Fechas del sprint:** 2026-10-27 → 2026-11-06 (toma las fechas que tenía el Sprint 9)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 15,7 SP (promedio de los Sprints 7 a 9)

## Sprint Goal
> Saber cuánto debo en cada tarjeta y cada deuda, y registrar sus pagos.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 0 | — | — | Dobles de inversiones con rollback | — | Acción A1 de la Retro del Sprint 9 |
| 0 | — | — | `App.test.tsx` estable en el CI | — | Acción A2 de la Retro del Sprint 9 |
| 1 | PF-56 | US-039 | Resumen del período | 3 | Usa las cuotas de PF-55 |
| 2 | PF-57 | US-040 | Pago de resumen | 3 | Sale de una cuenta del ledger: necesita un contrato en `app.shared` |
| 3 | PF-58 | US-041 | Registrar deuda o préstamo | 5 | Módulo nuevo: planear 2 PRs desde el arranque |
| 4 | PF-59 | US-042 | Pagos de deuda | 3 | Depende de PF-58 |

**Total comprometido:** 14 SP

## Decisiones
- US-041 y US-042 entran desde el Sprint 11 (decisión del PO).
- Sin release este sprint: **v0.3.0** al cierre del Sprint 11.

## Riesgos
- **Pago de resumen:** la tarjeta no es una cuenta del ledger; cómo se refleja el pago en la cuenta de origen se decide al arrancar PF-57.
- **Deudas:** la relación entre una deuda en otra moneda y la cotización se define al arrancar PF-58.
- El Postgres local se cae entre sesiones y Docker sigue sin arrancar.
