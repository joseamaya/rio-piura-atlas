# 04 · Datos

## Estructura

```
data/
├── sources.yml      registro maestro de fuentes (se edita a mano)
├── raw/             lo que se descarga o se recibe, sin tocar
└── processed/       datos derivados, locales; solo lo autorizado se copia a web/public
```

`raw/` es inmutable: si una fuente se actualiza, se guarda como versión nueva.
`processed/` se puede borrar y regenerar. No todo `processed/` es publicable:
una fuente puede estar procesada y seguir bloqueada por licencia o semántica.
Solo los productos autorizados se copian a `web/public/data/`. `limits.json` conserva `ring`/`holes` y,
si la fuente trae varios polígonos, `polygons`; los agujeros no se descartan. También
guarda un bloque `reconciliacion` con el CRS métrico, las caras del grafo de límites,
los slivers asignados, los solapamientos eliminados, los cambios de área por
subcuenca, la superficie asignada por solapamiento/proximidad y las métricas de
fidelidad (IoU, diferencia simétrica, Hausdorff, distancia media y p95). La cuenca y
las subcuencas comparten la rejilla de 1e-6° (~0,11 m) para que el redondeo no abra
slivers en el borde. Cada registro guarda `precision_decimales` y, si hubo que
fusionar componentes que se tocaban en un punto, `componentes_originales`,
`componentes_serializados` y `fusionado`.

La validez se comprueba antes de reparar. Cualquier reparación queda en
`reconciliacion.reparaciones` con nombre, motivo, tipo original, tipo reparado,
partes poligonales y componentes descartados. Un registro serializado que se vuelve
inválido por redondeo se detecta y se resuelve añadiendo decimales, no con una
reparación silenciosa.

Los archivos crudos se pueden reconstruir con `etl/download_ana.py`,
`etl/download_hydrorivers.py`, `etl/download_osm_water.py` y
`etl/download_emsr199.py`. Los scripts se niegan a sobrescribir sin `--force`.
`etl/check_data.py` valida que cada capa apunte a una fuente existente y que los
productos derivados sean coherentes.

La mancha de 2017 se construye en dos pasos: `download_emsr199.py` guarda los ZIP
oficiales en `data/raw/emsr199/` (ignorados por Git) y `build_layers.py` publica una
versión simplificada en `web/public/data/flood_2017.geojson`.

Las series históricas de SENAMHI se descargan en `data/raw/senamhi/` y se
procesan en `data/processed/senamhi/` con
`download_senamhi_historico.py` y `build_senamhi_historico.py`. El download
conserva los bytes crudos y un SHA-256 por archivo; el build genera
`estaciones_piura.csv` (tabla diaria con nulos y banderas `qc_*`),
`catalogo_estaciones.csv`, `inventario_estaciones.csv`,
`cobertura_estaciones.csv`, `huecos_estaciones.csv`, `metadata.json` y
`hashes.sha256`. No se publican en `web/public/` hasta confirmar los términos de
reutilización. La auditoría de INGEMMET y ZEE Piura se guarda en
`data/processed/geoservicios/` (también ignorado por Git) y se documenta en
`docs/16`; no se copia a `web/public/`. Cada AOI conserva `observaciones` por
fecha y sensor (`src_date` y `source_nam` del DBF), la suma de
observaciones, el solapamiento entre fechas, la unión original, el área filtrada, la
simplificada, la publicada en UTM y la geodésica. `area_km2` es el área publicada;
`area_original_km2` es la unión original, no la suma. Las reparaciones de geometrías
de origen quedan en `reparaciones`. Las obras esquemáticas (Poechos y canal Daniel
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
  estado: disponible        # disponible | por_solicitar | por_verificar (heredado)
  disponibilidad: validada  # localizada | descargable | procesada | validada |
                            # documental | pendiente | descartada
  publicacion: autorizada   # autorizada | bloqueada | pendiente | no_aplica
                            # una capa publicada no puede usar una fuente bloqueada
  tipo_evidencia: [oficial] # oficial | academica | cientifica | historica |
                            # observacion_satelital | dato_medido |
                            # reconstruccion_cartografica | modelamiento |
                            # prensa_documentacion_secundaria | colaborativa
  periodo: "2008"
  formato: "GeoJSON"
  crs: "EPSG:32717 / EPSG:4326"
  descarga: https://...
  limitaciones: "Escala 1:100 000; el área oficial se calculó en otra proyección."
  capas: [cuenca, subcuencas]
  metodo: descarga directa
  grupo: Límites, relieve y red
  certeza: medido           # medido | derivado | documentado | interpretacion | por_verificar
  tipo: dataset             # dataset | documento | prensa | elaboracion_propia
  documento: Unidades Hidrográficas Pfafstetter, R.M. 033-2008-AG
  consultado: "2026-11-16"
  notas: R.M. 033-2008-AG
```

`estado` se conserva por compatibilidad con el frontend y las pruebas anteriores.
`disponibilidad` es el estado operativo de la fase 2. Una capa publicada solo
puede referenciar fuentes `validada` o `procesada`; una fuente `documental` puede
sostener texto o una ficha, pero no una geometría publicada.

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
