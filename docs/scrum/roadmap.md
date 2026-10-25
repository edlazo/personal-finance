# Roadmap

Sprints de **2 semanas**. Capacidad estimada: **~13 SP por sprint** (unas 17 h netas de desarrollo con 10 h/semana). Se recalibra con la velocity real al cerrar los Sprints 1 y 2.

> Las fechas se fijan en el Sprint Planning del Sprint 1. La semana se cuenta desde el inicio del Sprint 1.

| Sprint | Semanas | Sprint Goal | Historias | SP | Release |
|---|---|---|---|---|---|
| 0 | — | Definir stack, requirements, marco Scrum y backlog; preparar repo y Jira | Definición | — | — |
| 1 | 1–2 | Base técnica lista: esqueleto hexagonal, Docker, Alembic y CI/CD | US-001, 002, 003, 004, 005 | 13 | — |
| 2 | — (2026-10-23) | Dashboard navegable con datos de ejemplo y logging estructurado | US-057, 058, 059, 060, 053 | 18 | — |
| 3 | — (2026-10-23) | Usuarios pueden registrarse y autenticarse de forma segura | US-006, 007, 008, 009, 010 + PF-80 | 13 | — |
| 4 | — (2026-10-24) | Gestionar cuentas ARS/USD y categorías, y entrar con login real | US-011, 012, 014, 015, 061 | 14 | — |
| 5 | — (2026-10-24) | Registrar ingresos, gastos y transferencias en la misma moneda, con saldo derivado | US-013, 016, 017, 018, 019 | 14 | — |
| 6 | — (2026-10-25) | Ver todo en ARS y USD con cotizaciones del dólar automáticas o cargadas a mano | US-021, 022, 023, 024, 025 | 15 | **v0.1.0 MVP** |
| 7 | 3–4 | Comprar o vender dólares y seguir la cartera de inversiones con posiciones y P&L | US-020, 026, 027, 028 | 16 | — |
| 8 | 5–6 | Precios manuales, rentas, credenciales seguras y cripto automática | US-029, 030, 031, 032, 035 | 13 | — |
| 9 | 7–8 | Valuación automática con IOL/data912 e import de Balanz | US-033, 034, 036 | 13 | **v0.2.0** |
| 10 | 9–10 | Controlar tarjetas de crédito, cuotas y resúmenes | US-037, 038, 039, 040 | 13 | — |
| 11 | 11–12 | Deudas y movimientos recurrentes automáticos | US-041, 042, 043, 044 | 14 | **v0.3.0** |
| 12 | 13–14 | Presupuestos, patrimonio neto y flujo de fondos | US-045, 046, 047, 048 | 14 | — |
| 13 | 15–16 | Reportes históricos, hardening y salida a producción | US-049, 050, 051, 052, 054 | 14 | **v1.0.0** |
| Futuro | — | Bienes (inmuebles, vehículos) | US-055, 056 | 8 | v1.1.0 |

**Total v1.0:** 182 SP en 13 sprints, unas 16 semanas desde el inicio del Sprint 1. Sin sprint asignado: US-062 y US-063 (4 SP, surgieron en el Sprint 5).

> **2026-10-23 (Planning del Sprint 2):** entra la épica PF-E12 Frontend; el PO prioriza el dashboard, así que todo el roadmap desde Identity se corre un sprint.
>
> **2026-10-23 (Review del Sprint 2):** el Sprint 2 se completó el mismo día de su Planning, antes de su inicio previsto (26/10), con 18 SP (sumó US-060). El Sprint 3 toma sus fechas (26/10 → 06/11), así que el calendario vuelve a la planificación original: v0.1.0 al cierre de la semana 10.
>
> **2026-10-23 (Review del Sprint 3):** el Sprint 3 también se completó el día de su Planning (13 SP). El Sprint 4 toma sus fechas (26/10 → 06/11) y suma US-061 (login en el front); US-013 (saldo derivado) pasa al Sprint 5 porque depende de los movimientos. El Sprint 5 queda en 17 SP: hay que re-planificarlo. v0.1.0 al cierre de la semana 8.
>
> **2026-10-24 (Review del Sprint 4):** el Sprint 4 también se completó antes de su inicio (14 SP). El PO fija la regla: 2 semanas por objetivo, y si el goal se cumple antes se cierra y se planifica el siguiente. El Sprint 5 toma las fechas 26/10 → 06/11 y US-020 (compra/venta de USD) pasa al Sprint 6, que queda en 18 SP y habrá que re-planificar. v0.1.0 al cierre de la semana 6.
>
> **2026-10-24 (Review del Sprint 5):** el Sprint 5 también se completó antes de su inicio (14 SP). El Sprint 6 toma las fechas 26/10 → 06/11 con las cotizaciones (15 SP) y US-020 pasa al Sprint 7, que queda en 16 SP. Entran US-062 y US-063 sin sprint asignado. v0.1.0 al cierre de la semana 4.
>
> **2026-10-25 (Review del Sprint 6):** el Sprint 6 también se completó antes de su inicio (15 SP) y sale **v0.1.0**. El Sprint 7 toma las fechas 26/10 → 06/11 con 16 SP (decisión del PO). v0.2.0 al cierre de la semana 8.

## Releases
| Versión | Contenido | Valor para el usuario |
|---|---|---|
| v0.1.0 MVP (2026-10-25) | Auth, cuentas, movimientos, transferencias, cotizaciones | Registrar el día a día y ver el total en ARS/USD |
| v0.2.0 | Inversiones + integraciones de mercado | Cartera valuada automáticamente |
| v0.3.0 | Tarjetas, deudas, recurrentes | Visión completa de pasivos y compromisos |
| v1.0.0 | Presupuestos, reportes, hardening | Producto completo listo para producción |

## Riesgos
| Riesgo | Impacto | Mitigación |
|---|---|---|
| La API de IOL requiere habilitación o cambia | Sprint 9 | Spike US-031 en el Sprint 8; data912 + carga manual como fallback |
| Balanz no tiene API | Sprint 9 | Import de archivo (US-036) |
| APIs públicas (dolarapi, data912, CoinGecko) limitan o cambian | Sprints 6–9 | Puertos/adaptadores, reintentos, historial persistido, carga manual |
| Velocity real menor a 13 SP | Fechas | Recalibrar en la Retro de los Sprints 1–2 y re-priorizar con el PO |
