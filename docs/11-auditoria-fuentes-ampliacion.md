# 11 · Auditoría de fuentes de la ampliación

Actualizado: 2026-11-17.
Alcance: siete fuentes prioritarias de la fase 2 y las fuentes complementarias
localizadas durante la búsqueda. Este documento distingue **investigado**,
**localizado**, **descargado**, **leído**, **procesado**, **validado** e
**incorporado**. Una URL encontrada no equivale a un dato incorporado.

## 1. Método

Para cada fuente se hizo, cuando fue posible:

1. Búsqueda en el portal institucional o en el repositorio original.
2. Descarga del archivo original, no solo de la página de resultados.
3. Lectura del índice, los capítulos relevantes y los anexos.
4. Verificación de autoría, fecha, escala, formato, sistema de coordenadas y
   licencia.
5. Revisión de la existencia de archivos GIS descargables.
6. Registro de lo que se puede afirmar, de lo que no se puede afirmar y de lo que
   falta solicitar.

No se digitalizaron mapas ni se convirtieron tablas en capas durante esta
auditoría. La única fuente con una eventual serie derivable es PISCOp v3.0; su
licencia quedó pendiente y no se publicó ninguna serie.

## 2. Resumen

| Fuente | Recuperación | Anexos y mapas | Datos aprovechables | Estado |
|---|---|---|---|---|
| A. ANA — Tratamiento del cauce | PDF de 199 pp, 13,4 MB, descargado | Índice, capítulos 2–7, tabla de 89 peligros, inventario de defensas, mapas PDF | Tramos críticos, erosión, sedimentación, propuestas; sin GIS | `documental` |
| B. INDECI — Piura y Castilla, 2009 | Vol. I de 320 pp y Vol. II de 419 pp, descargados | Índice, capítulos 2–3, planos 1–16, hidrogramas 1983/1998, drenaje y cuencas ciegas | Categorías de inundación, cifras, drenaje; sin shapefiles | `documental` |
| C. Lund — Ladewig Piscoya (2024) | PDF de 155 pp, 11 MB, descargado | Metodología, resultados, discusión y apéndices | Modelo HEC-RAS 1D; depósito en Virrilá; mayor exceso de esfuerzo cortante hacia Sechura | `documental` |
| D. INGEMMET | Metadatos y servicios consultados; PDFs de Piura no descargados | Carta 1:100 000, Geología Integrada, Peligros Geológicos | Geología y geomorfología; sin vector de susceptibilidad a inundaciones para Piura | `localizada` / `documental` |
| E. SENAMHI — PISCO | Readme y NetCDF mensual (54 MB) descargados; diario de 1,5 GB no descargado | Readme, artículo y ficha de Figshare | Precipitación diaria/mensual 1981–2025, 0,1°; serie por subcuenca posible | `descargable` + `pendiente` por licencia |
| F. PECHP / ANA / MIDAGRI / PSI — 2026 | Nota completa descargada | Dos fotografías; sin mapas ni coordenadas | Registro fechado de inspección y caudales puntuales reportados | `documental` |
| G. Expedición a la cuenca baja — 2002 | PDF de 27 pp, descargado | Texto, mapas 1–2 y anexo de 178 puntos GPS | Rutas San Pedro/Virrilá/Reventazón; Tres Bocas/Chutuque; sedimentación | `documental` |

## 3. Fuente A — ANA, Tratamiento del cauce del río Piura

### Identificación

- **Título:** *Tratamiento del cauce del río Piura para el control de inundaciones*.
- **Institución:** Autoridad Nacional del Agua, Dirección de Estudios de Proyectos
  Hidráulicos Multisectoriales.
- **Fecha:** estudio de 2014; aprobado por resolución directoral en 2018. La ficha
  de ALICIA consigna «002-2028», una probable errata; el número no se usa como
  dato verificado.
- **URL:** <https://hdl.handle.net/20.500.12543/2254>.
- **Descarga:** <https://sigrid.cenepred.gob.pe/sigridv3/documento/972/descargar>.
- **Formato:** PDF de 199 páginas y 13,4 MB.
- **Licencia:** los metadatos del repositorio ANA declaran **CC BY-NC-ND 4.0** y
  acceso abierto.

### Qué se recuperó y revisó

Se descargó el PDF completo. Se revisaron el índice, los capítulos 2–7, la tabla
de 89 ocurrencias de peligros geológicos y el inventario de estructuras de defensa
ribereña. No se revisó cada anexo página por página.

### Contenido útil

- Ámbito: 305 km de cauce, desde la laguna Ramón-pampa Salinas hasta la naciente;
  tres valles (Alto, Medio y Bajo Piura) y 17 distritos.
- Inventario de estructuras de defensa ribereña y de puntos críticos.
- Diagnóstico de erosión fluvial, sedimentación, secciones, pendientes y
  granulometría.
- Propuestas de medidas estructurales y no estructurales: descolmatación, diques,
  espigones, reforestación, ordenamiento territorial y alerta temprana.
- Tabla de 89 peligros geológicos con coordenadas UTM WGS84 17S; la tabla es una
  transcripción de la base de INGEMMET, no una capa propia.
- Propuesta de eje de canal en el tramo bajo (figura 17), que **no** es una obra
  ejecutada.

### Anexos y mapas

El PDF contiene mapas y figuras, pero no se encontraron archivos GIS
descargables. Las coordenadas de las tablas no vienen acompañadas de un
shapefile ni de un diccionario de campos. No se digitalizaron.

### Limitaciones

- Es un estudio técnico y una propuesta; no acredita obras ejecutadas.
- La licencia CC BY-NC-ND impide redistribuir versiones modificadas y, por tanto,
  no permite publicar sus mapas o tablas como capas derivadas sin permiso.
- El eje propuesto no es el eje oficial del río ni una geometría levantada.
- La tabla de peligros es una fuente secundaria de la base de INGEMMET.

### Recomendación

Mantener como fuente **documental**. No incorporar capas. Si en el futuro se
necesitan los puntos críticos o el eje propuesto, solicitarlos a ANA/INGEMMET con
licencia compatible y metadatos, o usar la base original de INGEMMET.

## 4. Fuente B — INDECI, Mapa de peligros de Piura y Castilla (2009)

### Identificación

- **Título de portada:** *Estudio Mapa de peligros de la ciudad de Piura*,
  Volumen I (informe final) y Volumen II (anexos).
- **Institución:** INDECI, Organización de Estados Americanos (OEA), PNUD y
  Municipalidades de Piura y Castilla, en el marco del Proyecto
  SEDI/AICD/AE/306/07.
- **Fecha:** junio de 2009; trabajos de campo entre diciembre de 2008 y febrero de
  2009.
- **URL:** <https://sigrid.cenepred.gob.pe/sigridv3/documento/2594>.
- **Descargas:** <https://sigrid.cenepred.gob.pe/sigridv3/documento/2594/descargar>
  (Vol. I) y <https://sigrid.cenepred.gob.pe/sigridv3/documento/3795/descargar>
  (Vol. II).
- **Formato:** PDF de 320 páginas (Vol. I) y 419 páginas (Vol. II).
- **Licencia:** documento público; no se localizó una licencia explícita de
  reutilización.

### Qué se recuperó y revisó

Se descargaron ambos volúmenes. Se revisaron el índice, los capítulos 2–3, la
lista de planos, los hidrogramas de 1983 y 1998, las secciones de drenaje pluvial
y de cuencas ciegas. No se revisó cada plano en detalle.

### Contenido útil

- El capítulo III se titula «Mapa de peligros de Piura y Castilla» y los planos
  incluyen ambas ciudades, aunque la portada solo mencione Piura.
- Hidrogramas y caudales medios diarios de 1983 y 1998 en la estación Puente
  Sánchez Cerro.
- Precipitación máxima en 24 horas de 1983 y 1998 en la estación Miraflores y en
  la estación UDEP.
- Categorías separadas de inundación fluvial, inundación pluvial, cuencas ciegas y
  escorrentía.
- Planos 1–16, incluidos el sistema de drenaje pluvial de Piura y Castilla y la
  delimitación de cuencas ciegas.
- Descripción de la infraestructura de drenaje y de las lagunas de retención.

### Anexos y mapas

Los planos son imágenes/PDF. El estudio menciona que se elaboraron shapes, pero no
los publica. No se localizaron archivos GIS descargables. No se digitalizaron los
planos.

### Limitaciones

- El título exacto no es «Estudio de peligros de las ciudades de Piura y Castilla»;
  es el estudio de Piura que incluye Castilla en su capítulo III. El estudio
  separado de Castilla de 2001 es otra fuente y no se fusiona.
- No hay shapefiles públicos ni georreferenciación directa de los planos.
- Las cifras de 1983/1998 son una corroboración documental, no una serie diaria
  descargable.
- No se pueden mezclar las cuatro categorías de inundación en una sola capa.

### Recomendación

Mantener como fuente **documental** y usar sus categorías en el documento 14 y en
la narrativa de escenarios. No digitalizar sin escala, georreferenciación y método.
Solicitar a ANA/INDECI la cartografía vectorial de 1983 y 1998.

## 5. Fuente C — Lund, transporte de sedimentos con HEC-RAS (2024)

### Identificación

- **Título:** *Sediment Transport in the Piura River. Piura, Peru. An application
  with the HEC-RAS model*.
- **Autora:** Ann Katrin Ladewig Piscoya.
- **Institución:** Lund University, Division of Water Resources Engineering.
- **Fecha:** 2024; serie TVVR 5000, informe TVVR24/5008.
- **URL:** <https://lup.lub.lu.se/student-papers/record/9170911>.
- **Descarga:** <https://lup.lub.lu.se/student-papers/record/9170911/file/9170913.pdf>.
- **Formato:** PDF de 155 páginas, 11 MB.
- **Licencia:** acceso abierto; no se localizó una licencia Creative Commons. Se
  cita y no se reutilizan figuras sin permiso.

### Qué se recuperó y revisó

Se descargó el PDF y se revisaron el resumen, la metodología, los datos, los
resultados y la discusión. No se reconstruyó el modelo ni se reutilizaron sus
secciones transversales.

### Contenido útil

- Modelo HEC-RAS 6.3.1 en régimen estacionario 1D.
- Calibración con el evento de 2017; caudal de calibración de 3 468 m³/s.
- Escenarios de 1 000 y 3 200 m³/s para velocidad, profundidad y esfuerzo cortante.
- Comparación entre la ruta actual por Virrilá y una ruta alternativa hacia
  Sechura.
- Tendencia al depósito en el tramo bajo de Virrilá, asociada a pendiente baja y
  velocidades bajas.
- Mayores valores de exceso de esfuerzo cortante hacia Sechura, lo que indica mayor
  capacidad de transporte.
- Discusión de la sedimentación en la laguna Ñapique/Ramón y de la incertidumbre
  de la topografía.

### Anexos y mapas

La tesis incluye figuras, perfiles longitudinales, secciones transversales y
apéndices con datos de geometría. No publica un GeoPackage ni un shapefile del
modelo. No se reutilizan las figuras.

### Limitaciones

- Es una tesis de maestría, no un artículo revisado por pares ni una decisión
  oficial.
- Modelo 1D en estado estacionario, con topografía ASTER/LiDAR y supuestos
  declarados.
- No había batimetría detallada del estuario; se asumió una cota de fondo y una
  pendiente.
- Los resultados de transporte dependen de la fórmula y de los parámetros; no son
  una predicción operacional.
- La ruta hacia Sechura es una alternativa modelada, no una obra decidida.

### Recomendación

Mantener como evidencia **académica** y **modelamiento**. Usarla en el documento
14 y en la ficha de fuentes. No presentarla como solución demostrada ni como
justificación de una obra. Si se necesita geometría, solicitarla a la autora o a
la Universidad de Piura.

## 6. Fuente D — INGEMMET, cartografía geológica y peligros

### Identificación

- **Carta Geológica Nacional 1:100 000:** 501 cuadrángulos cartografiados entre
  1960 y 1999; PDF/JPG por hoja.
  <https://portal.ingemmet.gob.pe/web/guest/carta-geologica-nacional>.
- **Geología Integrada 1:100 000:** 15 mapas integrados según la ficha (27 según el
  resumen), 2014 y 2016; servicio de teselas de ArcGIS.
  <https://www.arcgis.com/home/item.html?id=6219264c683649ae864de0442c047d35>.
- **GEOCATMIN — Peligros Geológicos del Perú:** inventario nacional, 32 019
  eventos declarados, actualización de enero de 2012; servicio de mapa.
  <https://www.arcgis.com/home/item.html?id=0df56a7235ff4dd88aad635fc949c4c9>.
- **Licencia:** la ficha de Geología Integrada dice «de uso y acceso público según
  escala de trabajo»; no es una licencia Creative Commons. Peligros Geológicos no
  declara licencia.

### Qué se recuperó y revisó

Se consultaron las fichas y los servicios. No se descargaron las hojas de Piura
de la Carta Geológica ni se verificó su georreferenciación. No se encontró una
capa vectorial de susceptibilidad a inundaciones para Piura; la búsqueda de
servicios de INGEMMET devolvió capas de susceptibilidad solo para Ancash y
Apurímac, que no se pueden extrapolar.

### Contenido útil

- Geología superficial, geomorfología y depósitos aluviales de la cuenca.
- Inventario de peligros geológicos (inundación fluvial, erosión fluvial, flujos,
  arenamientos, derrumbes).
- Contexto para entender la llanura aluvial y los procesos geodinámicos.

### Anexos y mapas

La Carta Geológica es PDF/JPG; no es vectorial. La Geología Integrada es un
servicio de teselas sin descarga vectorial verificada. El inventario de peligros
es un servicio de visualización. No se integró ninguno en runtime.

### Limitaciones

- No hay una capa vectorial de susceptibilidad a inundaciones para Piura.
- La susceptibilidad geológica no es probabilidad hidrológica de inundación.
- Usar el servicio de teselas en runtime añadiría una dependencia externa y
  rompería la reproducibilidad del sitio estático.
- No se verificaron los términos de reutilización de las hojas.

### Recomendación

Mantener como fuentes **localizadas/documentales**. No incorporar capas. Si se
quiere geología en el atlas, solicitar a INGEMMET los shapefiles de las hojas de
Piura con licencia y metadatos, y priorizar geología superficial, geomorfología y
depósitos aluviales.

## 7. Fuente E — SENAMHI, PISCOp v3.0

### Identificación

- **Título:** *PISCOp v3.0 — precipitación diaria y mensual grillada*.
- **Institución:** SENAMHI, Dirección de Hidrología.
- **Artículo:** Gutierrez, L., Huerta, A., Vásquez, S., Rau, P. y
  Lavado-Casimiro, W. (2026). *Updating a High-Resolution Gridded Rainfall Dataset
  for Peru (PISCOp v3.0)*. Hydrology 13(11):306.
  <https://doi.org/10.3390/hydrology13110306>.
- **Datos:** <https://figshare.com/articles/dataset/High-resolution_grids_of_rainfall_for_Peru_-_PISCOp_v3_0_dataset/32411886>.
- **Resolución:** 0,1° (~10 km), no ~5 km.
- **Periodo:** 1981–2025, diario y mensual.
- **Formatos:** NetCDF diario (1,5 GB), mensual (54 MB) y climatología (1,8 MB).
- **Licencia:** el artículo es CC BY 4.0; el conjunto de datos en Figshare declara
  **GPL 3.0+**. La discrepancia no se resolvió.

### Qué se recuperó y revisó

Se descargaron el readme y el NetCDF mensual (54 MB). No se descargó el diario de
1,5 GB. No se pudo abrir el NetCDF en el entorno de auditoría por falta de una
librería NetCDF/HDF5; la verificación se limitó al readme, al artículo y a la ficha
de Figshare. La versión v2.1 (0,1°, 1981–2018) está suspendida en su soporte cuasi
tiempo real.

### Contenido útil

- Precipitación diaria y mensual para todo el Perú.
- Posibilidad de calcular una serie media o acumulada por subcuenca.
- Comparación con caudales observados de 2015–2026 del PECHP y con las cifras de
  1983/1998 de SIAR/INDECI.

### Limitaciones

- Es una estimación grillada, no una medición directa en cada punto.
- 0,1° (~10 km) no resuelve la cuenca alta, media y baja con el mismo detalle.
- La licencia de los datos no está clara: GPL 3.0+ en Figshare, CC BY 4.0 en el
  artículo.
- El archivo diario es grande y no debe entrar en Git ni en CI.
- La ficha de sequías de SENAMHI menciona ~5 km, pero PISCOp v3.0 documenta 0,1°;
  no son la misma ficha.

### Recomendación

Catalogar como **descargable** y **pendiente** por licencia. Diseñar el ETL de
series por subcuenca, pero no publicar la serie hasta que SENAMHI aclare la
licencia o el proyecto acepte una licencia GPL separada. No presentar PISCO como
medición directa ni como 5 km.

## 8. Fuente F — PECHP, ANA, MIDAGRI y PSI, inspección de febrero de 2026

### Identificación

- **Título:** *PECHP garantiza libre desembocadura al mar del río Piura*.
- **Institución:** PECHP / Gobierno Regional Piura, con MIDAGRI-DGIHR, PSI y ANA.
- **Fecha de la nota:** 4 de marzo de 2026.
- **Fecha de la inspección:** jueves 26 de febrero de 2026.
- **URL:** <https://www.gob.pe/institucion/pechp/noticias/1361521-pechp-garantiza-libre-desembocadura-al-mar-del-rio-piura>.
- **Formato:** nota web con dos fotografías; sin mapas ni coordenadas.
- **Licencia:** documento público; las fotografías son del PECHP.

### Qué se recuperó y revisó

Se leyó la nota completa y su enlace de contexto. No hay anexos técnicos,
coordenadas ni mapas.

### Contenido útil

- Brazo del río aguas abajo de la laguna La Niña, en el sector Tapa de Cuy
  (Sechura), erosionado por el agua; flujo continuo hacia La Niña.
- Caudal aproximado de 280 m³/s en Tapa de Cuy; picos de hasta 300 m³/s en la presa
  Los Ejidos.
- Virrilá: trabajos de recuperación del dique con geobolsas por ANA.
- Puente de la carretera Bayóvar: paso de aguas de La Niña despejado.
- Canal Chutuque: tramo medio entre aguas arriba de Ramón y aguas abajo de La Niña;
  condiciones favorables y salida libre hacia La Niña.
- Participación de PECHP, DGIHR-MIDAGRI, PSI y ANA.

### Limitaciones

- No publica coordenadas, mapas ni fichas técnicas.
- El título afirma «libre desembocadura al mar», pero el cuerpo verifica el paso
  del agua en puntos concretos; no demuestra un cambio de desembocadura ni una
  conexión permanente.
- Los caudales son puntuales y reportados, no una serie.
- No se pueden convertir las fotografías en geometrías.
- El reporte diario del PECHP del 26/02/2026 registra 304 m³/s en Puente Sánchez
  Cerro; es otra estación y no se promedia con Tapa de Cuy.

### Recomendación

Incorporar como **registro documental fechado** en `/escenarios`, sin geometría.
Mantener la solicitud de coordenadas, fotografías georreferenciadas y fichas
técnicas.

## 9. Fuente G — Expedición a la cuenca baja del río Piura, 2002

### Identificación

- **Título:** *Expedición en la cuenca baja del río Piura, junio del 2002*.
- **Autores:** Manuel Apaza, Guido Seminario, Carolina Tovar y Pablo Martínez.
- **Institución:** Asociación Perú Verde y Comité Holandés de la IUCN, en el marco
  del Plan de Manejo Participativo del Estuario de Virrilá.
- **Fecha:** trabajo de campo del 22 al 24 de junio de 2002; documento de 2003.
- **URL:** <https://rsis.ramsar.org/RISapp/files/54275910/documents/PE2455_lit210522_7.pdf>.
- **Formato:** PDF de 27 páginas.
- **Licencia:** documento público; no se localizó una licencia explícita. Se cita y
  no se reutilizan mapas sin permiso.

### Qué se recuperó y revisó

Se descargó el PDF y se revisaron el texto, los mapas 1–2 y el anexo de
coordenadas. No se reconstruyó la ruta.

### Contenido útil

- Recorrido de 108 km entre el Puente Independencia y el Puente Virrilá, del 22 al
  24 de junio de 2002, en estiaje, con tirantes de 50–60 cm en los tramos menos
  profundos.
- Descripción de la salida principal por el Manglar de San Pedro, un aporte parcial
  por Virrilá y una tercera salida por la quebrada Reventazón en episodios
  excepcionales de El Niño.
- Tres Bocas: el brazo izquierdo conduce a Chutuque, el derecho a la laguna
  Ñapique y el central a la laguna Ramón.
- Tapa del Cuy y Tapa de Márquez; acumulación de sedimentos en la laguna Ramón.
- Observaciones sobre defensas ribereñas y antiguos encauzamientos.
- 178 puntos GPS; coordenadas originales en WGS84, convertidas a PSAD56 para los
  mapas.

### Limitaciones

- Es una navegación de estiaje de 2002, no un aforo continuo ni un eje oficial.
- Los puntos GPS son un track de navegación, no el centro del cauce.
- El documento describe rutas y condiciones de un momento; no prueba que todas
  estuvieran activas simultáneamente ni que sigan activas.
- La transformación de datum y el orden de los puntos requieren documentación si
  se quiere reconstruir la ruta.

### Recomendación

Mantener como **documental** y como fuente principal del futuro módulo «El
recorrido del agua». La reconstrucción cartográfica de la ruta queda como
candidata de fase 3, con método, incertidumbre y estilo de interpretación.

## 10. Fuentes complementarias

### PECHP — informe hidrometeorológico diario

- URL: <https://servicios.regionpiura.gob.pe/datosh>.
- Reportes PDF, Excel y CSV desde 2015 hasta 2026.
- La API devuelve las fechas disponibles por mes; los CSV incluyen estación,
  unidad, caudal de las 07 h, promedio 24 h, máximo 24 h y precipitación 24 h.
- Incluye Puente Sánchez Cerro y la presa Los Ejidos.
- Limitaciones: no cubre 1983/1998; no tiene API documentada ni licencia explícita;
  la cadena TLS del servidor está incompleta.
- Estado: `descargable`; no se publica el CSV crudo hasta aclarar términos.

### SENAMHI — PHISIS Piura

- URL: <https://www.senamhi.gob.pe/?p=monitoreo-piura>.
- Monitoreo hidrológico actual; no es una serie histórica descargable.
- Las series de 1983, 1998, 2017 y 2023 siguen requiriendo solicitud.

### PECHP — levantamiento topobatimétrico de 2026

- URL: <https://www.gob.pe/institucion/pechp/noticias/1418316-pechp-ejecuta-levantamiento-topobatimetrico-em-el-rio-piura-para-fortalecer-la-prevencion-ante-un-posible-fenomeno-de-el-nino>.
- Nota del 4 de julio de 2026; no publica datos, método ni cobertura.
- Estado: `pendiente`; se mantiene como solicitud.

### ANA — SNIRH

- URL: <https://snirh.ana.gob.pe/observatoriosnirh/Index.aspx>.
- Observatorio nacional; falta verificar cobertura y acceso para Piura.
- No se usa todavía.

## 11. Estado de cada fuente

| Fuente | Investigada | Localizada | Descargada | Leída | Procesada | Validada | Incorporada |
|---|---|---|---|---|---|---|---|
| A. ANA | sí | sí | sí | índice, capítulos y tablas | no | no | solo catálogo/documento |
| B. INDECI | sí | sí | sí | índice, capítulos y planos | no | no | solo catálogo/documento |
| C. Lund | sí | sí | sí | metodología, resultados y discusión | no | no | solo catálogo/documento |
| D. INGEMMET | sí | sí | parcial | fichas y servicios | no | no | no |
| E. PISCO | sí | sí | mensual | readme y artículo | no | no | no |
| F. PECHP 2026 | sí | sí | sí | nota completa | no | no | registro documental |
| G. Expedición 2002 | sí | sí | sí | texto, mapas y anexo | no | no | solo catálogo/documento |

## 12. Lo que no se recuperó

- Hojas de Piura de la Carta Geológica Nacional 1:100 000: no se descargaron.
- Shapefiles de Piura y Castilla de INDECI 2009: no se publican.
- Archivos GIS del estudio ANA 2014: no se encontraron.
- NetCDF diario de PISCOp v3.0: no se descargó por tamaño y por licencia pendiente.
- Coordenadas y mapas de la inspección de 2026: no se publican.
- Datos de la topobatimetría del PECHP de 2026: no se publican.
- Serie diaria oficial de SENAMHI para 1983/1998: sigue pendiente de solicitud.

## 13. Licencias: resumen operativo

| Fuente | Licencia | ¿Se puede publicar una capa derivada? |
|---|---|---|
| ANA 2014 | CC BY-NC-ND 4.0 | **No** sin permiso |
| INDECI 2009 | documento público; sin licencia explícita | No se redistribuyen planos; citar |
| Lund 2024 | acceso abierto; derechos de la autora | Citar; no reutilizar figuras |
| INGEMMET | uso público «según escala de trabajo»; sin licencia formal | No hasta confirmar |
| PISCOp v3.0 | artículo CC BY 4.0; datos GPL 3.0+ | **Pendiente** de aclaración |
| PECHP 2026 | documento público; fotografías del PECHP | Citar; no reutilizar fotografías |
| Expedición 2002 | documento público; sin licencia explícita | Citar; no reutilizar mapas |

## 14. Recomendaciones

1. No incorporar capas geométricas de A, B, D, F ni G en esta fase.
2. Mantener PISCO como prioridad 1, pero con compuerta de licencia.
3. Usar la expedición de 2002 como fuente principal del futuro módulo de la cuenca
   baja; no dibujar su ruta todavía.
4. Mantener las solicitudes de cartografía vectorial, batimetría, ejes de canales y
   series diarias.
5. Revisar los términos de INGEMMET antes de cualquier integración.
6. No confundir susceptibilidad geológica con probabilidad hidrológica.
7. No convertir propuestas de ANA en obras ejecutadas.
