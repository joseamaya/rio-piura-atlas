# 04 · Datos

## Estructura

```
data/
├── sources.yml      registro maestro de fuentes (se edita a mano)
├── raw/             lo que se descarga o se recibe, sin tocar
└── processed/       lo que consume el sitio, generado por etl/
```

`raw/` es inmutable: si una fuente se actualiza, se guarda como versión nueva.
`processed/` se puede borrar y regenerar. `limits.json` conserva `ring`/`holes` y,
si la fuente trae varios polígonos, `polygons`; los agujeros no se descartan. También
guarda un bloque `reconciliacion` con el CRS métrico, las caras del grafo de límites,
los slivers asignados, los solapamientos eliminados y los cambios de área por
subcuenca. La cuenca y las subcuencas comparten la rejilla de 1e-6° (~0,11 m) para
que el redondeo no abra slivers en el borde.

Los archivos crudos se pueden reconstruir con `etl/download_ana.py`,
`etl/download_hydrorivers.py`, `etl/download_osm_water.py` y
`etl/download_emsr199.py`. Los scripts se niegan a sobrescribir sin `--force`.
`etl/check_data.py` valida que cada capa apunte a una fuente existente y que los
productos derivados sean coherentes.

La mancha de 2017 se construye en dos pasos: `download_emsr199.py` guarda los ZIP
oficiales en `data/raw/emsr199/` (ignorados por Git) y `build_layers.py` publica una
versión simplificada en `web/public/data/flood_2017.geojson`. Cada AOI conserva
`observaciones` por fecha y sensor (`src_date` y `source_nam` del DBF), además del
área original y el área simplificada. Las obras esquemáticas (Poechos y canal Daniel
Escobar) se generan en `build_layers.py` desde `water.json` y el eje manual del canal;
no se descargan de ANA/PECHP.

## Formatos

| Tipo | Formato | Motivo |
|---|---|---|
| Ráster (DEM, imágenes) | COG (`*.tif`) | lectura por teselas sin descargar todo |
| Vectores grandes | PMTiles | un archivo, rápido en móvil |
| Vectores pequeños | GeoJSON simplificado | legible y versionable |
| Perfiles de corte | JSON + binario Int16 | perfil del DEM y malla de elevación sin cargar el ráster completo |
| Tablas | CSV | universal |
| Metadatos | YAML | legible y con comentarios |

## Registro de fuentes (`sources.yml`)

Cada entrada:

```yaml
- id: ana-subcuencas
  titulo: Unidades Hidrográficas Pfafstetter 1:100 000
  institucion: Autoridad Nacional del Agua
  url: https://...
  fecha: 2008-01-05
  escala: 1:100000
  licencia: dato público
  estado: disponible        # disponible | por_solicitar | por_verificar
  metodo: descarga directa
  grupo: Límites, relieve y red
  certeza: medido           # medido | derivado | documentado | interpretacion | por_verificar
  tipo: dataset             # dataset | documento | prensa | elaboracion_propia
  documento: Unidades Hidrográficas Pfafstetter, R.M. 033-2008-AG
  consultado: "2026-11-16"
  notas: R.M. 033-2008-AG
```

`documento`, `pagina` y `consultado` son opcionales. `pagina` solo se usa cuando hay
un `documento` concreto. Una fuente de `tipo: elaboracion_propia` debe atribuirse a
«Río Piura Atlas» y no puede declararse `certeza: medido`.

Todo elemento publicado debe referenciar un `id` existente en este archivo.

## Nombres de archivo

`<fuente>__<tema>__<fecha>__v<n>.<ext>`

Ejemplo: `ana__subcuencas__2008__v1.geojson`

Sin espacios, sin acentos, sin mayúsculas.

## Versionado

- Git para textos, metadatos, scripts y GeoJSON pequeños.
- Los archivos pesados (COG, PMTiles) **no** van en Git: se publican como *release* o
  en almacenamiento estático, y se enlazan desde `sources.yml` con su hash.
- Cada versión publicada del atlas queda etiquetada (`v0.2.0`) y citada en
  `docs/06-como-citar.md`.

## Privacidad y licencias

- Nada de datos personales.
- Los datos de terceros conservan su licencia; se listan en `LICENSES/DATOS.md`.
- Si una licencia no permite redistribuir, se enlaza a la fuente y no se copia.
