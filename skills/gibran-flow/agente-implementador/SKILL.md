---
name: agente-implementador
description: "Gibran Flow: implementa UNA tarjeta con TDD real, tocando solo sus archivos, y se autorrevisa con los mismos criterios que bloquearía el revisor antes de pedir revisión. Núcleo agnóstico; comandos y convenciones vienen del módulo stack-<tecnología>."
version: 2.7.1
metadata:
  hermes:
    tags: [gibran-flow, implementacion, tdd]
    related_skills: [stack-dotnet, test-driven-development]
---

# agente-implementador

## 0. Antes de escribir
- Trabaja SOLO en el worktree indicado. Confirma con `git -C <worktree> status`.
- Lee la tarjeta: archivos permitidos, archivos de otras tarjetas, criterios, límites.
  La tarjeta ya viene en tu primer mensaje (`# Kanban task …` con `## Body`,
  `## Prior attempts on this task` y `## Comment thread`): léela de ahí. No llames
  `kanban_show` sobre tu propia tarjeta aunque el protocolo de Kanban diga "Orient": repite
  lo mismo y pesa 15-35k caracteres. Úsalo solo si el body aparece recortado.
- Carga el módulo `stack-<tecnología>` del repo (hoy `stack-dotnet`): "Convenciones" y
  "Buenas prácticas" guían el código; "Compilar y probar" da los comandos (en Kanban, con el
  candado del worktree compartido). Respeta también las "Convenciones" del `.hermes.md` y, si existen,
  `CLAUDE.md` / `AGENTS.md` del repo: léelos tú (Hermes solo carga uno de esos archivos).
- **Librerías sin código fuente** (paquetes internos): sigue el orden de
  `dev-flow/references/repos-relacionados.md` § "Librerías internas" (uso en el repo → lo ya
  verificado en la tarjeta o el `.hermes.md` → fuente de la librería → binario solo si la duda
  bloquea un criterio). Anota lo que confirmaste para tu entrega (`verified_external`, paso 5).
- **Si una librería del repo exige algo para funcionar** (un servicio, una configuración, un
  contexto) y tu test falla por eso: primero busca tests o código del repo que ya la usen y copia
  cómo lo resuelven. Solo si no hay ninguno, revisa la librería, lo justo. Si sigue sin salir,
  `kanban_block` temprano diciendo qué falta y qué propones, en vez de seguir probando.
- **Línea base:** compila y corre los tests del proyecto afectado ANTES de tocar nada. Anota qué
  falla ya: no te atribuyas fallos previos ni los escondas.

## 1. Ciclo TDD (un criterio a la vez)
1. **RED:** un test por criterio, estructura preparar-actuar-verificar, nombre que describe la
   conducta. Córrelo y LEE la salida: debe fallar por una **aserción del criterio** (esperado ≠
   obtenido). Fallar por no compilar, por un error al preparar datos o porque "no hay tests" NO es
   RED válido: crea el mínimo (firma vacía que lanza "no implementado" o devuelve el valor por
   defecto) hasta que falle la aserción.
2. **GREEN:** el código mínimo que pasa ese test. Nada "por si acaso".
3. **Prueba de que el test sirve (mutación):** rompe a propósito la línea clave del cambio y
   confirma que el test vuelve a fallar; si sigue verde, el test no prueba nada. Restáurala y
   confirma con `git diff` que quedó igual. Va en la entrega (el revisor no muta: la verifica).
4. **Limpieza** solo dentro de tus archivos y con todo en verde.
5. Suite del proyecto: mismos fallos que la línea base, ni uno más.

**Criterio "en navegador" con E2E en la tarjeta** (reglas en `modo-feature/references/e2e.md`):
el mismo ciclo, contra la app levantada. RED: escribe la prueba E2E y córrela con la app SIN tu
cambio; debe fallar en la aserción del criterio (no en el login ni por tiempo agotado). GREEN:
implementa, vuelve a levantar la app y pasa. Corre también las E2E de las tarjetas anteriores de
la feature (el filtro acumulado viene en la tarjeta; nunca la categoría E2E completa: ver
`e2e.md` § "Qué E2E se corren"). No cambies la prueba de otra tarjeta salvo
que tu body lo diga. La app SIEMPRE con `app_local.py` (`detener` al empezar, `iniciar`, `detener`
al terminar). Entrega la evidencia `e2e` (rojo, verde, screenshots, consola) en el metadata.

**Un buen test:** verifica comportamiento público (no detalles internos), es independiente (sin
estado compartido ni orden), su valor esperado es un literal o ejemplo resuelto (nunca calculado
con la misma lógica del código), simula solo fronteras reales (API externa, reloj, correo,
archivos) y no piezas propias, e incluye los bordes que pida el criterio (null, vacío, límite,
no encontrado, error). Si el criterio depende de algo del motor de BD real, usa la base de test
que tenga el repo, no un sustituto en memoria.

## 2. Si no hay dónde testear
- Proyecto de tests inexistente, vacío o sin referencia al proyecto a probar: NO lo crees ni
  toques archivos de proyecto salvo que la tarjeta los liste. Termina con `kanban_block`:
  "falta proyecto de tests / referencia a <proyecto>" y propón el cambio exacto.
- Si la tarjeta sí lo permite: créalo como indica el módulo de stack, con la misma versión de
  framework que el proyecto probado y sin paquetes extra.
- Si el body dice "Sin test: aprobado en Control 1 porque …", verifica con build y evidencia
  manual, y decláralo en PENDIENTE. No inventes un test que no ejercita el código.

## 3. Si el build falla
- Junta TODOS los errores y lee cada mensaje (esperado contra obtenido). Arregla primero los que
  bloquean; usa la tabla de errores frecuentes del módulo de stack.
- Arreglo mínimo: sin refactorizar, sin renombrar, sin "mejorar de paso". Recompila tras cada uno.
- Error en un archivo fuera de tu tarjeta o que ya estaba en la línea base: no lo toques;
  repórtalo en HALLAZGOS, o `kanban_block` si te impide avanzar.
- 3 intentos sin progreso sobre el mismo error → `kanban_block` con la salida exacta.

## Prohibido
- Tocar archivos fuera de la tarjeta → `kanban_block` diciendo cuál y por qué.
- Cambiar endpoints, firmas, DTOs o esquema existentes, salvo que la tarjeta lo diga.
- Abstracciones especulativas: interfaz con una sola implementación (salvo que sustituya una
  frontera real en tests), factory de un producto, flag u opción que nadie usa, wrapper que solo delega.
- Dependencias nuevas.
- Instalar fuera del repo algo que el repo **no declara** (un SDK, un paquete global, otra
  versión de una herramienta): `kanban_block` diciendo qué falta y qué propones. Lo que el repo sí
  declara (los navegadores de su versión de Playwright, las dependencias de su lockfile) puedes
  instalarlo si falta; dilo en tu entrega (PENDIENTE: "instalé <qué>").
- **Silenciar en vez de arreglar:** desactivar warnings o reglas, saltar, borrar o debilitar
  tests, relajar configuración de calidad, forzar tipos para callar al compilador.
- Commit, push, reset, clean.

## 4. Autorrevisión antes de pedir revisión
Lo mismo que el revisor bloquearía; arréglalo tú y ahorra una ronda.
- [ ] `git status --porcelain`: solo aparecen archivos de la tarjeta (los nuevos `??` incluidos).
- [ ] Compila sin errores y sin warnings nuevos de las familias que indica el módulo.
- [ ] Cada criterio tiene su test, visto en RED (por aserción) y luego en GREEN; los "en
      navegador", su prueba E2E. App detenida y puerto libre.
- [ ] Suite = línea base. Formateador del repo sin cambios pendientes, si existe.
- [ ] **Propagación:** si agregaste un campo o regla, llega a todos sus caminos (modelo →
      persistencia → DTO → mapeo/proyección → validación → creación Y actualización →
      consumidores). Si corregiste un bug, el arreglo está en la función compartida y revisaste
      TODOS sus llamadores.
- [ ] **Limpieza objetiva:** sin código comentado o muerto, sin imports/variables sin uso, sin
      depuración olvidada, sin lógica copiada que ya exista en el repo (búscala antes de escribir
      un helper), sin números o textos mágicos repetidos, sin nombres sin significado.
- [ ] **Simplicidad:** retornos tempranos en vez de anidar más de 3 niveles; sin ternarios
      anidados; constantes con nombre; código nuevo que no parte un bloque que va junto.
- [ ] **Errores:** nada atrapado y convertido en "vacío" sin registrar; "no existe" es
      no-encontrado, no vacío; varias escrituras en transacción.
- [ ] Nada de lo "Prohibido".

## 5. Al terminar
- En Kanban: `kanban_request_review` con `reviewer="revisor"`, `summary` = el bloque de entrega
  y `metadata` = {"changed_files": [...], "tests_run": [<comandos reales>], "residual_risk":
  [<lo no verificado>], "mutations": ["<archivo:línea> <qué rompiste> → <test> rojo: <aserción>"],
  "e2e": {…} si la tarjeta trae E2E (formato en `modo-feature/references/e2e.md`),
  "verified_external": ["<Paquete> <versión> · <Tipo.Miembro>: <qué hace>
  (repo | fuente | .hermes.md | binario)"]}. Así el revisor y el orquestador no repiten la descompilación.
  Paquete y versión se copian tal cual del `PackageReference` del `.csproj` que lo usa (no de
  la DLL ni de memoria): si no coinciden, el revisor descompila de nuevo. En cada ronda repite
  la lista completa, no solo lo nuevo.
- En PENDIENTE: lo que la línea base ya traía roto y lo que no pudiste verificar.
- Después de `kanban_request_review` **termina tu turno**: no comentes ni toques la tarjeta (un
  comentario queda viejo en cuanto el revisor avanza y confunde al orquestador). Todo lo que
  quieras decir va en el `summary`.
