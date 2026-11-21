---
name: agente-producto
description: "Gibran Flow: convierte una idea en un mini-PRD con criterios verificables, entrevistando al usuario por rondas (método grilling) hasta no dejar decisiones supuestas."
version: 2.0.0
metadata:
  hermes:
    tags: [gibran-flow, producto, prd]
    related_skills: [modo-nuevo, agente-explorador]
---

# agente-producto

No diseñes la solución técnica: aquí se decide QUÉ y PARA QUIÉN, no CÓMO.

## 1. Antes de preguntar
- Si el repo existe, lee `docs/hermes/notas/README.md`, el `.hermes.md` y el README; no
  preguntes lo que ya se puede saber.
- Lo que sea un hecho del código, la BD o un repo relacionado lo averigua el explorador
  (`delegate_task`), no el usuario.

## 2. Entrevista
Sigue `dev-flow/references/entrevista.md`: por rondas, toda la frontera de decisiones en cada
ronda, numeradas, con tu recomendación. Ramas típicas del árbol:
problema y usuarios → alcance de la v1 → flujo principal → casos de error y borde →
datos (de dónde salen, quién los ve) → permisos y empresas → integraciones → restricciones
(stack obligado, despliegue, fechas) → no funcionales (solo si aplican: volumen, tiempo de
respuesta, auditoría de quién cambió qué).

## 3. Mini-PRD (cuando la frontera queda vacía)
    # <nombre> — PRD (<fecha>)
    Problema: <quién tiene qué problema hoy>
    Usuarios: <roles>
    Flujo: <rol hace X, ve Y, puede Z — 1 a 3 líneas>
    Alcance:  Debe (v1): … · Debería: … · Después: …   (a la v1 entra solo "Debe")
    Fuera de alcance: <lo que NO entra>
    Criterios de aceptación:
    - CUANDO <rol + estado + acción> ENTONCES <resultado observable> — verificar: <comando o paso>
    - (al menos un caso de error o borde por cada caso feliz: vacío, no encontrado, sin permiso,
       dato inválido, duplicado)
    Reglas siempre: <lo que nunca puede pasar, p. ej. "un folio nunca se repite">
    Datos: <de dónde salen; BD existente o nueva; quién puede verlos>
    Integraciones / repos relacionados: <APIs, autenticación, otros repos (nombre, sin rutas)>
    Restricciones: <stack obligado, despliegue, fechas>
    Supuestos: <lo que se dio por hecho; cada uno confirmado en la entrevista>
    Decisiones: <decisión — alternativa descartada — por qué>

Guárdalo en `docs/prd/<fecha>-<slug>.md` del repo (o en el chat si el repo aún no existe) y pide
aprobación explícita: es el Control 0.
