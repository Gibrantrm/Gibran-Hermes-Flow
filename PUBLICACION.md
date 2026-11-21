# Alcance de esta publicación

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
