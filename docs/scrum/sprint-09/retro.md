# Sprint 9: Retrospectiva

- **Fecha:** 2026-10-27
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 15 SP |
| Velocity promedio (últimos 3) | 15,7 SP |
| Historias completadas / comprometidas | 4 / 4 |
| Bugs encontrados | 2 antes del push: con el portafolio de IOL vacío volvían a contar las operaciones manuales; las cuotas se insertaban antes que su compra. Los dos se corrigieron en el mismo PR |
| Cobertura de tests | 99 % backend; frontend sin medir |
| Tiempo medio de PR abierto → merge | Mismo día o el siguiente (10 PRs) |

## Qué salió bien (mantener)
- Las decisiones del PO al arrancar cada historia evitaron retrabajo: la prioridad de precios, las monedas de la tarjeta y el reparto de las cuotas se definieron antes de escribir código.
- Los PRs apilados funcionaron sin fricción: PF-51 salió en 4 PRs y PF-54 y PF-55 en 2 cada uno, sin commits repetidos (PF-93 y acción A3).
- Los tests de integración contra Postgres atraparon el orden de los inserts de las cuotas antes del push.
- La prueba de la app completa usó data912 real y confirmó la regla de prioridad de precios.
- _(PO) sin aportes._

## Qué no salió bien (mejorar)
1. **(SM/Dev)** Un test del frontend (`App.test.tsx`) falló en el CI del PR del fix sin relación con el cambio; hubo que relanzarlo a mano.
2. **(SM/Dev)** Los PRs siguen al límite: el primero de PF-55 quedó en 400 líneas justas después de recortar tests, y PF-54 se partió en dos.
3. **(SM/Dev)** La acción A1 (dobles de inversiones que deshacen los cambios cuando la operación falla) no se hizo por segundo sprint.
4. El job de IOL no se probó con tenencias reales: el formato de una posición sale de la documentación.
5. Los checks requeridos de los rulesets siguen vacíos (cinco sprints) y el Postgres local se cae entre sesiones.
6. _(PO) sin aportes._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | Los dobles de inversiones deshacen los cambios cuando la operación falla, como los de ledger | Dev | Primer PR del Sprint 10 |
| A2 | Estabilizar `App.test.tsx` para que no falle por tiempos del CI | Dev | Durante el Sprint 10 |
| A3 | Revisar el log del job de IOL (`iol_holding_skipped`) cuando el portafolio del PO tenga una posición | PO + Dev | Cuando haya tenencias |
| A4 | Cargar los checks requeridos en los rulesets de develop y main | PO | Antes del primer PR del Sprint 10 |

## Seguimiento de las acciones del sprint anterior
- [ ] A1: los dobles de inversiones siguen sin rollback (vuelve como A1).
- [x] A2: el P&L realizado sin ventas sale con dos decimales (#105).
- [x] A3: los PRs apilados se abrieron desde los links antes de mergear el primero.
- [ ] A4: los rulesets siguen sin checks cargados (vuelve como A4).
