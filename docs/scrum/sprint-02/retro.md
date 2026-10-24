# Sprint 2: Retrospectiva

- **Fecha:** 2026-10-23
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 18 SP (13 comprometidos + 5 sumados) |
| Velocity promedio (últimos 3) | 15,5 SP (Sprints 1 y 2) |
| Historias completadas / comprometidas | 5 / 4 (una sumada en el sprint) |
| Bugs encontrados | 0 |
| Cobertura de tests | Backend ≥ 85 % (exigida en el CI); frontend sin medir |
| Tiempo medio de PR abierto → merge | Mismo día |

## Qué salió bien (mantener)
- Medir el diff antes de commitear (acción A1 del Sprint 1): PF-76 y PF-79 se dividieron a tiempo y ningún PR superó las 400 líneas.
- Verificar versiones antes de usar algo: se detectaron los cambios de la plantilla de Vite (oxlint, TypeScript 6), se verificó el paquete nuevo `cn` de shadcn y Recharts se subió a la última versión.
- El job `quality / frontend` funcionó desde su primer run, y la regla de un commit frenó dos PRs de Dependabot actualizados con merge commits.
- _(PO) sin aportes (confirmado en el cierre del Sprint 3)._

## Qué no salió bien (mejorar)
1. **(SM/Dev)** Dos asuntos de commit pasaron los 72 caracteres (PF-77 y PF-79) aunque se medían: se imprimía el largo pero no se frenaba el commit, y Git Bash contaba bytes. El PR #15 falló por lo mismo.
2. Los conflictos de los PRs de Dependabot se resolvieron desde GitHub ("Update branch" y el editor web): quedaron merge commits y, en el #17, un lockfile mezclado.
3. El primer intento de PF-76 dio 479 líneas por el código que genera shadcn.
4. No se pudo verificar la navegación por teclado en el navegador integrado, y los tests de integración de PF-22 no corrieron en local (Docker apagado); se confió en el CI.
5. El Sprint 2 se ejecutó antes de sus fechas planificadas: Jira y el acta del Planning no coinciden con lo que pasó.
6. Siguen abiertas las acciones A3 y A4 del Sprint 1, y faltan los aportes del PO en su Retro.
7. _(PO) sin aportes (confirmado en el cierre del Sprint 3)._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | El hook y el CI rechazan asuntos de más de 72 caracteres (PF-80) | Dev | Sprint 3, primer PR |
| A2 | No resolver conflictos de Dependabot en GitHub: comentar `@dependabot recreate` | PO | Permanente |
| A3 | Checks requeridos en los rulesets (sumar `quality / frontend`) y `pre-commit install` | PO | Antes del primer PR del Sprint 3 |
| A4 | Probar la navegación por teclado del dashboard en un navegador real | PO | Sprint 3 |
| A5 | Alinear las fechas del sprint en Jira con las reales | PO | Planning del Sprint 3 |

## Seguimiento de las acciones del sprint anterior
- [x] A1: se midió el diff antes de cada commit.
- [x] A2: no se borraron ramas sin confirmación (quedan `fix-pr17` y las `feature/*` ya mergeadas, a la espera del PO).
- [ ] A3: rulesets y `pre-commit install` siguen pendientes.
- [ ] A4: no se decidió lo de `gh`.
- [ ] A5: esta Review y Retro se hacen el mismo día del cierre, pero antes de la fecha planificada.
