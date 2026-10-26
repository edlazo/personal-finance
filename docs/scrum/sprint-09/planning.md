# Sprint 9: Planning

- **Fecha:** 2026-10-26
- **Fechas del sprint:** 2026-10-26 → 2026-11-06 (toma las fechas que tenía el Sprint 8)
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Capacidad:** unas 17 h netas · velocity de referencia: 15,7 SP (promedio de los Sprints 6 a 8)

## Sprint Goal
> Valuar la cartera de IOL automáticamente y empezar a seguir las tarjetas de crédito.

## Sprint Backlog (en orden de trabajo)
| # | Key Jira | ID | Ítem | SP | Notas |
|---|---|---|---|---|---|
| 0 | — | — | P&L realizado con dos decimales | — | Acción A2 de la Retro del Sprint 8 |
| 1 | PF-51 | US-033 | Portafolio y precios desde IOL | 5 | Usa las credenciales de PF-49; contador de llamadas con corte al 80 % |
| 2 | PF-52 | US-034 | Precios de respaldo desde data912 | 3 | Proveedores por prioridad: IOL > data912 > manual |
| 3 | PF-54 | US-037 | Alta de tarjeta de crédito | 2 | Módulo nuevo: planear 2 PRs desde el arranque |
| 4 | PF-55 | US-038 | Compras en cuotas | 5 | Depende de PF-54 |

**Total comprometido:** 15 SP

## Decisiones
- US-037 y US-038 entran desde el Sprint 10 (decisión del PO).
- Al cierre de este sprint sale **v0.2.0** (inversiones e integraciones de mercado).

## Riesgos
- **IOL:** el portafolio de la cuenta del PO estaba vacío en el spike; el formato de una posición real se confirma al implementar PF-51. Cada prueba contra IOL consume del cupo de 25.000 llamadas.
- **data912:** API pública sin documentación formal; se revisa al arrancar PF-52.
- **Tarjetas:** "la tarjeta es un pasivo en el patrimonio" depende del patrimonio neto (Sprint 12); en este sprint queda modelado el saldo adeudado.
- El Postgres local se cae con cada sesión y Docker sigue sin arrancar.
