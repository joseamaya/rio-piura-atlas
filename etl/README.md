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
├── check_data.py           # valida fuentes, capas y archivos publicados
├── tests/                  # pruebas de geometría y muestreo
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
```

Los tres escriben en `data/raw/` y se niegan a sobrescribir sin `--force`. No
modifican `data/processed/`.

## Construcción de capas

`build_layers.py` convierte los JSON crudos (cuenca, subcuencas, red, agua) en
GeoJSON simplificado y genera el relieve sombreado para la web.

```bash
python3 etl/build_layers.py
```

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

`check_data.py` verifica que las fuentes tengan los campos obligatorios, que cada
capa apunte a un `id` existente, que los cortes tengan perfil, que la malla de
elevación coincida con su metadata y que el presupuesto de datos no se dispare.
No necesita DEM ni conexión.

Los scripts del laboratorio (`../blender/projects/piura/scripts/`) resolvieron el
DEM y la textura del diorama; este ETL reutiliza esos productos. Los límites y la
red se pueden regenerar con los scripts de descarga de arriba.
