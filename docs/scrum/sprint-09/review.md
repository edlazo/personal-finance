# Sprint 9: Review

- **Fecha:** 2026-10-27
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Valuar la cartera de IOL automáticamente y empezar a seguir las tarjetas de crédito. → **Cumplido ✅**
- **Nota:** se completó al día siguiente de su inicio (2026-10-27). Por la regla de cadencia, se cierra y el Sprint 10 toma sus fechas.

## Historias y tareas
| Key Jira | Ítem | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| — | P&L realizado con dos decimales (acción A2 del Sprint 8) | — | Done | #105 | ✅ |
| PF-51 | Portafolio y precios desde IOL | 5 | Done | #101, #102, #103, #104 | ✅ |
| PF-52 | Precios de BYMA y EE.UU. desde data912 | 3 | Done | #107 | ✅ |
| PF-54 | Alta de tarjeta de crédito | 2 | Done | #109, #108 | ✅ |
| PF-55 | Compras en cuotas | 5 | Done | #111, #112 | ✅ |

- **Comprometido:** 15 SP · **Completado:** 15 SP

## Demo (app levantada contra Postgres)
- IOL: la comitente se vincula a IOL, las credenciales quedan guardadas y una compra manual en esa cuenta responde 422. No se llamó a IOL real: el portafolio del PO sigue sin tenencias.
- data912: el job trajo el precio real de GGAL (5.835) y le ganó a un precio manual más nuevo, como decidió el PO.
- Tarjetas: una Visa bimonetaria con límite; una tele de $1.000.000 en 3 cuotas (333.333,34 + 333.333,33 + 333.333,33) y una suscripción en USD entran en el resumen que cierra el 25/11, porque la compra del 27/10 es posterior al cierre de octubre.

## Cambios al Product Backlog
- **Decisiones del PO aplicadas:**
  - **IOL:** manda en la cuenta vinculada, aunque el portafolio llegue vacío; job en días hábiles cada 30 minutos de 11 a 17 h, unas 616 llamadas por mes.
  - **Prioridad de precios:** el precio automático (data912 o CoinGecko) gana al manual aunque sea más viejo.
  - **data912:** cubre BYMA y EE.UU., en el mismo horario que IOL.
  - **Tarjetas:** siempre en pesos y, si son bimonetarias, también en dólares; cierre y vencimiento en día fijo del mes (en un mes más corto, su último día).
  - **Cuotas:** los centavos que sobran van en la primera; son pendientes las de resúmenes que no vencieron; la compra no lleva categoría por ahora.
- **Sprint 10:** suma US-041 y US-042 (deudas) y queda en 14 SP.

## Release
- [x] **v0.2.0**: inversiones, integraciones de mercado y primeras tarjetas (ver CHANGELOG).
