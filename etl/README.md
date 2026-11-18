# ETL

Scripts que descargan `data/raw/` y lo convierten en `data/processed/`. Cada script
debe:

1. poder ejecutarse solo, con una ruta de entrada y una de salida;
2. fallar de forma explícita si falta un dato;
3. no reescribir `data/raw/` sin `--force` (los scripts `build_*` nunca lo tocan);
4. registrar en consola qué produjo y con qué fuente (`id` de `sources.yml`).

## Convención

```
etl/
├── download_<fuente>.py    # trae el dato a raw/
├── build_<producto>.py     # transforma raw/ en processed/
├── download_senamhi_historico.py  # API histórica por estación
├── build_senamhi_historico.py     # tabla, cobertura y calidad de estaciones
├── senamhi.py              # parseo, QC, cobertura y hashes de SENAMHI
├── senamhi_geo.py          # clasificación de estaciones contra la cuenca ANA
├── geoservicios.py         # parseo de WFS/WMTS, hojas y leyendas
├── audit_geoservicios.py   # auditoría local de INGEMMET y ZEE Piura
├── topology.py             # auditoría y reconciliación de la partición
├── check_data.py           # valida fuentes, capas y archivos publicados
├── tests/                  # geometría, topología, calidad y contrato de datos
└── requirements.txt
```

## Descargas reproducibles

```bash
# límites ANA (cuenca y subcuencas; requiere shapely)
python3 etl/download_ana.py --force

# red HydroRIVERS (~95 MB de ZIP, se cachea en data/raw/hydrorivers/)
python3 etl/download_hydrorivers.py --force

# cuerpos de agua OSM (Overpass; divide en teselas y reintenta endpoints)
python3 etl/download_osm_water.py --force

# vectores oficiales de la inundación de 2017 (Copernicus EMSR199, AOI10 + AOI11)
python3 etl/download_emsr199.py --force
```

Los cuatro escriben en `data/raw/` y se niegan a sobrescribir sin `--force`. No
modifican `data/processed/`.

## Series históricas de SENAMHI

```bash
# catálogo y series diarias de las 20 estaciones de Piura
python3 etl/download_senamhi_historico.py

# tabla diaria, catálogo, inventario, cobertura, huecos y metadatos
python3 etl/build_senamhi_historico.py
```

El download guarda **bytes crudos** en `data/raw/senamhi/` (ignorado por Git),
con SHA-256 por archivo en `manifest.json`, y se niega a sobrescribir sin
`--force`. El build verifica los hashes, conserva nulos, no interpola, añade
banderas `qc_*` y no publica en `web/public/`: la licencia de reutilización no
está confirmada. `--limit N` y `--raw-dir`/`--out-dir` permiten una prueba sin
tocar el repositorio.

Salidas de `build_senamhi_historico.py` en `data/processed/senamhi/`:

- `estaciones_piura.csv` — tabla diaria con nulos y banderas.
- `catalogo_estaciones.csv` — las 293 estaciones del catálogo.
- `inventario_estaciones.csv` — las 20 seleccionadas y sus hashes.
- `cobertura_estaciones.csv` — fechas, días faltantes, nulos, extremos y
  clasificación geográfica.
- `huecos_estaciones.csv` — intervalos contiguos faltantes.
- `metadata.json` y `hashes.sha256`.

## Auditoría de servicios geoespaciales

```bash
# solo revisión local; GEOCATMIN no presenta una cadena TLS confiable aquí
python3 etl/audit_geoservicios.py --insecure
```

Consulta metadatos de INGEMMET y ZEE Piura, cuenta polígonos contra la cuenca
ANA, verifica CRS, WFS/WMTS, paginación y leyendas, y descarga **solo el
subconjunto de geología de la cuenca**. Las salidas quedan en
`data/processed/geoservicios/` (ignorado por Git) y no se publican. El certificado
TLS se verifica por defecto; `--insecure` es una opción explícita y documentada.

## Construcción de capas

`build_layers.py` convierte los JSON crudos (cuenca, subcuencas, red, agua) en
GeoJSON simplificado, recorta la red con intersección exacta, genera las referencias
de Poechos y del canal, la mancha de 2017 (con observaciones por fecha y sensor) y el
relieve sombreado para la web.

```bash
python3 etl/build_layers.py
```

Salidas nuevas de `build_layers.py`:

- `web/public/data/flood_2017.geojson` — vector oficial EMSR199 (AOI10 + AOI11),
  filtrado a `Flooded Area`, disuelto, simplificado y reproyectado a WGS84. Publica
  áreas por observación, solapamiento, unión original, área filtrada, simplificada,
  publicada en UTM y geodésica.
- `web/public/data/obras.geojson` — Poechos y canal Daniel Escobar, esquemáticos.
- `web/public/data/flood_2017.jpg` — figura estática para `/escenarios`.

La mancha requiere `data/raw/emsr199/`; si falta, `build_layers.py` omite esa capa y
conserva el GeoJSON ya publicado. Los ZIP oficiales no se versionan.

`build_cortes.py` genera los cortes transversales de referencia, sus perfiles y la
malla de elevación que usa el mapa para los cortes dibujados por el visitante.

```bash
python3 etl/build_cortes.py
```

Necesita el DEM del laboratorio de modelos en
`../blender/projects/piura/data/dem.npz` (se puede cambiar con la variable
`PIURA_DEM`). Si no lo encuentra, `build_layers.py` genera solo las capas vectoriales
y `build_cortes.py` falla de forma explícita, porque sin DEM no hay perfiles.

Salidas de `build_cortes.py`:

- `data/processed/cortes.geojson` — cinco transectos de referencia.
- `data/processed/cortes_perfiles.json` — distancia y cota de cada transecto.
- `data/processed/dem_grid.bin` + `dem_grid.meta.json` — malla `Int16` para cortes
  dibujados a mano; se carga a demanda en el navegador.

## Validación y pruebas

```bash
python3 etl/check_data.py
python3 -m unittest discover -s etl/tests -v
```

`check_data.py` verifica fuentes, validez y topología de las capas, **solapamientos
por par de subcuencas, superficie fuera por subcuenca, huecos por componente y
agujeros interiores**, áreas geodésicas, líneas fuera de cuenca, perfiles y su
resolución efectiva, malla de elevación, estructura del GLB y presupuesto de datos.
No necesita DEM ni conexión.

`topology.py` concentra la auditoría y la reconciliación. La validez se comprueba
**antes** de reparar: `inspect_geometry()` no toca la geometría y
`repair_to_polygonal()` solo actúa cuando se autoriza, dejando un registro con el
motivo, el tipo reparado y los componentes descartados. `download_ana.py` usa esa
reconciliación para repartir los slivers de simplificación sin crear superficie
nueva; si una subcuenca trae un agujero interior o una geometría inválida, el proceso
se detiene salvo autorización explícita.

`reconciliacion.fidelidad` publica IoU, diferencia simétrica, Hausdorff, distancia
media y p95 entre límites, además de la superficie asignada por solapamiento y por
proximidad. `check_data.py` puede terminar con avisos de fidelidad; no se ocultan
para forzar un resultado verde.

Los scripts del laboratorio (`../blender/projects/piura/scripts/`) resolvieron el
DEM y la textura del diorama; este ETL reutiliza esos productos. Los límites y la
red se pueden regenerar con los scripts de descarga de arriba.
