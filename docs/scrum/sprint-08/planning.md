# Sprint 8: Planning

- **Fecha:** 2026-10-25
- **Fechas del sprint:** 2026-10-26 → 2026-11-06 (toma las fechas que tenía el Sprint 7)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 15 SP (promedio de los Sprints 5 a 7)

## Sprint Goal
> Valuar la cartera con precios cargados a mano y de cripto automáticos, registrar rentas y preparar las integraciones con brokers.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 1 | PF-46 | US-029 | Carga manual de precios | 3 | Reemplaza al precio de la última operación en las posiciones |
| 2 | PF-50 | US-035 | Precios de cripto desde CoinGecko | 2 | Puerto `PriceProvider`; job del worker |
| 3 | PF-47 | US-030 | Dividendos, rentas y amortizaciones | 3 | Acreditan la cuenta por el contrato de `app.shared` |
| 4 | PF-86 | US-062 | Gastos y transferencias sin saldo negativo | 3 | Pendiente desde el Sprint 5 |
| 5 | PF-48 | US-031 | Spike: API de IOL y exportación de Balanz | 2 | Necesita material del PO (acción A4) |
| 6 | PF-49 | US-032 | Credenciales de broker cifradas | 3 | Fernet; clave en variable de entorno |

**Total comprometido:** 16 SP

## Decisiones
- Se suma PF-86 (decisión del PO). PF-87 sigue sin sprint.
- No se publica una v0.1.1: el fix del worker sale con la v0.2.0.

## Riesgos
- **PF-48:** sin el archivo de Balanz y los datos de IOL del PO, el spike no puede cerrar sus criterios.
- **PF-49:** suma la dependencia `cryptography`; la rotación de la clave queda fuera de alcance.
- **PF-47:** decidir con el PO si dividendos y cupones cuentan como ingreso en los reportes, y cómo se ligan al instrumento.
- **PF-86:** el saldo se evalúa hacia adelante en el tiempo e incluye transferencias y operaciones.
- **CoinGecko:** API pública con límites de uso; va detrás de un puerto, con reintentos.
