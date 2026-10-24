# Sprint 2: Review

- **Fecha:** 2026-10-23
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Dashboard navegable con datos de ejemplo, sobre un frontend con CI, y logging estructurado en la API. → **Cumplido ✅**
- **Nota:** el sprint estaba planificado del 2026-10-26 al 2026-11-06, pero todo se completó el 2026-10-23, el mismo día del Planning. El PO decidió cerrarlo antes de tiempo.

## Historias
| Key Jira | Historia | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-76 | Esqueleto del frontend y CI | 3 | Done | #16, #24 | ✅ |
| PF-77 | Layout del dashboard | 3 | Done | #25 | ✅ |
| PF-78 | KPIs, evolución del patrimonio y presupuesto | 5 | Done | #26 | ✅ |
| PF-22 | Logging estructurado y errores RFC 9457 | 2 | Done | #27 | ✅ |
| PF-79 | Tarjetas, movimientos, seguridad, gastos e inversiones | 5 | Done (agregada en el sprint) | #28, #29 | ✅ |

- **Comprometido:** 13 SP · **Completado:** 18 SP (13 + PF-79, sumada con acuerdo del PO)

## Demo
- Dashboard completo con datos de ejemplo: 4 KPIs (dólar MEP destacado), evolución del patrimonio ARS/USD, dona de presupuesto, perfil, tarjeta de crédito, últimos movimientos, seguridad, gastos por categoría e inversiones. Responsive (3/2/1 columnas).
- API: cada request loguea en JSON con `request_id`; `X-Request-ID` en la respuesta; errores como `application/problem+json`.
- CI: job `quality / frontend` (lint, formato, tipos, tests y build) en cada PR y en cada push a `develop`.

## Cambios al Product Backlog
- **Sumada al sprint:** PF-79 (US-060), que estaba sin sprint.
- **Nueva:** PF-80, límite de 72 caracteres en el asunto del commit (origen: PR #15 falló porque GitHub cortó la key del título).
- **Stack del front:** la plantilla oficial de Vite trae oxlint (no ESLint); TypeScript pasó de 6 a 7 por Dependabot (PR #17).
- **Reglas de PR:** `pr-rules` no cuenta `frontend/package-lock.json` ni `frontend/src/components/ui/**` (código generado por shadcn).
- **Para decidir en el Planning del Sprint 3:**
  - US-006 pide crear las categorías por defecto al registrarse, pero las categorías llegan con US-014 (Sprint 4).
  - La pantalla de login del frontend no está en el backlog.

## Release
- [x] Sin release este sprint.
