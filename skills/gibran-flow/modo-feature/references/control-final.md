# Control final (plantilla fija)

Antes de escribirlo corre el cierre y pega su salida tal cual en la sección 7:

    python ${HERMES_SKILL_DIR}/../../../scripts/cierre.py --worktree "<ruta>" --rama <rama> \
        --modo feature|bug|nuevo --riesgo BAJO|ALTO --e2e "<arnés | manual | no aplica>"

El script cuenta tarjetas y revisiones del Kanban, alerta si alguna tarjeta terminó sin
aprobación del revisor o si queda una app corriendo, calcula el costo (solo si la marca de
/costos-inicio es de esta tarea), escribe la fila en metricas/tareas.md e imprime el comando de
`integrar.py` con las rutas reales. No calcules ni escribas nada de eso a mano.
Si sale una ALERTA, resuélvela o preséntala como hallazgo abierto antes de pedir la aprobación.

## Al aprobarlo el usuario: integrar
Corre el comando de `integrar.py` que imprimió el cierre. Pasa los cambios del worktree a la rama
de la que salió (la abierta en el repo principal: dev, una feature, la que sea) como cambios
**staged, sin commit**, y borra el worktree y su rama. Si falla (repo principal con cambios, rama
de origen distinta, app viva, conflicto), no toca nada: dile al usuario el motivo tal cual y no lo
rodees. Si sale bien, dile la rama y que el commit es suyo (`git diff --cached` y `git commit`).
Nunca commitees ni hagas push.

## Secciones, en este orden
1. **Qué cambió:** en 3-6 líneas, en términos del usuario. Cambios de contrato en negritas.
2. **Evidencia:** cada línea dice quién la produjo (orquestador, implementador, revisor,
   explorador): build y tests (comando y resultado), mutaciones, E2E (corridas, screenshots),
   verificaciones en DEV. Ej.: "mutación de la guarda → rojo (implementador; el revisor revisó
   que fuera la línea clave)".
3. **Hallazgos abiertos:** los que quedan del revisor o tuyos, con archivo:línea.
4. **Riesgos aceptados:** solo lo no verificable (paso 10), con este formato:
   `<qué> — no verificable porque <razón concreta> · intenté: <qué se hizo, o "nada: <por qué>">`.
   "No lo verifiqué" no es razón.
5. **Despliegue:** copiado del plan y revisado contra lo que se hizo. Si dice "solo código", di
   por qué (p. ej. "sin esquema, sin datos sembrados, sin configuración nueva").
6. **Memoria del repo:** ruta de la nota que dejó el escriba (`docs/hermes/notas/…`) y qué cambió
   en `.hermes.md`. Sin nota no hay Control final: llama primero al escriba (paso 11).
7. **Cierre:** la salida de `cierre.py`.

## Antes de presentarlo
- ¿Corrió el escriba y está su ruta en la sección 6?
- ¿Algún riesgo aceptado se podía verificar leyendo, con un comando o en DEV? Mándalo al
  explorador antes de presentar.
- ¿Cada línea de evidencia dice quién la produjo?
- ¿La sección 5 coincide con lo que hicieron las tarjetas (esquema, datos sembrados, config)?
- ¿Cada afirmación de estado ("aprobada por el revisor", "no hay procesos") sale de una
  consulta o del cierre, no de memoria?
- ¿El cierre salió sin ALERTA, o la ALERTA está en hallazgos abiertos?
