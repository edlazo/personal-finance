# Sprint 6: Retrospectiva

- **Fecha:** 2026-10-25
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 15 SP |
| Velocity promedio (últimos 3) | 14,3 SP |
| Historias completadas / comprometidas | 5 / 5 |
| Bugs encontrados | 0 |
| Cobertura de tests | 99 % backend; frontend sin medir |
| Tiempo medio de PR abierto → merge | Mismo día (5 PRs) |

## Qué salió bien (mantener)
- La suite completa contra Postgres antes de cada push (acción A1) frenó otra deprecación de SQLAlchemy 2.1 (`distinct` con columnas) antes de llegar al CI. El CI de develop no se rompió en todo el sprint.
- La acción A4 se decidió al arrancar PF-41 y quedó aplicada: ledger convierte saldos y lee la cotización preferida por contratos de `app.shared`, sin importar fx ni identity.
- El adaptador de dolarapi se probó una vez contra la API real además de los tests con datos fijos.
- _(PO) sin aportes._

## Qué no salió bien (mejorar)
1. **(SM/Dev)** El Postgres local se cayó al cerrarse la sesión y no arranca directo con un usuario administrador; se perdió tiempo hasta usar `pg_ctl`.
2. **(SM/Dev)** El criterio de PF-39 en Jira pedía respx, en contra de una decisión técnica anterior (httpx2). El backlog no se actualizó cuando se cambió la librería.
3. La imagen Docker nunca se construyó en CI: `docker.yml` solo corre en `main`, así que el primer build es el merge de la release.
4. Docker Desktop sigue sin arrancar y los checks requeridos siguen vacíos en los rulesets (acciones A2 y A3 del Sprint 5).
5. _(PO) sin aportes._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | Construir la imagen Docker (sin publicarla) en los checks de cada PR | Dev | Primer PR del Sprint 7 |
| A2 | Cargar los checks requeridos en los rulesets de develop y main (la regla existe pero sin checks); `pre-commit install` y cerrar el PR #19 | PO | Antes del primer PR del Sprint 7 |
| A3 | Documentar en CONTRIBUTING el Postgres local como alternativa a Docker para los tests de integración | Dev | Durante el Sprint 7 |
| A4 | Cuando una decisión técnica cambia un criterio, actualizar la historia en Jira y en el backlog en el mismo PR | Dev | Permanente |
| A5 | Decidir con el PO si el catálogo de instrumentos es global o por usuario (PF-43) y qué precio usa la valuación antes de la carga de precios del Sprint 8 (PF-45) | PO + Dev | Al arrancar cada historia |

## Seguimiento de las acciones del sprint anterior
- [x] A1: suite completa contra Postgres antes de cada push.
- [ ] A2: los rulesets tienen la regla de checks requeridos, pero sin checks cargados (pasa a A2).
- [ ] A3: Docker sigue sin arrancar; se documenta el Postgres local (pasa a A3).
- [x] A4: contratos en `app.shared` conectados por `main.py`.
