# Product Backlog

> Fuente de verdad: Jira (proyecto `PF`). Este documento es el snapshot inicial generado en el Sprint 0.
> Los IDs `US-xxx` se mantienen en Jira en el campo *Labels* (`id-US-xxx`) para trazabilidad.

**Estimación:** story points Fibonacci. **Prioridad:** Highest > High > Medium > Low.

**Total comprometido en roadmap v1.0:** 162 SP en 12 sprints.

## Resumen por épica

| Épica | Descripción | Historias | SP |
|---|---|---|---|
| **PF-E0** Setup & DevOps | Repositorio, CI/CD, Docker, Alembic, esqueleto hexagonal y observabilidad base. | 8 | 18 |
| **PF-E1** Identity | Registro, login JWT, refresh, perfil y preferencias. Aislamiento multiusuario. | 5 | 12 |
| **PF-E2** Cuentas | Cuentas en ARS/USD (caja de ahorro, efectivo, billetera, comitente, wallet cripto) con saldo derivado. | 3 | 9 |
| **PF-E3** Movimientos | Categorías, ingresos, gastos y transferencias (incluye compra/venta de USD). | 7 | 19 |
| **PF-E4** Cotizaciones | Cotizaciones MEP/oficial/blue/CCL/cripto automáticas y manuales; conversión ARS<->USD. | 5 | 15 |
| **PF-E5** Inversiones | Instrumentos (acciones, CEDEARs, bonos, ETFs, ONs, cripto), operaciones, posiciones y P&L. | 5 | 19 |
| **PF-E6** Integraciones de mercado | Precios desde IOL, data912 y CoinGecko; importación de Balanz. | 6 | 20 |
| **PF-E7** Tarjetas de crédito | Tarjetas, ciclos de resumen, compras en cuotas y pagos. | 4 | 13 |
| **PF-E8** Deudas | Préstamos y deudas con cronograma de pagos. | 2 | 8 |
| **PF-E9** Planificación | Movimientos recurrentes y presupuestos mensuales por categoría. | 4 | 12 |
| **PF-E10** Reportes | Patrimonio neto, flujo de fondos, gastos por categoría y evolución histórica. | 5 | 17 |
| **PF-E11** Bienes (futuro) | Inmuebles y vehículos con valuación manual incluidos en el patrimonio. | 2 | 8 |

## PF-E0 - Setup & DevOps

_Repositorio, CI/CD, Docker, Alembic, esqueleto hexagonal y observabilidad base._

### US-001 - Esqueleto hexagonal, configuración y healthcheck
`Task` | **3 SP** | Prioridad **Highest** | Sprint 1 | label `devops`

**Como** desarrollador, **quiero** una estructura de proyecto hexagonal por módulos con configuración tipada, **para** construir funcionalidades sobre una base consistente.

**Criterios de aceptación**
- [ ] Existe `src/app` con `shared/` y `modules/` siguiendo domain/application/infrastructure/api
- [ ] `Settings` (pydantic-settings) lee variables desde entorno y `.env`; existe `.env.example`
- [ ] `create_app()` usa `lifespan` (no `on_event`)
- [ ] `GET /health` responde 200 con estado de la app y de la base de datos
- [ ] `pyproject.toml` configura ruff, mypy strict, pytest (`error::DeprecationWarning`), coverage e import-linter

### US-002 - Docker y Docker Compose para desarrollo
`Task` | **2 SP** | Prioridad **Highest** | Sprint 1 | label `devops`

**Como** desarrollador, **quiero** levantar Postgres, API y worker con un comando, **para** tener el mismo entorno en local, CI y producción.

**Criterios de aceptación**
- [ ] `Dockerfile` multi-stage basado en `python:3.14.8-slim`, usuario no root, corre `fastapi run`
- [ ] `docker-compose.yml` con servicios `db` (postgres:17-alpine con volumen), `api` y `worker`
- [ ] Dado `docker compose up`, cuando termina el arranque, entonces `/health` responde 200

### US-003 - Alembic async y sesión de base de datos
`Task` | **2 SP** | Prioridad **Highest** | Sprint 1 | label `devops`

**Como** desarrollador, **quiero** migraciones versionadas con Alembic en modo async, **para** evolucionar el esquema de forma segura.

**Criterios de aceptación**
- [ ] Engine y session async de SQLAlchemy 2 en `shared/infrastructure`
- [ ] Alembic configurado con `DeclarativeBase` y convención de nombres de constraints
- [ ] `alembic upgrade head` y `alembic check` funcionan en local y CI
- [ ] UnitOfWork base implementado y testeado

### US-004 - Pipelines de CI: lint, tipos, tests, commits y lint-fix
`Task` | **3 SP** | Prioridad **Highest** | Sprint 1 | label `devops`

**Como** Product Owner, **quiero** que cada PR se verifique automáticamente, **para** garantizar calidad antes de integrar a develop/main.

**Criterios de aceptación**
- [ ] `ci.yml`: ruff check, ruff format --check, mypy, lint-imports, pytest con cobertura >= 85% y Postgres como service, alembic check
- [ ] `commits.yml`: válida titulo de PR (Conventional Commits + `[PF-n]`) y cada commit con commitlint
- [ ] `lint-fix.yml`: aplica `ruff --fix` y `ruff format` y commitea `style: auto-fix lint` en PRs del mismo repo
- [ ] `.pre-commit-config.yaml` con ruff y validación commit-msg
- [ ] Branch protection de `main` y `develop` exige los checks

### US-005 - Publicación de imagen en GHCR y Dependabot
`Task` | **1 SP** | Prioridad **High** | Sprint 1 | label `devops`

**Como** Product Owner, **quiero** que cada merge a main publique una imagen Docker versionada, **para** tener artefactos listos para desplegar.

**Criterios de aceptación**
- [ ] `docker.yml` construye y publica en `ghcr.io` con tags `latest`, SHA y `vX.Y.Z` en tags
- [ ] `dependabot.yml` semanal para pip y github-actions

### US-053 - Logging estructurado y manejo de errores RFC 9457
`Task` | **2 SP** | Prioridad **High** | Sprint 1 | label `devops`

**Como** desarrollador, **quiero** logs JSON con request_id y errores en formato problem+json, **para** diagnosticar problemas y dar respuestas de error consistentes.

**Criterios de aceptación**
- [ ] structlog configurado; cada request loguea método, path, status, duración y `request_id`
- [ ] Header `X-Request-ID` propagado en la respuesta
- [ ] Errores de dominio y validación se devuelven como `application/problem+json`

### US-052 - Hardening de seguridad
`Task` | **3 SP** | Prioridad **High** | Sprint 12 | label `devops`

**Como** Product Owner, **quiero** que la API este protegida ante abusos, **para** salir a producción con confianza.

**Criterios de aceptación**
- [ ] Rate limiting en login/registro
- [ ] Headers de seguridad y CORS configurables
- [ ] Revisión de dependencias (pip-audit en CI) y de OWASP API Top 10

### US-054 - Preparación release v1.0.0
`Task` | **2 SP** | Prioridad **High** | Sprint 12 | label `devops`

**Como** Product Owner, **quiero** documentación de despliegue y release, **para** poder poner el sistema en producción.

**Criterios de aceptación**
- [ ] README con despliegue usando la imagen de GHCR y variables de entorno
- [ ] CHANGELOG generado desde Conventional Commits
- [ ] Tag v1.0.0 en main

## PF-E1 - Identity

_Registro, login JWT, refresh, perfil y preferencias. Aislamiento multiusuario._

### US-006 - Registro de usuario
`Story` | **3 SP** | Prioridad **Highest** | Sprint 2 | label `identity`

**Como** usuario nuevo, **quiero** registrarme con email y contraseña, **para** tener mi propio espacio de finanzas.

**Criterios de aceptación**
- [ ] Dado un email no registrado y contraseña válida (>= 10 caracteres), cuando hago `POST /auth/register`, entonces se crea el usuario y responde 201 sin exponer el hash
- [ ] Dado un email ya registrado, entonces responde 409
- [ ] La contraseña se guarda con Argon2id (pwdlib)
- [ ] Al registrarse se crean las categorías por defecto (ver US-014) y preferencia de cotización MEP

### US-007 - Login con JWT
`Story` | **3 SP** | Prioridad **Highest** | Sprint 2 | label `identity`

**Como** usuario registrado, **quiero** iniciar sesión y obtener tokens, **para** acceder a mis datos de forma segura.

**Criterios de aceptación**
- [ ] Dado credenciales válidas, `POST /auth/login` devuelve `access_token` (15 min) y `refresh_token` (7 días)
- [ ] Dado credenciales inválidas, responde 401 sin indicar cual dato fallo
- [ ] Los endpoints protegidos rechazan tokens vencidos o inválidos con 401

### US-008 - Refresh y logout
`Story` | **2 SP** | Prioridad **High** | Sprint 2 | label `identity`

**Como** usuario autenticado, **quiero** renovar mi sesión y cerrarla, **para** no tener que loguearme seguido y poder revocar acceso.

**Criterios de aceptación**
- [ ] `POST /auth/refresh` emite nuevos tokens y rota el refresh (el anterior queda invalido)
- [ ] `POST /auth/logout` revoca el refresh token actual
- [ ] Reusar un refresh token revocado responde 401

### US-009 - Perfil y preferencias
`Story` | **2 SP** | Prioridad **Medium** | Sprint 2 | label `identity`

**Como** usuario, **quiero** ver mi perfil y elegir mi cotización por defecto, **para** ver mis reportes con el dólar que uso.

**Criterios de aceptación**
- [ ] `GET /me` devuelve email, nombre y preferencias
- [ ] `PATCH /me/preferences` permite elegir `default_rate_type` entre MEP, OFICIAL, BLUE, CCL, Cripto
- [ ] Valor por defecto: MEP

### US-010 - Aislamiento de datos multiusuario
`Task` | **2 SP** | Prioridad **Highest** | Sprint 2 | label `identity`

**Como** usuario, **quiero** que nadie más pueda ver ni modificar mis datos, **para** proteger mi información financiera.

**Criterios de aceptación**
- [ ] Dependencia `current_user` usada por todos los routers protegidos
- [ ] Los repositorios filtran siempre por `user_id`
- [ ] Test e2e: un usuario B recibe 404 al acceder a recursos del usuario A

## PF-E2 - Cuentas

_Cuentas en ARS/USD (caja de ahorro, efectivo, billetera, comitente, wallet cripto) con saldo derivado._

### US-011 - Crear cuenta
`Story` | **3 SP** | Prioridad **Highest** | Sprint 3 | label `accounts`

**Como** usuario, **quiero** crear cuentas en ARS o USD, **para** registrar donde tengo mi dinero.

**Criterios de aceptación**
- [ ] `POST /accounts` con nombre, tipo (SAVINGS, CASH, WALLET, BROKER, CRYPTO_WALLET), moneda (ARS/USD) y saldo inicial
- [ ] El saldo inicial usa Decimal con 2 decimales; montos negativos solo permitidos en tipos que lo admitan
- [ ] Nombre único por usuario entre cuentas activas (409 si se repite)

### US-012 - Listar, editar y archivar cuentas
`Story` | **3 SP** | Prioridad **High** | Sprint 3 | label `accounts`

**Como** usuario, **quiero** administrar mis cuentas, **para** mantener ordenada mi información.

**Criterios de aceptación**
- [ ] `GET /accounts` lista activas (filtro `include_archived`)
- [ ] `PATCH /accounts/{id}` edita nombre; la moneda no se puede cambiar si tiene movimientos
- [ ] `DELETE /accounts/{id}` archiva (soft delete); no se pueden cargar movimientos en cuentas archivadas

### US-013 - Saldo de cuenta derivado
`Story` | **3 SP** | Prioridad **Highest** | Sprint 3 | label `accounts`

**Como** usuario, **quiero** ver el saldo actual de cada cuenta, **para** saber cuánto dinero tengo.

**Criterios de aceptación**
- [ ] El saldo = saldo inicial + suma de movimientos; no se guarda un saldo mutable
- [ ] `GET /accounts` y `GET /accounts/{id}` incluyen `balance` en la moneda de la cuenta
- [ ] Parametro `as_of` permite consultar el saldo a una fecha

## PF-E3 - Movimientos

_Categorías, ingresos, gastos y transferencias (incluye compra/venta de USD)._

### US-014 - Categorías por defecto
`Story` | **2 SP** | Prioridad **High** | Sprint 3 | label `ledger`

**Como** usuario nuevo, **quiero** tener categorías de ingresos y gastos precargadas, **para** empezar a registrar sin configurar nada.

**Criterios de aceptación**
- [ ] Al registrarse se crean categorías de gasto (Supermercado, Servicios, Alquiler, Transporte, Salud, Ocio, Educación, Impuestos, Otros) e ingreso (Sueldo, Freelance, Rentas, Otros)
- [ ] Las categorías por defecto se pueden renombrar o archivar

### US-015 - Gestionar categorías y subcategorias
`Story` | **3 SP** | Prioridad **Medium** | Sprint 3 | label `ledger`

**Como** usuario, **quiero** crear y organizar mis categorías, **para** clasificar mis movimientos a mi manera.

**Criterios de aceptación**
- [ ] CRUD en `/categories` con tipo INCOME/EXPENSE y `parent_id` opcional (un nivel de subcategoria)
- [ ] No se puede archivar una categoría con presupuestos activos sin confirmación
- [ ] Nombre único por usuario, tipo y padre

### US-016 - Registrar ingreso o gasto
`Story` | **3 SP** | Prioridad **Highest** | Sprint 4 | label `ledger`

**Como** usuario, **quiero** registrar ingresos y gastos de mi día a día, **para** saber en que gasto y cuánto gano.

**Criterios de aceptación**
- [ ] `POST /transactions` con cuenta, tipo (INCOME/EXPENSE), monto > 0, fecha, categoría y descripción opcional
- [ ] La categoría debe coincidir con el tipo del movimiento (422 si no)
- [ ] El saldo de la cuenta se actualiza en consecuencia

### US-017 - Listar movimientos con filtros
`Story` | **3 SP** | Prioridad **High** | Sprint 4 | label `ledger`

**Como** usuario, **quiero** buscar mis movimientos, **para** revisar en que gaste.

**Criterios de aceptación**
- [ ] `GET /transactions` con filtros: rango de fechas, cuenta, categoría, tipo, texto, monto min/max
- [ ] Paginación por cursor o limit/offset con total
- [ ] Orden por fecha descendente por defecto

### US-018 - Editar y eliminar movimiento
`Story` | **2 SP** | Prioridad **High** | Sprint 4 | label `ledger`

**Como** usuario, **quiero** corregir o borrar un movimiento, **para** mantener mis datos correctos.

**Criterios de aceptación**
- [ ] `PATCH /transactions/{id}` y `DELETE /transactions/{id}`
- [ ] Editar o borrar una pata de una transferencia afecta a ambas patas

### US-019 - Transferencia entre cuentas de la misma moneda
`Story` | **3 SP** | Prioridad **High** | Sprint 4 | label `ledger`

**Como** usuario, **quiero** mover dinero entre mis cuentas, **para** reflejarlo sin que cuente como gasto ni ingreso.

**Criterios de aceptación**
- [ ] `POST /transfers` con cuenta origen, destino, monto y fecha genera 2 movimientos ligados por `transfer_group_id`
- [ ] Las transferencias no aparecen en reportes de ingresos/gastos
- [ ] Origen y destino deben ser distintos y del mismo usuario

### US-020 - Compra y venta de dólares
`Story` | **3 SP** | Prioridad **High** | Sprint 4 | label `ledger`

**Como** usuario, **quiero** registrar compra o venta de USD entre una cuenta ARS y una USD, **para** seguir mis dolarizaciones al tipo de cambio real.

**Criterios de aceptación**
- [ ] Transferencia entre monedas distintas requiere monto origen y monto destino (o tipo de cambio aplicado)
- [ ] Se guarda el tipo de cambio efectivo de la operación
- [ ] Comisión opcional registrada como gasto en categoría 'Comisiones'

## PF-E4 - Cotizaciones

_Cotizaciones MEP/oficial/blue/CCL/cripto automáticas y manuales; conversión ARS<->USD._

### US-021 - Cotizaciones del dólar: modelo y carga manual
`Story` | **3 SP** | Prioridad **Highest** | Sprint 5 | label `fx`

**Como** usuario, **quiero** cargar una cotización manualmente, **para** tener valores aunque falle la fuente automática.

**Criterios de aceptación**
- [ ] Cotización con tipo (MEP, OFICIAL, BLUE, CCL, Cripto), compra, venta, fecha-hora y fuente (API/MANUAL)
- [ ] `POST /fx/rates` para carga manual; `NUMERIC(28,10)`
- [ ] Historial completo, no se sobreescriben valores

### US-022 - Cotizaciones automáticas desde dolarapi
`Story` | **5 SP** | Prioridad **Highest** | Sprint 5 | label `fx`

**Como** usuario, **quiero** que las cotizaciones se actualicen solas, **para** no cargarlas a mano.

**Criterios de aceptación**
- [ ] Puerto `ExchangeRateProvider` y adaptador `DolarApiProvider` (oficial, blue, bolsa=MEP, contadoconliqui, cripto)
- [ ] Job del worker cada 30 min en días hábiles 10-18 h (configurable) y 1 vez al día el resto
- [ ] Reintentos con tenacity; si falla se loguea y se conserva el último valor
- [ ] Tests del adaptador con respx

### US-023 - Consultar cotizaciones
`Story` | **2 SP** | Prioridad **High** | Sprint 5 | label `fx`

**Como** usuario, **quiero** consultar cotizaciones actuales e historicas, **para** saber a cuánto esta el dólar.

**Criterios de aceptación**
- [ ] `GET /fx/rates/latest` devuelve la última de cada tipo
- [ ] `GET /fx/rates?type=&from=&to=` devuelve el historial

### US-024 - Conversión ARS <-> USD
`Story` | **3 SP** | Prioridad **Highest** | Sprint 5 | label `fx`

**Como** usuario, **quiero** ver montos convertidos con el dólar que elija, **para** comparar todo en una misma moneda.

**Criterios de aceptación**
- [ ] Servicio de dominio `CurrencyConverter` usa la cotización del tipo pedido más cercana a la fecha (no posterior)
- [ ] ARS->USD usa precio de venta; USD->ARS usa precio de compra (documentado)
- [ ] Sin cotización disponible responde error de dominio claro

### US-025 - Saldos consolidados en ARS y USD
`Story` | **2 SP** | Prioridad **Highest** | Sprint 5 | label `fx`

**Como** usuario, **quiero** ver el total de mis cuentas en ARS y en USD, **para** saber cuánto tengo en total.

**Criterios de aceptación**
- [ ] `GET /accounts/summary?rate_type=` devuelve cada cuenta con saldo en ARS y USD y totales
- [ ] Sin `rate_type` usa la preferencia del usuario

## PF-E5 - Inversiones

_Instrumentos (acciones, CEDEARs, bonos, ETFs, ONs, cripto), operaciones, posiciones y P&L._

### US-026 - Catalogo de instrumentos
`Story` | **3 SP** | Prioridad **High** | Sprint 6 | label `investments`

**Como** usuario, **quiero** registrar instrumentos financieros, **para** asociar mis operaciones a ellos.

**Criterios de aceptación**
- [ ] Instrumento: ticker, nombre, tipo (STOCK, CEDEAR, BOND, ETF, ON, CRYPTO), mercado (BYMA, NYSE, NASDAQ, CRYPTO), moneda de cotización
- [ ] Bonos y ONs indican que cotizan cada 100 VN
- [ ] Ticker único por mercado

### US-027 - Registrar compra y venta de instrumentos
`Story` | **5 SP** | Prioridad **High** | Sprint 6 | label `investments`

**Como** inversor, **quiero** registrar mis operaciones, **para** seguir mi cartera.

**Criterios de aceptación**
- [ ] `POST /trades` con cuenta comitente/wallet, instrumento, BUY/SELL, cantidad, precio, comisión, fecha
- [ ] Una compra debita la cuenta (precio x cantidad + comisión); una venta acredita
- [ ] No se puede vender más cantidad que la tenencia

### US-028 - Posiciones y resultados
`Story` | **5 SP** | Prioridad **High** | Sprint 6 | label `investments`

**Como** inversor, **quiero** ver mis tenencias con su costo y ganancia, **para** evaluar mis inversiones.

**Criterios de aceptación**
- [ ] `GET /positions` con cantidad, costo promedio ponderado, precio actual, valuación, P&L no realizado (monto y %)
- [ ] P&L realizado calculado al vender
- [ ] Valuación en moneda del instrumento y en ARS/USD

### US-029 - Carga manual de precios
`Story` | **3 SP** | Prioridad **High** | Sprint 7 | label `investments`

**Como** inversor, **quiero** cargar precios a mano, **para** valuar instrumentos sin fuente automática.

**Criterios de aceptación**
- [ ] `POST /prices` con instrumento, precio, fecha; fuente MANUAL
- [ ] La valuación usa el precio más reciente disponible

### US-030 - Dividendos, rentas y amortizaciones
`Story` | **3 SP** | Prioridad **Medium** | Sprint 7 | label `investments`

**Como** inversor, **quiero** registrar dividendos, cupones y amortizaciones, **para** medir el rendimiento total.

**Criterios de aceptación**
- [ ] Eventos DIVIDEND, COUPON, AMORTIZATION acreditan la cuenta y se asocian al instrumento
- [ ] Las amortizaciones reducen el VN residual del bono/ON

## PF-E6 - Integraciones de mercado

_Precios desde IOL, data912 y CoinGecko; importación de Balanz._

### US-031 - Investigar API de IOL y exportación de Balanz
`Spike` | **2 SP** | Prioridad **High** | Sprint 7 | label `integrations`

**Como** equipo, **quiero** conocer endpoints, límites y formatos, **para** estimar con precisión las integraciones.

**Criterios de aceptación**
- [ ] Documento con endpoints de IOL (auth, cotizaciones, portafolio), límites y requisitos de habilitación
- [ ] Ejemplo anonimizado del archivo exportado de Balanz y mapeo de columnas
- [ ] Decisión sobre openpyxl vs alternativa para leer Excel

### US-032 - Credenciales de broker cifradas
`Story` | **3 SP** | Prioridad **High** | Sprint 7 | label `integrations`

**Como** usuario, **quiero** guardar mis credenciales de IOL de forma segura, **para** sincronizar precios sin exponer mis datos.

**Criterios de aceptación**
- [ ] Credenciales cifradas con Fernet; clave en variable de entorno, nunca en la base
- [ ] Las credenciales nunca se devuelven en ninguna respuesta
- [ ] Endpoint para borrar credenciales

### US-035 - Precios de cripto desde CoinGecko
`Story` | **2 SP** | Prioridad **Medium** | Sprint 7 | label `integrations`

**Como** inversor, **quiero** que mis cripto se valuen solas, **para** ver su valor actualizado.

**Criterios de aceptación**
- [ ] Adaptador `CoinGeckoProvider` (puerto `PriceProvider`) para instrumentos CRYPTO
- [ ] Job periodico; tests con respx

### US-033 - Precios desde IOL
`Story` | **5 SP** | Prioridad **High** | Sprint 8 | label `integrations`

**Como** inversor, **quiero** obtener precios de acciones, CEDEARs, bonos y ONs desde IOL, **para** valuar mi cartera automáticamente.

**Criterios de aceptación**
- [ ] Adaptador `IolPriceProvider` con OAuth2 password grant y refresh de token
- [ ] Job que actualiza precios de instrumentos en cartera
- [ ] Errores de autenticación se notifican sin romper el job

### US-034 - Precios de respaldo desde data912
`Story` | **3 SP** | Prioridad **Medium** | Sprint 8 | label `integrations`

**Como** inversor, **quiero** tener precios aunque no use IOL, **para** valuar instrumentos del mercado local.

**Criterios de aceptación**
- [ ] Adaptador `Data912Provider` para CEDEARs, bonos y ONs
- [ ] Estrategia de proveedores configurable por prioridad (IOL > data912 > manual)

### US-036 - Importar movimientos de Balanz
`Story` | **5 SP** | Prioridad **Medium** | Sprint 8 | label `integrations`

**Como** inversor de Balanz, **quiero** subir el archivo exportado de Balanz, **para** no cargar mis operaciones a mano.

**Criterios de aceptación**
- [ ] `POST /imports/balanz` acepta CSV/XLSX (max 5 MB)
- [ ] Previsualización con filas válidas e inválidas antes de confirmar
- [ ] Importación idempotente: reimportar el mismo archivo no duplica operaciones

## PF-E7 - Tarjetas de crédito

_Tarjetas, ciclos de resumen, compras en cuotas y pagos._

### US-037 - Alta de tarjeta de crédito
`Story` | **2 SP** | Prioridad **High** | Sprint 9 | label `credit-cards`

**Como** usuario, **quiero** registrar mis tarjetas, **para** seguir sus consumos y vencimientos.

**Criterios de aceptación**
- [ ] Tarjeta con nombre, red, moneda(s), día de cierre y día de vencimiento, límite opcional
- [ ] La tarjeta es un pasivo en el patrimonio

### US-038 - Compras en cuotas
`Story` | **5 SP** | Prioridad **High** | Sprint 9 | label `credit-cards`

**Como** usuario, **quiero** registrar compras en cuotas, **para** saber cuánto voy a pagar en los próximos meses.

**Criterios de aceptación**
- [ ] Compra con monto total, cantidad de cuotas y fecha; genera N cuotas asignadas a resumenes futuros según fecha de cierre
- [ ] Compras en 1 cuota y en USD soportadas
- [ ] `GET /credit-cards/{id}/installments` muestra cuotas pendientes

### US-039 - Resumen del período
`Story` | **3 SP** | Prioridad **High** | Sprint 9 | label `credit-cards`

**Como** usuario, **quiero** ver el resumen de cada período, **para** saber cuánto debo pagar y cuando.

**Criterios de aceptación**
- [ ] `GET /credit-cards/{id}/statements/{period}` con consumos, cuotas, total ARS y USD, cierre y vencimiento

### US-040 - Pago de resumen
`Story` | **3 SP** | Prioridad **High** | Sprint 9 | label `credit-cards`

**Como** usuario, **quiero** registrar el pago total o parcial del resumen, **para** reflejar la deuda real de la tarjeta.

**Criterios de aceptación**
- [ ] El pago es una transferencia desde una cuenta a la tarjeta
- [ ] Pago parcial deja saldo pendiente en el resumen

## PF-E8 - Deudas

_Préstamos y deudas con cronograma de pagos._

### US-041 - Registrar deuda o préstamo
`Story` | **5 SP** | Prioridad **Medium** | Sprint 10 | label `debts`

**Como** usuario, **quiero** registrar deudas y préstamos, **para** saber cuánto debo.

**Criterios de aceptación**
- [ ] Deuda con acreedor, moneda, capital, tasa opcional, cantidad de cuotas y fecha de inicio
- [ ] Genera cronograma de cuotas (sistema francés o cuota fija manual)
- [ ] Préstamos otorgados a terceros se registran como activo

### US-042 - Pagos de deuda
`Story` | **3 SP** | Prioridad **Medium** | Sprint 10 | label `debts`

**Como** usuario, **quiero** registrar pagos de mis deudas, **para** ver el saldo pendiente.

**Criterios de aceptación**
- [ ] Pago debita una cuenta y marca cuotas como pagadas
- [ ] `GET /debts` muestra saldo pendiente y próxima cuota

## PF-E9 - Planificación

_Movimientos recurrentes y presupuestos mensuales por categoría._

### US-043 - Reglas de movimientos recurrentes
`Story` | **3 SP** | Prioridad **Medium** | Sprint 10 | label `planning`

**Como** usuario, **quiero** definir ingresos y gastos recurrentes, **para** no cargar todos los meses lo mismo.

**Criterios de aceptación**
- [ ] CRUD `/recurring` con plantilla de movimiento y frecuencia (semanal, mensual, anual, día del mes)
- [ ] Fecha de inicio y fin opcional; pausar/reanudar

### US-044 - Generación automática de recurrentes
`Story` | **3 SP** | Prioridad **Medium** | Sprint 10 | label `planning`

**Como** usuario, **quiero** que los recurrentes se registren solos, **para** mantener mis datos al día.

**Criterios de aceptación**
- [ ] Job diario genera los movimientos vencidos de forma idempotente
- [ ] Opción de generar como 'pendiente de confirmar'

### US-045 - Presupuestos mensuales
`Story` | **3 SP** | Prioridad **Medium** | Sprint 11 | label `planning`

**Como** usuario, **quiero** definir un presupuesto mensual por categoría, **para** controlar mis gastos.

**Criterios de aceptación**
- [ ] `/budgets` con categoría, mes y monto en ARS o USD
- [ ] Copiar presupuestos del mes anterior

### US-046 - Estado del presupuesto y alertas
`Story` | **3 SP** | Prioridad **Medium** | Sprint 11 | label `planning`

**Como** usuario, **quiero** ver cuánto consumi de cada presupuesto, **para** no pasarme.

**Criterios de aceptación**
- [ ] `GET /budgets/status?month=` con presupuestado, consumido, restante y %
- [ ] Flags de alerta al superar 80% y 100%

## PF-E10 - Reportes

_Patrimonio neto, flujo de fondos, gastos por categoría y evolución histórica._

### US-047 - Patrimonio neto
`Story` | **5 SP** | Prioridad **High** | Sprint 11 | label `reports`

**Como** usuario, **quiero** ver mi patrimonio neto en ARS y USD, **para** saber cuánto tengo realmente.

**Criterios de aceptación**
- [ ] `GET /reports/net-worth?currency=&rate_type=&as_of=`
- [ ] Activos: cuentas, inversiones valuadas, préstamos otorgados; Pasivos: tarjetas, deudas
- [ ] Desglose por tipo de activo y por moneda

### US-048 - Flujo de fondos mensual
`Story` | **3 SP** | Prioridad **High** | Sprint 11 | label `reports`

**Como** usuario, **quiero** ver ingresos vs gastos por mes, **para** saber si ahorro o gasto de más.

**Criterios de aceptación**
- [ ] `GET /reports/cash-flow?from=&to=&currency=` con ingresos, gastos, ahorro y tasa de ahorro por mes
- [ ] Excluye transferencias

### US-049 - Gastos por categoría
`Story` | **3 SP** | Prioridad **Medium** | Sprint 12 | label `reports`

**Como** usuario, **quiero** ver en que categorías gasto más, **para** identificar donde recortar.

**Criterios de aceptación**
- [ ] `GET /reports/by-category?from=&to=&currency=` con monto y % por categoría y subcategoria

### US-050 - Snapshot diario de patrimonio
`Story` | **3 SP** | Prioridad **Medium** | Sprint 12 | label `reports`

**Como** usuario, **quiero** que se guarde mi patrimonio cada día, **para** ver su evolución histórica.

**Criterios de aceptación**
- [ ] Job diario guarda patrimonio en ARS y USD por tipo de cotización
- [ ] Idempotente por usuario y fecha

### US-051 - Evolución histórica
`Story` | **3 SP** | Prioridad **Medium** | Sprint 12 | label `reports`

**Como** usuario, **quiero** ver la evolución de mi patrimonio, **para** ver si mis finanzas mejoran.

**Criterios de aceptación**
- [ ] `GET /reports/evolution?from=&to=&currency=&granularity=day|month`
- [ ] Usa snapshots; variación absoluta y %

## PF-E11 - Bienes (futuro)

_Inmuebles y vehículos con valuación manual incluidos en el patrimonio._

### US-055 - Registrar bienes
`Story` | **5 SP** | Prioridad **Low** | Futuro | label `assets`

**Como** usuario, **quiero** registrar inmuebles y vehículos, **para** incluirlos en mi patrimonio.

**Criterios de aceptación**
- [ ] Bien con tipo, descripción, moneda y valuación manual con historial

### US-056 - Bienes en el patrimonio neto
`Story` | **3 SP** | Prioridad **Low** | Futuro | label `assets`

**Como** usuario, **quiero** ver mis bienes dentro del patrimonio, **para** tener la foto completa.

**Criterios de aceptación**
- [ ] El reporte de patrimonio incluye bienes con su última valuación

