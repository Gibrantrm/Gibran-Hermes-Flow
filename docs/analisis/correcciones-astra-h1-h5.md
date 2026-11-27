# Correcciones Astra H1–H5

Estado al 26-nov-2026: las cinco correcciones están implementadas en este repositorio.
Este documento describe el comportamiento de esta distribución pública; no incorpora
registros privados de las pruebas originales. El diagrama de Pages es un resumen conceptual,
no la referencia operativa de estos controles.

## Cambios

| Hallazgo | Corrección | Implementación y evidencia |
|---|---|---|
| H1: detener procesos sin atribución | `app_local.py detener` solo detiene las apps registradas que le corresponden. Los listeners sin registro se reportan; no se matan ni se borra una copia deducida por su puerto. | `scripts/app_local.py`; `tests/test_app_local.py`, caso `test_detener_reporta_sin_tocar_proceso_ni_copia_sin_registro`. |
| H2: duplicación del flujo de bug | `modo-bug` reutiliza su worktree de diagnóstico al entrar en `modo-feature`, conserva entrevista/plan/Control 1 y ejecuta una sola secuencia de pendientes, escriba y Control final. | `skills/gibran-flow/modo-bug/SKILL.md`, sección 4; `modo-feature/SKILL.md`, sección 3. |
| H3: identidad de métricas | El cierre identifica la tarea con una huella de su primera tarjeta, no por igualdad de cifras. Una nueva corrida actualiza la fila preservando fecha y defectos; otra tarea conserva su propia fila. Sin tarjetas, con identidad duplicada o con fila inválida, alerta y no escribe. | `scripts/cierre.py`; `tests/test_cierre.py`. |
| H4: revisión con cambios en paralelo | Una tarjeta paralela no exime archivos ausentes de la foto inicial. Si cambia el worktree, el revisor no puede aprobar ni pedir cambios sobre esa revisión; puede bloquear. No se reemplaza silenciosamente la foto. | `hooks/guardia_revision.py`; `tests/test_guardia_revision.py`, clase `TestRevisionConSnapshots`. |
| H5: tests fuera del alcance aprobado | `dotnet_seguro.py test` exige tarea, worktree y coincidencia con un comando registrado por el orquestador: proyecto, filtro y opciones. Conserva evidencia completa antes de resumir la consola. | `scripts/dotnet_seguro.py`; `tests/test_dotnet_seguro.py`, clase `TestAlcanceTests`; guardias de build/rutas y sus tests. |

Para H3, conserva la primera tarjeta aunque esté archivada y el comentario HTML de identidad
al editar los defectos. Las filas históricas sin identidad no se reasignan por similitud.
Para H4, una revisión bloqueada por cambios necesita una nueva revisión sobre el worktree
estable, no una aprobación forzada.

## Operación de H5

1. El plan especifica los comandos de baseline/TDD, QA y E2E acumuladas que realmente necesita
   cada tarjeta. No autoriza una suite completa por costumbre.
2. El orquestador crea las tarjetas con tests .NET usando `initial_status: "blocked"`.
3. Con el id devuelto, registra cada comando aprobado, sin ejecutarlo:

   ```text
   python scripts\dotnet_seguro.py autorizar-test --tarea <id> --worktree "<worktree>" -- tests\Tests.csproj --filter "FullyQualifiedName~MiClaseTests" --nologo
   ```

4. Solo cuando todos los registros terminan con código 0, llama a `kanban_unblock`.
   Las dependencias `parents` siguen aplicando.
5. Implementador, revisor y orquestador ejecutan desde la raíz de ese worktree:

   ```text
   python "<hermes-flow>\scripts\dotnet_seguro.py" test --tarea <id> tests\Tests.csproj --filter "FullyQualifiedName~MiClaseTests" --nologo
   ```

`<hermes-flow>`, `<worktree>` e `<id>` son valores del entorno de quien ejecuta, no rutas
personales que deban guardarse en el repo. `--tarea` va antes del proyecto; suple
`HERMES_KANBAN_TASK` cuando no llega a la terminal. Si ambas identidades están presentes,
deben coincidir.

Se requiere un `.csproj` dentro del worktree y un `--filter` no vacío. La coincidencia incluye
el orden y la escritura de las opciones. Se admiten `--nologo`, `--no-build`, `--no-restore`,
configuración, framework, verbosity y logger; las formas exactas están en `stack-dotnet`.
Se rechazan soluciones, filtros duplicados, archivos de respuesta, propiedades MSBuild,
`--settings` y argumentos adicionales de VSTest tras `--`.

Si falta autorización o hace falta cambiar un comando, el worker bloquea la tarjeta:
no puede registrarse permisos mediante el comando de autorización. El orquestador resuelve
con el usuario cualquier cambio de lo aprobado y registra la selección correspondiente.
Las tarjetas de corrección tienen autorización propia; no la heredan de su padre.
En diagnóstico de bugs previo a Kanban, `modo-bug` permite un identificador único
`diag-<identificador>` tras acordar la selección con el usuario; luego se registra de nuevo
con el id real de la tarjeta.

### Evidencia y códigos de salida

El estado local vive en `%LOCALAPPDATA%\hermes\gibran-tests`, fuera del worktree:

- `autorizaciones`: comandos permitidos, tarea y worktree.
- `ejecuciones`: un par `.json`/`.log` por corrida, con comando, tarea, worktree, fechas,
  código de salida y stdout/stderr completos. Las repeticiones no sobrescriben otra corrida.

Si no puede preparar la evidencia, no lanza tests. Un error de lanzamiento queda explícito;
un código nulo no significa éxito. Una vez ejecutado el proceso, se conserva su código de
salida; errores del propio ejecutor se reportan aparte.
Código 2 puede indicar un bloqueo de alcance y 75 un timeout del candado; lee siempre el
mensaje, porque un proceso hijo también puede devolver esos números.
No publiques los logs sin revisar su contenido: pueden contener datos sensibles.

### Límites

Este control cubre la ruta normal de tests .NET del flujo, no una terminal arbitraria.
No es un sandbox ni prueba que el código de un test autorizado no escriba datos.
Las credenciales y permisos de BD siguen siendo controles independientes.
MAUI/Maestro fue objeto de una propuesta de adaptación, pero no se implementa en H1–H5:
`maestro test` no queda protegido por esta autorización .NET.

## Verificacion focalizada

Desde la raíz del repo, en PowerShell, con `$python` apuntando a tu Python de Hermes:

```powershell
& $python -B .\tests\run_app_local.py
$pythonBase = & $python -c "import sys; print(sys._base_executable)"
Push-Location .\tests
try {
    & $pythonBase -B -m unittest test_cierre test_guardia_revision test_dotnet_seguro test_guardia_build test_guardia_rutas -v
} finally {
    Pop-Location
}
```

Se usa el intérprete base para que los helpers de candado se ejecuten como procesos directos,
sin el launcher de un entorno virtual de Windows entre el test y el PID que termina.
Esta selección usa apps y ejecutables falsos, registros temporales y respuestas de BD
simuladas; no ejecuta pruebas de negocio ni las fixtures de integración que crean commits
y escriben SQLite. Los helpers de apps se detienen por `app_local` y los demás por su PID.
H2 se verificó además mediante lectura del recorrido y una sonda de comprensión de las
instrucciones; no se presenta como un test de ejecución de Hermes.

Esta selección no equivale a haber ejecutado toda la suite ni a repetir las pruebas completas
del flujo en repositorios de negocio. Las pruebas existentes de procesos pueden emitir
`ResourceWarning`; no se confunden con nuevos fallos de las correcciones.
