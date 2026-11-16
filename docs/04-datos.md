# 04 · Datos

## Estructura

```
data/
├── sources.yml      registro maestro de fuentes (se edita a mano)
├── raw/             lo que se descarga o se recibe, sin tocar
└── processed/       lo que consume el sitio, generado por etl/
```

`raw/` es inmutable: si una fuente se actualiza, se guarda como versión nueva.
`processed/` se puede borrar y regenerar.

## Formatos

| Tipo | Formato | Motivo |
|---|---|---|
| Ráster (DEM, imágenes) | COG (`*.tif`) | lectura por teselas sin descargar todo |
| Vectores grandes | PMTiles | un archivo, rápido en móvil |
| Vectores pequeños | GeoJSON simplificado | legible y versionable |
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
  notas: R.M. 033-2008-AG
```

Todo elemento publicado debe referenciar un `id` existente en este archivo.

## Nombres de archivo

`<fuente>__<tema>__<fecha>__v<n>.<ext>`

Ejemplo: `ana__subcuencas__2008__v1.geojson`

Sin espacios, sin acentos, sin mayúsculas.

## Versionado

- Git para textos, metadatos, scripts y GeoJSON pequeños.
- Los archivos pesados (COG, PMTiles) **no** van en Git: se publican como *release* o
  en almacenamiento estático, y se enlazan desde `sources.yml` con su hash.
- Cada versión publicada del atlas queda etiquetada (`v0.1.0`) y citada en
  `docs/06-como-citar.md`.

## Privacidad y licencias

- Nada de datos personales.
- Los datos de terceros conservan su licencia; se listan en `LICENSES/DATOS.md`.
- Si una licencia no permite redistribuir, se enlaza a la fuente y no se copia.
