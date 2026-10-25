# Sprint 5: Retrospectiva

- **Fecha:** 2026-10-24
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 14 SP |
| Velocity promedio (últimos 3) | 13,7 SP |
| Historias completadas / comprometidas | 5 / 5 |
| Bugs encontrados | 1 (CI de develop en rojo tras #57, corregido en #58) |
| Cobertura de tests | 99 % backend; frontend sin medir |
| Tiempo medio de PR abierto → merge | Mismo día (8 PRs) |

## Qué salió bien (mantener)
- Se repreguntó antes de implementar (acción A3): cómo se comunican movimientos y cuentas, subcategorías en el filtro, borrado definitivo y qué se edita en una transferencia. No hubo retrabajo por alcance.
- Las transferencias como dos movimientos normales ligados por `transfer_group_id` hicieron que el saldo derivado las sumara sin cambios.
- Con un Postgres local (binarios del paquete pgserver) volvieron a correr en local las integraciones, y la migración de PF-36 se generó con autogenerate y se probó subiendo y bajando.
- _(PO) sin aportes._

## Qué no salió bien (mejorar)
1. **(SM/Dev)** PF-30 se pusheó sin correr las integraciones (`Result.tuples()`, deprecado en SQLAlchemy 2.1) y su PR se mergeó con el CI en rojo: develop quedó roto hasta el fix #58.
2. Sin checks requeridos en los rulesets nada impide mergear un PR en rojo (acción A5 del Sprint 4, sigue abierta).
3. Docker Desktop sigue sin arrancar; el Postgres local es un parche que vive en una carpeta temporal.
4. _(PO) sin aportes._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | Correr toda la suite, integraciones incluidas, contra Postgres antes de cada push | Dev | Permanente (aplicado desde PF-34) |
| A2 | Rulesets con los checks requeridos (`quality / test` y el resto) para que un PR en rojo no se pueda mergear; `pre-commit install` y cerrar el PR #19 | PO | Antes del primer PR del Sprint 6 |
| A3 | Arreglar Docker Desktop, o dejar el Postgres local como alternativa documentada | PO + Dev | Durante el Sprint 6 |
| A4 | Decidir cómo ledger usa las cotizaciones (fx) y la cotización preferida del usuario (identity) sin importar otros módulos | PO + Dev | Al arrancar PF-41 |

## Seguimiento de las acciones del sprint anterior
- [x] A1: el commit frena por tamaño y por largo del asunto.
- [ ] A2: Docker sigue sin arrancar; las integraciones corren contra un Postgres local (pasa a A3).
- [x] A3: se repreguntó ante cada ambigüedad.
- [x] A4: accounts se unió a ledger (decisión del PO en PF-33).
- [ ] A5: rulesets, `pre-commit install` y PR #19 siguen pendientes (pasa a A2).
