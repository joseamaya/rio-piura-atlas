# Aplicación web (fase 1)

Aún sin implementar. Esta nota fija las decisiones técnicas para no improvisarlas
después.

## Stack

| Pieza | Elección | Por qué |
|---|---|---|
| Sitio | Astro (salida estática) | HTML mínimo, carga rápida, sin servidor |
| Mapa | **MapLibre GL JS** | relieve 3D nativo, teselas vectoriales, rótulos, móvil |
| Capas pesadas | deck.gl | inundaciones, cortes, agregados |
| Maqueta 3D | Three.js | solo para el diorama (`piura` / `piura-cuenca`) |
| Datos | COG + PMTiles + GeoJSON | servible desde CDN sin backend |
| Estilos | CSS propio, sin framework | menos peso y menos dependencias |

**Three.js no es el motor del atlas.** Es la herramienta de una pieza concreta: el
bloque 3D. Para el mapa, MapLibre resuelve proyección, relieve, teselas, etiquetas y
controles, que en Three.js habría que construir desde cero.

## Estructura prevista

```
web/
├── src/
│   ├── pages/
│   │   ├── index.astro        # entrada: qué es este atlas
│   │   ├── mapa.astro         # explorar
│   │   ├── escenarios.astro   # 1983 · 1998 · 2017
│   │   ├── maqueta.astro      # diorama 3D
│   │   └── fuentes.astro      # catálogo navegable
│   ├── components/
│   └── styles/
└── public/
    └── data/                  # enlaces a COG/PMTiles
```

## Presupuesto de rendimiento

- Carga inicial < 2 MB.
- Mapa utilizable en 4G en menos de 3 s.
- Sin fuentes externas bloqueantes.
- Funciona sin JavaScript para leer los textos.

## Accesibilidad

- Contraste mínimo AA.
- Navegación por teclado en mapa y fichas.
- Texto alternativo en cada figura.
- Los escenarios se pueden leer como tabla, no solo como mapa.
