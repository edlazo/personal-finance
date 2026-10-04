# Sprint 0: Planning

- **Inicio:** 2026-10-02
- **Asistentes:** PO (Elias), SM/Dev (Claude)
- **Tipo:** sprint de definición (sin código de producto)

## Sprint Goal
> Dejar definidos el stack tecnológico, el marco Scrum y el Product Backlog, con el repositorio y Jira listos para arrancar el Sprint 1.

## Decisiones tomadas en el Planning
| Tema | Decisión |
|---|---|
| Arquitectura | Hexagonal por módulos (domain / application / infrastructure / api) |
| Usuarios | Multiusuario con JWT (access + refresh) |
| Monedas | ARS/USD siempre visibles; MEP (default), oficial, blue, CCL y cripto, configurable |
| Activos | Cuentas ARS/USD, efectivo, acciones, CEDEARs, bonos, ETFs, ONs, cripto, deudas; bienes a futuro |
| Precios | Automáticos + manuales; brokers IOL (API) y Balanz (import de archivo) |
| Extras | Categorías, transferencias, tarjetas y cuotas, recurrentes, presupuestos, reportes |
| Dependencias | Solo `requirements.txt` / `requirements-dev.txt` con pip |
| Python | 3.14.8 |
| Git | `main` (producción) + `develop`; Conventional Commits; CI con lint-fix y tests; imagen en GHCR al mergear a `main` |
| Scrum | Sprints de 2 semanas, Jira, unas 10 h/semana; PO = Elias, SM + Dev = Claude |

## Sprint Backlog
| Ítem | Estado |
|---|---|
| Definir el stack y verificar que nada esté deprecado (`docs/stack.md`) | ✅ |
| `requirements.txt` y `requirements-dev.txt` con versiones fijadas | ✅ |
| `.gitignore` y `.gitattributes` | ✅ |
| README y CONTRIBUTING | ✅ |
| Working agreement (roles, ceremonias, DoR, DoD) | ✅ |
| Product Backlog con épicas, historias, criterios y SP | ✅ |
| Roadmap y releases | ✅ |
| CSV de importación para Jira | ✅ |
| Plantillas de ceremonias y de PR | ✅ |
| `git init`, ramas `main` / `develop` y commit inicial | ⏳ |
| Crear el repo en GitHub y las reglas de protección | ⏳ requiere `gh` y nombre/visibilidad del repo |
| Crear el proyecto `PF` en Jira e importar el backlog | ⏳ requiere el sitio Jira del PO |
| Verificar la instalación de `requirements-dev.txt` en Python 3.14.8 | ⏳ requiere instalar Python 3.14.8 |
