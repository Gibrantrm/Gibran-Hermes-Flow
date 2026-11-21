# PostgreSQL — lo propio del motor para agente-revisor-db

## Consultas útiles en DEV (solo lectura, vía dbhub)
- Columnas reales: `SELECT column_name, data_type, is_nullable, character_maximum_length,
  numeric_precision, numeric_scale, column_default FROM information_schema.columns
  WHERE table_name = '<tabla>' ORDER BY ordinal_position;`
- Índices de una tabla: `SELECT indexname, indexdef FROM pg_indexes WHERE tablename = '<tabla>';`
- Llaves foráneas sin índice:
  `SELECT c.conrelid::regclass AS tabla, c.conname FROM pg_constraint c
   WHERE c.contype = 'f' AND NOT EXISTS (SELECT 1 FROM pg_index i
   WHERE i.indrelid = c.conrelid AND (i.indkey::int2[])[0:cardinality(c.conkey)-1] = c.conkey);`
- Tamaño aproximado: `SELECT reltuples::bigint FROM pg_class WHERE relname = '<tabla>';`

## Plan estimado
- `EXPLAIN (FORMAT TEXT) <consulta>`: estima sin ejecutar. Nunca `EXPLAIN ANALYZE` en PROD.
- Leer: `Seq Scan` con `rows` estimadas > ~10k en tabla grande = revisar índice;
  `Nested Loop` con `Seq Scan` interno = falta índice en la columna de unión;
  `Sort` grande al paginar = falta índice en la columna del ORDER BY;
  condición del WHERE en `Filter:` y no en `Index Cond:` = el índice no se usa;
  `cost` que se dispara al quitar el `LIMIT` = la paginación depende del orden.

## Tipos
- Fechas: `timestamptz` con UTC en el código. `timestamp` (sin zona) mezclado con fechas UTC es
  hallazgo; con Npgsql 6+ las fechas no-UTC hacia `timestamptz` fallan salvo el modo heredado
  (`Npgsql.EnableLegacyTimestampBehavior`): revisa cuál usa el repo antes de reportar.
- Dinero: `numeric(p,s)`. Ids: `bigint` / `GENERATED ... AS IDENTITY` en tablas que crecen.
- Texto: `varchar(n)` o `text` según lo que diga el mapeo del repo; no exijas cambiarlo.

## Índices
- En tabla grande y en uso: `CREATE INDEX CONCURRENTLY` (no bloquea escrituras) — no puede ir
  dentro de una transacción (en la migración debe ir fuera de la transacción).
- `ILIKE '%x%'` o `lower(col)`: índice `pg_trgm` (GIN) o índice por expresión `(lower(col))`.
- Parcial: `CREATE INDEX ... WHERE NOT eliminado`. Cubriente: `... INCLUDE (col1, col2)`.

## Migraciones
- PostgreSQL 11+: `ADD COLUMN ... DEFAULT <constante> NOT NULL` es rápido (no reescribe la
  tabla); con default volátil sí la reescribe.
- Cambiar tipo de columna (`ALTER COLUMN TYPE`) suele reescribir la tabla y bloquearla.
- `ALTER TABLE` toma bloqueos fuertes: en tablas grandes, en ventana o por pasos.

## Concurrencia
- Token de concurrencia con la columna de sistema `xmin`.
- Bloqueo de filas: `SELECT ... FOR UPDATE` ordenado por id; colas: `FOR UPDATE SKIP LOCKED`.
- UPDATE atómico: `UPDATE saldo SET valor = valor - @x WHERE id = @id AND valor >= @x`.
- Folios: secuencia (`GENERATED AS IDENTITY` o `nextval`), no `MAX()+1`.
