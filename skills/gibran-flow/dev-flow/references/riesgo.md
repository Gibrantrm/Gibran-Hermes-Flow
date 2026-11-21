# Clasificación de riesgo

Se clasifica dos veces: al recibir la petición y después de explorar. Solo puede SUBIR: si el
explorador propone un riesgo mayor que el tuyo, gana el suyo; bajarlo solo lo decide el usuario.
Dilo citando el disparador: `Riesgo: ALTO — rechaza entradas que hoy se aceptan` o
`Riesgo: BAJO — ningún disparador`.

## ALTO si se cumple cualquiera
- **Cambia algo que otros consumen:** quitar, renombrar o cambiar el tipo o el significado de un
  campo, parámetro, valor, evento o firma pública.
  Ej.: un campo que era texto libre pasa a catálogo; un estatus cambia de nombre.
- **Rechaza lo que hoy se acepta:** validación nueva, campo que pasa a obligatorio, rango más
  estrecho. Lo que ya se guardaba deja de entrar.
  Ej.: un endpoint de alta empieza a rechazar registros sin un dato que antes era opcional.
- **Datos personales o sensibles donde antes no aparecían:** identificadores fiscales o
  personales, teléfono, correo, domicilio, salud, datos económicos.
  Ej.: "agrega el detalle del solicitante" y el detalle incluye su identificador fiscal y su
  teléfono. Agregarlo no lo vuelve inofensivo.
- **Seguridad:** autenticación, permisos, secretos, algo que queda accesible sin autenticar.
  Ej.: un endpoint de descarga de documentos que no valida a quién pertenecen.
- **Base de datos:** migración o esquema, cambio de mapeo del ORM, o escrituras (insert, update,
  delete). Una consulta de solo lectura (filtro, orden, proyección) NO cuenta.
- **Escrituras en lote:** procesar muchos registros en una operación (aprobación masiva,
  importación), con éxito parcial, transacciones o notificaciones de por medio.
- **Configuración o código compartido que afecta muchos puntos a la vez:** filtros globales de
  consulta (borrado lógico, multiempresa), ordenamiento o paginación global, middleware, mapeos
  compartidos, librerías internas, gateways.
  Ej.: "corrige el orden de esta lista" y el arreglo va en la configuración de ordenamiento que
  usan todos los listados de esa entidad.
- Más de 5 archivos existentes.
- Proyecto nuevo.
- Duda que la exploración no despejó (solo en la segunda clasificación).

## NO es ALTO
- **Arreglar algo para que haga lo que ya prometía**, sin cambiar la forma de su salida.
  Ej.: una lista que debía venir ordenada por fecha y no lo estaba; un filtro que no filtraba; un
  total mal calculado.
- **Convertir un error inesperado en un error controlado** por un dato inválido (una caída, un 500
  o una excepción sin manejar pasa a error de validación). Va en negritas en el Control final.
- Agregar algo **opcional** (parámetro, campo nuevo no sensible) que no cambia lo que ya funciona.

## Motivos que no valen
- "Lo pidió el usuario" no baja el riesgo: él pide el qué; el riesgo mide el cambio.
- Nunca elijas un diseño peor para quedarte en BAJO.
  Ej.: dejar un valor por defecto silencioso en vez de volver el campo obligatorio "porque
  obligatorio sube a alto". Elige el diseño correcto y clasifícalo como salga.
- Los ejemplos de arriba son guías: si un caso se parece a uno de ALTO, es ALTO.

El `.hermes.md` del repo puede listar disparadores propios (sección "Riesgo"); súmalos a estos.

## Qué decide el riesgo
Feature y bug van siempre por Kanban con QA ⛔ + revisor (perfil revisor). El riesgo decide
el resto:

| Riesgo | Plan | Controles del usuario |
|---|---|---|
| Bajo | Breve, sin `/reasoning high` | 1: diff final |
| Alto | Entrevista + plan completo con `/reasoning high` | 2: plan y diff final |
