# Entrevista por rondas (adaptado de "grilling", Matt Pocock)

Objetivo: llegar a un entendimiento compartido sin dejar ninguna decisión supuesta en silencio.

## Hechos vs. decisiones
- **Hechos** (lo que se puede averiguar en el código, la BD de DEV, la documentación o un repo
  relacionado): NO se preguntan. Los averigua el explorador (`delegate_task`). Mientras corre,
  sigue con las preguntas que no dependen de ese dato.
- **Decisiones** (qué debe hacer el sistema, qué se acepta, qué se prioriza): siempre del usuario.

## Árbol y frontera
- Trata el pedido como un árbol de decisiones: cada decisión abre las que dependen de ella.
- **Frontera** = decisiones cuyos prerrequisitos ya están resueltos. Pregunta TODA la frontera
  en una ronda. Una pregunta que depende de otra abierta espera a la siguiente ronda.

## Formato de cada ronda
    **Q1. <título corto>**
    <contexto en 1-3 líneas; opciones si las hay>
    → Recomiendo: <respuesta> (<por qué, con evidencia del repo si existe>)

    ---

    **Q2. …**
- Redáctala para que "sí" acepte tu recomendación. El usuario puede contestar "sí a todo
  salvo Q3: …".
- Máximo ~5 preguntas por ronda; si la frontera es mayor, empieza por las que más cambian el plan.

## Cuándo termina
Cuando la frontera queda vacía: no queda rama sin visitar ni nada asumido. Antes de actuar,
resume las decisiones en una lista corta y pide confirmación del entendimiento compartido.
Las decisiones tomadas pasan al plan (y luego al escriba, como "Decisiones" de la nota).

## Proporción
- Proyecto nuevo: entrevista completa.
- Riesgo alto: solo las decisiones que el explorador no pudo resolver con el código.
- Riesgo bajo: no se hace, salvo una decisión real abierta (entonces una ronda corta).
