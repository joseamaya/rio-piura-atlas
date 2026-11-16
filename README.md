# Río Piura Atlas

Atlas interactivo, documentado y citable de la cuenca del río Piura: qué es, cómo
funciona, dónde se desborda y qué se construyó para contenerlo.

> **Estado:** fase 0 (alcance y auditoría de fuentes). Todavía no hay aplicación web
> ni datos publicados. Este repositorio contiene, por ahora, el plan, el catálogo de
> fuentes y la estructura de datos.

## Para quién

Público general, docentes, periodistas, gestores municipales y cualquier persona que
necesite explicar o entender el río Piura sin ser especialista.

## Qué es

- Un **atlas**: mapa 2D/3D de la cuenca, sus subcuencas, su red hídrica, sus obras y
  sus cortes, con la fuente de cada capa a la vista.
- Un **visor de escenarios**: capas de inundación **históricas y documentadas**
  (1983, 1998, 2017), no pronósticos.

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
data/sources.yml      registro maestro de fuentes
data/raw/             datos tal como llegan (inmutables)
data/processed/       datos derivados, reproducibles
etl/                  scripts de descarga y transformación
web/                  sitio del atlas (a construir en fase 1)
LICENSES/             licencias de datos y de contenido
```

## Cómo citar

Ver [`docs/06-como-citar.md`](docs/06-como-citar.md). Versión citable pendiente de
publicación (Zenodo) al cerrar la fase 1.

## Licencias

Contenido y textos: CC BY 4.0. Código: MIT. Los datos conservan la licencia de su
fuente; ver [`LICENSES/DATOS.md`](LICENSES/DATOS.md).

## Contexto

Nace como pieza hermana del laboratorio [Del Trazo al Modelo](../blender), que aporta
el diorama 3D de la cuenca (`projects/piura`) y su versión recortada
(`projects/piura-cuenca`).
