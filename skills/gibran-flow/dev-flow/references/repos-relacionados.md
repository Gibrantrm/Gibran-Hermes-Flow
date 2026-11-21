# Repos relacionados (otro repo que este consume o del que depende)

Ejemplo: una app móvil cuya API vive en otro repo; un microservicio que valida tokens de otro;
un servicio que lee tablas que crea otro sistema.

## Esquema de base de datos sin migraciones en el repo
Si el cambio toca el esquema (tabla, columna, índice) y el repo no tiene migraciones, "¿quién
crea las tablas?" se responde ANTES de proponer SQL. Puede ser:
- **este mismo repo, con un ORM que actualiza el esquema solo** (XPO / XAF con su updater,
  Hibernate auto-DDL, `synchronize` de TypeORM): busca primero ese mecanismo (updater,
  `UpdateDatabase`, configuración del ORM, `CLAUDE.md`). Ahí la columna se agrega en la clase
  persistente y no hay script;
- **otro repo** (sigue la escalera de abajo).
En producción, el esquema puede crearlo otra área (p. ej. el área de base de datos): el plan y
el Control final lo dicen como paso de despliegue. Señales de que otro sistema es el dueño: no hay carpeta ni historial de
migraciones ni ORM que actualice solo; el esquema real y el mapeo del código difieren (longitudes, tipos, columnas de
más); otro repo usa los mismos nombres de tabla.
Ej.: un microservicio lee tablas que crea un backoffice; la columna nueva se agrega en el
backoffice (su modelo) y el microservicio solo la mapea. El plan dice el orden de despliegue
(dueño del esquema → servicio → front).
Un script SQL manual solo si el usuario confirma que nadie más administra el esquema; entonces
va en `docs/scripts/` con su reversión.

## Cómo se registra (compartido, va en el repo)
En el `.hermes.md` del repo, sección `## Repos relacionados`, una línea por relación con el
**nombre** y la **URL remota**. Nunca rutas locales: cada persona clona donde quiere.

    - API que consume: <nombre del gateway> (<URL remota sin credenciales>)
    - Autenticación: <nombre del servicio de identidad> (<URL remota sin credenciales>)

## Cómo se encuentra el clon local (personal, no va en ningún repo)
1. Lee las carpetas de trabajo del usuario en
   `local/workspace.yaml` (lista `raices`) en la raíz de hermes-flow: tres carpetas arriba del
   `skill_dir` que devuelve `skill_view("dev-flow")` (`<skill_dir>/../../../local/workspace.yaml`).
2. Busca en esas raíces una carpeta con el nombre del repo y confirma con
   `git -C <carpeta> remote get-url origin` que la URL coincide (ignora usuario/credenciales
   en la URL).
3. Lee ese repo en SOLO LECTURA. Nunca lo modifiques ni corras comandos que escriban.

## Escalera antes de decir "no lo sé"
1. Documentación del repo actual: `.hermes.md`, README, `docs/`, AGENTS.md / CLAUDE.md.
2. Sección "Repos relacionados" del `.hermes.md` y el catálogo (`catalogo-repos.md`, columna
   "relacionados"). Una relación marcada "por confirmar" es una pista: verifícala en el código
   (p. ej. la URL base de la API en la configuración de la app) antes de darla por buena.
3. Clon local (pasos de arriba) y verificar ahí lo que hace falta.
4. Si no aparece la relación o no hay clon local, la pregunta depende de qué falta:
   - No se sabe cuál es el repo → "¿en qué repo está la API que consume esta app?".
   - Se sabe cuál es pero no hay clon → "la API está en <repo> (<URL remota>) y no lo encuentro
     en tus carpetas de `local/workspace.yaml`: ¿lo clonas o me dices dónde está?".
   - Explorador / orquestador (al inicio): `RESULTADO: necesita-decisión` con esa pregunta;
     el orquestador se la hace al usuario antes de planear.
   - Revisor (worker): `[NECESITA VALIDACIÓN]`; si de confirmarse sería CRÍTICO → `kanban_block`
     con la pregunta, para que el usuario responda.
5. Con la respuesta del usuario, el escriba agrega la línea en "Repos relacionados" (nombre +
   URL remota) para no volver a preguntar.

## Librerías internas (paquetes cuyo código no está en este repo)
Para saber cómo se comporta una clase de una librería interna, en este orden:
1. **Uso en este repo:** busca la clase o el miembro (`grep`) y copia cómo se usa.
2. **Lo ya verificado:** `.hermes.md` y el "Verificado de librerías" de la tarjeta o el brief.
3. **Código fuente de la librería:** su repo, con los pasos de arriba (catálogo, clon local).
4. **Binario** (descompilar, Reflection, buscar texto en la DLL): solo si 1-3 no lo resuelven
   **y** la duda bloquea un criterio. Se declara como "(binario)" en la entrega; nunca como
   "confirmado".
Buscar texto dentro de una DLL solo prueba que existe un nombre, no cómo se comporta.
Ejemplos:
- ¿Qué constructor tiene una excepción de la librería? → busca `new <Excepción>(` en el repo;
  si no hay, el repo de la librería; la DLL al final.
- "La librería tiene un filtro de borrado lógico" porque el nombre aparece en la DLL → no es
  dato; lo es el código fuente o un test que lo muestre.
- Lo que el explorador ya verificó va en la tarjeta para que el implementador no lo repita.
