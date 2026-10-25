# Sprint 6: Planning

- **Fecha:** 2026-10-24
- **Fechas del sprint:** 2026-10-26 → 2026-11-06 (toma las fechas que tenía el Sprint 5)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 13,7 SP (promedio de los Sprints 3 a 5)

## Sprint Goal
> Ver todo en ARS y en USD con cotizaciones del dólar automáticas o cargadas a mano.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 1 | PF-38 | US-021 | Cotizaciones del dólar: modelo y carga manual | 3 | Módulo nuevo `fx` |
| 2 | PF-40 | US-023 | Consultar cotizaciones | 2 | Depende de PF-38 |
| 3 | PF-39 | US-022 | Cotizaciones automáticas desde dolarapi | 5 | Depende de PF-38; usa el scheduler del worker |
| 4 | PF-41 | US-024 | Conversión ARS <-> USD | 3 | Depende de PF-38 |
| 5 | PF-42 | US-025 | Saldos consolidados en ARS y USD | 2 | Depende de PF-41 y del saldo derivado (PF-30) |

**Total comprometido:** 15 SP

## Decisiones
- US-020 (compra/venta de USD) pasa al Sprint 7 para no superar la velocity (decisión del PO). El Sprint 7 queda en 16 SP.
- Al cierre de este sprint sale **v0.1.0 MVP**.

## Riesgos
- **Arquitectura:** el saldo consolidado (ledger) necesita las cotizaciones (fx) y la cotización preferida del usuario (identity), y el contrato de independencia impide importar otros módulos. Se decide con el PO al arrancar PF-41 (acción A4).
- **dolarapi:** API pública sin SLA; el adaptador va detrás de un puerto, con reintentos y la carga manual como respaldo.
- Docker sigue sin arrancar en la máquina del PO; las integraciones corren contra un Postgres local (acción A3).
