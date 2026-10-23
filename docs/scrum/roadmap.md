# Roadmap

Sprints de **2 semanas**. Capacidad estimada: **~13 SP por sprint** (unas 17 h netas de desarrollo con 10 h/semana). Se recalibra con la velocity real al cerrar los Sprints 1 y 2.

> Las fechas se fijan en el Sprint Planning del Sprint 1. La semana se cuenta desde el inicio del Sprint 1.

| Sprint | Semanas | Sprint Goal | Historias | SP | Release |
|---|---|---|---|---|---|
| 0 | — | Definir stack, requirements, marco Scrum y backlog; preparar repo y Jira | Definición | — | — |
| 1 | 1–2 | Base técnica lista: esqueleto hexagonal, Docker, Alembic y CI/CD | US-001, 002, 003, 004, 005 | 13 | — |
| 2 | 3–4 | Dashboard navegable con datos de ejemplo y logging estructurado | US-057, 058, 059, 053 | 13 | — |
| 3 | 5–6 | Usuarios pueden registrarse y autenticarse de forma segura | US-006, 007, 008, 009, 010 | 12 | — |
| 4 | 7–8 | Gestionar cuentas ARS/USD con saldo y categorías | US-011, 012, 013, 014, 015 | 14 | — |
| 5 | 9–10 | Registrar ingresos, gastos, transferencias y compra/venta de USD | US-016, 017, 018, 019, 020 | 14 | — |
| 6 | 11–12 | Ver todo en ARS y USD con cotizaciones automáticas | US-021, 022, 023, 024, 025 | 15 | **v0.1.0 MVP** |
| 7 | 13–14 | Seguir la cartera de inversiones con posiciones y P&L | US-026, 027, 028 | 13 | — |
| 8 | 15–16 | Precios manuales, rentas, credenciales seguras y cripto automática | US-029, 030, 031, 032, 035 | 13 | — |
| 9 | 17–18 | Valuación automática con IOL/data912 e import de Balanz | US-033, 034, 036 | 13 | **v0.2.0** |
| 10 | 19–20 | Controlar tarjetas de crédito, cuotas y resúmenes | US-037, 038, 039, 040 | 13 | — |
| 11 | 21–22 | Deudas y movimientos recurrentes automáticos | US-041, 042, 043, 044 | 14 | **v0.3.0** |
| 12 | 23–24 | Presupuestos, patrimonio neto y flujo de fondos | US-045, 046, 047, 048 | 14 | — |
| 13 | 25–26 | Reportes históricos, hardening y salida a producción | US-049, 050, 051, 052, 054 | 14 | **v1.0.0** |
| Futuro | — | Bienes (inmuebles, vehículos) | US-055, 056 | 8 | v1.1.0 |

**Total v1.0:** 178 SP en 13 sprints, unas 26 semanas desde el inicio del Sprint 1. US-060 (5 SP, módulos secundarios del dashboard) queda sin sprint asignado.

> **2026-10-23 (Planning del Sprint 2):** entra la épica PF-E12 Frontend; el PO prioriza el dashboard, así que todo el roadmap desde Identity se corre un sprint.

## Releases
| Versión | Contenido | Valor para el usuario |
|---|---|---|
| v0.1.0 MVP | Auth, cuentas, movimientos, transferencias, cotizaciones | Registrar el día a día y ver el total en ARS/USD |
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
