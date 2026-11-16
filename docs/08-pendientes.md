# 08 · Pendientes de la fase 1

Actualizado: 2026-11-16.

Este documento separa lo que ya está implementado, lo que se puede hacer sin datos
externos y lo que está bloqueado por solicitudes. La regla sigue siendo: **lo que no
tiene fuente, no se dibuja**.

## Implementado

- Capas base: cuenca ANA, 9 subcuencas, red HydroRIVERS, lagunas y salinas OSM.
- Relieve sombreado y maqueta 3D de la cuenca con el desierto y la bahía, exportada con Draco (1,7 MB).
- Cortes transversales de referencia (5) y corte dibujado por el visitante.
- Catálogo de fuentes generado desde `data/sources.yml`, con enlaces por capa.
- Escenarios históricos como texto documentado; sin manchas inventadas.
- ETL reproducible para capas y cortes.
- Scripts de descarga para ANA, HydroRIVERS y cuerpos de agua OSM.
- Validación de datos (`etl/check_data.py`) y pruebas de geometría.
- CI que compila el sitio y valida datos en cada push.
- Accesibilidad: enlace de salto, foco visible, texto alternativo del mapa y la
  maqueta, movimiento reducido y auditoría automática WCAG A/AA con axe en CI
  (`npm run check:a11y`), sin violaciones en las cinco páginas y el 404.
- Comprobación automática de tipos (`astro check`) y de enlaces/anclas internas en CI.
- Página 404, `robots.txt` y metadatos Open Graph/Twitter.
- `CITATION.cff` con los metadatos de la versión 0.1.0.
- Sitio publicado en GitHub Pages (`https://joseamaya.github.io/rio-piura-atlas/`)
  con despliegue automático desde `main` y comprobaciones previas de tipos, enlaces
  y accesibilidad.

## Desbloqueado

1. **Capa de obras hidráulicas.** Poechos, canal Daniel Escobar, bocatomas y diques.
   Se puede empezar con ubicaciones públicas y marcar como interpretación lo que no
   tenga geometría oficial. El inventario completo sigue en ANA / PECHP.
2. **Mancha 2017 con Sentinel-1.** Descargar escenas de marzo de 2017, aplicar umbral
   de agua, contrastar con UNOSAT / Copernicus EMS y documentar el método.
3. **Dominio propio (opcional).** Sustituir `joseamaya.github.io` por un dominio
   definitivo y actualizar `SITE_URL`.
4. **DOI Zenodo.** El tag `v0.1.0` ya existe; falta publicarlo y añadir el DOI a
   `CITATION.cff` y `docs/06-como-citar.md`.
5. **Prueba de accesibilidad con personas.** La auditoría automática está limpia;
   falta teclado real, lector de pantalla y prueba con los tres públicos.
6. **Rendimiento futuro.** Migrar a PMTiles/COG si crecen las capas vectoriales y
   optimizar el GLB de la maqueta.

## Bloqueado por solicitudes

| Dato | Entidad | Uso |
|---|---|---|
| Caudales y niveles | SENAMHI | hidrogramas, régimen, crecidas |
| Precipitación PISCO | SENAMHI | contexto climático |
| Cartografía de inundación 1983/1998/2017 | ANA | manchas históricas |
| Inventario de infraestructura | ANA | capa de obras |
| Operación de Poechos | PECHP | trasvase y regulación |
| Escenarios de riesgo | CENEPRED / SIGRID | exposición |

Mientras no lleguen, esas capas se muestran como «sin dato público» y no se dibujan.

## Contradicciones y límites conocidos

- **Área de la cuenca.** ANA reporta 11 021,8 km²; el atlas usa 11 022 km²
  redondeados. Es una diferencia de redondeo, no de delimitación.
- **Bajo Piura.** La capa oficial de subcuencas no publica «Bajo Piura» como polígono
  independiente. El atlas lo calcula como el resto de la cuenca; por eso su área varía
  entre 4 792 y 4 795 km² según se redondeen las subcuencas. El método está declarado
  en `data/raw/limits.json`.
- **Red hídrica.** HydroRIVERS incluye tramos que sobresalen levemente de la ventana
  del atlas. `build_layers.py` los recorta a la cuenca y el script de descarga usa un
  margen de 0,05° para no cortar tramos en el borde.
- **Poechos.** La represa figura como polígono manual en `water.json`, pero no se
  dibuja: falta fuente y licencia confirmadas para su geometría.
- **ENFEN y Sentinel-1.** Están disponibles como documentos o imágenes, pero no como
  capas geográficas listas para publicar. Por eso no hay mancha de inundación todavía.

## Criterios para cerrar la fase 1

- Una persona sin formación técnica entiende, en menos de 10 minutos, por qué el río
  no llega al mar.
- Toda capa visible tiene fuente consultable en dos clics.
- El sitio funciona en móvil y con conexión lenta: portada y páginas de texto
  por debajo de 1 MB; `/maqueta` es la excepción declarada por el GLB.
- Existe una versión etiquetada y citable.
