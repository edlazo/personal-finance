# Sprint 5: Planning

- **Fecha:** 2026-10-24
- **Fechas del sprint:** 2026-10-26 → 2026-11-06 (2 semanas por objetivo)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 15 SP (promedio de los Sprints 2 a 4)

## Sprint Goal
> Registrar ingresos, gastos y transferencias en la misma moneda, con el saldo de cada cuenta calculado a partir de sus movimientos.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 1 | PF-33 | US-016 | Registrar ingreso o gasto | 3 | Incluye los criterios de cuentas que dependían de movimientos (de US-012) |
| 2 | PF-30 | US-013 | Saldo de cuenta derivado | 3 | Depende de PF-33 |
| 3 | PF-34 | US-017 | Listar movimientos con filtros | 3 | Depende de PF-33 |
| 4 | PF-36 | US-019 | Transferencia entre cuentas de la misma moneda | 3 | Depende de PF-33 |
| 5 | PF-35 | US-018 | Editar y eliminar movimiento | 2 | Depende de PF-36 (las transferencias se editan por ambas patas) |

**Total comprometido:** 14 SP

## Decisiones
- Cadencia: 2 semanas por objetivo; si el goal se cumple antes, se cierra el sprint y se planifica el siguiente.
- US-020 (compra/venta de USD) pasa al Sprint 6, junto con las cotizaciones. El Sprint 6 queda en 18 SP y se re-planifica en su Planning.

## Riesgos
- **Arquitectura:** los movimientos (ledger) referencian cuentas (accounts) y el saldo (accounts) suma movimientos (ledger), pero el contrato de independencia impide que un módulo importe al otro. El mecanismo se decide con el PO al arrancar PF-33 (acción A4).
- Docker Desktop sigue sin arrancar en la máquina del PO: sin él, las migraciones e integraciones dependen del CI (acción A2).
