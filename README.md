# Río Piura Atlas

Atlas interactivo, documentado y citable de la cuenca del río Piura: qué es, cómo
funciona, dónde se desborda y qué se construyó para contenerlo.

> **Sitio publicado:** <https://joseamaya.github.io/rio-piura-atlas/>
>
> **Estado:** fase 1 en curso. El sitio ya funciona con las capas verificadas
> (cuenca, subcuencas, red, agua, relieve, cortes transversales y maqueta 3D).
> Faltan las capas que dependen de datos por solicitar: caudales, obras y manchas de
> inundación.

## Para quién

Público general, docentes, periodistas, gestores municipales y cualquier persona que
necesite explicar o entender el río Piura sin ser especialista.

## Qué es

- Un **atlas**: mapa 2D/3D de la cuenca, sus subcuencas, su red hídrica, sus obras y
  sus cortes, con la fuente de cada capa a la vista.
- Un **visor de escenarios**: capas de inundación **históricas y documentadas**
  (1983, 1998, 2017), no pronósticos.

## Qué NO es

- **No es un sistema oficial de alerta.** No emite avisos, no usa datos en tiempo
  real y no reemplaza a SENAMHI, ANA, INDECI ni al ENFEN.
- **No es un modelo hidráulico.** No calcula tirantes ni manchas de inundación
  nuevas: muestra lo que ya está documentado.
- **No es cartografía oficial.** Es una interpretación trazable de fuentes públicas.

## Cómo se sostiene el rigor

Cada capa, cifra y rótulo del atlas apunta a una entrada de [`data/sources.yml`](data/sources.yml)
con institución, escala, fecha, método, licencia e incertidumbre. Lo que no tiene
fuente, no se dibuja; lo que es interpretación, se marca como tal.

## Estructura

```
docs/                 por qué y cómo (empezar por 01-alcance.md)
docs/00-plan-fase-0.md  plan de trabajo inmediato
docs/08-pendientes.md   estado y pendientes de la fase 1
data/sources.yml      registro maestro de fuentes
data/raw/             datos tal como llegan (inmutables)
data/processed/       datos derivados, reproducibles
etl/                  descargas, transformación, validación y pruebas
web/                  sitio del atlas (Astro + MapLibre + Three.js)
.github/workflows/    CI: build del sitio y validación de datos
LICENSES/             licencias de datos y de contenido
```

## Cómo ejecutarlo

```bash
# dependencias del ETL
python3 -m pip install -r etl/requirements.txt

# datos crudos (opcional: reconstruye data/raw/)
python3 etl/download_ana.py --force
python3 etl/download_hydrorivers.py --force
python3 etl/download_osm_water.py --force

# capas (requiere el DEM del laboratorio de modelos)
python3 etl/build_layers.py
python3 etl/build_cortes.py
python3 etl/check_data.py

# sitio
cd web
npm install
npm run dev        # http://localhost:4321
npm run build      # estático en web/dist

# build con las rutas de GitHub Pages
SITE_URL=https://joseamaya.github.io BASE_PATH=/rio-piura-atlas npm run build
```

El despliegue es automático: cada push a `main` pasa las comprobaciones y publica
en GitHub Pages.

El presupuesto se mide por página. La portada y las páginas de texto no cargan
librerías 3D. `/mapa` añade MapLibre (~220 kB comprimidos) y las capas vectoriales
(~630 kB); la malla de elevación para cortes (~443 kB) solo se descarga al dibujar
un corte. `/maqueta` es la excepción declarada: 6,3 MB de GLB más Three.js, y por eso
solo se descarga al abrir esa página.

## Calidad

- `python3 etl/check_data.py` valida fuentes, capas, cortes, resoluciones, malla de
  elevación y presupuesto de datos.
- `python3 -m unittest discover -s etl/tests -v` prueba la geometría del ETL.
- En `web/`: `npm run check` (tipos), `npm run check:links` (enlaces y anclas) y
  `npm run check:a11y` (axe WCAG A/AA en Chrome headless). `npm run verify` ejecuta
  la secuencia completa.
- GitHub Actions compila el sitio, valida datos y ejecuta las tres comprobaciones web
  en cada push.

## Qué hay hoy

| Página | Contenido |
|---|---|
| `/` | qué es el atlas y qué no es |
| `/mapa` | relieve, cuenca ANA, 9 subcuencas, red hídrica, cortes transversales, lagunas y ciudades |
| `/maqueta` | bloque 3D recortado a la cuenca (Three.js) |
| `/escenarios` | los eventos documentados y lo que falta |
| `/fuentes` | catálogo generado desde `data/sources.yml`, con enlaces por capa |

## Cómo citar

Ver [`docs/06-como-citar.md`](docs/06-como-citar.md) y [`CITATION.cff`](CITATION.cff).
Versión citable pendiente de publicación (Zenodo) al cerrar la fase 1.

## Licencias

Contenido y textos: CC BY 4.0. Código: MIT. Los datos conservan la licencia de su
fuente; ver [`LICENSES/DATOS.md`](LICENSES/DATOS.md).

## Contexto

Nace como pieza hermana del laboratorio [Del Trazo al Modelo](../blender), que aporta
el diorama 3D de la cuenca (`projects/piura`) y su versión recortada
(`projects/piura-cuenca`).
