---
name: agente-revisor-db
description: "Gibran Flow: módulo de revisión para cambios que tocan base de datos (migraciones, mapeo, consultas, scripts). Agnóstico al ORM; lo propio del motor está en references/<motor>.md. Solo lectura: nunca DDL/DML."
version: 2.1.0
metadata:
  hermes:
    tags: [gibran-flow, code-review, base-de-datos]
    related_skills: [agente-revisor, revisor-csharp]
---

# agente-revisor-db

Lo carga `agente-revisor` cuando la tarjeta toca base de datos: migraciones, mapeo del ORM,
consultas nuevas o cambiadas, scripts SQL. Mismas severidades, filtro y veredicto del núcleo.
Lo de cada motor está en `references/<motor>.md` (hoy: `references/postgresql.md`); cómo se ven
estos problemas en un ORM concreto, en `revisor-<tecnología>` (EF Core → `revisor-csharp`).

## Límites (solo lectura)
- Usa dbhub en DEV (`*_dev`). En PROD solo `search_objects_*_prod` si el esquema de DEV no
  coincide; nunca consultas de datos ni planes con ejecución real (`ANALYZE`) en PROD.
- Nunca ejecutas DDL ni DML, ni aplicas migraciones. Si hace falta un índice, una columna o una
  restricción, escríbelo en el hallazgo, dirigido a quien administra el esquema.

## 1. Esquema real vs mapeo
Por cada entidad tocada, compara las columnas reales (tipo, nulabilidad, longitud, default,
restricciones) con el mapeo del ORM. Diferencia = hallazgo (ALTO si causa error o pérdida en
ejecución; MEDIO si solo es inconsistencia).

## 2. Migraciones y scripts (lo más caro: pérdida de datos irreversible)
- **ALTO "¿quién administra el esquema?":** DDL escrito a mano (script, `ALTER TABLE`) en un
  repo sin migraciones, salvo que la tarjeta diga que el usuario confirmó que nadie más lo
  administra.
- **CRÍTICO:** un renombre de columna o tabla que el ORM generó como borrar + crear (se pierden
  los datos); editar una migración que ya se aplicó en algún ambiente; borrar columna o tabla con
  datos sin que la tarjeta lo declare.
- **ALTO:** columna nueva NOT NULL sin default en una tabla con datos (falla o bloquea);
  crear un índice en una tabla grande de forma que bloquea escrituras; cambiar el tipo de una
  columna con conversión que puede perder precisión o fallar; mezclar cambio de esquema y
  migración masiva de datos en el mismo paso; reversión (`Down`) vacía o incorrecta sin marcar
  la migración como irreversible.
- Renombres y borrados en tablas en uso: expandir y contraer (agregar → copiar → cambiar código
  → borrar en una versión posterior), no en un solo paso.
- Datos masivos: por lotes, nunca en una sola transacción gigante.

## 3. Tipos y nulabilidad
- Dinero en punto flotante = ALTO (usa decimal exacto con precisión y escala).
- Fechas: que la columna, el código y la zona horaria sean consistentes (con zona o UTC en todos
  lados); mezclar = hallazgo. Verifica la versión del driver antes de afirmarlo (ver motor).
- Identificadores de tablas que crecen sin límite: tipo con rango suficiente.
- La nulabilidad del código coincide con la de la columna y con las validaciones.

## 4. Índices
- Toda llave foránea nueva necesita índice (muchos motores no lo crean solos).
- Columnas nuevas de filtro, unión u orden en consultas frecuentes: verifica el plan.
- Índice compuesto: primero las columnas de igualdad, después las de rango u orden.
- Aplicar una función a la columna (minúsculas, cast) o buscar con comodín inicial (`%texto%`)
  anula el índice normal: hace falta un índice por expresión o de texto.
- Borrado lógico (soft delete) o filtros fijos: considera un índice parcial.
- Unicidad garantizada solo con "consultar si existe y luego insertar" = MEDIO (se duplica con
  concurrencia): propón una restricción única en la BD.

## 5. Consultas
- N+1: consultas dentro de bucles o navegación de relaciones dentro de un recorrido.
- Filtrar, ordenar o paginar en memoria en vez de en la consulta.
- Varias colecciones cargadas a la vez (explosión cartesiana).
- Traer la entidad completa para un listado en vez de proyectar solo las columnas necesarias.
- Listados sin límite sobre tablas que crecen = ALTO; paginación sin orden estable (desempata
  por llave primaria).
- Paginación por desplazamiento (OFFSET) profunda en tablas grandes: anótala; para recorridos
  completos o exportes propone paginación por llave (`WHERE id > @ultimo`).

## 6. Concurrencia y transacciones
- Leer → calcular → guardar sobre saldo, stock, estado o folio sin control de concurrencia
  (token de versión, bloqueo de fila o UPDATE atómico) = ALTO. Folio con `MAX()+1` = ALTO.
- Llamadas externas (HTTP, colas, archivos) dentro de una transacción abierta = ALTO.
- Guardar dentro de un bucle (muchas transacciones y viajes a la BD) = MEDIO.
- Varias filas bloqueadas: siempre en el mismo orden (por id) para evitar interbloqueos; en colas
  de trabajo, saltar las filas bloqueadas.

## 7. Plan de ejecución (solo en DEV)
1. Obtén el SQL real que genera el código (el módulo de tecnología dice cómo); no lo reescribas
   a mano.
2. Pide el plan estimado en DEV, sin ejecutar la consulta (ver `references/<motor>.md`).
3. Busca: recorrido completo de una tabla grande; unión anidada cuyo lado interno recorre una
   tabla completa (falta índice en la columna de unión); ordenamiento de muchas filas al
   paginar (falta índice en la columna de orden); la condición del WHERE aplicada como filtro
   posterior y no como condición del índice (el índice no se usa).
4. Tabla pequeña o estimación de pocas filas: un recorrido completo es normal; no es hallazgo.

## Formato
`[CRÍTICO|ALTO|MEDIO] bd: archivo:línea — problema. Evidencia: <fragmento del plan o del esquema
real (dbhub)>. Cambio esperado: … SQL propuesto (docs/scripts/): … (confianza NN%)`
Los hallazgos se suman al veredicto de la misma revisión.
