# Sprint 1: Review

- **Fecha:** 2026-10-23 (el sprint terminó el 2026-10-16; la ceremonia se hizo una semana tarde)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Base técnica lista: esqueleto hexagonal corriendo en Docker, con migraciones y CI/CD que valida cada PR. → **Cumplido ✅**

## Historias
| Key Jira | Historia | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-17 | Esqueleto hexagonal, configuración y `/health` | 3 | Done | #4 | ✅ |
| PF-19 | Alembic async, sesión de base de datos y Unit of Work | 2 | Done | #5, #6 | ✅ |
| PF-18 | Docker y Docker Compose | 2 | Done | #7 | ✅ |
| PF-20 | CI, hooks locales y reglas de PR | 5 | Done | #8 | ✅ |
| PF-21 | Imagen en GHCR + Dependabot | 1 | Done | #9 | ✅ |

- **Comprometido:** 13 SP · **Completado:** 13 SP

## Demo
- `docker compose up -d --build --wait` levanta `db`, `migrate`, `api` y `worker`; `GET /health` responde 200 con `checks.database: ok` y 503 si la base no responde.
- `pr-checks` en verde en su primer run (PR #8): `pr-rules`, `prefix`, `quality / lint`, `quality / typecheck`, `quality / test` y `quality / migrations`.
- Dependabot abrió 5 PRs (#10 a #14) con títulos `build(deps): …`; los 5 pasan los 6 checks, lo que valida las exenciones de rama y key.
- Tests: 34, cobertura 99 %.
- Feedback del PO: pide empezar el frontend (dashboard), tomando como referencia el diseño compartido el 2026-10-23.

## Cambios al Product Backlog
- **Movido:** el chequeo de la base en `/health` pasó de PF-17 a PF-19 (la conexión se crea en PF-19).
- **Cambio de stack:** `httpx` → `httpx2` y `respx` → `httpx2.MockTransport` (Starlette depreca su TestClient sobre httpx). pytest falla también con `FastAPIDeprecationWarning` y `StarletteDeprecationWarning`.
- **Agregado en PF-18:** worker mínimo con APScheduler (el compose lo necesitaba; los jobs llegan con sus historias).
- **Agregado en PF-20:** Dependabot exento del nombre de rama en `pr-rules`.
- **Sprint 2:** PF-22 (logging + RFC 9457, 2 SP) entra junto con autenticación (US-006 a US-010, 12 SP).
- **Nuevo pedido del PO:** frontend con dashboard. Falta definir stack, alcance e historias en el Planning del Sprint 2.

## Release
- [x] Sin release este sprint (según el roadmap, la primera es v0.1.0 al cierre del Sprint 5).
