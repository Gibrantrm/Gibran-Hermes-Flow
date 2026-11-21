---
name: stack-dotnet
description: "Gibran Flow: módulo de stack C#/.NET para cualquier repo .NET. Operación (detectar, compilar y probar, señales de QA, mapa para explorar) y buenas prácticas del lenguaje. Las convenciones propias de cada repo viven en su .hermes.md."
version: 3.5.0
metadata:
  hermes:
    tags: [gibran-flow, dotnet, csharp]
    related_skills: [revisor-csharp]
---

# stack-dotnet

Módulo de stack: lo usan el explorador, el implementador y QA a través de sus secciones fijas.
Las **convenciones de cada repo** (qué librerías usa y cómo) están en su `.hermes.md` y en los
patrones que reporta el explorador; si chocan con esta guía, **gana el repo**.

## Detectar
Hay `*.sln` o `*.csproj`. El `TargetFramework` de cada `.csproj` fija qué APIs existen y el
`LangVersion` por defecto (net5.0 = C# 9, net6 = C# 10, net7 = C# 11, net8 = C# 12).

## Compilar y probar
- Build del proyecto afectado: `dotnet build <proyecto>.csproj --nologo -v q`.
- Tests: `dotnet test <proyecto-de-tests>.csproj --nologo` (no toda la solución si es lenta);
  para iterar: `--filter "FullyQualifiedName~<Clase>"`.
- **En workers de Kanban** (worktree compartido) escribe `dotnet build/test/run/publish`
  normal en la terminal: la guardia lo pasa sola por el candado (`dotnet_seguro`), que además
  quita avisos repetidos de la salida. No busques el script ni la ruta de Python.
  Código de salida 75 = el candado siguió ocupado 15 min (problema de entorno, no del código).

**Pruebas E2E** (si el repo trae guía, `CLAUDE.md` o `docs/…e2e…`, esa manda):
1. Si cambió el esquema o datos que siembra el updater (XAF/XPO): corre antes el comando de
   actualización del repo (p. ej. `dotnet run -- --updateDatabase --forceUpdate`).
2. `dotnet build <proyecto de tests>` (compila también el proyecto web que referencia).
3. Levanta la app desde una copia (Windows bloquea las DLL de una app viva):
   `python <app_local> iniciar --puerto auto --copia <proyecto web>/bin/Debug/<TFM>
   --env ASPNETCORE_ENVIRONMENT=Development -- dotnet {copia}/<Ensamblado>.dll --urls
   https://localhost:{puerto} --contentRoot <proyecto web>` (verificado con una app XAF/Blazor:
   estáticos y páginas responden desde la copia).
4. `dotnet test <proyecto-de-tests> --no-build --filter "Category=E2E&FullyQualifiedName~<Clase>"`
   con `E2E_BASE_URL=https://localhost:<PUERTO>` (o la variable del arnés). `--no-build`: ya está
   compilado y así no toca binarios.
5. `python <app_local> detener`.
`UseUrls(...)` en el código del host le gana a `--urls` y a `ASPNETCORE_URLS`: esa app queda en su
puerto fijo (usa `--puerto <n>`).

**Proyecto de tests** (solo si la tarjeta lo permite): `dotnet new xunit -n <Proyecto>.Tests
--framework <mismo TargetFramework>` y `dotnet add <Proyecto>.Tests reference <Proyecto>.csproj`;
sin paquetes extra a los de la plantilla. Sin `TargetFramework` soportado por la plantilla
(net5): crea el `.csproj` de tests a mano con el mismo `TargetFramework` y bloquea si dudas.

## Señales de QA
- Sin tests: "Total tests: 0", "No test is available" o un `--filter` que no coincide = FALLA.
- Warnings a vigilar en archivos de la tarjeta: nullable (CS86xx), llamada async sin await
  (CS4014). "Compilación correcta" con warnings nuevos de esas familias = reportar.
- Fallo de entorno, no de código: "being used by another process" / "está siendo utilizado por
  otro proceso" (archivos en `bin/` u `obj/`), o `dotnet_seguro` con código 75.
- Formato: si el repo tiene `.editorconfig`, `dotnet format <proyecto> --verify-no-changes
  --include <archivos de la tarjeta>`.

## Mapa para explorar
- Entrada: Controller o endpoint de Minimal API → capa de aplicación (si el repo usa MediatR:
  Request → `IPipelineBehavior`/Validator → Handler; si no, el servicio que llama el endpoint) →
  persistencia (`DbContext` + configuración del modelo) → tabla.
- Anota: ramas, async, try/catch, qué excepción se convierte en qué código HTTP (middleware),
  dónde se guarda (`SaveChanges`) y si hay transacción.
- Excepción → HTTP: no lo dejes "incierto". Busca el filtro o middleware de excepciones
  (`ExceptionFilter`, `UseExceptionHandler`, `*ExceptionMiddleware`) y lee qué tipo mapea a qué
  código; un tipo que no esté ahí suele caer en 500.
- Piezas reutilizables: `*Extensions.cs`, `Common/`, `Helpers/`, perfiles de mapeo, validadores,
  configuración de filtros/paginación existente. Revisa los paquetes del `.csproj`.
- XAF (DevExpress): para dudas de API usa el MCP `dxdocs` (`devexpress_docs_search` y luego
  `devexpress_docs_get_content`), máximo 3 llamadas, y cita la URL.

## Buenas prácticas de C#
**Asincronía y cancelación**
- `async` de punta a punta. Nunca `.Result`, `.Wait()` ni `.GetAwaiter().GetResult()`.
  Nunca `async void` (salvo manejadores de eventos de UI).
- Si el método recibe un `CancellationToken`, propágalo a todas las llamadas async
  (`ToListAsync(ct)`, `SaveChangesAsync(ct)`, `HttpClient`).
- No ejecutes en paralelo (`Task.WhenAll`) consultas sobre el mismo `DbContext`.

**Errores**
- Nada de `catch {}` ni `catch` que devuelve null/vacío sin registrar. Atrapa la excepción
  específica o relanza con `throw;` (nunca `throw ex;`). Al envolver, pasa la `innerException`.
- Log estructurado con contexto: `_logger.LogError(ex, "No se pudo X {Id}", id)`.
- Configuración obligatoria: falla al arrancar si falta; no la leas con un default silencioso.

**Tipos y nulabilidad**
- Si el proyecto tiene `<Nullable>enable</Nullable>`: cero warnings nuevos, sin silenciarlos con
  `!` ni `#pragma`. Si no lo tiene, no lo actives por tu cuenta.
- Casts con `is T t`/`as`, no `(T)obj` sin comprobar. Nombres de miembros con `nameof`.
- Sin `dynamic`. `record` solo si el `LangVersion` lo soporta y el repo ya lo usa.

**Recursos e inyección de dependencias**
- `using`/`await using` para todo `IDisposable`. `IHttpClientFactory` en lugar de `new HttpClient()`.
- Un singleton no recibe servicios scoped ni un `DbContext`. Nada de estado `static` mutable.

**Datos (EF Core)**
- Lecturas con `AsNoTracking()` o proyección a DTO; no devuelvas la entidad completa en listados.
- Evita N+1: `Include` o proyección; nunca navegues relaciones dentro de un bucle.
- Filtra y pagina en la consulta, no en memoria (`Where`/`Skip`/`Take` antes de `ToListAsync`).
- SQL crudo solo con `FromSqlInterpolated` o parámetros; nunca interpolar en `FromSqlRaw`.
- Sin migraciones automáticas ni `EnsureCreated`. Un cambio de esquema es riesgo ALTO: se
  propone el script SQL en `docs/scripts/`, no se aplica.

**APIs según versión** (usa solo lo que existe en el TargetFramework)
- net6+: `ArgumentNullException.ThrowIfNull`, `Chunk`, `DistinctBy`/`MaxBy`, `DateOnly`/`TimeOnly`,
  `PeriodicTimer`. net7+: `required`, `ExecuteUpdate`/`ExecuteDelete` (EF7). net8+: primary
  constructors en clases, collection expressions, `TimeProvider`.

**Tests (xUnit)**
- Usa el proyecto de tests existente y sus librerías (asserts, mocks); no agregues otras.
- Clase `<ClaseProbada>Tests`; método `Metodo_Escenario_Resultado`; estructura Arrange-Act-Assert.
- `[Fact]` para un caso; `[Theory]` + `[InlineData]` para bordes (null, vacío, límite, error).
- Prueba comportamiento público, no detalles internos; simula solo fronteras reales.
- Si la lógica depende de restricciones o SQL del motor real, usa la base de test que ya tenga
  el repo; la BD en memoria no detecta eso.

**Errores de compilación frecuentes**
| Código | Causa típica | Arreglo |
|---|---|---|
| CS8602 / CS8618 | nulabilidad | null check, inicializar o `?` en el tipo; no `!` |
| CS0246 | falta `using` o referencia de proyecto | agrega el `using`; si es otro `.csproj`, bloquea |
| CS1061 | miembro que no existe en ese TargetFramework | usa el equivalente de la versión |
| CS4014 | llamada async sin `await` | agrega `await` |
| NU1xxx | restauración de paquetes | no agregues paquetes: bloquea |
