# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones [SemVer](https://semver.org/lang/es/) con tags `vX.Y.Z` sobre `main`.

## [0.2.0] - 2026-10-27

Inversiones y tarjetas: la cartera se valúa sola con precios de mercado y se empiezan a seguir las compras con tarjeta.

### Agregado
- **Dólares:** compra y venta de USD entre cuentas, con comisión.
- **Inversiones:** catálogo propio de instrumentos (acciones, CEDEARs, bonos, ETFs, ONs y cripto); compras y ventas que mueven el saldo de la cuenta; posiciones por cuenta con costo promedio, P&L realizado y no realizado, valuadas en ARS y USD.
- **Precios:** carga manual; cripto desde CoinGecko cada hora; BYMA y EE.UU. desde data912 en días hábiles cada 30 minutos. El automático gana al manual.
- **Rentas:** dividendos y cupones como ingreso en la categoría Rentas y amortizaciones como rescate parcial; suman al P&L realizado.
- **IOL:** credenciales cifradas; una comitente vinculada toma sus tenencias y precios del portafolio de IOL cada 30 minutos en horario de mercado, con un tope propio de 20.000 llamadas por mes (el 80 % del cupo).
- **Tarjetas de crédito:** alta con red, día de cierre y de vencimiento, límite opcional y saldo en dólares si es bimonetaria; compras en una o más cuotas asignadas a cada resumen, y cuotas pendientes por vencimiento.

### Cambiado
- Ningún gasto, transferencia ni compra deja una cuenta con saldo negativo (salvo las comitentes).

### Corregido
- El worker registra todas las tablas antes de guardar cotizaciones.
- Los montos de las posiciones salen siempre con dos decimales.

## [0.1.0] - 2026-10-25

Primera versión (MVP): registrar el día a día y ver el total en ARS y USD.

### Agregado
- **Base técnica:** API FastAPI hexagonal por módulos (identity, ledger, fx), PostgreSQL con migraciones Alembic, worker con APScheduler, logging estructurado, health check con la base, CI de calidad y publicación de la imagen en GHCR.
- **Usuarios:** registro, login con JWT (refresh en cookie httpOnly con rotación), logout, perfil y cotización preferida; cada usuario ve solo sus datos.
- **Cuentas:** cuentas en ARS y USD (caja de ahorro, efectivo, billetera, comitente, wallet cripto) con saldo derivado de los movimientos, también a una fecha; edición y archivado.
- **Categorías:** 13 por defecto, propias y subcategorías de un nivel.
- **Movimientos:** ingresos y gastos; listado con filtros, paginación y orden por fecha; edición y borrado; transferencias entre cuentas de la misma moneda.
- **Cotizaciones:** MEP, oficial, blue, CCL y cripto desde dolarapi cada 30 minutos en horario hábil, carga manual propia, última de cada tipo e historial.
- **Conversión:** ARS ↔ USD con la cotización elegida y resumen de todas las cuentas en ARS y USD.
- **Frontend:** dashboard en React con datos de ejemplo, login y registro reales, header y perfil del usuario.

[0.2.0]: https://github.com/edlazo/personal-finance/releases/tag/v0.2.0
[0.1.0]: https://github.com/edlazo/personal-finance/releases/tag/v0.1.0
