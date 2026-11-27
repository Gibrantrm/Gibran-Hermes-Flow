---
name: modo-feature
description: "Gibran Flow: agregar o cambiar comportamiento en un repo existente, siempre por Kanban con QA y revisor. Cómo armar el plan en references/plan.md."
version: 3.8.0
metadata:
  hermes:
    tags: [gibran-flow, feature]
    related_skills: [dev-flow, agente-explorador, agente-implementador]
---

# modo-feature

## 1. Explorar (siempre)
`delegate_task` con brief de dev-flow §4, skill `agente-explorador`, objetivo = la petición.
Verifica 2-3 de sus citas archivo:línea tú mismo antes de creerle.

## 2. Reclasificar riesgo
Con los hallazgos, aplica `dev-flow/references/riesgo.md` de nuevo (solo puede subir).
Si el explorador dice que ya existe o contradice la petición → `necesita-decisión` al usuario.
**Pendientes que cambian el plan, ahora:** si un PENDIENTE del explorador puede cambiar el plan
(una longitud, quién administra algo, si existe otro script o servicio), resuélvelo antes de
planear, no al final. Ej.: el código dice 300 caracteres y el dueño del esquema dice 600: se
averigua cuál manda antes de escribir el criterio.
**Worktrees ajenos:** todo worktree que no creaste en esta tarea (`git worktree list`:
`<repo>.wt-*`, `.worktrees/`, `.claude/worktrees/`…) es trabajo de otras tareas o personas. Son solo
lectura y nunca base del plan: el plan sale de la rama base del repo. Puedes mencionarlos como
dato, no esperar a que se integren.

## 3. Implementar (siempre Kanban, con QA y revisor)
No hay camino corto: quien dirige el trabajo no lo revisa con ojos frescos. El riesgo decide
solo cuánto plan y cuántos controles (pasos 1-4); de ahí en adelante es igual.
1. **Entrevista** de las decisiones abiertas que el explorador no pudo resolver, según
   `dev-flow/references/entrevista.md` (por rondas, con tu recomendación; los hechos no se
   preguntan). Si no queda ninguna decisión abierta, sáltala.
   **No escribas el plan hasta tener la respuesta de la última ronda.** Entrevista, pedido de
   `/reasoning`, plan y Control 1 van en mensajes distintos: un plan escrito junto a preguntas
   abiertas decide por el usuario.
2. Solo riesgo ALTO: pide al usuario "Escribe `/reasoning high` para el plan (si no estás en la
   TUI, relánzame con `--reasoning high`)". Termina el mensaje ahí y espera; no adelantes el plan.
   Va también sin TUI (sesiones `hermes -z`): ahí el usuario lo sube con `--reasoning`.
3. **Plan** según `references/plan.md`. ALTO: tabla Crear/Modificar, tarjetas como rebanadas
   verticales, fases si aplican, criterios CUANDO/ENTONCES con caso borde, test por tarjeta, decisiones
   (las de la entrevista incluidas); revísalo con su lista "Antes del Control 1". BAJO: la
   versión breve ("Riesgo bajo"), normalmente una tarjeta.
4. ALTO: pide `/reasoning medium`. **Control 1:** presenta el plan; marca en negritas cualquier
   cambio de contrato; si falta dónde testear, ofrece las dos opciones. Con la entrevista
   hecha, el Control 1 es confirmar, no descubrir. Espera aprobación explícita.
   BAJO: muestra el plan breve y sigue sin esperar, salvo "Sin test" (siempre lo decide el
   usuario).
5. Si vienes de `modo-bug` con el worktree creado en el diagnóstico de esta tarea, reutiliza
   ese worktree y su rama `bugfix/<slug>`; no ejecutes otro `worktree add`.
   Para una feature, crea UN worktree (uno por repo si el cambio cruza repos):
   `git -C <repo> worktree add ../<repo>.wt-<slug> -b feature/<slug>`
6. Crea las tarjetas tú mismo con la herramienta `kanban_create`, una llamada por tarjeta
   (guarda cada id para `parents`). Nunca dejes el comando en un archivo ni le pidas al usuario
   que lo cree. Campos:
   `title`, `assignee: "implementador"`, `workspace_kind: "dir"`,
   `workspace_path: "<ruta-absoluta-del-worktree>"`,
   `skills: ["agente-implementador", "stack-<tecnología del repo>"]`,
   `max_runtime_seconds: 2700`, `body: "<plantilla de references/plan.md>"`,
   `parents: ["<id-previo>"]` si depende de otra. (Reintentos: el tope viene de
   `kanban.failure_limit` = 2 y cuenta **intentos totales**, no reintentos extra: el primero y
   uno más. Lo mismo `max_retries` si lo pones en una tarjeta: con 1 se rinde al primer fallo.)
   **Tarjetas con tests .NET:** añade `initial_status: "blocked"` al crearlas. Con el id
   devuelto registra CADA comando del plan (sin ejecutarlo):
   `python "${HERMES_SKILL_DIR}\..\..\..\scripts\dotnet_seguro.py" autorizar-test
   --tarea <id> --worktree "<worktree>" -- <proyecto>.csproj --filter "<filtro>" <opciones>`.
   Incluye las selecciones de baseline/TDD, QA y E2E acumuladas previstas; ver `stack-dotnet`
   § "Compilar y probar". Solo después de que TODOS los registros salgan con código 0,
   `kanban_unblock` con `task_id: "<id>"` (respeta `parents`). Si falla el registro, la tarjeta
   permanece bloqueada. Esto evita que el despachador arranque antes de tener autorización.
   No registres comandos más amplios que el plan ni autorices suites enteras por costumbre.
   Precarga solo lo imprescindible: cada skill precargada entra completa en cada llamada del
   worker; el resto lo carga él si lo necesita.
   `kanban_create` te suscribe a la tarjeta (`subscribed: true`): en la TUI (`hermes --tui`)
   recibes un aviso cuando termina o se bloquea. Si no tienes `kanban_create` o falla con
   "delegate_task child contexts cannot mutate Kanban tasks", no lo rodees: bloquea y dile al
   usuario.
7. Dile al usuario: "Tarjetas listas; el despachador las toma solo". No menciones `/despachar`
   de antemano. Si al consultar el tablero ves una tarjeta `ready` que lleva más de ~2 min sin
   pasar a `running`, antes de pedir nada revisa la línea `Gateway:` de `hermes status` y
   `hermes kanban diagnostics`:
   - `Gateway: ✗ stopped` → el despachador vive en el gateway y sin él nada se toma. Pídele al
     usuario `hermes gateway start` (o `hermes gateway install` para que quede permanente). El
     gateway que arranca solo con una sesión se apaga tras 10 min sin actividad
     (`gateway.unmanaged_idle_exit_seconds`) y crear tarjetas no lo despierta.
   - Gateway corriendo y la tarjeta sigue sin tomarse → pide `/despachar` y cita lo que diga
     diagnostics.
   **El estado de una tarjeta no se supone:** antes de afirmarlo consúltalo (`kanban_list` o
   `hermes kanban show <id>`). Sin aviso de la TUI (`subscribed: false`, CLI clásica), pídele
   al usuario que te avise cuando el tablero cambie.
8. Cada tarjeta: implementador → `kanban_request_review` → revisor corre QA y revisión →
   `kanban_request_changes` (vuelve al implementador) o `kanban_complete`. Al llegar al
   tope de rondas (SOUL del revisor) el revisor bloquea; tú traes el bloqueo al usuario.
   **Lo aprobado en el Control 1 no lo cambias tú:** un bloqueo que pide una decisión
   (`needs_input`, `necesita-decisión`) o quitar, cambiar o dejar de probar un criterio aprobado
   se le pregunta al usuario, con tu recomendación. Lo que sí resuelves solo: dudas de hecho que
   se verifican (código, DEV, documentación).
   Un bloqueo por **algo que falta instalar**: pregúntale al usuario con tu recomendación. Si
   aprueba, desbloquea la tarjeta con un comentario ("autorizado: instalar <qué>") y el worker
   sigue; si no, propón otro camino (simularlo, riesgo aceptado), que también decide él.
   Lo que un worker instaló sin preguntar (lo que el repo declara) va en el Control final.
   Un bloqueo del revisor porque **una tarjeta en paralelo cambió el worktree** durante su
   revisión (lo avisa `guardia_revision`) es correcto, no una falla: por ruta no se sabe de qué
   tarjeta es un archivo que ya existía. Espera a que la vecina pase a `review` o `done` y
   desbloquéala con un comentario ("worktree estable, revisa de nuevo"); cuesta una ronda más.
   Si la **tarjeta de verificación en navegador** se bloquea con una falla: aplica "Hallazgos
   después de las tarjetas" (abajo).
9. Cuando todas estén `done`: **primero lee el resumen del revisor** de cada tarjeta
   (`hermes kanban show <id>`): lo que ya verificó con evidencia (p. ej. el comportamiento
   de una clase de un NuGet) no lo repites ni lo reportas como "no revisado". Luego verifica
   tú: build + selecciones de tests autorizadas en el worktree, diff completo contra los
   criterios del plan. En .NET usa explícitamente `dotnet_seguro.py test --tarea <id>` con
   cada comando registrado para esa tarjeta, también después de `done`; no una suite global. Atiende
   sus HALLAZGOS; no los ignores. Las pruebas en navegador NO las corres tú (quien dirige no
   revisa con ojos frescos): lees su resultado en el resumen del revisor. Sin arnés, la tarjeta
   final de verificación ya la creaste en el paso 6 (`references/plan.md`).
10. **Pendientes.** Si hubo E2E o app levantada: `python
    ${HERMES_SKILL_DIR}/../../../scripts/app_local.py detener` en el worktree (no afirmes que no
    queda nada corriendo sin correrlo). Junta los PENDIENTE del explorador, del plan y de los
    revisores y sepáralos:
    - **verificables** (leer código, correr un comando, consultar DEV en solo lectura, leer un
      repo relacionado): mándalos TODOS en un solo `delegate_task` con skill
      `agente-explorador` y el worktree; cada uno vuelve con su cita (archivo:línea, salida o
      consulta). No los dejes como riesgo por ser caros de verificar tú. Lo que vuelva con un
      problema: "Hallazgos después de las tarjetas" (abajo).
    - **no verificables** (requieren escribir en DEV/PROD, un permiso o un acceso): van a
      "Riesgos aceptados" con el formato de `references/control-final.md`.
11. **Escriba** (`delegate_task`, skill `agente-escriba`), con la ruta absoluta del worktree
    ("escribe en `<worktree>`"; el hijo arranca en el repo principal), las decisiones del plan,
    lo verificado en el paso 10 y el `verified_external` de las tarjetas. En el encargo marca
    cada dato como **hecho** (con su fuente) o **supuesto**: el escriba no puede distinguirlos
    solo.
12. **Control final** con la plantilla fija de `references/control-final.md`: corre primero
    `scripts/cierre.py` (cuenta tarjetas y revisiones, costo, fila de métrica, apps vivas y
    comando para integrar) y pega su salida; llena las 7 secciones en orden. Cuando el usuario
    lo aprueba, corre `scripts/integrar.py` (cambios staged en la rama de origen, sin commit;
    borra worktree y rama). El usuario revisa un solo diff y hace el commit.

## Hallazgos después de las tarjetas
Un hallazgo que aparece cuando las tarjetas ya están `done` (tarjeta de verificación bloqueada,
pendiente que el explorador verificó mal, tu propia verificación del paso 9) se clasifica igual:
- **Confirma** que está bien → evidencia del Control final, con su cita.
- **De esta tarea** (no cumple un criterio aprobado o rompió algo) → no lo corriges tú: tarjeta
  de corrección con `kanban_create` (`assignee: "implementador"`, mismo worktree, `parents` = la
  tarjeta que lo causó, el hallazgo como criterio con su evidencia). Pasa por implementador y
  revisor como cualquier otra; si lleva tests .NET, créala bloqueada, registra su alcance y
  desbloquea como en el paso 6 (no hereda la autorización de su padre).
  Si venía de la verificación en navegador, crea además una nueva
  tarjeta de verificación con `parents` = la de corrección (la bloqueada queda como registro).
  Luego vuelve al paso 9.
- **Ya existía o es de otro tema** → "Hallazgos abiertos" del Control final; decide el usuario si
  va aparte. No se arregla de paso.
- **Arreglarlo cambia algo aprobado** (alcance o criterio) → pregúntale al usuario con tu
  recomendación.
Topes: 2 vueltas de corrección por el mismo hallazgo; y **3 tarjetas de corrección en total en la
feature** (aunque cada una sea por un problema distinto). Al llegar a cualquiera, detente y
tráelo al usuario con la lista de lo corregido y lo que sigue saliendo: varias correcciones
después de terminar suelen indicar que el plan o los criterios estaban incompletos.
