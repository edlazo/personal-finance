# Sprint 10: Retrospectiva

- **Fecha:** 2026-11-02
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 14 SP |
| Velocity promedio (últimos 3) | 15 SP |
| Historias completadas / comprometidas | 4 / 4 |
| Bugs encontrados | 2 antes del push: el alta de una deuda devolvía el capital sin decimales y la consulta con dos; una llamada deprecada de SQLAlchemy 2.1 (`Result.tuples()`) que atrapó la suite. Los dos se corrigieron en el mismo PR |
| Cobertura de tests | 99 % backend; frontend sin medir |
| Tiempo medio de PR abierto → merge | Mismo día (10 PRs: #116 a #118 y #129 a #135) |

## Qué salió bien (mantener)
- Las acciones A1 y A2 del Sprint 9 salieron en los primeros PRs del sprint: la A1 venía arrastrándose desde hacía dos sprints.
- El contrato `CashMovements` de `app.shared` sirvió sin cambios para los pagos de tarjeta, los pagos de deuda y los cobros de préstamos: los 3 contratos de import-linter siguen en verde.
- Las decisiones del PO al arrancar cada historia (pago por moneda, sistema francés, imputación de pagos) evitaron retrabajo, como en el Sprint 9.
- Los warnings como error atraparon la deprecación de SQLAlchemy antes del push.
- El smoke test contra Postgres pasó entero a la primera, con los saldos de las cuentas cuadrando.
- _(PO) sin aportes._

## Qué no salió bien (mejorar)
1. **(SM/Dev)** Los PRs siguen al límite:
   - PF-58 midió 485 líneas y salió en 3 PRs, en vez de los 2 planeados;
   - PF-59 quedó en 400 justas después de sacar un test que repetía otro;
   - el primero de PF-57 quedó en 398.
2. **(SM/Dev)** Un `git stash` sin `-u` dejó afuera un archivo nuevo, que terminó en el primer PR de PF-58. Hubo que corregir el commit y rearmar la pila antes del merge.
3. **(SM/Dev)** Dependabot abrió una segunda tanda de PRs (#119 a #128) mientras se aplicaba la primera, y nadie la revisa hasta que existe una tarea.
4. Los checks requeridos de los rulesets de develop y main siguen vacíos (seis sprints, verificado por la API de GitHub). El job de IOL sigue sin probarse con tenencias reales.
5. _(PO) sin aportes._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | En historias de módulo nuevo, planear un PR por capa (dominio, persistencia, API) y medir el diff antes de sumar los tests de integración | Dev | Sprint 11 (recurrentes y patrimonio neto) |
| A2 | Al partir PRs apilados, usar `git stash -u` y revisar que `git status` quede limpio antes de cada commit | Dev | Desde el Sprint 11 |
| A3 | Revisar el log del job de IOL (`iol_holding_skipped`) cuando el portafolio del PO tenga una posición | PO + Dev | Cuando haya tenencias |
| A4 | Cargar los checks requeridos en los rulesets de develop y main | PO | Antes del primer PR del Sprint 11 |

## Seguimiento de las acciones del sprint anterior
- [x] A1: los dobles de inversiones deshacen los cambios cuando la operación falla (PF-97, #117).
- [x] A2: `App.test.tsx` no volvió a fallar en el CI (PF-98, #118).
- [ ] A3: el portafolio del PO sigue sin tenencias (vuelve como A3).
- [ ] A4: los rulesets siguen sin checks cargados (vuelve como A4).
