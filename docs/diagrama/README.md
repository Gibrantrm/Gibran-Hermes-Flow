# Diagrama Archify

- [Vista estática PNG](gibran-flow.png), visible en el README de GitHub.
- [Vector SVG](gibran-flow.svg), exportación canónica con tema automático.
- [HTML interactivo](gibran-flow.html): descarga el archivo mediante **Download raw
  file** en GitHub y ábrelo localmente. Incluye visor, fuentes y estilos; no
  requiere subir el código a un servicio de previsualización.
- [Fuente JSON editable](candidate.json).
- [Resumen portable de verificación](verificacion.json).

El mapa muestra el motor común y las entradas feature/bug/nuevo. QA y revisión
son dos fases del **mismo perfil revisor**. Los detalles y excepciones están en
las tarjetas informativas del HTML y en las skills enlazadas por cada nodo.
El diagrama no sustituye la configuración del runtime ni garantiza aislamiento.

## GitHub y Pages

**Estado de entrega:** código, HTML, JSON y previews publicados en GitHub.
Las fuentes enlazadas al commit fijado ya están disponibles. Pages ya fue
habilitado por el propietario; el despliegue está en verificación.
Hasta que haya una URL comprobada, descarga el HTML.

GitHub muestra imágenes SVG/PNG en Markdown, pero no ejecuta el JavaScript de
Archify dentro del README. El archivo HTML en la vista de código tampoco es
una sesión del visor. GitHub Pages sí puede servir HTML/CSS/JS estáticos.

El workflow `diagrama-pages.yml` intenta habilitar Pages y publica **solo una lista
explícita de artefactos del diagrama**, nunca el código completo, configs ni
recibos locales. Usa `contents: read`, `pages: write` e `id-token: write`.
No ejecuta el flujo, no arranca apps y no accede a bases de datos.

Si GitHub no permite habilitar Pages con `GITHUB_TOKEN`, el propietario debe ir a
**Settings → Pages → Build and deployment → Source → GitHub Actions** y ejecutar
el workflow. No cambies la visibilidad de un repo privado para resolverlo.
Mientras no haya un despliegue verificado, usa el HTML descargado.

### Diagnóstico del primer reintento

El intento 2 del [run 44936048690](https://github.com/Gibrantrm/Gibran-Hermes-Flow/actions/runs/44936048690)
usó el commit `af2862b`. Configurar Pages, preparar archivos y subir el artefacto
terminaron correctamente. El upload finalizó `github-pages` con ID `14721949488`
a las 19:49:15.880 UTC; a las 19:49:16.249 UTC el descubrimiento de deploy-pages
devolvió cero artefactos. Posteriormente la API del mismo run sí listó ese
artefacto, no expirado.

No faltaba el upload ni había diferencia de nombre/ruta. La inconsistencia
observada está en el descubrimiento del artefacto; su causa interna en GitHub
no se puede determinar solo con estos logs. El warning de `punycode` no fue
el error que detuvo el despliegue. Se verifica una ejecución nueva desde `main`
sin cambiar versiones, permisos, bytes del diagrama ni pasos del workflow.

La ejecución nueva `44943224309` reprodujo el mismo fallo: upload finalizado
con ID `14722353100`, seguido de cero resultados al desplegar en el mismo job.
Se separan ahora preparación y despliegue con `needs: preparar`, como recomienda
[deploy-pages](https://github.com/actions/deploy-pages/tree/v4#usage):
el despliegue comienza después de finalizar correctamente el job que subió el
artefacto. Se conserva la lista de archivos, nombres y versiones de actions;
no se añaden permisos, esperas fijas ni reintentos que oculten fallos.

Documentación oficial:
- [Qué es GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).
- [Diagramas nativos en GitHub](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams).

## Reproducir

Se generó con Archify **3.1.0**, sin instalar ni actualizar paquetes. Node 22.14.0
en Windows reportó identificadores de volumen inconsistentes entre `stat` y
`fstat`; se usó el Node **22.23.2 ya instalado**, que devuelve identidad coherente.
No se desactivó ninguna comprobación de publicación.

Desde la raíz del clon, indica la ruta de **tu** instalación de Archify:

```powershell
$archify = Read-Host 'Ruta de bin\archify.mjs de tu instalación de Archify'
node $archify finalize workflow .\docs\diagrama\candidate.json .\docs\diagrama\gibran-flow.html --repo-root . --quality showcase --json
```

Si regeneras un HTML que ya tiene evidencia de navegador, agrega
`--out-dir .\docs\diagrama\review-2` (y otro directorio nuevo para cada corrida).
Actualiza las fuentes del JSON a un commit que contenga los cambios que quieras
documentar; no cites bytes sin commit como si pertenecieran al commit fijado.

Se ejecutaron `validate`, `deliver`, `check` estricto y `browser-check`; todos
pasaron sin diagnósticos. También se abrió el visor, se exportaron SVG/PNG con su
menú y se inspeccionó visualmente la imagen PNG. No se solicitó el protocolo
adicional de capturas `visual-check`: no se afirma haberlo ejecutado.

Los recibos completos contienen rutas de la máquina y se excluyen. El resumen
portable publicado conserva hashes y resultados, **no reemplaza** los sidecars
de procedencia estricta de Archify. Para obtenerlos, vuelve a ejecutar `finalize`.
`.gitattributes` conserva los bytes canónicos de HTML/SVG y exceptúa únicamente
sus espacios al final de línea generados por Archify; no se editó el HTML
después de verificarlo. Los archivos escritos a mano mantienen el chequeo normal.

Licencias de terceros: [Archify](ARCHIFY-LICENSE.txt) y
[JetBrains Mono](JetBrainsMono-OFL.txt). No son una licencia del proyecto Gibran Flow.
