# Río Piura Atlas

Atlas interactivo, documentado y citable de la cuenca del río Piura: qué es, cómo
funciona, dónde se desborda y qué se construyó para contenerlo.

> **Sitio publicado:** <https://joseamaya.github.io/rio-piura-atlas/>
>
> **Estado:** fase 1 en curso. El sitio ya funciona con las capas verificadas
> (cuenca, subcuencas, red, agua, relieve, cortes transversales y maqueta 3D), la
> mancha oficial de la inundación de 2017 y las obras esquemáticas de Poechos y el
> canal Daniel Escobar. Faltan las capas que dependen de datos por solicitar:
> caudales, bocatomas/diques y las manchas de 1983 y 1998.

## Para quién

Público general, docentes, periodistas, gestores municipales y cualquier persona que
necesite explicar o entender el río Piura sin ser especialista.

## Qué es

- Un **atlas**: mapa 2D/3D de la cuenca, sus subcuencas, su red hídrica, sus obras
  esquemáticas y sus cortes, con la fuente de cada capa a la vista.
- Un **visor de escenarios**: la mancha oficial de la inundación de 2017 y el relato
  documentado de 1983 y 1998. No es un pronóstico.

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
docs/09-auditoria-estabilizacion.md  auditoría, evidencias y límites
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
python3 etl/download_emsr199.py --force

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
(~650 kB iniciales); la mancha de 2017 (~518 kB) se carga solo al activar esa capa,
y la malla de elevación para cortes (~443 kB) solo al dibujar un corte. `/maqueta`
es la excepción declarada: 1,6 MB de GLB, ~250 kB de decodificador Draco y Three.js;
solo se descarga al abrir esa página.

## Calidad

- `python3 etl/check_data.py` valida fuentes, **solapamientos por par de subcuencas,
  superficie fuera por subcuenca, huecos por componente y agujeros interiores**, áreas
  geodésicas, cortes, resolución efectiva, malla de elevación, GLB y presupuesto de
  datos. Las tolerancias están justificadas a escala 1:100 000.
- `python3 -m unittest discover -s etl/tests -v` ejecuta 38 pruebas de geometría,
  topología sintética y contrato de datos publicados.
- En `web/`: `npm run check` (tipos), `npm run check:links` (enlaces y anclas),
  `npm run check:a11y` (axe WCAG A/AA en Chrome headless) y `npm run test:e2e`
  (Playwright: mapa, dibujo de perfil, capas, ficha, teclado, fallo de red, móvil y
  maqueta). `npm run verify` ejecuta la secuencia completa.
- GitHub Actions compila el sitio, valida datos y ejecuta las comprobaciones web en
  cada push.

## Qué hay hoy

| Página | Contenido |
|---|---|
| `/` | qué es el atlas y qué no es |
| `/mapa` | relieve, cuenca ANA, 8 subcuencas + Bajo Piura derivado, red hídrica, inundación 2017, referencias de obras, cortes transversales, lagunas y ciudades |
| `/maqueta` | la cuenca, el desierto y el mar en un bloque 3D (Three.js + Draco) |
| `/escenarios` | los eventos documentados, la mancha de 2017 y lo que falta |
| `/fuentes` | catálogo generado desde `data/sources.yml`, con enlaces por capa |

## Cómo citar

Ver [`docs/06-como-citar.md`](docs/06-como-citar.md) y [`CITATION.cff`](CITATION.cff).
Versión 0.2.1; release en GitHub y DOI pendiente de Zenodo.

## Licencias

Contenido y textos: CC BY 4.0. Código propio: MIT. Dependencias de terceros:
[`LICENSES/CODIGO.md`](LICENSES/CODIGO.md). Los datos conservan la licencia de su
fuente; ver [`LICENSES/DATOS.md`](LICENSES/DATOS.md).

## Contexto

Nace como pieza hermana del laboratorio [Del Trazo al Modelo](../blender), que aporta
el diorama 3D de la cuenca (`projects/piura`). La versión web se exporta con
compresión Draco desde `projects/piura/scripts/export_web.py` (21 MB → 1,6 MB); el
resultado (`projects/piura/exports/piura-web.glb`) se copia a
`web/public/models/piura.glb`.
