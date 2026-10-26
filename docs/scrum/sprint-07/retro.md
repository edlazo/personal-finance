# Sprint 7: Retrospectiva

- **Fecha:** 2026-10-25
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 16 SP (más 2 tareas sin SP) |
| Velocity promedio (últimos 3) | 15 SP |
| Historias completadas / comprometidas | 4 / 4 |
| Bugs encontrados | 1 (el worker no guardaba cotizaciones; venía de la v0.1.0) |
| Cobertura de tests | 99 % backend; frontend sin medir |
| Tiempo medio de PR abierto → merge | Mismo día (10 PRs) |

## Qué salió bien (mantener)
- La imagen Docker ya se construye en cada PR (acción A1): no volvió a haber sorpresas de build.
- Las decisiones se tomaron al arrancar cada historia (acción A5): catálogo por usuario, precio de la última operación, movimientos ligados a operaciones, tenencia por cuenta.
- La operación y su movimiento de cuenta se guardan en la misma transacción aunque viven en módulos distintos: el contrato de `app.shared` usa la sesión de quien lo pide.
- Levantar la app completa encontró un bug que ningún test veía.
- _(PO) sin aportes._

## Qué no salió bien (mejorar)
1. **(SM/Dev)** Dos historias pasaron las 400 líneas (PF-43 con 479 y PF-44 con 481) y hubo que dividirlas sobre la marcha; el freno del commit funcionó, pero la estimación de tamaño sigue fallando en módulos nuevos.
2. **(SM/Dev)** El bug del worker llegó a la v0.1.0: los tests corren en un solo proceso que ya importó todos los modelos, así que nunca vieron que al worker le faltaba la tabla `users`.
3. El Postgres local se cae con cada sesión y hay que reiniciarlo.
4. Los checks requeridos siguen vacíos en los rulesets (acción A2) y Docker sigue sin arrancar.
5. _(PO) sin aportes._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | En historias con módulo nuevo, planear desde el inicio dos PRs (dominio y casos de uso; base y API) | Dev | Permanente |
| A2 | Cargar los checks requeridos en los rulesets de develop y main; `pre-commit install` y cerrar el PR #19 | PO | Antes del primer PR del Sprint 8 |
| A3 | Antes de cada cierre, levantar la app completa (API, worker y frontend) contra Postgres y probar lo nuevo | Dev | Cierre de cada sprint |
| A4 | Conseguir un archivo exportado de Balanz (anonimizado) y los datos de habilitación de la API de IOL para el spike PF-48 | PO | Antes de arrancar PF-48 |

## Seguimiento de las acciones del sprint anterior
- [x] A1: build de la imagen en cada PR (PF-90).
- [ ] A2: los rulesets siguen sin checks cargados (pasa a A2).
- [x] A3: Postgres local documentado en CONTRIBUTING (en este cierre).
- [x] A4: criterios actualizados en el mismo PR (Comisiones en el backlog, PF-39 en Jira).
- [x] A5: catálogo por usuario y precio de la última operación, decididos al arrancar.
