# Pruebas en navegador (E2E)

Los casos de prueba son los criterios "en navegador" del plan, aprobados en el Control 1.

**Qué es un arnés E2E:** una librería de pruebas de navegador (Playwright, Cypress, Selenium,
EasyTest…) + su configuración o fixture (URL base, login) + una forma de marcar o filtrar esas
pruebas. Que falten ayudas para ESTA pantalla no significa que no haya arnés: se crean en la
primera tarjeta con E2E de esa pantalla.

## Reglas de una buena prueba E2E (tomadas de ECC `e2e-testing`)
- Busca elementos por rol, texto visible o `data-testid`; nunca por CSS frágil (clases de estilo,
  posiciones, XPath).
- Nada de esperas fijas (`sleep`, `WaitForTimeout`): espera la condición (que aparezca el texto,
  que el botón se habilite, que llegue la respuesta).
- Independiente: prepara sus propios datos o solo lee; no depende de otra prueba ni del orden.
- La aserción es la del criterio (el texto o el elemento que el usuario debe ver), no "la página
  cargó".
- Guarda un screenshot del estado final y falla si hay errores en la consola del navegador. Si el
  arnés no trae esas ayudas, la primera tarjeta con E2E las agrega. Los screenshots van a una
  carpeta que git ignora (p. ej. `TestResults/`), nunca al commit; el revisor solo los mira.
- Reutiliza las ayudas del arnés (login, abrir pantalla, combos); si falta una, agrégala ahí.

## Qué E2E se corren
Solo las de esta feature: el filtro de la tarjeta y el acumulado (por nombre de clase o archivo).
Nunca la categoría completa ni las E2E de otras features: pueden escribir en DEV (altas,
importaciones) y su resultado no dice nada de esta tarea. Si el filtro de la tarjeta trae una
categoría entera o no viene, no lo adivines: `kanban_block` pidiendo el filtro.

## La app: siempre con app_local.py
Script: `hermes-flow/scripts/app_local.py` (desde una skill:
`${HERMES_SKILL_DIR}/../../../scripts/app_local.py`). Corre desde el worktree:
- `python <script> detener` **al empezar tu tarjeta**: limpia apps que dejó un worker anterior.
- `python <script> iniciar --puerto auto [--copia <carpeta de salida>] [--env N=v] -- <comando>`:
  toma un puerto libre del rango de los agentes (51300-51399, lejos de los de desarrollo), lo
  imprime como `PUERTO=<n>`, lanza la app, espera a que responda y registra el árbol de procesos.
  `{puerto}` y `{copia}` se sustituyen en el comando. Pásale el puerto a las pruebas por la
  variable del arnés (p. ej. `E2E_BASE_URL`).
- `--copia`: si la app bloquea sus propios binarios mientras corre (.NET en Windows), cópiala a
  la temporal y córrela desde ahí: el worktree queda libre y otras tarjetas compilan en paralelo.
  `detener` borra la copia.
- **Puertos fijos.** Si la app solo escucha en un puerto (fijado en código) o otro componente la
  busca en uno (un frontend con la URL de la API en `.env`, un gateway con sus rutas), usa
  `--puerto <n>`; si está ocupado (quizá la instancia del usuario), falla sin compartirlo ni
  matarlo: dilo, no lo rodees. Prefiere mover la referencia (p. ej. `--env
  VITE_API_BASE_URL=https://localhost:{puerto}`) a usar el puerto fijo. El plan dice cómo se
  conectan los componentes en la prueba.
- **Login externo (OIDC):** el proveedor solo regresa a los puertos registrados. Las E2E que lo
  necesiten simulan el login (p. ej. interceptando la petición) o usan un puerto registrado; no
  inventes registros en el proveedor.
- **Pasa `--tarea <id-de-tu-tarjeta>` a `iniciar` y a `detener`**: el shell de los workers no
  siempre trae `HERMES_KANBAN_TASK`, y sin dueño tu app queda como "desconocida": protegida de
  los `detener` ajenos mientras haya tarjetas activas, pero tu propio `detener` tampoco la podrá
  cerrar. Con `--tarea` queda a tu nombre y tu `detener --tarea` sí la mata.
- `python <script> detener` **al terminar**: mata el árbol completo y confirma el puerto libre.
  No toca la app de otra tarjeta que sigue corriendo o en revisión (paralelo en el mismo
  worktree). Lo que escucha en el rango sin registro solo se reporta: no se puede demostrar que
  sea de esta tarea; no lo cierres ni borres su posible copia. No uses taskkill,
  Stop-Process ni process_manage para la app: dejan hijos vivos o los bloquea la guardia. Si
  `detener` reporta algo vivo, dilo; no le pases el `taskkill` al usuario.
- Una sola app a la vez. La salida de la app queda en la carpeta temporal (el script dice dónde),
  nunca en el worktree.
- Con qué comando se levanta y cómo se corren las pruebas: guía del repo (`CLAUDE.md`,
  `docs/…e2e…`) si existe; si no, la sección "Pruebas E2E" del módulo de stack.

## Evidencia obligatoria
- Implementador: en el `metadata` de `kanban_request_review`, `"e2e": {"red": "<comando y
  aserción que falló con la app SIN el cambio>", "green": "<comando y resultado>",
  "screenshots": ["<rutas>"], "consola": "<sin errores | errores vistos>"}`.
- Revisor: sin `e2e.red` = ALTO "prueba sin evidencia de que detecta el fallo" (igual que la
  mutación); sin screenshot o sin revisión de consola = MEDIO. En su resumen dice cuántas
  corridas hizo y qué vio en los screenshots.
