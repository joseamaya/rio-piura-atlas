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
auditoría. Las fuentes con series derivables son PISCOp v3.0 y la API histórica
por estación de SENAMHI; sus licencias o términos quedaron pendientes y no se
publicó ninguna serie. La segunda ronda de búsqueda (2026-11-17) encontró capas
vectoriales de INGEMMET y ANA que antes se creían inexistentes; se documentan en
la sección 15 y se mantienen como candidatas, no como capas publicadas.

## 2. Resumen

| Fuente | Recuperación | Anexos y mapas | Datos aprovechables | Estado |
|---|---|---|---|---|
| A. ANA — Tratamiento del cauce | PDF de 199 pp, 13,4 MB, descargado | Índice, capítulos 2–7, tabla de 89 peligros, inventario de defensas, mapas PDF | Tramos críticos, erosión, sedimentación, propuestas; sin GIS | `documental` |
| B. INDECI — Piura y Castilla, 2009 | Vol. I de 320 pp y Vol. II de 419 pp, descargados | Índice, capítulos 2–3, planos 1–16, hidrogramas 1983/1998, drenaje y cuencas ciegas | Categorías de inundación, cifras, drenaje; sin shapefiles | `documental` |
| C. Lund — Ladewig Piscoya (2024) | PDF de 155 pp, 11 MB, descargado | Metodología, resultados, discusión y apéndices | Modelo HEC-RAS 1D; depósito en Virrilá; mayor exceso de esfuerzo cortante hacia Sechura | `documental` |
| D. INGEMMET | Metadatos y servicios consultados; PDFs de Piura no descargados | MapServer vectorial de geología 1:100 000, geomorfología, susceptibilidad a inundación y peligros geológicos | Geología y geomorfología vectoriales; susceptibilidad y peligros con metadatos incompletos | `localizada` / `documental` |
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
- **Geología Integrada 1:100 000:** MapServer vectorial con hojas, secciones,
  fallas, pliegues, contactos y geología; 27 mapas digitales de 2014 y 2016.
  <https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_100K_INTEGRADA/MapServer>.
- **Geomorfología:** MapServer vectorial; 2.281 polígonos en el área de Piura.
  <https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOMORFOLOGIA/MapServer>.
- **Susceptibilidad a inundación fluvial:** MapServer vectorial; 59.152 polígonos
  en el área de Piura, clases Bajo/Medio/Alto.
  <https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_SUSCEPTIBILIDAD_INUNDACION_FLUVIAL_MIL1/MapServer>.
- **GEOCATMIN — Peligros Geológicos:** MapServer vectorial de puntos; 1.729
  puntos en el área de Piura.
  <https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_PELIGROS_GEOLOGICOS/MapServer>.
- **Licencia:** la ficha de Geología Integrada dice «de uso y acceso público según
  escala de trabajo»; no es una licencia Creative Commons. Peligros Geológicos no
  declara licencia.

### Qué se recuperó y revisó

Se consultaron las fichas y los MapServer vectoriales. No se descargaron las
hojas completas de la Carta Geológica, pero sí se consultaron las capas
vectoriales de geología, geomorfología, susceptibilidad y peligros. La capa de
geología tiene 2.608 polígonos en el área de Piura y cubre las hojas 10d, 11d,
12d y 13d, entre otras.

La conclusión anterior —«solo PDF/teselas, sin vector»— era incompleta: el ítem de
ArcGIS Online es una vista de teselas, pero el MapServer subyacente tiene
capacidades `Map, Query, Data` y capas vectoriales.

### Contenido útil

- Geología superficial, geomorfología y depósitos aluviales de la cuenca.
- Inventario de peligros geológicos (inundación fluvial, erosión fluvial, flujos,
  arenamientos, derrumbes).
- Susceptibilidad a inundación fluvial, con clases Bajo/Medio/Alto; sin metadatos
  de escala, fecha ni metodología.
- Contexto para entender la llanura aluvial y los procesos geodinámicos.

### Anexos y mapas

La Carta Geológica sigue disponible en PDF/JPG. La Geología Integrada, la
Geomorfología y la susceptibilidad son servicios vectoriales consultables, no
paquetes de descarga independientes. El inventario de peligros es un servicio de
puntos. No se integró ninguno en runtime.

### Limitaciones

- La susceptibilidad de INGEMMET no es una probabilidad hidrológica ni una
  inundación observada; no se usa como equivalente de la mancha de 2017.
- La capa de susceptibilidad no declara escala, fecha, metodología ni leyenda en
  atributos; el servicio no tiene descripción.
- La licencia no es formal y no se verificaron los términos de cada hoja.
- Usar estos servicios en runtime añadiría una dependencia externa y rompería la
  reproducibilidad del sitio estático.
- La geología y la geomorfología son regionales; no sustituyen un levantamiento
  local.

### Recomendación

Mantener como fuentes **localizadas/documentales**. No incorporar capas hasta
confirmar licencia, escala, fecha y metodología. Si se integran, priorizar geología
superficial, geomorfología y depósitos aluviales; no usar la susceptibilidad como
probabilidad de inundación.

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
- **Portal:** <https://observatorio.senamhi.gob.pe/investigadores/descarga-pisco>;
  permite descargar por punto, archivo o área en CSV/XLSX, pero usa Cloudflare
  Turnstile.
- **Licencia:** el artículo es CC BY 4.0 y aclara que el **código** es GPL 3.0; el
  conjunto de datos en Figshare declara **GPL 3.0+**, pero la licencia del NetCDF
  no está explícita. La discrepancia no se resolvió.

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

- Las 501 hojas de la Carta Geológica Nacional no se descargaron completas; sí se
  consultó el MapServer vectorial de 27 mapas de la Geología Integrada.
- Shapefiles de Piura y Castilla de INDECI 2009: no se publican.
- Archivos GIS del estudio ANA 2014: no se encontraron.
- NetCDF diario de PISCOp v3.0: no se descargó por tamaño y por licencia pendiente.
- Coordenadas y mapas de la inspección de 2026: no se publican.
- Datos de la topobatimetría del PECHP de 2026: no se publican.
- No se localizó una cobertura vectorial de las inundaciones de 1983/1998 para
  toda la cuenca; existen mapas PDF/JPG de Sullana y Cura Mori.
- No se localizó batimetría pública del cauce del río; solo notas del PECHP sobre
  Poechos y el levantamiento de 2026.
- La precipitación diaria por estación sí está disponible (1961–2015); los
  caudales diarios de 1983/1998 siguen pendientes.

## 13. Licencias: resumen operativo

| Fuente | Licencia | ¿Se puede publicar una capa derivada? |
|---|---|---|
| ANA 2014 | CC BY-NC-ND 4.0 | **No** sin permiso |
| INDECI 2009 | documento público; sin licencia explícita | No se redistribuyen planos; citar |
| Lund 2024 | acceso abierto; derechos de la autora | Citar; no reutilizar figuras |
| INGEMMET | uso público «según escala de trabajo»; sin licencia formal | No hasta confirmar |
| PISCOp v3.0 | artículo CC BY 4.0; código GPL 3.0; dataset GPL 3.0+ | **Pendiente** de aclaración |
| SENAMHI histórico por estación | dato público; términos por confirmar | No publicar el crudo hasta confirmar |
| ANA / MINAM ZEE Piura | servicio público; términos por confirmar | No hasta confirmar |
| SIGRID Sullana / Cura Mori | documento público; sin licencia explícita | Citar; no reutilizar mapas |
| PECHP 2026 | documento público; fotografías del PECHP | Citar; no reutilizar fotografías |
| Expedición 2002 | documento público; sin licencia explícita | Citar; no reutilizar mapas |

## 14. Recomendaciones

1. Incorporar la API histórica de SENAMHI como fuente de precipitación por
   estación para 1983/1998, con ETL reproducible y sin publicar el crudo hasta
   confirmar términos.
2. Evaluar la geología 1:100 000 de INGEMMET y la geomorfología como candidatas;
   confirmar licencia, escala y fecha antes de publicar.
3. Evaluar la capa ZEE Piura de peligro de inundación solo si se localiza el
   estudio que explique el método; no usarla como probabilidad.
4. Usar los mapas de Sullana y Cura Mori como evidencia documental; no
   digitalizarlos sin georreferenciación.
5. Mantener PISCO como prioridad, pero con compuerta de licencia.
6. Usar la expedición de 2002 como fuente principal del futuro módulo de la cuenca
   baja; no dibujar su ruta todavía.
7. Mantener las solicitudes de caudales diarios, batimetría del cauce, ejes de
   infraestructura y cartografía vectorial 1983/1998.
8. No confundir susceptibilidad geológica con probabilidad hidrológica.
9. No convertir propuestas de ANA en obras ejecutadas.

## 15. Segunda ronda de búsqueda (2026-11-17)

Esta ronda revisó portales, API y servicios ArcGIS, no solo resultados de búsqueda.
Corrige dos conclusiones anteriores: **INGEMMET sí tiene geología vectorial** y
**ANA tiene capas ZEE de Piura con peligro de inundación**. También encuentra una
API pública de series históricas por estación de SENAMHI.

### 15.1 SENAMHI — series históricas por estación

- **Catálogo:** <https://servicios.senamhi.gob.pe/api/researchers/historical-download/stations>.
- **Serie:** `https://servicios.senamhi.gob.pe/api/researchers/historical-download/stations/{id}/series`.
- **Variables:** precipitación diaria, temperatura máxima y mínima.
- **Estaciones:** 20 en Piura, entre ellas Ayabaca, Bernal, Chulucanas, Chusis,
  Miraflores, Morropón, San Miguel, Huarmaca, Lancones y Mallares.
- **Cobertura:** aproximadamente 1961–2015 por estación. Chulucanas tiene 1983 y
  1998 completos; no cubre 2017 ni 2023.
- **Caudales:** no están en esta API.
- **Licencia:** no declarada; usar con atribución y no redistribuir el crudo hasta
  confirmar términos.
- **Uso:** ETL `download_senamhi_historico.py` + `build_senamhi_historico.py`;
  salida local en `data/processed/senamhi/`, no publicada en el sitio.

### 15.2 INGEMMET — geología, geomorfología y susceptibilidad vectorial

- **Geología Integrada 1:100 000:** MapServer con 7 capas vectoriales; 2.608
  polígonos en el área de Piura; hojas 10d, 11d, 12d y 13d.
- **Geomorfología:** 2.281 polígonos en el área de Piura; escala no declarada.
- **Susceptibilidad a inundación fluvial:** 59.152 polígonos en el área de Piura;
  clases Bajo/Medio/Alto; sin escala, fecha ni metodología.
- **Peligros geológicos:** 1.729 puntos en el área de Piura; inventario, no
  probabilidad de inundación.
- **Licencia:** «de uso y acceso público según escala de trabajo»; no es una
  licencia formal. No se publica como capa hasta confirmar términos y metadatos.

### 15.3 ANA / MINAM — capas ZEE de Piura

- **Geología:** 1.155 polígonos.
- **Geomorfología:** 70 polígonos.
- **Peligro Inundación:** 78 polígonos; Muy Alta 38, Alta 30, Media 6 y Baja 4.
- **Vulnerabilidad frente a Inundaciones:** 19 polígonos.
- **Infraestructura Productiva:** 64 polígonos de distritos, no ejes de canales.
- **Metadata:** el servicio no declara fecha, escala ni metodología; el campo se
  llama `Nivel_Vuln` aunque la capa se llame Peligro Inundación.
- **Uso:** candidata; no se publica hasta localizar el estudio ZEE Piura.

### 15.4 Mapas históricos de 1983 y 1998

- **Sullana:** documentos 170 y 3165; PDF de 1 página con áreas de inundación de
  1983 y 1998.
- **Cura Mori:** documento 9400; ZIP de 976 MB con 1 PDF y 48 mapas JPG. Incluye
  altura y velocidad de inundación con Niño 1998, peligro de inundación 1998,
  sectores críticos, riesgo de líneas vitales, infraestructura agrícola y canales.
- **Piura:** documentos 676 y 761; mapas de peligros por inundación y origen
  climático, PDF de 1 página.
- **Geometría:** no hay shapefiles; son mapas e imágenes. No se digitalizan sin
  georreferenciación, escala y método.

### 15.5 PISCO — portal de descarga

- El Observatorio de SENAMHI permite descargar PISCO por punto, archivo o área,
  en CSV/XLSX, diario o mensual, 1981–2025.
- La consulta usa Cloudflare Turnstile; no es automatizable sin resolver el
  captcha.
- El artículo aclara que el **código** es GPL 3.0; la ficha de Figshare del
  dataset declara GPL 3.0+, pero la licencia del NetCDF no está explícita.
- Se mantiene `pendiente` para publicación de series derivadas.

### 15.6 Lo que sigue faltando

- Caudales y niveles diarios de 1983, 1998, 2017 y 2023.
- Batimetría y secciones transversales del cauce del río.
- Ejes oficiales de canales, diques y bocatomas.
- Cartografía vectorial de las inundaciones de 1983 y 1998 para toda la cuenca.
- Informe hidrológico de La Niña 2023 con área y volumen.
- Metadatos, fecha, escala y licencia de las capas INGEMMET y ZEE Piura.
