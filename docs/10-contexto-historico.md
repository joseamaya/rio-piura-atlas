# 10 · Contexto histórico y registro de afirmaciones

Actualizado: 2026-11-16.
Alcance: afirmaciones publicadas en `/escenarios`, `docs/03-metodologia.md` y
`docs/08-pendientes.md`. Cada fila distingue lo que se abrió y se leyó de lo que
solo se conoce por referencia bibliográfica.

## Criterio

- **Dato medido:** serie, aforo o vector con método y unidad.
- **Registro histórico:** documento que describe un hecho, sin medición propia.
- **Interpretación científica:** explicación de un mecanismo, no un hecho observado.
- **Reconstrucción cartográfica:** geometría derivada por el atlas.
- **Hipótesis / no verificado:** no se localizó evidencia suficiente.

Una fuente genérica no respalda una cifra específica. Si el documento no se pudo
abrir, se dice y no se usa para una afirmación concreta.

## Registro

| # | Afirmación | Fuente | Documento / fecha | Página o sección | ¿Abierto directamente? | Cita o evidencia | Estado |
|---|---|---|---|---|---|---|---|
| 1 | Antes de 1891 el río desembocaba en el mar; desde 1891 va a la laguna San Ramón | SIAR Piura | *Cambios de la embocadura del río Piura* (s. f.) | p. 5 | Sí, PDF | «al mar (antes 1891 y en 1983); a laguna San Ramón (desde 1891)» | Registro histórico |
| 2 | En 1983 el río reocupó el cauce antiguo y volvió al mar | SIAR Piura | *Cambios de la embocadura…* | p. 7 | Sí, PDF | «cambio de la embocadura al mar por reocupación del cauce antiguo» | Registro histórico |
| 3 | El mecanismo general es avulsión por progradación o reocupación | SIAR Piura | *Cambios de la embocadura…* | p. 9 | Sí, PDF | «avulsiones… originados por progradación del lóbulo de derrame o por reocupación de cauces antiguos» | Interpretación científica |
| 4 | El detalle de 1891 incluye crecidas y avulsión y se apoya en Huertas (1999) y Rocha (2014) | Tesis PUCP, Orellana Cabello (2021) | *Modelamiento hidrológico e hidráulico… HEC-HMS y HEC-RAS* | Sin página verificada | **No**: el repositorio devolvió 403/Anubis; solo se leyó el registro y el resumen | El resumen menciona 1925, 1983, 1998 y 2017; no menciona 1891 ni a Huertas/Rocha | No verificado; retirado de la afirmación específica |
| 5 | 1983: 3 200 m³/s el 21/04/1983 en Puente Sánchez Cerro | SIAR Piura | *Evaluación hidrológica y erosión-sedimentación del Río Piura* | p. 15 | Sí, PDF | «el 21 de abril del mismo año… 3200 m3/s» | Dato medido |
| 6 | 1983: 3 200 m³/s en la serie anual | SIAR Piura | *Estudio para el Tratamiento Integral del Río Piura, Apéndice D* (2000) | p. 49, tabla 3.1 | Sí, PDF | Serie 1983 = 3200,0 | Dato medido |
| 7 | 1983 y 1998: descarga total hasta 12 veces la media anual | SIAR Piura | *Apéndice D* | p. 13 | Sí, PDF | «la descarga total supera en doce veces la media anual» | Documentado |
| 8 | 1998: 4 424 m³/s | SIAR Piura | *Apéndice D*; *Evaluación hidrológica…* | p. 27 y 49; p. 1 y 15 | Sí, PDF | Serie 1998 = 4424,0 | Dato medido |
| 9 | 1998: el pico aparece el 12 de marzo en una sección y el 16 de marzo en otra | SIAR Piura | *Evaluación hidrológica…* | p. 1 vs p. 15 | Sí, PDF | «12 de marzo 1998» vs «16 de marzo de 1998» | Discrepancia documentada |
| 10 | 1998: «período de 161 días» | SIAR Piura | *Evaluación hidrológica…* | p. 1 | Sí, PDF | «durante de un período de 161 días el caudal… alcanzó el valor máximo» | Documentado con salvedad: no prueba duración exacta |
| 11 | La Niña: 2 326 km² en 1997-98 | IMARPE, Escudero & Xu (2019) | *Formación y evolución de la laguna La Niña 2017…* | Resumen | Sí, página del artículo | «no fue mayor a la registrada durante El Niño 1997-98 cuando se estimó en 2.326 km2» | Estimación satelital (MODIS-Aqua 500 m) |
| 12 | La Niña: 2 172 km² el 5/04/2017 | IMARPE, Escudero & Xu (2019) | Ibídem | Resumen | Sí, página del artículo | «alcanzó su máxima extensión el 5 de abril (2.172 km2)» | Estimación satelital (MODIS-Aqua 500 m) |
| 13 | 2017: AOI10 usa Radarsat el 26/03 y Cosmo-SkyMed el 30/03; AOI11 Radarsat el 26/03 | Copernicus EMSR199 | Shapefile `crisis_information_poly` (DBF) | Campos `src_date` y `source_nam` | Sí, atributos del vector | 1 472 registros AOI10; 474 AOI11 | Dato medido / delineación satelital |
| 14 | 2017: AOI10 tiene 80,785 km² el 26/03 y 73,040 km² el 30/03; 56,772 km² de solapamiento; unión 97,053 km²; publicado 96,507 km² | Copernicus EMSR199 | Cálculo propio en EPSG:32717 | — | Sí, geometrías originales | Tabla de `docs/03-metodologia.md` | Reconstrucción cartográfica verificable |
| 15 | 2017: el PDF v2 declara Sentinel-1A | Copernicus EMSR199 | PDF del producto 10PIURA v2 | Sin página verificada en esta auditoría | **No** en v0.2.2 | Se conserva como discrepancia reportada, no como hecho reabierto | Pendiente de confirmar |
| 16 | 2023: La Niña desbordó y destruyó 120 m de la carretera Bayóvar–Chiclayo | Agencia Andina | *Emergencia por lluvias: piden priorizar obras…* (22/03/2023) | Cuerpo de la nota | Sí, página web | «ha arrasado con 120 metros de la carretera» | Documentado (prensa) |
| 17 | 2023: la laguna se ve el 24/02 y el 12/03; el desborde ocurrió el 23/03 | NASA Earth Observatory | *Warming Water and Downpours in Peru* (10/04/2023) | Texto e imágenes | Sí, página web | Landsat 9 OLI-2; «On March 23, overflow from the lagoon destroyed a section…» | Documentado (teledetección) |
| 18 | 2023: no cambió la desembocadura | — | — | — | **No hay fuente** | Andina y NASA describen el desborde hacia el desierto y la carretera, no la desembocadura | Sin evidencia; no se afirma |

| 19 | 1983: 3 200 m³/s el 21/04/1983 en Puente Sánchez Cerro | INDECI / OEA / PNUD | *Estudio Mapa de peligros de la ciudad de Piura*, Vol. I (2009) | Cap. 2, hidrogramas y tabla de caudales | Sí, PDF | Serie 1983 = 3 200,0; «21/04/1983» | Dato medido (corroboración) |
| 20 | 1998: 4 424 m³/s el 12/03/1998 en Puente Sánchez Cerro | INDECI / OEA / PNUD | Ibídem | Cap. 2 y tabla de caudales | Sí, PDF | «12/03/1998 4424» | Dato medido (corroboración; la discrepancia 12/16 sigue visible) |
| 21 | En 2002 la salida principal era el Manglar de San Pedro; Virrilá era la segunda salida y Reventazón la tercera en El Niño | Asociación Perú Verde / IUCN | *Expedición en la cuenca baja del río Piura, junio del 2002* (2003) | Introducción y resultados | Sí, PDF | «curso regular por su desembocadura principal a través del Manglar de San Pedro»; «Virrilá… segunda desembocadura»; «tercera salida… Reventazón» | Registro histórico |
| 22 | En 2002, Tres Bocas dividía el cauce en Chutuque, Ñapique y Ramón | Asociación Perú Verde / IUCN | Ibídem | Resultados, sector 1 | Sí, PDF | «se divide en tres canales conocidos como Tres Bocas» | Registro histórico |
| 23 | El modelo de Lund encuentra depósito en el tramo bajo de Virrilá y mayor exceso de esfuerzo cortante hacia Sechura | Lund University | Ladewig Piscoya (2024), tesis TVVR24/5008 | Resumen, resultados y discusión | Sí, PDF | «general trend for Virrilá is deposition»; «course towards Sechura produces considerably larger excess shear values» | Modelamiento académico |
| 24 | En 2026 se verificó paso de agua en Tapa de Cuy, Virrilá, el puente de Bayóvar y Chutuque | PECHP / MIDAGRI / PSI / ANA | Nota del PECHP, 04/03/2026 | Nota completa | Sí, web | «caudal aproximado de 280 m³/s»; «paso de las aguas… despejado»; «condiciones favorables» en Chutuque | Documentado (prensa institucional) |
| 25 | PISCOp v3.0 tiene 0,1° (~10 km) y cubre 1981–2025 | SENAMHI / *Hydrology* | Artículo y ficha de Figshare (2026) | Artículo y readme | Sí, metadatos | «0.1°»; «1981–2025» | Dato derivado; licencia en disputa |
| 26 | No se localizó una capa vectorial de susceptibilidad a inundaciones para Piura en INGEMMET | INGEMMET | Fichas y servicios consultados (2026) | Ítems de ArcGIS | Sí, metadatos | Solo se encontraron servicios de Ancash y Apurímac | Pendiente / no incorporado |

## Notas de lectura

- SIAR 1392 p. 4 habla de una bahía antigua al sur de la ciudad de Piura, pero no de
  «Sechura». La frase «litoral de Sechura» se retiró.
- El resumen de IMARPE no cuantifica 2023. La nota de Andina y la imagen de NASA sí
  documentan el evento, pero no un cambio de desembocadura.
- La tesis PUCP no se pudo abrir. El registro bibliográfico y el resumen no respaldan
  la afirmación específica de 1891; por eso `pucp-1891` queda `por_verificar`.
- El PDF de Copernicus no se reabrió en esta auditoría. La discrepancia Sentinel-1A
  queda visible como pendiente, no como hecho confirmado.

## Pendientes de verificación

1. Abrir el PDF 10PIURA v2 y localizar la frase exacta sobre Sentinel-1A.
2. Abrir la tesis PUCP por una vía que no bloquee el acceso y verificar las citas a
   Huertas (1999) y Rocha (2014).
3. Obtener una serie diaria de SENAMHI para la fecha del pico de 1998 y la duración
   de 1983.
4. Obtener un informe hidrológico de SENAMHI/ANA para área y volumen de 2023.
5. Verificar si alguna fuente documenta explícitamente la desembocadura en 2023.
6. Aclarar la licencia de PISCOp v3.0 antes de publicar una serie derivada.
7. Obtener los shapefiles de la Carta Geológica de Piura y verificar su licencia.
8. Obtener coordenadas y fichas técnicas de la inspección de 2026.
9. Si se reconstruye la ruta de 2002, documentar PSAD56, orden de puntos e
   incertidumbre.
