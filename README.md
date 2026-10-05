# Personal Finance API

Backend para gestionar finanzas personales: **activos, ingresos, gastos, inversiones, tarjetas y deudas**, con vista consolidada siempre disponible en **ARS y USD** (MEP, oficial, blue, CCL, cripto).

> Estado: **Sprint 1, base técnica.** Ver el [roadmap](docs/scrum/roadmap.md).

## Funcionalidades (v1.0)
- Multiusuario con autenticación JWT.
- Cuentas en ARS/USD: caja de ahorro, efectivo, billeteras virtuales, cuentas comitentes, wallets cripto.
- Ingresos, gastos y categorías; transferencias entre cuentas (incluye compra y venta de dólares).
- Cotizaciones automáticas (dolarapi) y manuales; conversión ARS↔USD con el tipo de dólar que elijas.
- Inversiones: acciones, CEDEARs, bonos, ETFs, ONs y cripto, con P&L; precios desde IOL, data912 y CoinGecko, e import de Balanz.
- Tarjetas de crédito con cuotas, deudas y préstamos.
- Movimientos recurrentes y presupuestos mensuales.
- Reportes: patrimonio neto, flujo de fondos, gastos por categoría y evolución histórica.

## Stack
Python 3.14.8 · FastAPI · PostgreSQL 17 · SQLAlchemy 2 (async) · Alembic · Docker · GitHub Actions · Jira (Scrum).
Detalle y justificación en [docs/stack.md](docs/stack.md).

## Entorno local
```powershell
# 1. Python 3.14.8 (instalador de python.org; winget puede instalar otro patch)
#    https://www.python.org/downloads/release/python-3148/
py -3.14 --version          # debe decir Python 3.14.8

# 2. Entorno virtual + dependencias
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pip check

# 3. Hooks de git
pre-commit install          # pre-commit, commit-msg y pre-push (con el venv activado)
```

### Levantar todo con Docker
```powershell
docker compose up -d --build --wait   # db, migraciones, api y worker
curl http://localhost:8000/health     # {"status":"ok","checks":{"database":"ok"}}
docker compose down                   # los datos quedan en el volumen pgdata (-v para borrarlos)
```

### Desarrollar la API con recarga automática
```powershell
Copy-Item .env.example .env
docker compose up -d --wait db
alembic upgrade head
fastapi dev src/app/main.py   # http://127.0.0.1:8000/health y /docs
python -m app.worker          # worker de jobs (con PYTHONPATH=src)
```

### Migraciones
```powershell
alembic revision --autogenerate -m "crear tabla x"   # se formatea con ruff automáticamente
alembic upgrade head
alembic check                                        # falla si los modelos no coinciden con las migraciones
```

### Chequeos de calidad
```powershell
ruff check . ; ruff format --check .
mypy
$env:PYTHONPATH = "src"; lint-imports
pytest -m "not integration"   # unitarios, sin Docker
pytest --cov                  # todos; los de integración levantan Postgres con testcontainers
```

## Forma de trabajo
- **Scrum**: sprints de 2 semanas gestionados en Jira (proyecto `PF`). Ver el [working agreement](docs/scrum/working-agreement.md).
- **Ramas**: `main` (producción) y `develop` (integración), más `feature/PF-<n>-<slug>`.
- **Commits**: Conventional Commits. Ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentación
| Documento | Contenido |
|---|---|
| [docs/stack.md](docs/stack.md) | Tecnologías, arquitectura, reglas de dinero, integraciones |
| [docs/scrum/working-agreement.md](docs/scrum/working-agreement.md) | Roles, ceremonias, DoR, DoD, estimación |
| [docs/scrum/product-backlog.md](docs/scrum/product-backlog.md) | Épicas e historias de usuario |
| [docs/scrum/roadmap.md](docs/scrum/roadmap.md) | Sprints y releases |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Flujo de git, commits y PRs |
