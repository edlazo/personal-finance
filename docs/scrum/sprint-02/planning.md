# Sprint 2: Planning

- **Fecha:** 2026-10-23
- **Fechas del sprint:** 2026-10-26 → 2026-11-06
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 13 SP (real del Sprint 1)

## Sprint Goal
> Dashboard navegable con datos de ejemplo, sobre un frontend con CI, y logging estructurado en la API.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 1 | PF-76 | US-057 | Esqueleto del frontend y CI | 3 | Ajusta `pr-rules` (lockfile) y Dependabot (npm) |
| 2 | PF-77 | US-058 | Layout del dashboard | 3 | Depende de PF-76 |
| 3 | PF-78 | US-059 | Dashboard: KPIs, evolución del patrimonio y presupuesto | 5 | Depende de PF-77 |
| 4 | PF-22 | US-053 | Logging estructurado y errores RFC 9457 | 2 | Viene del Sprint 1 |

**Total comprometido:** 13 SP

## Decisiones
- Nueva épica **PF-E12 Frontend** (PF-75): React + Vite + TypeScript en `frontend/` del mismo repo; datos mock tipados hasta que existan los endpoints.
- El PO prioriza el frontend: Identity (US-006 a US-010) pasa al Sprint 3 y el roadmap se corre un sprint (v0.1.0 al cierre del Sprint 6).
- PF-79 (US-060, módulos secundarios del dashboard, 5 SP) queda en el backlog sin sprint.
- Versiones verificadas en npm el 2026-10-23, sin deprecaciones: React 19.3, Vite 8.3, TypeScript 7.0, Tailwind 4.3, Recharts 3.10, Vitest 5.0, ESLint 10.13. Node 24 LTS.

## Riesgos
- Primer código frontend del proyecto: el esqueleto puede superar las 400 líneas aun sin el lockfile. Si pasa, se divide en dos PRs.
- Los mocks pueden diferir de la API real; los tipos se ajustan cuando salgan los endpoints.
