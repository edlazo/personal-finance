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
| A4 | Pedir a IOL la habilitación de la API para la cuenta del PO (ver el detalle abajo) | PO | Antes de arrancar PF-48 |

### Detalle de la acción A4: por qué pedimos la API de IOL
- **Para qué:** la app valúa la cartera con el precio de cada instrumento. Hoy ese precio se carga a mano (US-029); con la API, las acciones, CEDEARs, bonos y ONs de BYMA se actualizan solos (US-033).
- **Qué se usa:** solo lectura de cotizaciones (y, si el spike lo confirma, del portafolio para comparar tenencias). La app no envía órdenes ni opera.
- **Uso:** personal y no comercial, con la cuenta del propio PO y sin terceros.
- **Seguridad:** las credenciales se guardan cifradas (US-032) y nunca se devuelven en ninguna respuesta.
- **Frecuencia:** baja, del orden de cada 30 minutos en horario de mercado (unas 286 corridas por mes).
- **Límite:** IOL permite 25.000 llamadas por mes y pasarlo se cobra. La app cuenta cada llamada y se frena sola al 80 % (20.000). Con una llamada por instrumento entran unos 68 instrumentos; si IOL trae varias cotizaciones por llamada, mucho menos uso.
- **Decisión del PO:** Balanz queda fuera; solo se integra IOL.

## Seguimiento de las acciones del sprint anterior
- [x] A1: build de la imagen en cada PR (PF-90).
- [ ] A2: los rulesets siguen sin checks cargados (pasa a A2).
- [x] A3: Postgres local documentado en CONTRIBUTING (en este cierre).
- [x] A4: criterios actualizados en el mismo PR (Comisiones en el backlog, PF-39 en Jira).
- [x] A5: catálogo por usuario y precio de la última operación, decididos al arrancar.
