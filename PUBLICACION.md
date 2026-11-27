# Alcance de esta publicación

## Actualización H1–H5 (26-nov-2026)

Se incorporan las correcciones H2–H5 y su documentación, conservando H1, ya publicado:
reutilización del worktree de bugs, identidad estable de métricas, invalidación de revisiones
cuando cambia el worktree y autorización/evidencia de tests .NET.
[Detalle operativo](docs/analisis/correcciones-astra-h1-h5.md).

Se trasladan los cambios revisados sin importar el historial local, métricas privadas ni
la eliminación de un diagrama en el repositorio de trabajo. Se conserva la sanitización
de ejemplos y comentarios de la distribución pública.
Las pruebas nuevas incluidas usan ejecutables falsos, snapshots y respuestas de BD simuladas;
se excluye la clase original de integración del revisor que crea commits y escribe SQLite.
Los artefactos del diagrama y su workflow no cambian en esta actualización.
La copia pública pasó 48 pruebas focalizadas de cierre, revisión, ejecución .NET y guardias.
Los seis módulos de producción afectados se compararon mediante AST con el origen:
su lógica coincide, conservando los comentarios/documentación saneados.
H1 y su runner no cambiaron; conservan la validación de 12 casos de la publicación inicial.

## Estado: código y Pages publicados

El repositorio de destino autorizado es
https://github.com/Gibrantrm/Gibran-Hermes-Flow.git y estaba público y vacío.
Se preparó esta copia en una rama `main` nueva, sin importar historial ajeno.
Tras autenticar el propietario mediante Git Credential Manager, el push normal
publicó `main`; el hash remoto coincidió con el local. Se verificó HTTP 200 para
la imagen PNG enlazada desde el README. Las fuentes del diagrama fijadas al
commit `b705aa7d5d83cbccff9c5ef3f3f889d0a1fe7b5d` ya están disponibles en GitHub.
No se extrajeron tokens ni se modificó la configuración global de Git.

**Sitio verificado:** https://gibrantrm.github.io/Gibran-Hermes-Flow/

El [run 44943338017](https://github.com/Gibrantrm/Gibran-Hermes-Flow/actions/runs/44943338017)
desplegó correctamente el commit `4d9271784d973770e886511be34fd56809608fe4`.
Se abrió el visor en navegador y se verificó HTTP 200 e igualdad byte por byte
del HTML, SVG, PNG y JSON servidos con los artefactos aprobados.

El
[primer workflow](https://github.com/Gibrantrm/Gibran-Hermes-Flow/actions/runs/44936048690)
falló al intentar crear el sitio:
`Create Pages site failed. Error: Resource not accessible by integration`.
El propietario habilitó Pages. Después se reprodujo un fallo de descubrimiento:
el upload terminaba correctamente, pero deploy-pages encontraba cero artefactos
al continuar inmediatamente en el mismo job. Separar preparación y despliegue
con `needs: preparar` resolvió ese fallo en la ejecución verificada, sin nuevas
dependencias ni permisos. La causa interna del servicio no se infiere de los logs;
la evidencia y los intentos están en la [guía del diagrama](docs/diagrama/README.md).

El README renderiza el PNG y enlaza al visor vivo; SVG y HTML descargable siguen
disponibles para uso local. El código del flujo y los bytes del diagrama no
cambiaron durante la corrección del despliegue.

## Qué contiene

Copia actual del flujo, sin importar historial del repositorio de trabajo.
Incluye instalador, hooks, scripts, skills y sus referencias, SOULs, ejemplos de
configuración vacíos, documentación y pruebas focalizadas de H1, H3, H4 y H5.
H1 conserva procesos y copias sin atribución demostrable: solo reporta PID/puerto.

La publicación inicial documentó el comportamiento existente; esta actualización añade
las correcciones autorizadas indicadas arriba. La sanitización del código
ejecutable se limita a comentarios/docstrings y notas de precios; las reglas
solo cambian ejemplos identificables por ejemplos genéricos y catálogo vacío.
El runner público añadido solo aísla la frontera Kanban de las pruebas.

## Qué se excluyó

- `.git` e historial del origen, configs personales, credenciales, certificados.
- Catálogo de repos privados, sus nombres/URLs y ejemplos con identidades internas.
- Métricas, consumos facturados, propuestas previas, reportes privados de hallazgos,
  planes de trabajo históricos, auditorías e incidentes.
- Logs, bases de datos, caches, transcripciones, capturas de apps empresariales.
- Fixtures de integración con escrituras de SQLite o commits.
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

La operación de publicación no modifica los repositorios de trabajo ni importa su historial.

## Licencia del proyecto

No había una licencia aplicable declarada para el trabajo original del flujo.
No se agrega una por decisión del publicador. El propietario debe decidirla.
Las licencias de terceros en `THIRD_PARTY_NOTICES.md` no relicencian este proyecto.
