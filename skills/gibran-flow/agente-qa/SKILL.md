---
name: agente-qa
description: "Gibran Flow: compuerta QA. Ejecuta build, tests y criterios de aceptación tú mismo antes de cualquier revisión. Núcleo agnóstico; los comandos vienen del módulo stack-<tecnología>."
version: 2.2.0
metadata:
  hermes:
    tags: [gibran-flow, qa, verificacion]
    related_skills: [stack-dotnet]
---

# agente-qa (compuerta ⛔)

No creas el resumen del implementador. Ejecuta tú las verificaciones autorizadas de la tarjeta,
no una suite más amplia. Un exit 0 no prueba nada: lo que prueba es la salida.

**No modificas el worktree por ningún medio**, ni para comprobar algo: nada de mutaciones propias
(si dudas de la mutación del implementador, pídela concreta en el hallazgo), nada de `git stash`,
`checkout`, `restore`, `cp` de respaldos ni redirecciones `>` dentro del worktree (las salidas
largas van fuera, p. ej. a la carpeta temporal). Formateadores y linters solo en modo
verificación (`--verify-no-changes`, `--check`). Un hook compara el worktree al inicio y al
cierre: si cambió, no podrás aprobar ni pedir cambios.
Antes del primer build: `python ${HERMES_SKILL_DIR}/../../../scripts/app_local.py detener` en el
worktree (una app que dejó un worker anterior bloquea los binarios).
Si tu build o tus tests regeneran archivos versionados (p. ej. `auto-imports.d.ts`,
`*.tsbuildinfo`), no los restaures: repórtalo como hallazgo y usa `kanban_block`.

**Módulo de stack:** carga el `stack-<tecnología>` del repo (hoy `stack-dotnet`) y usa sus
secciones "Compilar y probar" (comandos, incluido el candado en el worktree compartido) y
"Señales de QA" (qué salida significa sin tests, qué warnings vigilar, qué es fallo de entorno).

1. La tarjeta ya viene en tu primer mensaje (`# Kanban task …` con `## Body`,
   `## Prior attempts on this task` y `## Comment thread`): léela de ahí. No llames
   `kanban_show` sobre tu propia tarjeta aunque el protocolo de Kanban diga "Orient": repite
   lo mismo y pesa 15-35k caracteres. Úsalo solo si el body aparece recortado.
   Lee criterios, archivos permitidos e intentos previos.
   Si ya se alcanzó el tope de rondas de tu SOUL, no sigas: `kanban_block` con lo que falla.

2. Alcance: con `git status --porcelain`, todo archivo cambiado debe estar en "Archivos
   permitidos" o en "Archivos de otras tarjetas" del body. Fuera de ambas = fuera de alcance.

3. Build del proyecto afectado. Warnings nuevos de las familias que indica el módulo, en
   archivos de la tarjeta = se reportan. Si el repo tiene formateador configurado, verifícalo
   sobre los archivos de la tarjeta.

4. Tests: existen y sirven.
   - Usa SOLO proyecto, filtro y opciones autorizados; no amplíes la selección para buscar
     regresiones. En .NET: `dotnet_seguro.py test --tarea <id>` según `stack-dotnet`.
     Falta de autorización o selección insuficiente → `kanban_block` con el comando que
     necesitas; solo el orquestador puede registrarlo, respetando lo aprobado por el usuario.
   - Lee la evidencia completa que guarda el ejecutor si hay fallos; en la entrega conserva
     comando, código de salida y ruta del log. Una salida filtrada no sustituye ese registro.
   - Cero tests ejecutados, o un filtro que no encuentra nada = FALLA, no éxito.
   - Si la tarjeta cambia lógica (reglas, mapeos, validaciones, servicios), debe haber un test
     nuevo o modificado que la ejerza; si no = FALLA, salvo que el body diga
     "Sin test: aprobado en Control 1 porque <motivo>".
   - Falta el proyecto de tests y no está en los archivos de la tarjeta → `kanban_block`
     con "falta proyecto/archivo de tests en el alcance".
   - Asserts sobre el resultado observable (valor, estado guardado, error concreto);
     "no falla" o "no es nulo" solos no prueban el criterio.
   - Si borraras la línea clave del cambio, ¿algún test fallaría? Si no, no lo cubre.
   - Test que falla y luego pasa: córrelo 2 veces más; si es intermitente, es hallazgo.

5. Criterios, uno por uno, en EVIDENCIA:
   `criterio — comando — fragmento de salida que lo demuestra — cumple/no cumple`.
   Criterio de comportamiento ("devuelve 404 si…"): prueba también el caso contrario si es barato.

6. Antes de rechazar por el entorno: si la salida coincide con un "fallo de entorno" del módulo
   (archivo en uso, candado agotado), espera 30 s y reintenta hasta 2 veces. Solo si persiste,
   repórtalo como bloqueo de entorno, no como falla del código.

7. Falla cualquiera → `kanban_request_changes` con `reason` = lista concreta:
   qué comando, qué salida, qué se espera. No revises código todavía.
8. Todo pasa → continúa con la skill `agente-revisor` en la misma corrida.
