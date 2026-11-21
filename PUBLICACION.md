# Alcance de esta publicación

## Estado: preparada, publicación bloqueada

El repositorio de destino autorizado es
https://github.com/Gibrantrm/Gibran-Hermes-Flow.git y estaba público y vacío.
Se preparó esta copia en una rama `main` nueva, sin importar historial ajeno.
El primer `git push -u origin main` falló antes de publicar:
`Cannot prompt because user interactivity has been disabled` /
`unable to get password from user`.

No había autenticación Git utilizable de forma no interactiva. No se extrajeron
tokens ni se intentó rodear el bloqueo. **Los commits siguen solo en el clon
local; Pages no se desplegó y los enlaces de evidencia a esos commits no están
disponibles en GitHub todavía.** El propietario debe configurar autenticación
Git para GitHub y repetir el push normal desde este clon de publicación.
Después hay que comprobar el resultado de Actions y la URL de Pages antes
de anunciarla como disponible.

## Qué contiene

Copia actual del flujo, sin importar historial del repositorio de trabajo.
Incluye instalador, hooks, scripts, skills y sus referencias, SOULs, ejemplos de
configuración vacíos, documentación y pruebas focalizadas de `app_local.py`.
H1 conserva procesos y copias sin atribución demostrable: solo reporta PID/puerto.

Se documentó el comportamiento existente; no se implementaron hallazgos pendientes
ni se cambiaron permisos o decisiones del flujo. La sanitización del código
ejecutable se limita a comentarios/docstrings y notas de precios; las reglas
solo cambian ejemplos identificables por ejemplos genéricos y catálogo vacío.
El runner público añadido solo aísla la frontera Kanban de las pruebas.

## Qué se excluyó

- `.git` e historial del origen, configs personales, credenciales, certificados.
- Catálogo de repos privados, sus nombres/URLs y ejemplos con identidades internas.
- Métricas, consumos facturados, propuestas previas, reportes de hallazgos,
  planes de trabajo históricos, auditorías e incidentes.
- Logs, bases de datos, caches, transcripciones, capturas de apps empresariales.
- Fixtures ajenas al alcance H1, algunas con escrituras de SQLite o commits.
- Diagramas históricos: uno había sido eliminado y otro indicaba un revisor
  distinto al actual. No se restauró el archivo eliminado ni se reutilizó como
  fuente de verdad. El diagrama publicado se genera de nuevo a partir de esta copia.

`metricas/`, `propuestas-de-mejora.md` y el catálogo se distribuyen como plantillas
vacías. Cuando los uses, su contenido puede volverse privado: revisa antes de subir.

## Validación y límites

- Comparación del código con la copia actual de origen, sin cambios en su lógica.
- Suite focalizada de 12 casos de `app_local`, con Kanban simulado en el runner.
  Una corrida directa sin BD falló porque la protección conservadora mantuvo
  procesos sin dueño; se detuvieron exclusivamente los PIDs propios de esa corrida.
  El runner evita esa dependencia ambiental sin alterar producción.
- No se ejecutó descubrimiento global de tests, workers, instalador, cierre,
  integración, aplicaciones de negocio ni escrituras en BD.
- Los checks de publicación/diagrama no equivalen a auditoría de seguridad ni a
  una prueba integral de Hermes/proveedores/infraestructura.

El origen se mantiene intacto, incluidos sus cambios previos sin commit.

## Licencia del proyecto

No había una licencia aplicable declarada para el trabajo original del flujo.
No se agrega una por decisión del publicador. El propietario debe decidirla.
Las licencias de terceros en `THIRD_PARTY_NOTICES.md` no relicencian este proyecto.
