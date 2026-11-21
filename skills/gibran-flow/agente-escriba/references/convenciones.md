# Sección "Convenciones" del .hermes.md

Son las costumbres de ESTE repo (qué librerías usa y cómo), no buenas prácticas del lenguaje
(esas viven en el módulo `stack-<tecnología>`). Se escriben solo con lo verificado en el código:
lo que reportó el explorador en "Patrones", con un archivo de ejemplo por línea.
No copies el ejemplo de abajo a ciegas: incluye una línea solo si el repo realmente lo hace así.

Formato: una línea por convención, `- <qué se hace así> (ejemplo: <ruta>)`. Máximo ~10 líneas.

## Ejemplo: microservicio .NET (verificar en cada repo)
- Un caso de uso = Request MediatR + Handler + Validator de FluentValidation (ejemplo: <ruta>).
- Controllers delgados: reciben, `await _mediator.Send(...)`, devuelven; sin lógica.
- Listados con filtros, orden y paginación vía Sieve (`SieveModel`), como los endpoints vecinos.
- Mapeo con AutoMapper en el Profile del módulo (`CreateMappings`); no mapear a mano.
- Mapeo de EF en `IEntityTypeConfiguration<T>`, no en atributos.
- Esquema: lo cambia quien lo administra (este repo con migraciones, u otro repo; ver repos
  relacionados). Si hace falta un script SQL, va en `docs/scripts/` con su reversión.
- Tests: proyecto `<Nombre>.Tests` con xUnit (si existe y referencia al proyecto).
