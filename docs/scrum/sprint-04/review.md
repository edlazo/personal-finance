# Sprint 4: Review

- **Fecha:** 2026-10-24
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Gestionar cuentas en ARS/USD y categorías, y entrar a la app con un login real. → **Cumplido ✅**
- **Nota:** se completó antes de su inicio previsto (2026-10-26), igual que los Sprints 2 y 3. Desde este cierre rige la regla de 2 semanas por objetivo (working agreement).

## Historias
| Key Jira | Historia | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-28 | Crear cuenta | 3 | Done | #40, #41, #42 | ✅ |
| PF-29 | Listar, editar y archivar cuentas | 3 | Done | #43, #44 | ✅ |
| PF-31 | Categorías por defecto | 2 | Done | #45 | ✅ |
| PF-32 | Gestionar categorías y subcategorías | 3 | Done | #46, #47 | ✅ |
| PF-82 | Login y registro en el frontend | 3 | Done | #48 a #52 | ✅ |

- **Comprometido:** 14 SP · **Completado:** 14 SP

## Demo
- Cuentas: alta con reglas de saldo (solo la comitente admite negativo), nombre único sin distinguir mayúsculas, listado, edición, archivado de solo lectura y 404 con las cuentas de otro usuario.
- Categorías: las 13 por defecto en el primer uso, subcategorías de un nivel, renombrar, mover y archivar con sus hijas.
- Front: login y registro con errores de la API, dashboard protegido, sesión que sobrevive a la recarga, header y perfil con el usuario real y Salir.
- Seguridad: refresh token en cookie httpOnly + SameSite=Strict (Secure en producción); access token solo en memoria; renovación compartida entre pedidos simultáneos.
- **Pendiente para la demo:** el flujo completo en el navegador contra la API real no se probó porque Docker Desktop no arranca en la máquina del PO.

## Cambios al Product Backlog
- **Decisiones del PO aplicadas:** solo BROKER admite saldo negativo; las cuentas y categorías archivadas son de solo lectura; las categorías por defecto se crean en el primer uso; archivar una categoría archiva sus subcategorías; refresh en cookie httpOnly.
- **Criterios movidos:** las validaciones de cuentas que dependen de movimientos pasan a US-016 (PF-33); la de presupuestos activos al archivar una categoría pasa a US-045 (PF-62).
- **Cambio de API:** `POST /auth/login` y `/auth/refresh` ya no devuelven `refresh_token` en el cuerpo.
- **Sprint 5:** US-020 (compra/venta de USD) pasa al Sprint 6.

## Release
- [x] Sin release este sprint.
