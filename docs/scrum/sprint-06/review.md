# Sprint 6: Review

- **Fecha:** 2026-10-25
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Sprint Goal:** Ver todo en ARS y en USD con cotizaciones del dólar automáticas o cargadas a mano. → **Cumplido ✅**
- **Nota:** se completó antes de su inicio previsto (2026-10-26). Por la regla de cadencia, se cierra y el Sprint 7 toma sus fechas.

## Historias
| Key Jira | Historia | SP | Estado | PRs | Aceptada por el PO |
|---|---|---|---|---|---|
| PF-38 | Cotizaciones del dólar: modelo y carga manual | 3 | Done | #63 | ✅ |
| PF-40 | Consultar cotizaciones | 2 | Done | #64 | ✅ |
| PF-39 | Cotizaciones automáticas desde dolarapi | 5 | Done | #65 | ✅ |
| PF-41 | Conversión ARS <-> USD | 3 | Done | #66 | ✅ |
| PF-42 | Saldos consolidados en ARS y USD | 2 | Done | #67 | ✅ |

- **Comprometido:** 15 SP · **Completado:** 15 SP

## Demo
- Cotizaciones: `POST /fx/rates` (manual, propia de cada usuario), `GET /fx/rates/latest` y `GET /fx/rates?type=&from=&to=`. Historial completo, nunca se pisa.
- Automáticas: el worker trae oficial, blue, MEP, CCL y cripto de dolarapi cada 30 minutos en días hábiles y una vez por día los fines de semana; reintenta 3 veces y, si falla, conserva el último valor. Verificado una vez contra la API real.
- Conversión: ARS → USD con la venta y USD → ARS con la compra, con la última cotización no posterior a la fecha.
- Resumen: `GET /accounts/summary` con cada cuenta y los totales en ARS y USD, con la cotización preferida o la pedida.

## Cambios al Product Backlog
- **Decisiones del PO aplicadas:** las cotizaciones manuales son de cada usuario y las de la API son de todos; los módulos se comunican por contratos en `app.shared` que conecta `main.py` (acción A4 del Sprint 5).
- **Criterio corregido:** PF-39 pedía tests con respx, que solo soporta httpx; se usa `httpx2.MockTransport`, como ya decía el backlog.
- **Sprint 7:** se mantiene en 16 SP (decisión del PO).

## Release
- [x] Release `v0.1.0`: PR develop → main, tag `v0.1.0` e imagen en GHCR. Entrada en el [CHANGELOG](../../../CHANGELOG.md).
- Antes del primer build de la imagen se verificó que las 78 dependencias tienen wheel para Linux y Python 3.14.
