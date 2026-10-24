# Sprint 4: Retrospectiva

- **Fecha:** 2026-10-24
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 14 SP |
| Velocity promedio (últimos 3) | 15 SP |
| Historias completadas / comprometidas | 5 / 5 |
| Bugs encontrados | 0 |
| Cobertura de tests | 99 % backend; frontend sin medir |
| Tiempo medio de PR abierto → merge | Mismo día (13 PRs) |

## Qué salió bien (mantener)
- Las decisiones de alcance se consultaron antes de implementar (acción A2 del Sprint 3): saldos negativos, archivadas, criterios que dependían de movimientos, categorías al primer uso, subcategorías y almacenamiento de tokens. No hubo retrabajo por sorpresas de alcance.
- Seguridad del login decidida antes de escribirlo: cookie httpOnly para el refresh y una sola renovación compartida entre pedidos simultáneos.
- Con Docker caído, las migraciones escritas a mano se validaron con el SQL offline de Alembic y el CI las confirmó en verde.
- _(PO) sin aportes._

## Qué no salió bien (mejorar)
1. Docker Desktop no arrancó en todo el sprint (error del socket `userAnalyticsOtlpHttp.sock`): los tests de integración y las migraciones no se pudieron correr en local y el login no se probó de punta a punta en el navegador.
2. **(SM/Dev)** Estimaciones de tamaño erradas: PF-28 pasó de 2 a 3 PRs y un commit de PF-82 de 453 líneas llegó a pushearse porque el comando solo frenaba por el largo del asunto.
3. Una respuesta del PO con opciones contradictorias (saldos negativos) la interpretó el Dev; se avisó, pero conviene confirmar antes.
4. El sprint volvió a cerrarse antes de su fecha de inicio (resuelto con la regla de cadencia).
5. Siguen abiertas las acciones de rulesets, `pre-commit install` y el PR #19.
6. _(PO) sin aportes._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | El comando de commit frena por tamaño (≤ 400) además de por el largo del asunto | Dev | Permanente (aplicado) |
| A2 | Arreglar Docker Desktop y probar el flujo de login completo en el navegador | PO + Dev | Antes del primer PR del Sprint 5 |
| A3 | Ante respuestas ambiguas o contradictorias del PO, repreguntar antes de implementar | Dev | Permanente |
| A4 | Decidir cómo se comunican ledger y accounts (movimientos ↔ cuentas, saldo derivado) sin que un módulo importe al otro | PO + Dev | Al arrancar PF-33 |
| A5 | Rulesets con los checks requeridos, `pre-commit install` y cerrar el PR #19 | PO | Antes del primer PR del Sprint 5 |

## Seguimiento de las acciones del sprint anterior
- [x] A1: se planeó la división de PRs al arrancar cada historia (con dos errores de estimación, ver punto 2).
- [x] A2: los cambios de alcance se propusieron antes de implementarlos.
- [x] A3: cadencia decidida (2 semanas por objetivo).
- [ ] A4: rulesets, `pre-commit install` y PR #19 siguen pendientes.
- [x] A5: el Sprint 5 se re-planificó a 14 SP.
