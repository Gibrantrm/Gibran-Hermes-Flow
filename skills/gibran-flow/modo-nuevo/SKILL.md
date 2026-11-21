---
name: modo-nuevo
description: "Gibran Flow: arrancar un proyecto nuevo hasta un walking skeleton, desde un repo de referencia o desde cero con aprobación."
version: 1.0.0
metadata:
  hermes:
    tags: [gibran-flow, proyecto-nuevo]
    related_skills: [agente-producto, modo-feature, agente-escriba]
---

# modo-nuevo

Siempre riesgo ALTO.

1. **PRD:** carga `agente-producto`. **Control 0:** el usuario aprueba el PRD.
2. Pide `/reasoning high` (sin TUI: que te relance con `--reasoning high`). Termina el mensaje
   ahí y espera.
3. **Base:** lee `dev-flow/references/catalogo-repos.md`.
   - Hay referencia que encaja → propón replicar su estructura (carpetas, proyectos,
     paquetes, pipeline). Explora la referencia con `delegate_task` + `agente-explorador`.
   - No hay → propone 2-3 stacks con trade-offs (costo, encaje con el equipo, despliegue)
     y tu recomendación. El usuario elige.
4. Pide `/reasoning medium`.
5. **Plan del walking skeleton** (Control 1): compila, corre, UN endpoint o pantalla de
   punta a punta, tests corriendo, README con cómo correrlo. Nada más.
6. Crea el repo vacío en la ruta que diga el usuario (`git init`), un primer commit vacío
   lo hace el usuario, y luego worktree + tarjetas como en `modo-feature` paso 3.
7. **Escriba:** `.hermes.md`, `docs/hermes/notas/` y una fila nueva en el catálogo
   (como propuesta en `propuestas-de-mejora.md`; el usuario la pasa al catálogo).
8. **Control final.** Las funcionalidades se piden después, en modo feature.
