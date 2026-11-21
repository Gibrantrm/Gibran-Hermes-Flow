---
name: dev-flow
description: "Router de Gibran Flow: clasifica una petición de desarrollo (proyecto nuevo, feature, bug) y su riesgo, y la lleva al modo correcto."
version: 1.3.0
metadata:
  hermes:
    tags: [gibran-flow, router, desarrollo]
    related_skills: [modo-feature, modo-bug, modo-nuevo, agente-explorador]
---

# dev-flow

Úsala para CUALQUIER petición de desarrollo. Tú eres el orquestador.

## 1. Modo
- Proyecto que no existe → `modo-nuevo`.
- Algo no funciona como debería → `modo-bug`.
- Comportamiento nuevo o cambio en un repo existente → `modo-feature`.
- Petición mixta (bug + feature, dos features sin relación) → divídela, dilo al usuario
  en una línea y procesa una por una.
- Si no puedes decidir el modo, pregunta (una pregunta).

## 2. Riesgo inicial
Clasifica con `references/riesgo.md` ANTES de explorar. Dilo en una línea:
`Modo: feature · Riesgo inicial: bajo (motivo)`. Solo existen BAJO y ALTO; ante la duda, ALTO.

## 3. Carga el modo
`skill_view("<modo>")` y síguelo. Feature y bug siempre empiezan con el explorador.

## 4. Delegar a un hijo (delegate_task)
Los hijos empiezan sin contexto. El `context` del brief SIEMPRE incluye:

    Repo: <ruta absoluta> · Rama/worktree: <ruta>
    Primero ejecuta skill_view("<skill del agente>") y síguela.
    Objetivo: <una frase>
    Lo que ya sabemos: <hallazgos previos relevantes, con archivo:línea>
    Límites: <qué NO tocar>
    Entrega con el formato de dev-flow/references/formato-entrega.md

Si un hijo falla con "quota exceeded" o 429 de Copilot, no reintentes: dile al usuario
"Copilot sin cuota: ejecuta `/hijos-claude` y abre una sesión nueva" (los hijos no
tienen respaldo automático; los workers del Kanban sí).

## 5. Reglas comunes
- Cualquier agente puede detenerse con `RESULTADO: necesita-decisión`; tú lo traes al usuario.
  Igual si para seguir habría que cambiar algo que el usuario ya aprobó (un criterio, el
  alcance, una decisión de la entrevista): recomienda, pero decide él.
- Si la pregunta es "¿en qué repo está…?" (la API que consume una app, el servicio de
  identidad), pregúntala ANTES de planear y pasa la respuesta (nombre del repo; la URL remota la
  saca el escriba) al escriba para que quede en "Repos relacionados" del `.hermes.md`.
  Ver `references/repos-relacionados.md`.
- Si la exploración contradice la petición (ya existe, no es un bug), detente y dilo.
- **Reglas del repo:** Hermes carga UN solo archivo de contexto (`.hermes.md`, si no `AGENTS.md`,
  si no `CLAUDE.md`). Si el repo tiene `CLAUDE.md` o `AGENTS.md`, léelos tú al empezar y pon en
  cada brief y tarjeta "lee `CLAUDE.md` del repo": sus reglas mandan sobre las de Gibran Flow
  salvo en lo de seguridad (commit, push, PROD, secretos).
- Ningún commit ni push: el commit lo hace el usuario tras el control final.
