# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones [SemVer](https://semver.org/lang/es/) con tags `vX.Y.Z` sobre `main`.

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

[0.1.0]: https://github.com/edlazo/personal-finance/releases/tag/v0.1.0
