# Sprint 0: Retrospectiva

- **Fecha:** 2026-10-04
- **Asistentes:** PO (Elias), SM/Dev (Claude)

## Métricas
| Métrica | Valor |
|---|---|
| Velocity | N/A (sprint de definición, sin SP comprometidos) |
| Ítems completados / planificados | 13 / 13 |
| PRs mergeados | 2 (PF-73 y back-merge) |
| Incidentes | 1 (PR mergeado en `main` por error) |

## Qué salió bien (mantener)
- Hacer preguntas antes de actuar: se aclararon la arquitectura, las monedas, los brokers y las reglas de PR antes de decidir.
- Verificar las versiones reales (PyPI, python.org): nada deprecado; se descartaron `gunicorn`/`uvicorn.workers`.
- Documentación completa: stack, Scrum, contribución y roadmap.
- Backlog cargado en Jira con el conector, con criterios y SP.

## Qué no salió bien (mejorar)
1. El PR de PF-73 se mergeó en `main` (era la rama por defecto): merge commit inesperado y back-merge.
2. Se presentó como textual un aviso de GitHub que no estaba verificado.
3. El Sprint 1 quedó iniciado en Jira antes del Planning.
4. La sesión se cortó a mitad de trabajo y quedaron dudas sobre el push inicial.
5. `winget` instaló Python 3.14.7 en lugar de la 3.14.8.
6. Las reglas de PR llegaron con el sprint avanzado y ampliaron PF-20.
7. Jira no tiene el estado *En revisión*, y quedó PF-4 de ejemplo.
8. **(PO)** Respuestas demasiado largas.
9. **(PO)** Se ejecutaron acciones sin explicar antes qué se iba a tocar.

## Acciones
| # | Acción | Responsable | Para cuándo |
|---|---|---|---|
| A1 | Rama por defecto en `develop` | PO | ✅ Hecho |
| A2 | `pr-rules` rechaza PRs a `main` que no vengan de `develop` o `hotfix/*` | Dev | Sprint 1 (PF-20) |
| A3 | Afirmar sobre herramientas externas solo con fuente verificada; si no, decir "no lo verifiqué" | SM/Dev | Permanente |
| A4 | Al retomar una sesión, revisar `git status`, `git log` y el remoto antes de seguir | SM/Dev | Permanente |
| A5 | Agregar el estado *En revisión* en Jira y borrar PF-4 | PO | Antes del Planning |
| A6 | README: instalar Python desde python.org con la versión exacta | Dev | ✅ Este PR |
| A7 | Respuestas cortas y al punto | SM/Dev | Permanente |
| A8 | Antes de tocar Jira, GitHub o hacer push, explicar qué se va a hacer | SM/Dev | Permanente |
