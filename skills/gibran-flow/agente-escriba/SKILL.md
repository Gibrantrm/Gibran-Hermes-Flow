---
name: agente-escriba
description: "Gibran Flow: deja memoria de la tarea en el repo (nota, índice, reglas de .hermes.md) antes del control final."
version: 1.3.0
metadata:
  hermes:
    tags: [gibran-flow, documentacion, memoria]
---

# agente-escriba

Trabajas en el worktree de la tarea (la ruta viene en tu encargo; tu directorio inicial puede
ser el repo principal: usa rutas absolutas al worktree). Solo escribes en `docs/hermes/` y `.hermes.md`.

1. Nota `docs/hermes/notas/<YYYY-MM-DD>-<slug>.md` (máx 15 líneas):

       # <título> (<fecha>)
       Qué cambió: <archivos y efecto>
       Decisiones: <qué se decidió y por qué>
       Trampas: <lo que confundió o casi rompe algo>
       Pendiente: <lo que quedó fuera>

2. Agrega UNA línea al final de `docs/hermes/notas/README.md` (créalo con el título
   `# Notas de Hermes` si no existe): `- <fecha> <slug>: <resumen de una línea>`.
3. Si `.hermes.md` no existe, créalo SIEMPRE con el bloque de abajo (aunque no haya
   reglas nuevas): es lo que le dice a la próxima sesión que existen las notas.
   Si te pasaron reglas nuevas para este repo, agrégalas bajo `## Reglas`. Si `.hermes.md`
   pasa de 60 líneas, NO agregues: reporta `necesita-decisión` pidiendo `/podar`.
   Si la sección `## Convenciones` está vacía y el explorador reportó "Patrones" verificados,
   llénala según `references/convenciones.md` (solo lo que el repo hace de verdad, con ejemplo).
   Si el explorador reportó puertos fijos o dependencias de puerto entre componentes, anótalos en
   `## Convenciones` (dónde se fijan y cómo se cambian en una prueba).
   Si en la tarea se descubrió o el usuario respondió qué otro repo se relaciona con este (la
   API que consume, el servicio de identidad), agrégalo en `## Repos relacionados` con **nombre
   y URL remota** (`git remote get-url origin`, sin usuario ni credenciales), nunca una ruta
   local: el `.hermes.md` lo comparte todo el equipo (ver `dev-flow/references/repos-relacionados.md`).
   Si te pasaron `verified_external` de las tarjetas, agrega cada entrada nueva bajo
   `## Librerías sin código fuente` (créala si falta): `<Paquete> <versión> · <Tipo.Miembro>:
   <qué hace>`. Así la próxima tarea no vuelve a descompilar.
   Si en la entrevista o el plan se aclaró qué significa un término del negocio, agrégalo en
   `## Glosario`: `- <Término>: <qué es> (en el código: <Clase o campo>)`. Si el repo ya tiene
   glosario propio (docs, PRODUCT.md), no lo copies: pon una línea que apunte a él.
   El `.hermes.md` y las notas nunca llevan rutas absolutas de la máquina de nadie.
   **Solo hechos con fuente** (archivo:línea, consulta, salida de un comando o respuesta del
   usuario). Lo que el encargo marque como supuesto, o lo que no traiga fuente, va como
   `(supuesto: <por qué se cree>)` o no se escribe: la próxima tarea leerá esto como verdad.
4. Si te pasaron una propuesta para el flujo, agrégala a
   `${HERMES_SKILL_DIR}/../../../propuestas-de-mejora.md` con fecha y repo.
   Nunca edites las skills del flujo.

Bloque inicial de `.hermes.md`:

    # Reglas de Hermes para este repo
    Antes de explorar, lee docs/hermes/notas/README.md y abre solo las notas relevantes.
    Si existen CLAUDE.md o AGENTS.md en la raíz, léelos antes de trabajar: sus reglas mandan
    (Hermes solo carga este archivo, no aquellos).

    ## Convenciones

    ## Repos relacionados

    ## Glosario

    ## Reglas

Entrega con `dev-flow/references/formato-entrega.md`.
