# 06 · Cómo citar

## Versión citable

Al cerrar cada fase se publica una versión con etiqueta (`v0.1.0`, `v0.2.0`,
`v0.2.1`, `v1.0.0`) y un identificador persistente en Zenodo. Mientras no exista, se
cita el repositorio con la fecha de consulta. El archivo
[`CITATION.cff`](../CITATION.cff) contiene los metadatos de la versión actual y sirve
para que GitHub y Zenodo los muestren.

La versión **0.2.1** corrige la topología de las subcuencas (0 solapamientos, 0
superficie fuera y 0 huecos por encima de 0,01 km²), documenta las observaciones de
2017 por fecha y sensor, resuelve la atribución de Bajo Piura y actualiza las fuentes
históricas. El release `v0.2.1` se publica sobre esta versión; el DOI queda pendiente
de depositar esa versión en Zenodo y añadirlo aquí.

### Texto

> Río Piura Atlas (2026). *Atlas de la cuenca del río Piura*. Versión 0.2.1.
> https://github.com/joseamaya/rio-piura-atlas
> Sitio: https://joseamaya.github.io/rio-piura-atlas/

### BibTeX

```bibtex
@misc{riopiuraatlas,
  title  = {Atlas de la cuenca del río Piura},
  author = {{Río Piura Atlas}},
  year   = {2026},
  note   = {Versión 0.2.1},
  url    = {https://github.com/joseamaya/rio-piura-atlas}
}
```

## Citar una capa concreta

Cada capa tiene su propia ficha con la fuente original. Lo correcto es citar la
fuente primaria, no el atlas:

> Autoridad Nacional del Agua (2008). *Unidades Hidrográficas del Perú*.
> Delimitación Pfafstetter, 1:100 000. R.M. N.° 033-2008-AG.

El atlas añade valor al **integrar** y **explicar**; la autoridad del dato es de su
productor.

## Condiciones

- CC BY 4.0 para textos y gráficos propios: se puede reutilizar citando.
- Los datos de terceros mantienen su licencia (ver `LICENSES/DATOS.md`).
- No se autoriza presentar el atlas como fuente oficial ni como pronóstico.
