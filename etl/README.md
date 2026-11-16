# ETL

Scripts que convierten `data/raw/` en `data/processed/`. Cada script debe:

1. poder ejecutarse solo, con una ruta de entrada y una de salida;
2. fallar de forma explícita si falta un dato;
3. no modificar nunca `data/raw/`;
4. registrar en consola qué produjo y con qué fuente (`id` de `sources.yml`).

## Convención

```
etl/
├── download_<fuente>.py    # trae el dato a raw/
├── build_<producto>.py     # transforma raw/ en processed/
└── requirements.txt
```

## Estado

`build_layers.py` ya funciona: convierte los JSON crudos (cuenca, subcuencas, red,
agua) en GeoJSON simplificado y genera el relieve sombreado para la web.

```bash
python3 etl/build_layers.py
```

Necesita el DEM del laboratorio de modelos en
`../blender/projects/piura/data/dem.npz` (se puede cambiar con la variable
`PIURA_DEM`). Si no lo encuentra, genera solo las capas vectoriales.

Los scripts del laboratorio (`../blender/projects/piura/scripts/`) resolvieron el
DEM, la red hídrica, los límites y la textura del diorama; este ETL reutiliza esos
productos, no los recalcula.
