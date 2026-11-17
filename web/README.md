# Aplicación web (fase 1)

El sitio está implementado en Astro con salida estática. Esta nota fija las decisiones
técnicas y el estado real para no improvisarlas después.

## Stack

| Pieza | Elección | Por qué |
|---|---|---|
| Sitio | Astro (salida estática) | HTML mínimo, carga rápida, sin servidor |
| Mapa | **MapLibre GL JS** | relieve 3D nativo, teselas vectoriales, rótulos, móvil |
| Capas pesadas | deck.gl (previsto) | agregados y teselas; la mancha 2017 cabe en GeoJSON |
| Maqueta 3D | Three.js + DRACOLoader | solo para el diorama (`piura`) |
| Datos | COG + PMTiles + GeoJSON | servible desde CDN sin backend |
| Estilos | CSS propio, sin framework | menos peso y menos dependencias |

**Three.js no es el motor del atlas.** Es la herramienta de una pieza concreta: el
bloque 3D. Para el mapa, MapLibre resuelve proyección, relieve, teselas, etiquetas y
controles, que en Three.js habría que construir desde cero.

## Estructura actual

```
web/
├── src/
│   ├── pages/
│   │   ├── index.astro        # entrada: qué es este atlas
│   │   ├── mapa.astro         # mapa, capas, cortes transversales
│   │   ├── escenarios.astro   # 1983 · 1998 · 2017
│   │   ├── maqueta.astro      # diorama 3D
│   │   └── fuentes.astro      # catálogo generado desde data/sources.yml
│   ├── layouts/Base.astro
│   ├── fonts/                 # Newsreader y Archivo (OFL 1.1)
│   ├── styles/
│   │   ├── tokens.css         # color, tipografía y espaciado
│   │   ├── base.css           # reset, prosa y estructura
│   │   ├── components.css     # cabecera, pie, botones y estados
│   │   ├── home.css           # portada
│   │   ├── map.css            # mapa interactivo
│   │   └── global.css         # maqueta y estilos heredados
└── public/
    ├── data/                  # GeoJSON, relieve JPG y malla de elevación
    ├── draco/                 # decodificador Draco (Apache 2.0)
    ├── img/                   # láminas y recortes de la portada
    └── models/                # piura.glb (Draco, ~1,6 MB)
```

El GLB se genera en el proyecto Blender hermano
(`../blender/projects/piura/scripts/export_web.py`) y se copia a
`public/models/piura.glb`. El decodificador de `public/draco/` se copia de
`three/examples/jsm/libs/draco/gltf/` y conserva su licencia Apache 2.0; ver
[`../LICENSES/CODIGO.md`](../LICENSES/CODIGO.md).

## Capas y datos

- `cuenca.geojson`, `subcuencas.geojson`, `red_hidrica.geojson`, `agua.geojson`,
  `lugares.geojson`, `obras.geojson` y `flood_2017.geojson` se generan con
  `etl/build_layers.py`.
- `obras.geojson` contiene Poechos como punto en el dique y el canal Daniel Escobar
  como recta de referencia, marcados con `esquematico: true`; no es un inventario
  de ANA/PECHP ni el eje oficial del canal.
- `flood_2017.geojson` es el vector oficial de Copernicus EMSR199 (AOI10 + AOI11),
  simplificado. Publica áreas por observación, solapamiento, unión original, filtrada,
  simplificada y publicada en UTM/geodésica. Cubre la llanura baja y el desierto
  adyacente, no toda la cuenca.
- `flood_2017.jpg` es la figura estática de `/escenarios`, generada por
  `build_layers.py` a partir del relieve y de la mancha.
- `cortes.geojson`, `cortes_perfiles.json`, `dem_grid.bin` y `dem_grid.meta.json` se
  generan con `etl/build_cortes.py`.
- El mapa carga la mancha de 2017 solo al activar la capa (o con
  `?capa=inundacion`) y la malla de elevación solo al pulsar «Dibujar un corte».

## Tipografías

Newsreader y Archivo se autoalojan en `src/fonts/` bajo SIL Open Font License
1.1. No hay peticiones a Google Fonts. Los textos de licencia están en la misma
carpeta y la procedencia en [`../LICENSES/TIPOGRAFIA.md`](../LICENSES/TIPOGRAFIA.md).

## Estado de UI-01

El rediseño «Lámina y margen» está aplicado a los fundamentos (tokens,
tipografía, cabecera, pie y componentes), la portada, el mapa, Escenarios,
Fuentes y la maqueta 3D. El mapa usa panel en el layout, leyenda contextual,
ficha lateral, hojas móviles, encuadre del Bajo Piura y nueva simbología del agua
y la inundación. Fuentes dejó las tablas y usa registros con filtros. La maqueta
conserva su interacción Three.js y ahora se presenta como espécimen editorial. La propuesta completa está en
[`../docs/ui/`](../docs/ui/) y los mockups en
[`../design-proposal/`](../design-proposal/).

## Presupuesto de rendimiento

- Portada y páginas de texto: carga inicial < 1 MB.
- `/mapa`: MapLibre comprimido (~220 kB) y datos iniciales (~650 kB); la mancha de
  2017 (~518 kB) y el DEM de cortes (~443 kB) se descargan aparte, solo al activarlos.
- `/maqueta`: 1,6 MB de GLB, ~250 kB de decodificador Draco y Three.js; se asume como
  excepción y no contamina la carga de las demás páginas.
- Mapa utilizable en 4G en menos de 3 s.
- Sin fuentes externas bloqueantes: las tipografías se autoalojan (~165 kB en total).
- Funciona sin JavaScript para leer los textos.

La malla de elevación pesa ~443 kB y se descarga a demanda. El modelo 3D pesa 1,6 MB
y el decodificador Draco ~250 kB; solo se descargan al abrir `/maqueta`.

## Accesibilidad

- Contraste mínimo AA.
- Enlace «Saltar al contenido» y foco visible en todos los controles.
- Navegación por teclado en mapa, capas, fichas y maqueta (flechas, +/− y Home);
  `Escape` cierra el panel de corte y devuelve el foco al botón que lo abrió.
- Texto alternativo y resumen para el mapa y la maqueta.
- Los escenarios se pueden leer como tabla, no solo como mapa.
- El perfil del corte se ofrece como gráfico SVG con etiqueta accesible.
- Respeta `prefers-reduced-motion`.
- `npm run check` (Astro/TypeScript), `npm run build`, `npm run check:links`
  (enlaces y anclas internas), `npm run check:a11y` (axe WCAG A/AA en Chrome
  headless) y `npm run test:e2e` (Playwright: dibujo de perfil, capas, ficha de
  cuenca, teclado, fallo de red, móvil y maqueta). `npm run verify` encadena la
  secuencia completa.
- Auditoría automática WCAG A/AA con axe: sin violaciones en las cinco páginas, el
  404 y los visores en móvil.

Pendiente: prueba con teclado real, lector de pantalla y personas de los tres
públicos.

## Metadatos y errores

- `<title>`, descripción, Open Graph, Twitter Card y `theme-color` en el layout base.
- Página `404.html` propia.
- `robots.txt` en `public/`.

## Pendiente en la web

- Bocatomas y diques: no hay geometría pública; el inventario está en ANA/PECHP.
- Manchas de inundación de 1983 y 1998.
- Caudales y niveles (SENAMHI).
- Sustituir las capas GeoJSON por PMTiles/COG si el volumen crece.
- Dominio propio (opcional). El despliegue en GitHub Pages ya está activo en
  `https://joseamaya.github.io/rio-piura-atlas/`.
