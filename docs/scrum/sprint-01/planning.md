# Sprint 1: Planning

- **Fechas:** 2026-10-05 → 2026-10-16
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 13 SP (supuesta; primer sprint con SP)

## Sprint Goal
> Base técnica lista: esqueleto hexagonal corriendo en Docker, con migraciones y CI/CD que valida cada PR.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 1 | PF-17 | US-001 | Esqueleto hexagonal, configuración y `/health` | 3 | Incluye la corrección de `sprint-00/retro.md` (punto 7 y acción A5) |
| 2 | PF-19 | US-003 | Alembic async y sesión de base de datos | 2 | Depende de PF-17 |
| 3 | PF-18 | US-002 | Docker y Docker Compose | 2 | Depende de PF-17 y PF-19 |
| 4 | PF-20 | US-004 | CI, hooks locales y reglas de PR | 5 | Re-estimado de 3 a 5 por el alcance ampliado |
| 5 | PF-21 | US-005 | Imagen en GHCR + Dependabot | 1 | Depende de PF-18 y PF-20 |

**Total comprometido:** 13 SP

## Decisiones
- PF-20 se re-estima de 3 a 5 SP (1 commit por PR, ≤ 400 líneas, prefijos, lint local + CI, validación del origen de los PRs a `main`).
- PF-22 (logging + RFC 9457, 2 SP) vuelve al backlog y pasa al Sprint 2, para no superar la capacidad.
- El chequeo de la base de datos en `/health` pasa de PF-17 a PF-19, porque la conexión se crea recién en PF-19. PF-17 deja la respuesta preparada (`checks`) para agregarlo sin romper el contrato. Los SP no cambian.
- httpx se reemplaza por httpx2 y respx por `httpx2.MockTransport`: Starlette depreca su TestClient sobre httpx. Además, pytest falla también con `FastAPIDeprecationWarning` y `StarletteDeprecationWarning`, que heredan de `UserWarning` y se escapaban de `error::DeprecationWarning`.
- Hasta que PF-20 esté mergeado, los PRs no tienen checks automáticos; las reglas se verifican a mano.

## Riesgos
- Primer sprint con código: la velocity real puede diferir de 13 SP. Se recalibra en la Retro.
- PF-20 es el ítem más grande; si se atrasa, PF-21 puede pasar al Sprint 2.
