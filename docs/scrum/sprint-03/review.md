# Sprint 3: Review

- **Fecha:** 2026-10-23
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Los usuarios pueden registrarse e iniciar sesión de forma segura, y cada uno ve solo sus datos. → **Cumplido ✅**
- **Nota:** como el Sprint 2, se completó el mismo día del Planning, antes de su inicio previsto (2026-10-26).

## Historias
| Key Jira | Historia | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-80 | Límite de 72 caracteres en el asunto del commit | 1 | Done | #30 | ✅ |
| PF-23 | Registro de usuario | 3 | Done | #32, #33 | ✅ |
| PF-24 | Login con JWT | 3 | Done | #34, #35 | ✅ |
| PF-27 | Aislamiento de datos multiusuario | 2 | Done | #36 | ✅ |
| PF-25 | Refresh y logout | 2 | Done | #37 | ✅ |
| PF-26 | Perfil y preferencias | 2 | Done | #38 | ✅ |

- **Comprometido:** 13 SP · **Completado:** 13 SP

## Demo
- `POST /auth/register` (201, 409 sin distinguir mayúsculas, 422 sin repetir la contraseña) y `POST /auth/login` (mismo 401 para email o contraseña incorrectos).
- `POST /auth/refresh` rota el refresh token (el anterior da 401) y `POST /auth/logout` lo revoca.
- `GET /me` y `PATCH /me/preferences` (MEP por defecto).
- Aislamiento: un usuario recibe 404 con los recursos de otro (test e2e con dos usuarios reales).
- Seguridad: Argon2id, `JWT_SECRET` obligatorio en producción, 401 con `WWW-Authenticate: Bearer`.

## Cambios al Product Backlog
- **Registro:** suma el campo `name` (lo necesitan `GET /me` y el front).
- **Arquitectura:** `CurrentUserId` y la validación de tokens viven en `app.shared`; contrato de independencia entre módulos; `UserScopedRepository` para todo recurso propio.
- **Sprint 4:** entra PF-82 (login en el front); US-013 (saldo derivado) pasa al Sprint 5 porque depende de los movimientos, y entra US-015 en su lugar.
- **Propuestas sin decidir:** revocar todas las sesiones si se reusa un refresh rotado (detección de robo) y un job que limpie los refresh tokens vencidos.

## Release
- [x] Sin release este sprint.
