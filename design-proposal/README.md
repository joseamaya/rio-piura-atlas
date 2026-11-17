# Propuesta visual UI-01 · Río Piura Atlas

Prototipos aislados de la propuesta **«Lámina y margen»** para el Atlas del río Piura. No forman parte de la aplicación de producción y no modifican `web/`.

## Cómo verlos

Desde la raíz del repositorio:

```bash
python3 -m http.server 4330
```

Abre <http://127.0.0.1:4330/design-proposal/index.html>.

- `home.html` — portada responsive.
- `mapa.html` — mapa MapLibre con datos reales. Prueba `mapa.html?capa=inundacion`.
- `escenarios.html` — línea de tiempo, capítulos y lámina 2017.
- `fuentes.html` — catálogo de 30 fuentes con filtros.
- `maqueta.html` — la maqueta 3D como espécimen.
- `sistema.html` — paleta, tipografía, espaciado, símbolos y componentes.

El mapa y los filtros necesitan el servidor local porque cargan GeoJSON y `assets/sources.js`. Las capturas de `captures/` se pueden abrir sin servidor.

## Qué hay aquí

```
index.html              galería de la propuesta
home.html               portada
mapa.html               mapa interactivo propuesto
escenarios.html         escenarios históricos
fuentes.html            catálogo de fuentes
maqueta.html            pieza 3D
sistema.html            hoja de sistema visual
styles/                 tokens, base, componentes y estilos de página
assets/                 fuentes, imágenes, GeoJSON auxiliar y datos de fuentes
captures/               capturas de los mockups (1440×900 y 390×844)
tools/                  scripts de preparación de activos
```

## Qué es real y qué es propuesta

- **Mapa:** MapLibre con los GeoJSON publicados: cuenca y subcuencas ANA, red HydroRIVERS, agua y lugares OSM, obras esquemáticas, cortes y la mancha oficial de Copernicus EMSR199. La **geometría no se modificó**; el color y la interfaz son propuesta.
- **Relieve:** derivado del mismo DEM del ETL (`dem.npz`). `tools/build_relief.py` solo reclasifica la paleta y el sombreado; no cambia altitudes ni extensión. El original sigue en `web/public/data/relieve.jpg`.
- **Maqueta:** render del GLB existente `web/public/models/piura.glb`. `tools/hero-scene.html` reproduce la escena, oculta rótulos para la portada y conserva un subconjunto en la página 3D. No se modificó el modelo.
- **Inundación:** vector real de Copernicus EMSR199. La trama diagonal es una propuesta de lectura, no una nueva geometría.
- **Fuentes:** los 30 registros se generan desde `data/sources.yml` con `tools/build_sources.py`. No se inventó ninguna fuente.
- **Cifras:** provienen de la documentación del proyecto; las que tienen límite o discrepancia lo declaran.
- **Esquemas:** la pendiente y el trasvase son diagramas conceptuales, rotulados como tales. No son geografía.

## Activos y licencias

- **Newsreader** y **Archivo**: SIL Open Font License 1.1. Textos de licencia en `assets/fonts/OFL-*.txt`.
- **Copernicus DEM**: ESA/Airbus, uso libre con atribución.
- **ANA, HydroRIVERS, OpenStreetMap, Copernicus EMSR199**: conservan la licencia de su fuente; ver `../LICENSES/DATOS.md` y `../data/sources.yml`.
- **Render 3D**: proyecto Río Piura Atlas / laboratorio Del Trazo al Modelo.

## Scripts

```bash
python3 design-proposal/tools/build_relief.py     # relieve propuesto desde el DEM
python3 design-proposal/tools/build_mini_map.py   # mini mapa SVG de la portada
python3 design-proposal/tools/build_sources.py    # fuentes reales para el prototipo
```

`tools/hero-scene.html` se usa con un servidor local y Playwright para el render 3D; no es una página pública de la propuesta.

## Límites

- Es un prototipo visual: la maqueta es un render estático y los controles 3D no están conectados.
- El mapa es funcional para capas, ficha, corte de ejemplo y deep link de inundación; no reproduce todos los estados del mapa de producción.
- Los filtros de Fuentes son una propuesta funcional aislada; su inclusión en producción requiere aprobación.
- No se probó en Safari/iOS ni con lector de pantalla real.
- No se publicó ni se mergeó nada.

## Documentación

- `../docs/ui/01-auditoria-visual.md`
- `../docs/ui/02-direccion-de-arte.md`
- `../docs/ui/03-propuesta-redisenio.md`
- `../docs/ui/04-plan-implementacion.md`
