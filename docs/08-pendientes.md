# 08 · Pendientes de la fase 1

Actualizado: 2026-11-16.

Este documento separa lo que ya está implementado, lo que se puede hacer sin datos
externos y lo que está bloqueado por solicitudes. La regla sigue siendo: **lo que no
tiene fuente, no se dibuja**.

## Implementado

- Capas base: cuenca ANA, 8 subcuencas oficiales + Bajo Piura derivado, red
  HydroRIVERS v1.0 recortada, lagunas y salinas OSM.
- Partición de subcuencas **reconciliada topológicamente**: 0 solapamientos,
  0 superficie fuera y 0 huecos por encima del umbral de 0,01 km². El método y los
  cambios de área están en `data/raw/limits.json → reconciliacion`.
- Mancha oficial de la inundación de marzo de 2017 (Copernicus EMSR199, AOI10 y
  AOI11), con observaciones por fecha, sensor, área original y área simplificada.
- Referencia de Poechos como punto en el dique y del canal Daniel Escobar como recta
  de referencia en el mapa 2D; no se dibujan el vaso, bocatomas ni diques sin geometría.
- Relieve sombreado y maqueta 3D de la cuenca con el desierto y la bahía, exportada con Draco (1,6 MB).
- Cortes transversales de referencia (5) y corte dibujado por el visitante.
- Catálogo de fuentes generado desde `data/sources.yml`, con enlaces por capa.
- Escenarios históricos documentados; la mancha de 2017 usa un vector oficial y
  1983/1998 siguen como texto. Sin manchas inventadas.
- ETL reproducible para capas y cortes.
- Scripts de descarga para ANA, HydroRIVERS, cuerpos de agua OSM y Copernicus
  EMSR199.
- Validación de datos (`etl/check_data.py`) con auditoría por par de subcuencas,
  superficie fuera por subcuenca, huecos por componente y agujeros interiores;
  38 pruebas de Python y pruebas Playwright de mapa, móvil, fallo de red y maqueta.
- Catálogo de fuentes con `certeza` y `tipo`: distingue dato medido, derivado,
  documentado, interpretación y pendiente de verificación.
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
| Caudales y niveles diarios | SENAMHI | hidrogramas, duración y fecha exacta de 1998 |
| Precipitación PISCO | SENAMHI | contexto climático |
| Cartografía de inundación 1983/1998 | ANA | manchas históricas |
| Bocatomas y diques | ANA / PECHP | capa de obras completa |
| Operación de Poechos | PECHP | trasvase y regulación |
| Escenarios de riesgo | CENEPRED / SIGRID | exposición |
| Informe hidrológico de La Niña 2023 | SENAMHI / ANA | área y volumen del evento |
| Informe ENFEN concreto | ENFEN | edición exacta de 1982-83, 1997-98 o 2017 |

Mientras no lleguen, esas capas se muestran como «sin dato público» y no se dibujan.

## Contradicciones y límites conocidos

- **Área de la cuenca.** La geometría mide **10 938,4 km²** (geodésica). ANA publica
  11 021,8 km² en `Shape_Area`, pero ese campo está calculado en **EPSG:32718 (UTM 18S)**,
  fuera de la zona 17S del polígono; la diferencia no es redondeo. El atlas muestra la
  cifra medida y conserva la oficial como referencia.
- **Bajo Piura.** La capa oficial de subcuencas no publica «Bajo Piura» como polígono
  independiente. El atlas lo calcula como el resto de la cuenca **antes** de simplificar
  y lo atribuye a `bajo-piura-derivado`, no a ANA. Su área medida es **4 752,9 km²**.
  La reconciliación topológica eliminó 0,7828 km² de solapamientos, 1,4725 km² de
  huecos y 0,6747 km² de superficie fuera de la cuenca; no se crea superficie nueva.
  El método, las 374 caras y los cambios de área por subcuenca están en
  `data/raw/limits.json → reconciliacion`. El resultado tiene 0 solapamientos,
  0 superficie fuera y 0 huecos por encima de 0,01 km².
- **Red hídrica.** HydroRIVERS v1.0 incluye tramos que sobresalen de la ventana y de la
  cuenca. `build_layers.py` usa intersección geométrica exacta con el polígono ANA;
  ningún tramo publicado queda fuera (solo el redondeo de 6 decimales, <0,2 m).
- **Poechos y canal Daniel Escobar.** Poechos se publica como **punto en el dique**
  (4°40′07″S, 80°30′13″W, PECHP), no como vaso inventado. El canal es una **recta de
  referencia** Poechos–Curumuy, no su eje oficial; el PECHP documenta 54 km y 70 m³/s.
  No hay geometría oficial publicada del vaso ni del eje: no se dibujan como si lo fueran.
- **Inundación de 2017.** La mancha es el vector oficial de Copernicus EMSR199
  (AOI10 + AOI11), no una reconstrucción propia. Los atributos del vector declaran
  Radarsat Ultra-Fine Beam (26/03) y Cosmo-SkyMed (30/03) para AOI10, y Radarsat
  (26/03) para AOI11; el PDF v2 declara Sentinel-1A y esa discrepancia se deja visible.
  La capa publica la **unión de las observaciones**, no una mancha simultánea: AOI10
  pasa de 80,8 + 73,0 km² por fecha a 96,5 km² de unión simplificada; AOI11 pasa de
  457,4 a 459,0 km². Cubre la llanura baja y el desierto adyacente, no toda la cuenca;
  el total (≈555 km²) no es una estimación hidráulica ni una extensión simultánea. No
  se publica una clase potencial porque el vector no la trae. El AOI12 Piura North se
  descartó por falta de fecha y sensor en sus registros.
- **Color del terreno.** La maqueta usa una rampa hipsométrica: el verde indica
  altitud, no cobertura vegetal.
- **Lagunas.** Los polígonos son de OSM; Ramón y Las Salinas figuran como
  intermitentes. La maqueta las pinta como agua permanente por el relato y las sitúa
  a una cota simbólica (+25 m), no a un nivel medido.
- **Rótulos del GLB.** El rótulo de cota «Naciente ~2 700 m» fue retirado del GLB
  regenerado: el DEM en esa posición mide ~1 935 m y el máximo de la ventana es
  3 019 m. «Reserva Nacional Illescas» se conserva como referencia de lugar, no como
  límite oficial; el área protegida no está dibujada. Poechos se rotula en el dique
  real y el canal en su punto medio de referencia.
- **1998: fecha del pico.** SIAR 200 consigna el 12 de marzo en la introducción (p. 1)
  y el 16 de marzo en el análisis de niveles (p. 15). El atlas mantiene la cifra de
  4 424 m³/s y marca la fecha como discrepancia; no elige una sin una fuente adicional.
- **1983: duración.** El pico de 3 200 m³/s del 21 de abril está documentado (SIAR 200
  p. 15; SIAR 204 p. 49), pero no se localizó una duración diaria del episodio.
- **1891: mecanismo.** SIAR registra el cambio de embocadura (p. 5 y 7); el detalle de
  crecidas y avulsión se apoya en una tesis de la PUCP y se marca como interpretación
  histórica, no como medición.
- **2023: La Niña.** Andina y NASA documentan el desborde y la afectación de la
  carretera. No hay informe hidrológico de SENAMHI/ANA en el catálogo; no se publica
  área ni volumen para 2023.
- **ENFEN, Sentinel-1 y UNOSAT.** ENFEN se usa solo como contexto: falta identificar la
  edición concreta de sus informes. Sentinel-1 no es la fuente del vector publicado; el
  vector EMSR199 se basa en Radarsat/Cosmo según sus atributos. UNOSAT se usa como
  contraste, no como geometría. Las manchas de 1983 y 1998 siguen sin geometría pública
  localizada.

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
