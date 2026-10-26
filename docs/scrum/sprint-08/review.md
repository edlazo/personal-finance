# Sprint 8: Review

- **Fecha:** 2026-10-26
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Valuar la cartera con precios cargados a mano y de cripto automáticos, registrar rentas y preparar las integraciones con brokers. → **Cumplido ✅**
- **Nota:** se completó el día de su inicio (2026-10-26). Por la regla de cadencia, se cierra y el Sprint 9 toma sus fechas.

## Historias y tareas
| Key Jira | Ítem | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-46 | Carga manual de precios | 3 | Done | #85 | ✅ |
| PF-50 | Precios de cripto desde CoinGecko | 2 | Done | #86, #87 | ✅ |
| PF-47 | Dividendos, rentas y amortizaciones | 3 | Done | #89, #90, #88 | ✅ |
| PF-86 | Gastos y transferencias sin saldo negativo | 3 | Done | #92 | ✅ |
| PF-48 | Spike: API de IOL | 2 | Done | #84 | ✅ |
| PF-49 | Credenciales de broker cifradas | 3 | Done | #97, #98 | ✅ |
| PF-93 | pr-rules acepta PRs apilados (tarea) | — | Done | #99 | ✅ |

- **Comprometido:** 16 SP · **Completado:** 16 SP

## Demo (app levantada contra Postgres, acción A3 del Sprint 7)
- Precios: `POST /prices` y la posición toma el de fecha más reciente (`MANUAL`, `API` o `LAST_TRADE`). El job horario trajo de CoinGecko el precio real de BTC.
- Rentas: cupón y dividendo acreditan la cuenta como ingreso en "Rentas" y suman al P&L realizado; la amortización de 250 VN bajó la tenencia de AL30 de 1.000 a 750 y dejó 17.500 de P&L realizado.
- Saldo no negativo: un gasto que dejaba una caja en negativo y una compra de BTC sin fondos en la wallet respondieron 422 con la cuenta y el día.
- Credenciales de IOL: se guardan cifradas, el estado solo muestra la pista del usuario y se borran.
- Spike de IOL: con la prueba real, el diseño de US-033 baja de ~20.000 a ~570 llamadas por mes (portafolio en una llamada).

## Cambios al Product Backlog
- **Decisiones del PO aplicadas:** el precio de fecha más reciente gana (a igual fecha, el guardado); CoinGecko cada hora y gana el último que entró; dividendos y cupones son ingreso en Rentas y suman al P&L; la amortización es un rescate parcial; la regla de saldo no negativo vale para todo lo que resta (también compras desde una wallet); credenciales sin verificar contra IOL y con consulta de estado; solo IOL (Balanz fuera); la comitente vinculada a IOL toma tenencias y precios del portafolio; órdenes reales a IOL a futuro con sandbox (US-064 → PF-92).
- **Sprint 9:** suma US-037 y US-038 (tarjetas de crédito) y queda en 15 SP.

## Release
- [x] Sin release este sprint (v0.2.0 al cierre del Sprint 9).
