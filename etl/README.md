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

Todavía no hay scripts. En la fase 0 solo se identifican las fuentes; la
implementación empieza en la fase 1.

Los scripts del laboratorio de modelos (`../blender/projects/piura/scripts/`) sirven
como referencia: ya resuelven DEM, red hídrica, límites y textura.
