# Sprint 4: Planning

- **Fecha:** 2026-10-23
- **Fechas del sprint:** 2026-10-26 → 2026-11-06 (toma las fechas que tenía el Sprint 3)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 14,7 SP (promedio de los Sprints 1 a 3)

## Sprint Goal
> Gestionar cuentas en ARS/USD y categorías, y entrar a la app con un login real.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 1 | PF-28 | US-011 | Crear cuenta | 3 | Primer recurso con `UserScopedRepository` + test de aislamiento propio |
| 2 | PF-29 | US-012 | Listar, editar y archivar cuentas | 3 | Depende de PF-28 |
| 3 | PF-31 | US-014 | Categorías por defecto | 2 | Incluye la migración para usuarios ya registrados |
| 4 | PF-32 | US-015 | Gestionar categorías y subcategorías | 3 | Depende de PF-31 |
| 5 | PF-82 | US-061 | Login y registro en el frontend | 3 | Usa los endpoints de Identity del Sprint 3 |

**Total comprometido:** 14 SP

## Decisiones
- US-013 (saldo derivado, PF-30) pasa al Sprint 5: su criterio es "saldo inicial + suma de movimientos" con consulta a una fecha, y los movimientos llegan con US-016. Entra US-015 (mismo tamaño).
- Las categorías por defecto se crean "al registrarse", pero el registro vive en `identity` y las categorías en otro módulo, que no se pueden importar entre sí: el mecanismo (por ejemplo, un evento compartido de usuario registrado) se decide al arrancar PF-31 y se consulta con el PO.

## Riesgos
- Primer módulo de dominio con dinero: montos como `Decimal` (`NUMERIC(20,2)`), nunca `float`.
- El Sprint 5 queda en 17 SP (seis historias): hay que re-planificarlo.
