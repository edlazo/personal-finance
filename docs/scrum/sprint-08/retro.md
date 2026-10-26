# Sprint 8: Retrospectiva

- **Fecha:** 2026-10-26
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity del sprint | 16 SP (más 1 tarea sin SP) |
| Velocity promedio (últimos 3) | 15,7 SP |
| Historias completadas / comprometidas | 6 / 6 |
| Bugs encontrados | 1 cosmético en la prueba de la app: el P&L realizado sin ventas sale como "0" en vez de "0.00" |
| Cobertura de tests | 99 % backend; frontend sin medir |
| Tiempo medio de PR abierto → merge | Mismo día (13 PRs) |

## Qué salió bien (mantener)
- Las decisiones se tomaron al arrancar cada historia, y el PO cambió el rumbo de la integración con datos reales (solo IOL, portafolio, límite de llamadas) antes de escribir código.
- El spike con la cuenta real del PO bajó el consumo estimado de IOL de ~20.000 a ~570 llamadas por mes.
- La prueba de la app completa antes del cierre (acción A3) pasó de punta a punta, incluido el job de cripto contra CoinGecko real.
- Las historias con módulo o tabla nueva se planearon en varios PRs desde el arranque (acción A1).
- _(PO) sin aportes._

## Qué no salió bien (mejorar)
1. **(SM/Dev)** Los PRs apilados generaron fricción: el #98 quedó con 2 commits y con un título armado con el nombre de la rama. Se resolvió de raíz con PF-93 (pr-rules cuenta solo commits nuevos).
2. **(SM/Dev)** Los tamaños siguen al límite: un PR de PF-47 dio 407 líneas y hubo que recortar tests.
3. **(SM/Dev)** Los dobles en memoria no deshacían los cambios cuando una operación fallaba; en ledger se corrigió en PF-86, en inversiones sigue igual.
4. Los checks requeridos de los rulesets siguen vacíos (cuatro sprints), Docker sigue sin arrancar y el Postgres local se cae con cada sesión.
5. _(PO) sin aportes._

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | Los dobles de inversiones deshacen los cambios cuando la operación falla, como los de ledger | Dev | Durante el Sprint 9 |
| A2 | El P&L realizado sin ventas se muestra con dos decimales | Dev | Primer PR del Sprint 9 |
| A3 | Con varios PRs, abrirlos todos desde los links (base = PR anterior) antes de mergear el primero | PO + Dev | Permanente |
| A4 | Cargar los checks requeridos en los rulesets de develop y main | PO | Antes del primer PR del Sprint 9 |

## Seguimiento de las acciones del sprint anterior
- [x] A1: PF-49 se planeó en 2 PRs y PF-47 en 3 desde el arranque.
- [ ] A2: los rulesets siguen sin checks cargados (pasa a A4).
- [x] A3: la app se levantó y probó completa antes de este cierre.
- [x] A4: el PO pidió y obtuvo la habilitación de la API de IOL.
