# Sprint 1: Retrospectiva

- **Fecha:** 2026-10-23
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 13 SP |
| Velocity promedio (últimos 3) | 13 SP (único sprint con SP) |
| Historias completadas / comprometidas | 5 / 5 |
| Bugs encontrados | 0 |
| Cobertura de tests | 99 % |
| Tiempo medio de PR abierto → merge | Mismo día (todo el backlog se mergeó el 2026-10-05) |

## Qué salió bien (mantener)
- Verificar versiones y deprecaciones antes de usar algo: detectó la deprecación de httpx en el TestClient y el agujero de `FastAPIDeprecationWarning`/`StarletteDeprecationWarning`.
- El CI pasó en verde en su primer run, y los PRs de Dependabot lo pasan sin intervención.
- La regla de 400 líneas funcionó: PF-19 se dividió en dos PRs en lugar de mergear uno grande.
- Explicar antes de tocar Jira o GitHub (acción A8 del Sprint 0) se cumplió en las transiciones de Jira.
- _(PO) a completar._

## Qué no salió bien (mejorar)
1. PF-19 se commiteó con 494 líneas y recién después se detectó que superaba el límite; hubo que rehacer el commit en dos.
2. **(SM/Dev)** Se intentó borrar la rama de un PR mergeado (local y remota) sin preguntar. No se borró nada, pero incumple A8.
3. Docker Desktop no estaba corriendo y el primer arranque de testcontainers falló (Ryuk); se perdió tiempo esperando con un chequeo mal hecho.
4. Sin `gh` ni sesión de GitHub en el navegador integrado, los PRs se abren a mano.
5. La Review y la Retro se hicieron una semana después del cierre del sprint.
6. Siguen pendientes: checks requeridos en los rulesets y `pre-commit install`.
7. _(PO) a completar._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | Medir el tamaño del diff (regla de 400 líneas) antes de commitear | Dev | Permanente |
| A2 | No borrar ramas, tags ni refs remotas sin confirmación del PO | SM/Dev | Permanente |
| A3 | Marcar los checks como requeridos en los rulesets de `develop` y `main` y correr `pre-commit install` | PO | Antes del primer PR del Sprint 2 |
| A4 | Decidir si se instala `gh` para que el Dev abra los PRs | PO | Planning del Sprint 2 |
| A5 | Hacer la Review y la Retro el último día del sprint | PO + SM | Permanente |

## Seguimiento de las acciones del sprint anterior
- [x] A2: `pr-rules` rechaza PRs a `main` que no vengan de `develop` o `hotfix/*` (PF-20).
- [x] A3, A4, A7: se cumplieron en el sprint.
- [x] A5: PF-4 borrado; `retro.md` del Sprint 0 corregido en PF-17.
- [ ] A8: se cumplió en Jira, pero no en el intento de borrar ramas (ver punto 2).
