---
name: modo-bug
description: "Gibran Flow: corregir un bug encontrando la causa raíz con un circuito de prueba que se pone rojo, hipótesis comprobables y un test de regresión. Cómo diagnosticar en references/diagnostico.md."
version: 2.2.0
metadata:
  hermes:
    tags: [gibran-flow, bug, debugging]
    related_skills: [dev-flow, agente-explorador, agente-implementador, modo-feature]
---

# modo-bug

Basado en `diagnosing-bugs` de Matt Pocock (MIT, github.com/mattpocock/skills).
Regla de oro: **sin un comando que se ponga rojo con este bug, no hay arreglo.** Y nada es
"causa confirmada" o "establecido" sin evidencia citada (comando, consulta, archivo:línea):
lo deducido es hipótesis.

## 1. Explorar (siempre, solo lectura)
`delegate_task` con brief de dev-flow §4, skill `agente-explorador`, objetivo = el síntoma
exacto del usuario (mensaje de error, entrada, salida esperada contra obtenida). Pídele además:
- **Clasificación:** lógica · estado/datos · entorno/configuración · contrato entre sistemas;
  determinista o intermitente.
- La función donde probablemente nace y **todos sus llamadores**.
- **Fallas silenciosas** en la zona (errores atrapados y convertidos en vacío, null, false).
- **Un ejemplo que sí funciona:** código hermano que hace lo mismo sin fallar.
Verifica 2-3 de sus citas tú mismo. Si dice que no es un bug (es la conducta esperada o falta
una feature) → `necesita-decisión` al usuario.

## 2. Diagnosticar (tú mismo, no un hijo)
Los hijos de `delegate_task` corren con un modelo barato; el diagnóstico es la parte difícil y
lo haces tú. Crea el worktree: `git -C <repo> worktree add ../<repo>.wt-<slug> -b bugfix/<slug>`
y sigue `skill_view("modo-bug", "references/diagnostico.md")` en ese worktree (rutas
absolutas). No corrijas. Para no llenar tu contexto: corre solo el test que importa y recorta
salidas largas (`| tail -40`, `grep`). El camino depende de la clasificación del explorador:
- **Lógica determinista** (el defecto se ve en el código: una condición al revés, un campo que no
  llega a la proyección, un caso sin manejar): puedes hallar la causa leyendo y comparando con el
  ejemplo que funciona. Dila como "causa por lectura (archivo:línea), sin rojo aún"; el rojo lo
  pone el implementador como primer paso de la tarjeta.
- **Estado/datos, entorno/configuración, contrato entre sistemas o intermitente:** evidencia
  ANTES de hipótesis (fase 1 de diagnostico.md). Ej.: "solo algunos registros salen mal" →
  una consulta en DEV que separe los buenos de los malos; "en mi máquina sí sale" → la misma
  entrada en los dos ambientes. Teorizar sin eso produce hipótesis seguras y falsas.
- **Filtro que se ve correcto y aun así salen registros de más o de menos:** revisa los
  filtros globales de la capa de datos (borrado lógico, multiempresa, filtros del ORM o de la
  librería) antes de culpar al entorno.
- **Hermanos, antes de recomendar alcance:** busca el patrón del defecto con grep en todo el
  repo, empezando por el mismo archivo y el mismo request (otros campos). Lista cada resultado
  con su destino: "se corrige", "no aplica porque …" o "decide el usuario". Por defecto se
  corrige todo el patrón; acotarlo lo decide el usuario. Ejemplos:
  - el mismo error en 9 handlers → se corrigen los 9, no solo el reportado;
  - un campo del request se corrige y otro campo del mismo request tiene el mismo defecto;
  - dos entidades nombradas "pendientes" sin buscar las otras 6 con el mismo mapeo;
  - unas acciones comparadas contra los permisos y otras no: compara todas.
- **Checkpoint de hipótesis:** antes de probarlas, muestra al usuario la lista ordenada (3-5).
  Si no responde, sigue con tu orden.
- Si no logras un comando rojo: muestra al usuario lo que intentaste y pide una de tres cosas
  (acceso al ambiente donde falla, un artefacto capturado y sin secretos, o permiso para
  instrumentar). No adivines la causa.

## 3. Reclasificar riesgo
Con la causa confirmada, aplica `dev-flow/references/riesgo.md` (solo puede subir).
Si el arreglo cambia un contrato (endpoint, DTO, esquema), dilo en negritas.

## 4. Corregir con el motor de modo-feature
Sigue `modo-feature` paso 3 (Kanban con QA y revisor; el riesgo decide plan y Control 1).
Diferencias:
- Rojo: si ya lo viste, en la tarjeta va "RED ya visto: `<comando>` — <salida>" y el
  implementador lo confirma. Si la causa fue por lectura, va "RED pendiente: <síntoma que el
  test debe afirmar>" y el implementador lo escribe primero; si no se pone rojo, la causa era
  otra: `kanban_block`.
- Criterio obligatorio: el arreglo va donde convergen los llamadores, no solo en el camino
  reportado. La lista de hermanos del paso 2 va en la tarjeta (campo "Hermanos"), con el
  comando grep usado.
- Criterio obligatorio: limpieza de `[DEBUG-` (`git grep "\[DEBUG-"` vacío) y de los
  arneses temporales.
- Si no hubo una costura correcta para el test (ver diagnostico.md, fase 5), va a PENDIENTE como
  hallazgo de arquitectura y el usuario lo acepta en el Control 1 o el Control final.

## 5. Escriba
`delegate_task` con skill `agente-escriba`. La nota lleva: categoría, causa raíz, hipótesis
descartadas, llamadores revisados y test agregado. Si la trampa puede repetirse en el repo,
propónla como regla del `.hermes.md`.

## 6. Pendientes y Control final
Como en modo-feature (pasos 10, 11 y 12: pendientes, escriba y Control final con la plantilla `modo-feature/references/control-final.md` y `scripts/cierre.py --modo bug`): vuelve a correr el comando rojo original (sin
minimizar) y muestra que ahora pasa.
