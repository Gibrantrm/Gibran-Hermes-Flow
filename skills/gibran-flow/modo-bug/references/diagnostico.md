# Diagnóstico de un bug

Adaptado de `diagnosing-bugs` de Matt Pocock (MIT). Trabajas en el worktree del bug.
No corriges el bug: entregas la causa confirmada y un test rojo. No commits.

## Secretos y datos
- Todo lo que muestres (comandos, salidas, logs, respuestas HTTP) va sin secretos: escribe
  `<REDACTED>` en su lugar. Las credenciales viven en variables de entorno, no en el comando.
- Datos personales enmascarados. BD: DEV por defecto; PROD solo SELECT con LIMIT y solo para
  confirmar el estado que dispara el bug.
- De un log o respuesta capturada, cita solo las líneas que dan la señal.

## Fase 1: un circuito que se pone rojo (lo más importante)
Obligatoria antes de hipótesis en bugs de estado/datos, entorno, contrato o intermitentes; en
lógica determinista, ver `modo-bug` paso 2. Si tienes un comando que se pone rojo con **este** bug, encontrarás la causa; sin él, leer código
no basta. Dedícale el mayor esfuerzo. Opciones, más o menos en este orden:
1. Test que falla en la costura que llega al bug (unitario, integración).
2. Petición HTTP contra la app corriendo en DEV.
3. Invocación por línea de comandos con una entrada fija, comparando contra una salida buena.
4. Repetir una entrada capturada (payload, evento) por el camino del código, aislado.
5. Arnés desechable: lo mínimo del sistema que ejecuta el camino del bug con una llamada.
6. Bucle de muchas entradas, si es "a veces sale mal".
7. Bisección: si apareció entre dos estados conocidos (commit, versión), automatiza
   `git bisect run`.
8. Diferencial: misma entrada en versión vieja y nueva (o dos configuraciones); compara.
9. Último recurso: un humano reproduce siguiendo pasos fijos y te pega la salida.

**Aprieta el circuito:** más rápido (solo el test que importa), señal más precisa (afirma el
síntoma exacto, no "no tronó"), determinista (fija reloj, semilla, datos).
**Intermitente:** la meta es subir la tasa de reproducción (repetir 100 veces, en paralelo,
con carga); 50% se puede depurar, 1% no. Sospechosos: concurrencia, caché, zona horaria.

**Terminada cuando** puedes nombrar UN comando, ya corrido al menos una vez (muestra la
invocación y la salida), que:
- [ ] recorre el camino real del bug y afirma el síntoma **del usuario**;
- [ ] da el mismo veredicto en cada corrida;
- [ ] tarda segundos;
- [ ] lo corres tú sin ayuda.
Si te descubres leyendo código para armar una teoría sin ese comando: detente.
**Si no se puede:** dilo, lista lo que intentaste y pide al usuario acceso, un artefacto o
permiso para instrumentar. No pases a la fase 3.

## Fase 2: reproducir y minimizar
- Confirma que el rojo es el síntoma que describió el usuario, no otro fallo cercano.
  Bug equivocado = arreglo equivocado.
- Repite: el rojo debe salir siempre (o con la tasa alta de la fase 1).
- **Minimiza:** quita entradas, llamadores, configuración, datos y pasos **uno a la vez**,
  corriendo el circuito tras cada corte. Termina cuando todo lo que queda es necesario
  (quitar cualquier cosa lo pone verde). Esa repro mínima será el test de regresión.

## Fase 3: hipótesis
- **Compara con el ejemplo que funciona** (lo trae el explorador): lista cada diferencia entre
  el camino roto y el bueno, por pequeña que sea. Las diferencias son candidatas.
- Escribe **3 a 5 hipótesis ordenadas** antes de probar ninguna (con una sola te casas con la
  primera idea). Cada una debe poder fallar:
  "Si la causa es X, entonces cambiar Y hará que desaparezca / cambiar Z lo empeorará."
  Sin predicción, no es hipótesis: descártala o afínala.
- Revisa también los patrones típicos de código hecho con IA: campo nuevo que no llega a la
  proyección o `Select`; dos caminos y solo uno corregido; validación que nunca corre.

## Fase 4: instrumentar y confirmar
- Cada sonda prueba una predicción de la fase 3. **Una variable a la vez.**
- Preferencia: depurador o REPL > logs puntuales en las fronteras que separan hipótesis >
  nunca "loguear todo y buscar".
- Etiqueta cada log temporal con un prefijo único, p. ej. `[DEBUG-a4f2]`; al final se quitan con
  una búsqueda.
- Observa antes de cambiar: `git log -L` / `git blame` de la zona, consulta en DEV del dato
  que dispara el bug.
- Rendimiento: no logs; mide una línea base (cronómetro, plan de consulta) y luego bisecta.
- **Regla de tres:** si 3 hipótesis o intentos seguidos fallan, deja de probar parches. Lo más
  probable es que el modelo mental (o el diseño) esté mal: vuelve a la comparación con el
  ejemplo que funciona y repórtalo como posible problema de arquitectura.
- El test sigue rojo tras "confirmar" una causa = la hipótesis estaba mal.

## Fase 5 (la hace el implementador): test de regresión en la costura correcta
Una costura es correcta si el test ejercita el patrón real del bug como ocurre en el llamador.
Si la única disponible es demasiado superficial (un llamador cuando el bug necesita varios, un
test unitario que no reproduce la cadena; un sustituto en memoria cuando el bug depende del
motor de BD real), el test da falsa confianza. **Que no exista costura correcta es un hallazgo:**
anótalo en PENDIENTE.
Con costura correcta: la repro mínima se vuelve test → se ve rojo por la aserción → se
corrige → verde → se vuelve a correr el circuito original sin minimizar.

## Entrega
Bloque de `dev-flow/references/formato-entrega.md` con HALLAZGOS:
**Circuito** (comando + salida, sin secretos) · **Repro mínima** · **Hipótesis** (cada una:
confirmada / descartada, con la evidencia) · **Causa raíz** (archivo:línea) · **Llamadores y
hermanos** con el mismo patrón · **Costura** para el test (o por qué no hay) · **Limpieza
pendiente** (logs `[DEBUG-…]` y arneses que dejaste, con su ruta).
