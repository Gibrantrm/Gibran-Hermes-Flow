# Cómo armar el plan (riesgo alto; versión breve para riesgo bajo)

## Estructura
1. **Tabla Crear / Modificar:** cada archivo → qué tarjeta lo toca. Así se ven los solapes antes
   de definir dependencias.
2. **Tarjetas = rebanadas verticales** (tracer bullets): cada tarjeta entrega un comportamiento
   que se comprueba con su propio test, atravesando las capas que necesite (el mapa del módulo
   de stack dice cuáles son). Ejemplo: "GET /voluntarios?activo=true devuelve solo activos" =
   query + controlador + test en UNA tarjeta, no una por capa. Dentro de la tarjeta, el
   implementador va de adentro hacia afuera. Cada tarjeta arranca 2 workers en frío
   (implementador y revisor, ~$15 MXN de arranque): una tarjeta es la unidad más pequeña con su
   propio test que un revisor podría rechazar mientras aprueba la de al lado.
   - **Si todo el cambio cabe en el límite** (~150 líneas de producción), es UNA tarjeta, aunque
     mezcle lógica nueva y su aplicación: separar cuesta otro implementador y otro revisor.
   - Si no cabe: la **lógica nueva** (con sus tests) va en su tarjeta, separada de su
     **aplicación repetitiva**.
   - **Cambios de la misma forma y sin lógica nueva** (el mismo patrón en varios archivos o
     pantallas) van juntos en UNA tarjeta, hasta ~150 líneas de código de producción o ~500 de
     contenido o datos. El revisor de esa tarjeta compara que todos queden consistentes entre sí.
   - Lógica nueva: hasta ~150 líneas de código de producción por tarjeta (los tests no cuentan;
     el contenido o los datos cuentan aparte, hasta ~500).
   - Separa además solo si las partes pueden ir en paralelo sin tocar los mismos archivos, si se
     pasa de esos límites, o si el cambio va en otro repo.
   - Paralelo en el mismo worktree tiene un costo: si una tarjeta modifica un archivo suyo que
     ya existía mientras revisan la otra, el revisor de la otra se bloquea (es correcto: por ruta
     no se sabe de quién es) y revisa de nuevo cuando el worktree se estabiliza. Si el paralelo
     no ahorra tiempo real (tarjetas cortas), encadénalas con `parents`.
3. **Fases (opcional):** solo si la feature es grande o el usuario quiere integrar por partes.
   Dicen qué se puede integrar por separado y en qué orden; NO son motivo para partir tarjetas
   (una tarjeta puede cubrir varias fases).
4. **Decisiones:** "Decisión — alternativa descartada — por qué". Se pasan al escriba.
5. **Despliegue:** todo lo que NO se aplica solo al desplegar el código, con quién lo hace y
   cuándo: esquema (lo crea otra área o un updater que no corre solo), datos sembrados o de
   catálogo, configuración y variables de ambiente, jobs o tareas programadas, permisos. Verifica
   cómo corre en producción (p. ej. si el updater/migración se ejecuta al desplegar o a mano)
   antes de afirmarlo. Si no hay nada: "Despliegue: solo código".

## Cada tarjeta lleva (va en el `--body`)
    Objetivo: <una frase>  ·  Por qué: <una línea>
    Archivos permitidos: <lista cerrada, rutas relativas>
    Archivos de otras tarjetas de esta feature: <lista>
    Criterios:
    - CUANDO <situación> ENTONCES <resultado observable> — verificar: <comando>
    - (al menos un caso de error o borde por cada caso feliz: vacío, no encontrado,
       sin permiso, dato inválido, duplicado)
    - (de contenido, no de forma: "la nota dice qué cambió y dónde", no "la nota tiene 3
       líneas"; un conteo o posición exactos solo si el usuario lo pidió así)
    (criterio que se ve en pantalla: termina en "— en navegador")
    Test: <clase/archivo de test y comando que lo corre>
    Alcance .NET: <comandos exactos desde la raíz del worktree: .csproj + --filter + opciones;
        baseline/TDD y QA usan estas selecciones, NO la suite entera; no aplica si no es .NET
        o si hay "Sin test" aprobado>. El orquestador registra cada comando por id antes del
        despacho; el worker usa `dotnet_seguro.py test --tarea <id>` y no se autoriza a sí mismo.
    E2E: <archivo y filtro de la tarjeta> + <filtro acumulado de la feature> (si hay arnés;
        filtros por NOMBRE de las pruebas de esta feature, p. ej. `FullyQualifiedName~TooltipVacio`
        o el archivo `tests/evento-estado-vacio.spec.ts`; nunca una categoría entera como
        `Category=E2E` ni la suite completa) |
        "Manual: abrir… hacer… debe verse…"
        (sin arnés: los pasos van a la tarjeta final de verificación) | no aplica
          o "Sin test: aprobado en Control 1 porque <motivo>" (solo si el usuario lo aprobó)
    Límites: <qué NO tocar>
    Hermanos (bugs): `<comando grep>` → <archivo:línea — se corrige | no aplica porque … |
        decide el usuario>, uno por resultado
    Verificado de librerías: <verified_external que ya confirmaste tú o el explorador>
    BD: sí/no (si sí: "Revisor: cargar también agente-revisor-db"; si hay migración, debe
        tener reversión revisable)
    Riesgo/mitigación: <solo si la tarjeta no es de riesgo bajo>

## Verificación en navegador
Para cada criterio que se ve en pantalla (`references/e2e.md` tiene las reglas):
- **Con arnés E2E:** el criterio se vuelve una prueba E2E de la tarjeta. La primera tarjeta con
  E2E de una pantalla crea sus ayudas en el arnés (abrir la pantalla, llenar el formulario: el
  archivo de ayudas va en sus "Archivos permitidos"); las siguientes las reutilizan. El
  recorrido completo de una pantalla es criterio de su última tarjeta.
- **Sin arnés:** los pasos "Manual:" van a una tarjeta final "Verificación en navegador"
  (assignee `revisor`, sin implementador, `parents` = la última tarjeta).
- Tarjetas con E2E en paralelo: sí, si cada una levanta su app con puerto automático y (en .NET)
  desde copia, y sus pruebas no se pisan los datos. Las que necesitan el **mismo puerto fijo** van
  encadenadas (`parents`). Si la prueba junta componentes (frontend + API, gateway + servicio),
  el plan dice cómo se conectan (qué variable apunta a qué puerto).
- Si una tarjeta cambia la prueba de una tarjeta anterior (porque cambió su criterio), su body
  lo dice con el motivo.
- **Control 1**, solo cuando aplica: (1) permiso para levantar la app y escribir en DEV (Updater,
  datos de prueba) y, si el explorador reportó que falta algo para correr las pruebas
  (navegadores, dependencias, SDK), permiso para instalarlo; (2) sin arnés: "¿agrego una tarjeta para crear el arnés E2E o verificamos a
  mano al final?"; (3) pantalla nueva o cambio visual: "¿agrego una exploración manual al
  final?" (tarjeta del revisor, como la de verificación). Las decide el usuario.

## Sin dónde testear
Si el explorador reporta que no hay proyecto de tests (o no referencia al proyecto a probar),
dilo en el Control 1 y ofrece dos opciones: una tarjeta previa que cree el proyecto de tests, o
aprobar "Sin test" con su motivo. Nunca decidas tú: si el usuario aprueba "Sin test", escríbelo
en el body de la tarjeta (QA lo exige así).

## Repos relacionados
Si el cambio cruza a otro repo (la API que consume una app), el plan lo dice: qué tarjetas van en
cada repo y en qué orden. Cada repo tiene su propio worktree.

## Antes del Control 1: revisa tu propio plan
- ¿Alguna tarjeta sin rutas exactas de archivos?
- ¿Alguna sin criterio verificable con comando, o sin caso de error/borde?
- ¿Algún criterio de forma (número de líneas, palabras, posición exacta) que el usuario no pidió?
  El revisor lo exige al pie de la letra y gasta rondas en eso: cámbialo por lo que debe decir.
- ¿Alguna sin test y sin "Sin test" aprobado?
- ¿Algún test .NET sin proyecto/filtro/opciones concretos, o baseline/QA más amplia que lo
  permitido? ¿Falta registrar alguna selección acumulada de E2E prevista?
- ¿Hay tarjetas separadas sin una de las razones del punto 2 (p. ej. el mismo patrón repartido
  en varias tarjetas)? Únelas.
- ¿Alguna tarjeta que no se pueda probar sin otra (partida por capa)? Únelas.
- ¿Algún criterio pide tocar un archivo que no está en los "Archivos permitidos" de su tarjeta,
  o que la tarjeta prohíbe en "Límites"? Corrige una de las dos.
- ¿Alguna interfaz, capa o abstracción nueva con una sola implementación?
- ¿Se reutiliza lo que el explorador reportó en "Patrones" y "Reusar"? ¿Se copia la convención
  del `.hermes.md`?
- ¿Tarjetas que comparten archivos en paralelo? (deben encadenarse con `--parent`)
- ¿Algún cambio de contrato sin marcar en negritas?
- ¿Algún criterio que afirma cómo funciona algo hoy ("hoy responde 500") sin verificar? Verifícalo
  o márcalo "(supuesto)".
- ¿Algún DDL o script de esquema sin saber quién administra el esquema?
- ¿Algún dato sembrado, configuración o esquema que no llega solo a producción y no está en
  "Despliegue"?
- ¿Algún criterio "en navegador" sin E2E ni pasos "Manual:"? ¿Alguna E2E sin el filtro acumulado? ¿Dos tarjetas con E2E en
  paralelo que necesitan el mismo puerto fijo? ¿La primera E2E llega en la tercera tarjeta o después sin decir por qué las
  anteriores no se pueden ver?
Si alguna respuesta es sí, corrige antes de presentar.

## Riesgo bajo (versión breve)
Archivos, cambio, criterio con su caso borde y test, en el chat y en el body de la tarjeta
(misma plantilla). No requiere aprobación, pero si no hay dónde testear, pregunta igual (la
excepción "Sin test" siempre la decide el usuario).
