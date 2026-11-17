# 06 · Cómo citar

## Versión citable

Al cerrar cada fase se publica una versión con etiqueta (`v0.1.0`, `v0.2.0`,
`v0.2.1`, `v0.2.2`, `v0.2.3`, `v1.0.0`) y un identificador persistente en Zenodo.
Mientras no exista, se cita el repositorio con la fecha de consulta. El archivo
[`CITATION.cff`](../CITATION.cff) contiene los metadatos de la versión actual y sirve
para que GitHub y Zenodo los muestren.

La versión **0.2.3** añade la auditoría de fidelidad geométrica de la inundación de
2017 por etapas (unión, filtro, simplificación y publicación), valida los
componentes de `limits.json` antes de unirlos y amplía las pruebas sintéticas. La
geometría publicada de 2017 no cambió; solo se añadieron metadatos y el informe
`flood_2017_audit.json`. El release `v0.2.3` se publica sobre esta versión; el DOI
queda pendiente de depositar esa versión en Zenodo y añadirlo aquí.

### Texto

> Río Piura Atlas (2026). *Atlas de la cuenca del río Piura*. Versión 0.2.3.
> https://github.com/joseamaya/rio-piura-atlas
> Sitio: https://joseamaya.github.io/rio-piura-atlas/

### BibTeX

```bibtex
@misc{riopiuraatlas,
  title  = {Atlas de la cuenca del río Piura},
  author = {{Río Piura Atlas}},
  year   = {2026},
  note   = {Versión 0.2.3},
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
