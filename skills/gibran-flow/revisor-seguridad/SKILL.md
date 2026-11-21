---
name: revisor-seguridad
description: "Gibran Flow: módulo de seguridad por tarjeta, agnóstico al lenguaje. Lo carga agente-revisor bajo demanda cuando el diff cruza una frontera de confianza; mismas severidades y veredicto. Solo lectura."
version: 1.0.0
metadata:
  hermes:
    tags: [gibran-flow, code-review, seguridad]
    related_skills: [agente-revisor, revisor-csharp]
---

# revisor-seguridad

Profundiza el punto "Seguridad" del Eje 1 de `agente-revisor`: mismas severidades, filtro y
veredicto; aquí solo va lo propio de seguridad. Las APIs concretas viven en `revisor-<tecnología>`.
Material adaptado de Cloudflare `security-audit` (modo guía, sin su flujo de auditoría completa).

## Cuándo cargarla
Si el diff de la tarjeta toca cualquiera de estos puntos:
- autenticación, autorización, roles, sesiones, cookies, tokens o claves de API;
- endpoints, rutas, handlers o consumidores de mensajes nuevos o modificados;
- archivos o rutas del sistema (leer, escribir, subir, descargar, descomprimir);
- entrada del usuario que llega a consultas, comandos, plantillas, expresiones, URLs o redirecciones;
- datos de varios tenants, empresas o usuarios (filtros por dueño, listados, exportaciones, cachés);
- secretos o configuración (cadenas de conexión, llaves, flags, modo depuración, CORS);
- dependencias nuevas, archivos de build o de CI;
- llamadas a servicios externos, webhooks (entrantes o salientes) o a un LLM.
Si no toca ninguno, no la cargues. Si la cargas, dilo en el resumen: "seguridad: revisada".

## Límites (solo lectura)
- No ejecutas código del repo para probar un exploit. No levantas servicios ni llamas a endpoints
  desplegados, APIs externas, colas o bases compartidas. No usas credenciales reales.
- No instalas ni descargas nada, tampoco escáneres que salen a la red.
- No supongas presente ni ausente un control que vive fuera del repo actual.

## Cuando el control vive en otro repo o fuera del código
Antes de marcar algo como "no se puede saber", sigue la escalera de
`dev-flow/references/repos-relacionados.md`: documentación del repo → "Repos relacionados" del
`.hermes.md` y catálogo → clon local en solo lectura (encontrado con `local/workspace.yaml`).
- Si lo encuentras: verifica ahí el control (filtro por empresa, autorización, validación del
  token) y cita archivo:línea de ese repo.
- Si no aparece: `[NECESITA VALIDACIÓN]` con la pregunta concreta ("¿en qué repo está la API
  que consume esta app?"). Si de confirmarse el problema sería CRÍTICO → `kanban_block` con esa
  pregunta, para que el usuario responda; si no, va a PENDIENTE y la tarjeta sigue.
- Lo que solo existe desplegado (proxy, gateway configurado, IdP, firewall, versión real de una
  librería) es siempre `[NECESITA VALIDACIÓN]`.

## Método por tarjeta (no es auditoría del repo)
1. **Fronteras tocadas.** Por cada punto de entrada del diff anota quién puede llamarlo (anónimo,
   usuario, otra empresa, admin, otro servicio, webhook), qué recurso toca y qué control lo protege.
   Busca el control donde vive de verdad: atributo/política, middleware, filtro global, la consulta.
2. **Entrada → destino.** Sigue cada valor que controla el llamador (ruta, query, body, encabezados,
   nombre de archivo, nombre de campo/orden/filtro) hasta donde se usa. Incluye claves y nombres,
   no solo valores, y el segundo orden: un dato guardado "limpio" que después se usa como ruta,
   URL, plantilla o consulta.
3. **Autorización por recurso.** En cada lectura, escritura, borrado, conteo o listado por id,
   comprueba que la consulta misma ate el recurso al usuario/empresa/tenant autenticado. Un campo
   tenant en la entidad no es aislamiento, y estar autenticado no es estar autorizado.
4. **Caminos paralelos.** La seguridad efectiva es la del camino más débil. Compara con los
   hermanos: crear y actualizar, uno y lote, importar/exportar, admin, job de fondo, versión anterior.
5. **Fallas y defaults.** ¿Qué pasa si falta la config, el token no trae el claim, el servicio
   externo falla o la verificación lanza? Si sigue sin verificar (falla abierta), es hallazgo.
6. **Copias derivadas.** Si el dato protegido llega a logs, caché, búsqueda, exportación,
   notificación o respuesta de error, la copia debe respetar el mismo alcance.
Detente en cuanto el invariante quede resuelto en un sentido o en otro.

## Qué buscar (conceptos)
**Control de acceso**
- IDOR: un id de ruta/body/query que se carga o modifica sin filtrar por dueño/empresa/tenant =
  CRÍTICO aunque el endpoint exija login.
- Endpoint nuevo sin autorización cuando sus vecinos la tienen. Permiso más débil que el de otro
  camino que logra el mismo efecto.
- Asignación masiva: el body fija campos que el llamador no debe controlar (dueño, tenant, rol,
  estado, precio, aprobado).
- Lote, importación o exportación sin permiso verificado por elemento. Cambio de rol, membresía
  o empresa propia sin permiso de administrador.

**Identidad y sesión**
- Token aceptado sin verificar firma, emisor, audiencia o expiración, o con algoritmo/llave
  elegidos por el propio token.
- Identidad tomada de un encabezado, parámetro o body no verificado (usuario o tenant en el
  request) en lugar de la sesión verificada.
- Tokens de recuperación, invitación o enlace: aleatoriedad criptográfica, atados a usuario y
  acción, de un solo uso y con expiración. Logout o cambio de contraseña invalidan la sesión anterior.
- Autenticación por cookie: mutaciones sin protección anti-CSRF efectiva. Con token bearer no aplica.

**Inyección y destinos peligrosos**
- Consultas (SQL, NoSQL, LDAP, búsqueda) armadas con texto del usuario. Nombres de columna, orden
  o filtro sin lista permitida.
- Comandos del sistema, evaluación dinámica, plantillas compiladas a partir de texto del usuario.
- Path traversal: ruta o nombre de archivo del usuario (incluidos nombres dentro de un zip) sin
  normalizar ni verificar que queda dentro de la carpeta permitida.
- SSRF: el servidor pide una URL que controla el usuario (webhook, callback, importar desde URL)
  sin lista permitida. Incluye las redirecciones.
- Redirección abierta (`returnUrl`, `next`, `redirect`) a un destino externo sin validar.
- Deserialización en la que el payload elige qué tipo se instancia. Encabezados de respuesta
  (Location, Set-Cookie) armados con texto del usuario.

**Secretos y criptografía**
- Secreto real en el código, en config versionada, logs, URLs o respuestas. Un identificador
  público llamado "key" no es un secreto.
- Aleatoriedad no criptográfica para tokens o códigos. Comparación de secretos o firmas que no es
  de tiempo constante.
- Webhook entrante sin verificar la firma o sin protección contra repetición (timestamp/nonce).
- Cripto casera, cifrado sin autenticación, IV fijo, error de cripto que acaba en "sin cripto".

**Exposición y depuración**
- Mensaje de excepción, traza, SQL, rutas internas o versión en la respuesta al cliente: ALTO.
- Endpoints o modo de depuración/admin/diagnóstico activables sin protección. CORS que refleja
  cualquier origen y además permite credenciales.
- Respuesta distinta para "no existe" y "sin acceso" sobre recursos de otro tenant: MEDIO.

**Límites de recursos** (solo si un usuario puede afectar a otros o al servicio compartido)
- Tamaño de página, lote, archivo, cuerpo, profundidad o expansión tomados del request sin tope.
- Descompresión sin límite, regex con backtracking sobre la entrada, trabajo caro antes de
  autenticar, llamadas pagadas (LLM, SMS, correo) que se pueden disparar sin cuota.
- Antes de reportar, busca topes en el parser, el framework, la cola o la configuración.

**Cadena de suministro**
- Dependencia nueva que la tarjeta no pidió: ALTO. Si se pidió: origen, versión fijada y scripts
  de instalación; el escaneo de vulnerabilidades va como NECESITA VALIDACIÓN.
- Cambio en CI/build que expone secretos a código no confiable o descarga herramientas sin
  versión fija.

**LLM** (si el backend llama a un modelo)
- Lo que devuelven el modelo y sus herramientas es entrada no confiable: aplican las mismas reglas.
- Herramienta que actúa con credencial de servicio sin volver a verificar el permiso del usuario
  sobre ese recurso. Prompt armado con datos de otro usuario o tenant.
- La inyección de prompt sola no es hallazgo, y un prompt de sistema no es un control.

## Severidad en seguridad
- **CRÍTICO:** ejecución de código o comandos, inyección en consultas, lectura o escritura de datos
  de otro usuario/empresa/tenant, salto de autenticación, secreto real expuesto.
- **ALTO:** se derrota por completo un control explícito con consecuencia real pero alcance
  acotado: escalada de rol dentro del tenant, token sin validar audiencia o expiración, detalles
  internos en la respuesta, recurso sin tope que tumba el servicio compartido.
- **MEDIO:** debilita sin derrotar, requiere precondiciones raras o la evidencia de la ruta es parcial.
Pregunta decisiva: ¿el control se derrota o solo se debilita? Si no puedes nombrar el daño
concreto, la severidad es menor de lo que parece. No infles: una excepción no es ejecución de
código, el trabajo propio no es caída del servicio y actuar sobre lo propio no es escalada.

## Filtro de evidencia (se suma al del núcleo)
Un hallazgo de seguridad CRÍTICO o ALTO necesita los cuatro elementos:
1. **Quién:** el principal de menor confianza y lo que ya puede hacer (anónimo, usuario de empresa A).
2. **Qué:** el recurso o la acción afectados (registros de la empresa B, archivo fuera de la carpeta).
3. **Frontera:** el control que debía impedirlo y por qué no actúa en este camino (archivo:línea).
4. **Ruta:** entrada (archivo:línea) → propagación → destino (archivo:línea), sin una capa visible
   que la frene.
- Si falta uno pero la ruta es real, es MEDIO. Si falta la ruta o el principal, se descarta.
- Si lo único que falta es un hecho fuera del repo, sigue la sección "Cuando el control vive en
  otro repo".

**No reportar (falsos positivos de seguridad):**
- Desviación de checklist sin nadie afectado: encabezado, flag de cookie, rate limit, MFA o
  "buena práctica" que falta.
- Endurecimiento sin frontera cruzada. Autoimpacto: el usuario solo se afecta a sí mismo.
- Lo que ya frena el framework o una capa visible (escape por defecto, parámetros, filtro global
  de tenant, validador del pipeline). Rastréalo antes de descartar.
- Endpoints públicos por diseño o porque la tarjeta lo pide. Credenciales ficticias en tests.
- Un comentario que dice "esto es seguro": verifica la explicación, no la creas ni la ignores.

## Formato y veredicto
Hallazgo (el formato del núcleo con la cadena de evidencia):
`[CRÍTICO|ALTO|MEDIO] seguridad: archivo:línea — problema. Quién: … Qué: … Frontera: … Ruta: … Cambio esperado: <invariante + arreglo mínimo en el último punto de decisión confiable> (confianza NN%)`
Necesita validación (en PENDIENTE del bloque de entrega, sin severidad):
`[NECESITA VALIDACIÓN] archivo:línea — hipótesis. Falta saber: <hecho exacto>. Cómo verificarlo: <dónde mirar o a quién preguntar>`
No es un cajón de ideas: si el código ya refuta la hipótesis, descártala.
Veredicto: el del núcleo (CRÍTICO y ALTO bloquean). "Seguridad: sin hallazgos." es un resultado válido.
