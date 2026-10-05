# Working Agreement (Scrum)

## Roles
| Rol | Quién | Responsabilidades |
|---|---|---|
| **Product Owner** | Elias | Visión del producto, prioriza el Product Backlog, escribe y acepta historias, aprueba PRs y releases. |
| **Scrum Master** | Claude | Facilita las ceremonias, mantiene Jira actualizado, remueve impedimentos, mide la velocity y cuida el proceso. |
| **Developer** | Claude (con revisión del PO) | Diseña, implementa, testea y documenta los incrementos según la DoD. |

## Cadencia
- **Sprint:** 2 semanas.
- **Dedicación:** unas 10 h/semana, o sea unas 20 h por sprint.
- **Ceremonias:** unas 3 h por sprint, así que quedan **unas 17 h netas de desarrollo**.

| Ceremonia | Cuándo | Timebox | Entrada | Salida |
|---|---|---|---|---|
| **Sprint Planning** | Día 1 | 1 h | Backlog refinado, velocity | Sprint Goal + Sprint Backlog en Jira, sprint iniciado |
| **Daily (async)** | Al empezar cada sesión de trabajo | 5 min | Tablero Jira | Nota: *ayer / hoy / impedimentos* (chat o comentario en Jira) |
| **Backlog Refinement** | Mitad del sprint | 30 min | Historias del próximo sprint | Historias en estado *Ready* (DoR) y estimadas |
| **Sprint Review** | Último día | 30 min | Incremento en `develop` | Demo de endpoints, aceptación o rechazo de historias por el PO, backlog actualizado |
| **Retrospective** | Último día, después de la Review | 30 min | Métricas del sprint | 1–2 acciones de mejora con responsable |
| **Release** | Tras la Review, si corresponde | — | Aprobación del PO | PR `develop` → `main`, tag `vX.Y.Z`, imagen en GHCR |

Las actas se guardan en `docs/scrum/sprint-NN/` usando las plantillas de `docs/scrum/templates/`.

## Estimación
- **Story points** con escala Fibonacci: 1, 2, 3, 5, 8, 13.
- Referencias:
  - **1 SP:** cambio trivial (un campo, un filtro).
  - **3 SP:** endpoint CRUD con tests.
  - **5 SP:** caso de uso con reglas de negocio no triviales o integración externa.
  - **8 SP:** historia compleja; se considera dividirla.
- Las historias de **13 SP se dividen antes** de entrar a un sprint.
- Los **spikes** (investigación) tienen un timebox en horas y se estiman en SP para la capacidad.
- **Velocity:** promedio móvil de los últimos 3 sprints. La inicial supuesta es de 13 SP.

## Definition of Ready (DoR)
Una historia puede entrar a un sprint si:
- [ ] Tiene formato *Como… quiero… para…*.
- [ ] Tiene criterios de aceptación verificables.
- [ ] Está estimada en SP (≤ 8).
- [ ] Sus dependencias están resueltas o planificadas antes en el mismo sprint.
- [ ] El PO la priorizó.

## Definition of Done (DoD)
Una historia está terminada cuando:
- [ ] El código está en `feature/PF-<n>-<slug>` y mergeado a `develop` vía PR (squash).
- [ ] El título del PR es un Conventional Commit con la key de Jira, por ejemplo `feat(accounts): crear cuenta [PF-14]`.
- [ ] El CI está en verde: ruff, ruff format, mypy `--strict`, import-linter, pytest con cobertura ≥ 85 %, `alembic check` y prefijo de commits.
- [ ] Sin `DeprecationWarning`: pytest falla si aparece alguno.
- [ ] Hay tests unitarios de dominio y tests de integración/e2e del endpoint.
- [ ] Incluye la migración de Alembic, si cambia el esquema.
- [ ] Los endpoints están documentados en OpenAPI (summary, descripción y ejemplos).
- [ ] Todos los criterios de aceptación se cumplen y el PO aprobó el PR.
- [ ] El issue de Jira está en **Done**.

**DoD de release:** todo lo anterior, más el PR `develop` → `main` aprobado, el tag SemVer, la imagen publicada en GHCR y la entrada en el CHANGELOG.

## Jira
- **Proyecto:** Scrum, key `PF`.
- **Tipos de issue:** Epic, Historia, Tarea, Subtask (más Bug, si se agrega). Los spikes son *Tarea* con el label `spike`.
- **Sitio:** https://personal-finance-edlazo.atlassian.net. El mapeo `US-xxx` ↔ `PF-n` está en [jira-mapping.md](jira-mapping.md).
- **Workflow:** `Backlog → To Do → In Progress → In Review → Done`.
  - *In Progress* corresponde a una rama creada.
  - *In Review* corresponde a un PR abierto.
  - *Done* corresponde al PR mergeado y aceptado.
- **Campos:** Story Points, Priority, Labels (módulo e `id-US-xxx`), Sprint.
- **Reportes:** Burndown (seguimiento en el Daily) y Velocity (en la Retro).
- **Integración:** la app *GitHub for Jira* vincula ramas, commits y PRs que contienen `PF-<n>`.

### Carga inicial del backlog
1. Crear el proyecto Scrum con key `PF` y habilitar el campo *Story Points*.
2. Crear los sprints vacíos `PF Sprint 1` … `PF Sprint 12`, o ignorar la columna *Sprint* al importar.
3. Ir a *Settings → System → External System Import → CSV* y elegir `docs/scrum/jira-import.csv` (UTF-8).
4. Mapear las columnas *Issue Id*, *Parent* (vincula historias con épicas), *Story Points*, *Labels* (ambas) y *Sprint*.
5. Verificar: 12 épicas y 56 ítems con SP.

## Gestión de bugs e impedimentos
- **Bug en `develop`:** se crea un issue *Bug*. Si es bloqueante entra al sprint actual; si no, se prioriza en Refinement.
- **Bug en producción:** rama `hotfix/PF-<n>` desde `main`, PR a `main` y back-merge a `develop`.
- **Impedimentos:** se reportan en el Daily, el SM los registra en Jira (flag) y se resuelven o escalan al PO.

## Acuerdos
- El Sprint Goal no cambia a mitad de sprint. Si aparece algo urgente, el PO decide qué historia sale.
- No se empieza una historia nueva si hay un PR propio esperando revisión por más de 2 días.
- Toda decisión técnica relevante se documenta en `docs/stack.md` o en un ADR (`docs/adr/NNNN-titulo.md`).
