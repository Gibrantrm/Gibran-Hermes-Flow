---
name: revisor-csharp
description: "Gibran Flow: módulo de revisión para C#/.NET (EF Core, MediatR, AutoMapper, Sieve, xUnit). Lo carga agente-revisor cuando el diff tiene .cs o .csproj; aplica sus mismos ejes y severidades."
version: 1.4.0
metadata:
  hermes:
    tags: [gibran-flow, code-review, dotnet, csharp]
    related_skills: [agente-revisor, stack-dotnet, agente-revisor-db]
---

# revisor-csharp

Traduce los conceptos de `agente-revisor` a .NET. Mismos ejes, severidades y filtro.
Las secciones de librerías (AutoMapper, MediatR, Sieve, FluentValidation) aplican solo si el repo las usa.
Antes de sugerir una API, confirma que existe en el `TargetFramework` del proyecto
(p. ej. `ArgumentNullException.ThrowIfNull`, `Chunk`, `DistinctBy`, `DateOnly` son net6+;
`ExecuteUpdate/ExecuteDelete` son EF7+). Si el repo usa otra convención, gana el repo.

## Eje 1 en .NET
**Errores y fallas silenciosas**
- `catch {}` o `catch (Exception) { return null / new List<>() / false; }` sin log ni re-throw.
- `throw ex;` (pierde la traza; debe ser `throw;`) o envolver sin `innerException`.
- `FirstOrDefault()`/`?? default` donde "no existe" debería ser 404/excepción.
- Campo de request `enum`/`int`/`bool`/`Guid` no anulable: si el cliente no lo manda llega como
  0/false/vacío sin error. Si ese valor significa algo (0 = Inactivo) = ALTO: `T?` + regla de requerido.
- Varias escrituras sin transacción; `SaveChanges` dentro de un bucle.
- ALTO: `ex.Message`, stack trace, SQL o rutas internas en la respuesta al cliente; configuración
  obligatoria leída con default silencioso (`config["X"] ?? ""`) en vez de fallar al arrancar.

**Asincronía**
- `.Result`, `.Wait()`, `GetAwaiter().GetResult()`, `async void` (salvo eventos de UI/XAF),
  llamada `async` sin `await` (CS4014).
- `Task.WhenAll` sobre consultas que usan el mismo `DbContext` = bloquea ("A second operation
  was started on this context").
- `CancellationToken` recibido en el handler y no propagado a `ToListAsync`/`SaveChangesAsync`/
  `HttpClient` = MEDIO (solo en handlers y consultas, no como regla universal).

**Ciclo de vida y recursos (DI)** — ALTO
- Singleton que recibe un servicio scoped o un `DbContext` (dependencia cautiva).
- Campo `static` mutable compartido entre requests.
- `new HttpClient()` por llamada (usa `IHttpClientFactory`).
- `IDisposable`/`Stream` sin `using`/`await using`.

**EF Core**
- Lazy loading o navegación dentro de un `foreach` (N+1) → `Include` o proyección.
- `ToList()`/`AsEnumerable()` antes de `Where`/`Skip` (filtra en memoria).
- Lecturas sin `AsNoTracking()` o devolviendo la entidad completa en un listado → proyección.
- `IgnoreQueryFilters` sin justificación.
- Migración destructiva no declarada en la tarjeta (el detalle lo ve `agente-revisor-db`).

**EF Core y base de datos** (los conceptos están en `agente-revisor-db`)
- SQL real de una consulta: `query.ToQueryString()` o el log de EF; úsalo para el plan en DEV.
- Migraciones: abre el archivo generado. `RenameColumn` que aparece como `DropColumn` +
  `AddColumn` = CRÍTICO (pérdida de datos). `Down()` vacío sin marcarla irreversible = ALTO.
  Índice en tabla grande: `migrationBuilder.Sql("CREATE INDEX CONCURRENTLY …", suppressTransaction: true)`.
- Varias colecciones con `Include` → `AsSplitQuery()` o proyección (explosión cartesiana).
- Dinero: `decimal` con `HasPrecision(p, s)`; `double`/`float` = ALTO.
- Concurrencia: `IsConcurrencyToken`/`[ConcurrencyCheck]` o `UseXminAsConcurrencyToken()` (Npgsql)
  sobre saldos, stock, estados o folios; unicidad con `HasIndex(...).IsUnique()`, no con
  `AnyAsync` + `Add`.
- `SaveChanges` dentro de un bucle → acumula y guarda una vez (o `ExecuteUpdate` en EF7+).

**AutoMapper** (solo si el repo lo usa)
- Propiedad nueva del DTO sin `ForMember` cuando el nombre no coincide: queda en null sin error.
- Campo nuevo en el DTO que una proyección manual `Select(new Dto { … })` no llena.
- `ProjectTo` con `MapFrom` que no se traduce a SQL.
- `ExplicitExpansion` perdido al insertar o reordenar `ForMember`.

**Consultas dinámicas y seguridad (APIs .NET)**
- `FromSqlRaw`/`ExecuteSqlRaw` con interpolación = CRÍTICO (usa `FromSqlInterpolated` o parámetros).
- Si el repo usa Sieve: propiedad nueva con `[Sieve(CanFilter/CanSort)]` sobre dato sensible (hash, tenant, costo
  interno) = ALTO. Campo de orden/filtro tomado del request sin lista permitida = ALTO.
- Ruta de archivo del usuario sin `Path.GetFullPath` + verificar prefijo; `Process.Start` con
  entrada del usuario; `BinaryFormatter`; `TypeNameHandling.All`; `HttpClient` hacia URL del
  usuario sin lista permitida = CRÍTICO.
- Endpoint o handler nuevo sin `[Authorize]`/policy cuando sus vecinos sí la tienen.

**Seguridad en .NET** (los conceptos y el filtro de evidencia están en `revisor-seguridad`)
- `[AllowAnonymous]` nuevo donde los vecinos tienen `[Authorize]` = ALTO. Falsa alarma: una
  `FallbackPolicy`/`RequireAuthorization()` global ya protege el endpoint sin atributo (rastréala).
- JWT: `TokenValidationParameters` con `ValidateIssuer/ValidateAudience/ValidateLifetime/
  ValidateIssuerSigningKey = false`, `RequireSignedTokens = false`, un `SignatureValidator` que
  devuelve el token sin validar, o `ReadJwtToken` usado como validación = CRÍTICO.
- Identidad tomada de `Request.Headers[...]` o de un `tenantId`/`userId` en query/body en vez de
  `User.FindFirst(...)` o del servicio de usuario actual = CRÍTICO si decide el acceso.
- `IgnoreQueryFilters()` sobre una entidad con filtro global de tenant = IDOR (CRÍTICO), salvo
  que la tarjeta lo justifique.
- Asignación masiva: entidad EF recibida directo como `[FromBody]`, o `TryUpdateModelAsync` sin
  lista de propiedades = ALTO (usa un DTO).
- Dapper/ADO.NET: `Query($"… {x}")`, `SqlCommand`/`NpgsqlCommand` con texto concatenado = CRÍTICO.
- Deserialización además de lo ya listado: `TypeNameHandling.Auto/Objects/Arrays`,
  `NetDataContractSerializer`, `SoapFormatter`, `LosFormatter`, `ObjectStateFormatter`,
  `JavaScriptSerializer` con `SimpleTypeResolver` = CRÍTICO.
- XML del usuario con `DtdProcessing.Parse` o `XmlResolver` no nulo (XXE) = ALTO. Los defaults
  de .NET Core son seguros: reporta solo si se activa explícitamente.
- Zip: `entry.FullName` con `Path.Combine` + `ExtractToFile` sin verificar el prefijo = CRÍTICO.
  Falsa alarma: `ZipFile.ExtractToDirectory` ya lo valida.
- `IFormFile.FileName` usado como nombre o ruta en disco → `Path.GetRandomFileName()`.
  `Path.Combine(base, x)` descarta `base` si `x` es absoluta.
- `Redirect(returnUrl)` sin `Url.IsLocalUrl` → `LocalRedirect` = ALTO.
- `Random`/`Random.Shared` para tokens o códigos → `RandomNumberGenerator`. Secretos o firmas
  comparados con `==`/`SequenceEqual` → `CryptographicOperations.FixedTimeEquals`.
- `new Regex(<entrada del usuario>)` sin `matchTimeout` ni `RegexOptions.NonBacktracking` (net7+)
  = MEDIO, ALTO si se alcanza sin autenticar.
- `UseDeveloperExceptionPage()` o `ProblemDetails` con `exception.ToString()` fuera de
  `IsDevelopment()` = ALTO.
- CORS: `SetIsOriginAllowed(_ => true)` o reflejar `Origin` junto con `AllowCredentials()` = ALTO.
  Falsa alarma: `AllowAnyOrigin()` + `AllowCredentials()` (el framework lo rechaza).
- Autenticación por cookie: POST/PUT/DELETE sin `[ValidateAntiForgeryToken]`/
  `AutoValidateAntiforgeryToken` cuando sus vecinos lo tienen = ALTO. Con JWT bearer no aplica.
- Secretos reales en `appsettings*.json` o `launchSettings.json` versionados = CRÍTICO (user-secrets,
  variables de entorno o Key Vault).
- Si el repo usa Sieve: sin `MaxPageSize`, o `pageSize`/`Take` del request sin tope = MEDIO (ALTO si
  es anónimo o la tabla crece sin límite).
- `ILogger` registrando el request completo, el encabezado `Authorization`, contraseñas o tokens = ALTO.

**Silenciar en vez de arreglar (.NET)**
`#pragma warning disable`, `<NoWarn>`, `<Nullable>disable</Nullable>`, `!` (null-forgiving) sin
guard previo, `[Fact(Skip=…)]`/`[Theory(Skip=…)]`, cambios que relajan `.editorconfig`,
`Directory.Build.props` o `TreatWarningsAsErrors`.

**Tipos**
- Cast `(T)obj` sin comprobar → `is T t`/`as`. Strings mágicos para propiedades → `nameof`.

## Propagación en .NET
Con las piezas que el repo use: entidad → `IEntityTypeConfiguration` → DTO → perfil de mapeo (AutoMapper) o proyección
`Select`/`ProjectTo` → validador (FluentValidation) → caso de uso de creación **y** de actualización →
configuración de filtros/orden (Sieve) si se filtra u ordena.

## Tests en .NET
- Simula código propio: `Mock<IMapper>`, `Mock<IMediator>`, repositorios propios, `Verify` de
  llamadas internas. Para mapeos, el test usa el Profile real (`MapperConfiguration` +
  `AssertConfigurationIsValid`).
- Proveedor equivocado: `UseInMemoryDatabase` o SQLite cuando el criterio depende de un unique,
  una transacción, mayúsculas o SQL de PostgreSQL.
- `Thread.Sleep`/`Task.Delay` fijos o estado `static` compartido entre tests = MEDIO.

## Limpieza en .NET
- Depuración olvidada: `Console.WriteLine`, `Debug.WriteLine`, `Trace.WriteLine`.
- `using` sin uso. Equivalentes de librería estándar (`stdlib:`), condicionados al TFM:
  validar null/blanco a mano → `string.IsNullOrWhiteSpace`/`ThrowIfNull`; diccionario como caché
  → `IMemoryCache`; reintentos a mano → Polly/Resilience si ya está instalado; `Thread.Sleep` en
  bucles async → `PeriodicTimer`; cargar-recorrer-guardar → `ExecuteUpdate` (EF7+); paginar en
  memoria → `Skip/Take` en la consulta.

## Falsas alarmas en .NET (no reportar)
- Falta de try/catch cuando hay middleware global de excepciones o un `IPipelineBehavior` de
  MediatR que lo cubre.
- Falta de validación cuando hay un `AbstractValidator` registrado en el pipeline (rastrea uno).
- `ConfigureAwait(false)` ausente en ASP.NET Core (no aplica).
- Interfaz con una sola implementación que existe para DI o para sustituir una frontera real
  en tests (`IClock`, `IEmailSender`): es patrón, no yagni.
- No exigir `sealed`, `record` ni otra convención que el repo no usa.
