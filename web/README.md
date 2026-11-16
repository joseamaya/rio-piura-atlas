# Aplicación web (fase 1)

El sitio está implementado en Astro con salida estática. Esta nota fija las decisiones
técnicas y el estado real para no improvisarlas después.

## Stack

| Pieza | Elección | Por qué |
|---|---|---|
| Sitio | Astro (salida estática) | HTML mínimo, carga rápida, sin servidor |
| Mapa | **MapLibre GL JS** | relieve 3D nativo, teselas vectoriales, rótulos, móvil |
| Capas pesadas | deck.gl (previsto) | inundaciones y agregados; aún no se usa |
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
│   └── styles/global.css
└── public/
    ├── data/                  # GeoJSON, relieve JPG y malla de elevación
    └── models/                # piura.glb (Draco, ~1,7 MB)
```

## Capas y datos

- `cuenca.geojson`, `subcuencas.geojson`, `red_hidrica.geojson`, `agua.geojson` y
  `lugares.geojson` se generan con `etl/build_layers.py`.
- `cortes.geojson`, `cortes_perfiles.json`, `dem_grid.bin` y `dem_grid.meta.json` se
  generan con `etl/build_cortes.py`.
- El mapa carga la malla de elevación solo cuando el visitante pulsa «Dibujar un
  corte»; la primera carga no incluye el DEM.

## Presupuesto de rendimiento

- Portada y páginas de texto: carga inicial < 1 MB.
- `/mapa`: MapLibre comprimido (~220 kB) y datos (~630 kB); el DEM de cortes se
  descarga aparte, solo al dibujar.
- `/maqueta`: 6,3 MB de GLB más Three.js; se asume como excepción y no contamina la
  carga de las demás páginas.
- Mapa utilizable en 4G en menos de 3 s.
- Sin fuentes externas bloqueantes.
- Funciona sin JavaScript para leer los textos.

La malla de elevación pesa ~443 kB y se descarga a demanda. El modelo 3D pesa 6,3 MB
y solo se descarga al abrir `/maqueta`.

## Accesibilidad

- Contraste mínimo AA.
- Enlace «Saltar al contenido» y foco visible en todos los controles.
- Navegación por teclado en mapa, capas y fichas.
- Texto alternativo y resumen para el mapa y la maqueta.
- Los escenarios se pueden leer como tabla, no solo como mapa.
- El perfil del corte se ofrece como gráfico SVG con etiqueta accesible.
- Respeta `prefers-reduced-motion`.
- `npm run check` (Astro/TypeScript), `npm run build`, `npm run check:links`
  (enlaces y anclas internas) y `npm run check:a11y` (axe WCAG A/AA en Chrome
  headless). `npm run verify` encadena las cuatro.
- Auditoría automática WCAG A/AA con axe: sin violaciones en las cinco páginas y el
  404.

Pendiente: prueba con teclado real, lector de pantalla y personas de los tres
públicos.

## Metadatos y errores

- `<title>`, descripción, Open Graph, Twitter Card y `theme-color` en el layout base.
- Página `404.html` propia.
- `robots.txt` en `public/`.

## Pendiente en la web

- Capa de obras hidráulicas (diques, bocatomas, canal Daniel Escobar, Poechos).
- Manchas de inundación de 1983, 1998 y 2017.
- Caudales y niveles (SENAMHI).
- Sustituir las capas GeoJSON por PMTiles/COG si el volumen crece.
- Dominio propio (opcional). El despliegue en GitHub Pages ya está activo en
  `https://joseamaya.github.io/rio-piura-atlas/`.
