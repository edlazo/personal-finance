# Sprint 10: Review

- **Fecha:** 2026-11-02
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Saber cuánto debo en cada tarjeta y cada deuda, y registrar sus pagos. → **Cumplido ✅**
- **Nota:** se completó el 2026-11-02, cuatro días antes de su fin (06/11). Por la regla de cadencia, se cierra y el Sprint 11 toma los días que le quedaban.

## Historias y tareas
| Key Jira | Ítem | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-96 | Actualizaciones de Dependabot (FastAPI 0.161, httpx2 2.16 y otras) | — | Done | #116 | ✅ |
| PF-97 | Dobles de inversiones con rollback (acción A1 del Sprint 9) | — | Done | #117 | ✅ |
| PF-98 | `App.test.tsx` estable en el CI (acción A2 del Sprint 9) | — | Done | #118 | ✅ |
| PF-56 | Resumen del período | 3 | Done | #129 | ✅ |
| PF-57 | Pago de resumen | 3 | Done | #130, #131 | ✅ |
| PF-58 | Registrar deuda o préstamo | 5 | Done | #132, #133, #134 | ✅ |
| PF-59 | Pagos de deuda | 3 | Done | #135 | ✅ |

- **Comprometido:** 14 SP · **Completado:** 14 SP

## Demo (app levantada contra Postgres)
- **Tarjeta:** una Visa bimonetaria con una tele de $900.000 en 3 cuotas y Spotify en USD, comprados el 02/11. El resumen de noviembre cierra el 25/11, vence el 05/12 y suma ARS 300.000 y USD 12,99; el período `2026-13` responde 422.
- **Pago del resumen:**
  - Pagos aceptados: un parcial de $100.000, el resto de $200.000 y los USD 12,99 desde la cuenta en dólares. El resumen queda en cero en las dos monedas.
  - Pagos rechazados con 422: los dólares desde la cuenta en pesos y un pago mayor a lo que falta.
- **Deudas:**
  - Préstamo de $120.000 a 12 meses con TNA 60 %: cuotas de $13.539,05 desde el 02/12. Con tasa y cuota fija juntas responde 422.
  - Préstamo de USD 60 a Juan, en 3 cuotas.
- **Pagos de deuda:**
  - Pago de cuota y media ($20.308,58): la cuota 1 queda pagada, la próxima es la 2 y faltan $142.160,02. Desde la cuenta en dólares responde 422.
  - Cobro de USD 20 a Juan: entra a la cuenta en dólares.
  - Los saldos de las dos cuentas cuadran con todos los movimientos.

## Cambios al Product Backlog
- **Decisiones del PO aplicadas:**
  - **Pago de resumen:** cada moneda se paga desde una cuenta en esa moneda; un pago mayor a lo que falta se rechaza; son pendientes las cuotas de resúmenes sin pagar.
  - **Deudas:**
    - el cronograma se arma con la TNA y el sistema francés, con una cuota fija o, sin ninguna, con el capital en partes iguales;
    - deudas y préstamos son la misma entidad, con sentido "debo" o "me deben";
    - registrarla no mueve plata;
    - la primera cuota vence un mes después del inicio.
  - **Pagos de deuda:** monto libre que cubre las cuotas en orden; el movimiento va sin categoría, como el pago de la tarjeta; el saldo pendiente incluye el interés de las cuotas que quedan.
- **Sprint 11:** suma US-047 (patrimonio neto) y US-048 (flujo de fondos) y queda en 14 SP. Los presupuestos (US-045 y US-046) pasan al Sprint 12.
- **PF-100:** nueva tarea para la segunda tanda de Dependabot (#119 a #128), primera del Sprint 11.

## Release
- Sin release: **v0.3.0** al cierre del Sprint 11.
