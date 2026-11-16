# 08 · Pendientes de la fase 1

Actualizado: 2026-11-16.

Este documento separa lo que ya está implementado, lo que se puede hacer sin datos
externos y lo que está bloqueado por solicitudes. La regla sigue siendo: **lo que no
tiene fuente, no se dibuja**.

## Implementado

- Capas base: cuenca ANA, 9 subcuencas, red HydroRIVERS, lagunas y salinas OSM.
- Mancha oficial de la inundación de marzo de 2017 (Copernicus EMSR199, AOI10 y
  AOI11), con fecha, sensores, cobertura y método declarados.
- Capa esquemática de Poechos y del canal Daniel Escobar en el mapa 2D, marcada como
  interpretación; no se dibujan bocatomas ni diques sin geometría.
- Relieve sombreado y maqueta 3D de la cuenca con el desierto y la bahía, exportada con Draco (1,7 MB).
- Cortes transversales de referencia (5) y corte dibujado por el visitante.
- Catálogo de fuentes generado desde `data/sources.yml`, con enlaces por capa.
- Escenarios históricos documentados; la mancha de 2017 usa un vector oficial y
  1983/1998 siguen como texto. Sin manchas inventadas.
- ETL reproducible para capas y cortes.
- Scripts de descarga para ANA, HydroRIVERS, cuerpos de agua OSM y Copernicus
  EMSR199.
- Validación de datos (`etl/check_data.py`) y pruebas de geometría.
- CI que compila el sitio y valida datos en cada push.
- Accesibilidad: enlace de salto, foco visible, texto alternativo del mapa y la
  maqueta, movimiento reducido y auditoría automática WCAG A/AA con axe en CI
  (`npm run check:a11y`), sin violaciones en las cinco páginas y el 404.
- Comprobación automática de tipos (`astro check`) y de enlaces/anclas internas en CI.
- Página 404, `robots.txt` y metadatos Open Graph/Twitter.
- `CITATION.cff` con los metadatos de la versión 0.2.0.
- Sitio publicado en GitHub Pages (`https://joseamaya.github.io/rio-piura-atlas/`)
  con despliegue automático desde `main` y comprobaciones previas de tipos, enlaces
  y accesibilidad.

## Desbloqueado

1. **Dominio propio (opcional).** Sustituir `joseamaya.github.io` por un dominio
   definitivo y actualizar `SITE_URL`.
2. **DOI Zenodo.** El release `v0.2.0` ya está creado sobre esta versión. Falta
   depositarlo en Zenodo y añadir el DOI a `CITATION.cff` y
   `docs/06-como-citar.md`. El tag `v0.1.0` es anterior al diorama actual.
3. **Prueba de accesibilidad con personas.** La auditoría automática está limpia;
   falta teclado real, lector de pantalla y prueba con los tres públicos.
4. **Rendimiento futuro.** Migrar a PMTiles/COG si crecen las capas vectoriales.

## Bloqueado por solicitudes

| Dato | Entidad | Uso |
|---|---|---|
| Caudales y niveles | SENAMHI | hidrogramas, régimen, crecidas |
| Precipitación PISCO | SENAMHI | contexto climático |
| Cartografía de inundación 1983/1998 | ANA | manchas históricas |
| Bocatomas y diques | ANA / PECHP | capa de obras completa |
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
- **Poechos y canal Daniel Escobar.** Se dibujan en la maqueta y en el mapa 2D como
  **geometría esquemática**: un polígono manual de 9 puntos y un eje de 4 puntos.
  No son levantamientos ni provienen de ANA/PECHP. Las bocatomas y los diques no se
  dibujan porque no hay geometría pública.
- **Inundación de 2017.** La mancha es el vector oficial de Copernicus EMSR199
  (AOI10 + AOI11), no una reconstrucción propia. Usa Radarsat-2 y Cosmo-SkyMed, no
  Sentinel-1. Cubre la llanura baja y el desierto adyacente, no toda la cuenca; el
  área publicada (≈555 km²) es la del vector simplificado, no una estimación
  hidráulica. El AOI12 Piura North se descartó por falta de fecha y sensor en sus
  registros.
- **Color del terreno.** La maqueta usa una rampa hipsométrica: el verde indica
  altitud, no cobertura vegetal.
- **Lagunas.** Los polígonos son de OSM; Ramón y Las Salinas figuran como
  intermitentes. La maqueta las pinta como agua permanente por el relato y las sitúa
  a una cota simbólica (+25 m), no a un nivel medido.
- **Rótulos del GLB.** «Naciente ~2 700 m» no coincide con el DEM en su posición
  (1 933 m; máximo de ventana 3 019 m) y «Reserva Illescas» no dibuja el área
  protegida. Corregirlos o retirarlos en una próxima exportación; el GLB actual no se
  toca.
- **ENFEN, Sentinel-1 y UNOSAT.** ENFEN aporta el relato; Sentinel-1 y UNOSAT se usan
  como contraste. La geometría publicada de 2017 es el vector oficial de Copernicus
  EMSR199. Las manchas de 1983 y 1998 siguen sin geometría pública localizada.

## Criterios para cerrar la fase 1

- Una persona sin formación técnica entiende, en menos de 10 minutos, por qué el río
  no llega al mar.
- Toda capa visible tiene fuente consultable en dos clics.
- La mancha de 2017 declara fuente, fecha, sensores, cobertura y método; las obras
  esquemáticas están marcadas como interpretación.
- El sitio funciona en móvil y con conexión lenta: portada y páginas de texto
  por debajo de 1 MB; `/maqueta` es la excepción declarada por el GLB y la mancha de
  2017 se carga a demanda en `/mapa`.
- Existe una versión etiquetada y citable.
