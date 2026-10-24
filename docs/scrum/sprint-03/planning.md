# Sprint 3: Planning

- **Fecha:** 2026-10-23
- **Fechas del sprint:** 2026-10-26 → 2026-11-06 (toma las fechas que tenía el Sprint 2)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 15,5 SP (promedio de los Sprints 1 y 2)

## Sprint Goal
> Los usuarios pueden registrarse e iniciar sesión de forma segura, y cada uno ve solo sus datos.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 1 | PF-80 | — | Límite de 72 caracteres en el asunto del commit | 1 | Acción A1 de la Retro del Sprint 2; PR ya abierto |
| 2 | PF-23 | US-006 | Registro de usuario | 3 | Sin categorías por defecto (pasan a US-014) |
| 3 | PF-24 | US-007 | Login con JWT | 3 | Depende de PF-23 |
| 4 | PF-27 | US-010 | Aislamiento de datos multiusuario | 2 | Depende de PF-24 (`current_user`) |
| 5 | PF-25 | US-008 | Refresh y logout | 2 | Depende de PF-24 |
| 6 | PF-26 | US-009 | Perfil y preferencias | 2 | Depende de PF-24 |

**Total comprometido:** 13 SP

## Decisiones
- Se compromete por debajo del promedio (13 de 15,5 SP): es el primer módulo de dominio y toca seguridad; el Sprint 2 llegó a 18 SP porque sumó una historia ya refinada.
- Las categorías por defecto salen de US-006 y pasan a US-014 (Sprint 4), que además se las crea a los usuarios ya registrados.
- Nueva historia **PF-82** (US-061): login y registro en el frontend, 3 SP, al backlog para un próximo sprint.

## Riesgos
- Primer código con datos sensibles (contraseñas, tokens): revisar Argon2id, expiración y rotación de tokens con tests antes de cada merge.
- La migración de categorías para usuarios existentes (US-014) depende de que el modelo de usuario de este sprint no cambie.
