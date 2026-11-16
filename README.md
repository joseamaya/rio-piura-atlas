# Río Piura Atlas

Atlas interactivo, documentado y citable de la cuenca del río Piura: qué es, cómo
funciona, dónde se desborda y qué se construyó para contenerlo.

> **Estado:** fase 1 en curso. El sitio ya funciona con las capas verificadas
> (cuenca, subcuencas, red, agua, relieve y maqueta 3D). Faltan las capas que dependen
> de datos por solicitar: caudales, obras y manchas de inundación.

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

## Cómo ejecutarlo

```bash
# capas (requiere el DEM del laboratorio de modelos)
python3 etl/build_layers.py

# sitio
cd web
npm install
npm run dev        # http://localhost:4321
npm run build      # estático en web/dist
```

El sitio pesa menos de 2 MB en la primera carga: relieve 490 kB, capas vectoriales
~200 kB y el modelo 3D 6,3 MB que solo se descarga al abrir la maqueta.

## Qué hay hoy

| Página | Contenido |
|---|---|
| `/` | qué es el atlas y qué no es |
| `/mapa` | relieve, cuenca ANA, 9 subcuencas, red hídrica, lagunas y ciudades |
| `/maqueta` | bloque 3D recortado a la cuenca (Three.js) |
| `/escenarios` | los eventos documentados y lo que falta |
| `/fuentes` | catálogo generado desde `data/sources.yml` |

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
