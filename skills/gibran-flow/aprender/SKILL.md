---
name: aprender
description: "Gibran Flow: /aprender <qué salió mal>. Convierte una corrección del usuario en una regla escrita en el lugar correcto."
version: 1.0.1
metadata:
  hermes:
    tags: [gibran-flow, aprendizaje]
---

# aprender

1. Redacta UNA regla: imperativa, una línea, con porqué y fecha. Ejemplo:
   `- No modifiques endpoints existentes al agregar uno nuevo; son contrato (2026-10-16, /health).`
2. Decide el destino y dilo:
   - Solo aplica a este repo → `.hermes.md` del repo (vía agente-escriba en el worktree
     actual, o directo si no hay tarea en curso; el usuario la verá en su diff).
   - Aplica a todo el flujo → agregar a `${HERMES_SKILL_DIR}/../../../propuestas-de-mejora.md`.
   - Es preferencia personal del usuario → memoria (herramienta de memoria).
3. Agrega una fila a `${HERMES_SKILL_DIR}/../../../metricas/correcciones.md`:
   `| <fecha> | <repo> | <modo> | <categoría> | <regla> | <destino> |`
   Categorías: contrato, alcance, patrón, verificación, datos, seguridad, comunicación, otro.
4. Muestra la regla y el destino en dos líneas. Sin más.
