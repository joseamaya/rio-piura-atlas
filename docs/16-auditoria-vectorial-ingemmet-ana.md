# 16 · Auditoría vectorial de INGEMMET y de la ZEE Piura

Actualizado: 2026-11-18.

Esta auditoría responde a una pregunta concreta: **¿qué geometría existe
realmente, qué cubre, con qué escala y licencia, y se puede extraer de forma
reproducible?** No incorpora capas al mapa. Las consultas se hicieron contra los
servicios publicados; las salidas completas quedan en
`data/processed/geoservicios/` (ignorado por Git).

## 1. Método y geometría de referencia

- Cuenca: `web/public/data/cuenca.geojson`, SHA-256
  `09e6d974969807a3d8c637503d4653276e74b5a0a603bcf47b0d4cddbd17fc43`,
  EPSG:4326; área geodésica publicada 10.938,4 km².
- Para contar polígonos se envió la geometría de la cuenca (no una envolvente)
  a cada capa con `spatialRel=esriSpatialRelIntersects`.
- Para áreas y distancias se reproyectó a EPSG:32717.
- Fecha de consulta: 2026-11-18. El servicio declara ArcGIS `currentVersion`
  10.91.
- Script: `etl/audit_geoservicios.py`. El certificado TLS de GEOCATMIN no es
  confiable en este entorno; la auditoría se ejecutó con `--insecure` explícito
  y eso queda registrado en el JSON. La opción no es el valor por defecto.

## 2. Geología Integrada 1:100 000

Servicio:
`https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_100K_INTEGRADA/MapServer`.

### 2.1 Qué hay realmente en la cuenca

- **576 polígonos** de la capa `Geología` (id 6) intersectan la cuenca ANA.
- **12 hojas** intersectan la cuenca. La capa `Hojas` (id 0) confirma los
  mismos códigos:

| Hoja | Nombre | Polígonos | ¿Está en la descripción oficial? |
|---|---|---|---:|
| 10b | Sullana | 9 | no |
| 10c | Las Lomas | 149 | no |
| 10d | Ayabaca | 9 | no |
| 11a | Paita | 3 | no |
| 11b | Piura | 68 | no |
| 11c | Chulucanas | 96 | no |
| 11d | Morropón | 127 | no |
| 11e | Huancabamba | 2 | sí |
| 12b | Sechura | 74 | no |
| 12c | La Redonda | 6 | no |
| 12d | Olmos | 31 | no |
| 12e | Pomahuaca | 2 | sí |

La descripción oficial del servicio enumera **27 mapas**:
09a, 09b, 09c, 09d, 09f, 09g, 09h, 10e, 10f, 10g, 10h, 11e, 11f, 11g, 11h,
12e, 12f, 12g, 12h, 13e, 13f, 13g, 13h, 14e, 14f, 14g y 14h. **No incluye
10d, 11d ni 12d**, aunque la capa sí contiene polígonos de esas hojas. Tampoco
incluye 10b, 10c, 11a, 11b, 11c, 12b, 12c ni 12d, que también están en la capa.

La lista antigua «10d, 11d, 12d y 13d» no describe la cuenca:

- **13d no intersecta la cuenca**; aparece en una consulta de rectángulo, no en
  el área de estudio.
- Faltan 10b, 10c, 11a, 11b, 11c, 11e, 12b, 12c y 12e.
- 10d, 11d y 12d sí están, pero no son la lista completa.

**Conclusión:** la descripción del servicio está desactualizada o incompleta y
no sirve como inventario de hojas. El inventario verificable es el de la capa
`Hojas` y los valores `HOJA` de la capa `Geología`.

### 2.2 Conteos anteriores y conteos actuales

| Capa | Docs 2.1 | Cuenca ANA (actual) | Rectángulo Piura (actual) |
|---|---:|---:|---:|
| Geología | 2.608 | **576** | 3.133 |
| Geomorfología | 2.281 | **573** | 2.651 |
| Susceptibilidad | 59.152 | **16.341** | 116.902 |
| Peligros geológicos (capa 0) | 1.729 | **230** | 2.311 |

Los conteos de 2.608, 2.281, 59.152 y 1.729 **no se reprodujeron** con el
servicio actual. No se deben presentar como cifras de la cuenca. La diferencia
se explica por el área consultada y por la fecha de la consulta; el servicio es
dinámico.

### 2.3 Geometrías, área y validez

Se descargó solo el subconjunto de la cuenca, no la capa nacional. El GeoJSON
local tiene 576 features y 23 MB:

- 575 geometrías válidas.
- 1 geometría inválida: `OBJECTID 6738`, hoja `11c`, unidad «Depósito fluvial»,
  con `Ring Self-intersection[-80.163707374 -5.12254285300003]`.
- 0 geometrías vacías.
- Área de los polígonos devueltos, sin recortar: **18.167,348 km²**.
- Área de la intersección con la cuenca, solo polígonos válidos:
  **10.804,291 km²** de los 10.938,4 km² de la cuenca.

La diferencia de ~134 km² no se rellena ni se interpreta como un vacío
geológico: incluye el polígono inválido excluido y posibles huecos de cobertura.
El polígono inválido **no se reparó** en esta fase; si se usara, habría que
registrar la reparación y medir su efecto.

### 2.4 CRS

| Elemento | CRS |
|---|---|
| Servicio MapServer | EPSG:102100 (Web Mercator) |
| Capa `Geología` consultada con `outSR=4326` | EPSG:4326 |
| WFS `Geología` | `urn:ogc:def:crs:EPSG::4326` |
| WFS `Hojas` | `urn:ogc:def:crs:EPSG::32718` |
| Cuenca ANA publicada | EPSG:4326 |
| Área y distancia de la auditoría | EPSG:32717 |
| ImageServer de susceptibilidad | EPSG:32718 |

El WFS de `Hojas` en 32718 es una trampa: no es el CRS de la cuenca. Además, el
bbox EPSG:4326 del WFS usa orden lat/lon; el orden lon/lat devolvió 0.

## 3. Extracción reproducible y límites del servicio

- `maxRecordCount = 1000`.
- `supportsPagination = false`.
- `resultOffset` y `resultRecordCount` devuelven **HTTP 400 «Pagination is not
  supported»**.
- La vía que funciona es paginar por `OBJECTID`:
  `where=OBJECTID>último`, `orderByFields=OBJECTID`, hasta 1.000 features por
  respuesta. Se probaron cuatro páginas consecutivas.
- Para el subconjunto de la cuenca (576 < 1.000) basta una consulta; por eso se
  descargó solo ese subconjunto.
- WFS 2.0 está anunciado con 7 feature types y `numberMatched=113.051` para
  `Geología`. En la prueba, `GetFeature&count=2` devolvió
  `numberReturned=2` pero **0 miembros**. No se usa como vía de extracción.
- WFS declara `Fees=1` y `AccessConstraints=referencial`. No son una licencia.
- WMTS está disponible: formatos `image/png`, tile matrix sets `default028mm` y
  `GoogleMapsCompatible`. Es un servicio de **teselas ráster**, no vectorial.
- El certificado TLS no es confiable con el almacén local. El script exige
  `--insecure` explícito para la consulta local; en un entorno institucional
  debe corregirse la cadena de certificados.

## 4. Geomorfología

Servicio:
`https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOMORFOLOGIA/MapServer`.

- **573 polígonos** intersectan la cuenca.
- Campos: `ETIQUETA`, `SUBUNIDAD`, `CODIGO`.
- Clases principales en la cuenca: Abanico de piedemonte (105), Terraza aluvial
  (101), Vertiente o piedemonte aluvial (37), Vertiente o piedemonte
  aluvio-torrencial (34), Montaña en roca metamórfica (30), Llanura o planicie
  aluvial (29).
- Metadato IDEP `893f41d0-cd70-4bcb-bfad-92bc215e2d82`: proyecto desde 2012;
  abstract con escala de trabajo **1:100 000** y presentación **1:250 000**;
  denominador del registro **1:3 000 000**. La capa del servicio no declara
  escala propia.
- No se usa para cálculos locales ni se publica.

## 5. Susceptibilidad a inundación fluvial

Servicio vectorial:
`SERV_SUSCEPTIBILIDAD_INUNDACION_FLUVIAL_MIL1`. ImageServer:
`SERV_IMG_SUSCEP_INUN_FLUVIAL`.

- **16.341 polígonos** intersectan la cuenca.
- `GRIDCODE`: 2 = 12.604; 3 = 2.587; 4 = 1.150.
- `LEYENDA` está nula o vacía en todos los registros.
- El renderizador asigna 2 = Bajo, 3 = Medio, 4 = Alto.
- El metadato 2018 (`2183b121-1f29-4cef-96e2-dc102ae96a76`) declara escala
  **1:1 000 000**, formato ráster, y dos variables: pendiente y subunidades
  geomorfológicas. La pendiente se derivó de la topografía IGN 1:100 000.
- La leyenda oficial 2018 tiene **cuatro clases**: Alto, Moderado, Bajo y Muy
  bajo o nulo. La capa vectorial solo tiene tres códigos (2/3/4) y no contiene
  la clase «Muy bajo o nulo». No es una reproducción completa de la leyenda.
- El ImageServer tiene píxel de **50 m** y EPSG:32718.
- Es una susceptibilidad, no una probabilidad hidrológica ni una mancha
  observada. No se publica.

## 6. Peligros geológicos

Servicio:
`https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_PELIGROS_GEOLOGICOS/MapServer`.

Conteos en la cuenca:

| Capa | Tipo | Conteo |
|---|---|---:|
| 0 Peligros Geológicos | puntos | 230 |
| 1 Otros Peligros Geológicos | puntos | 63 |
| 2 Zonas Críticas | puntos | 12 |
| 3 Peligros por Región | polígonos | 2 |
| 4 Regiones con Estudios de Riesgo | polígonos | 2 |
| 5 Estudios de Riesgo por Franjas | polígonos | 0 |
| 6 Cartografía de Peligros | polígonos | 37 |
| 7 Cartografía Peligros Fotointerpretado | polígonos | 0 |

La descripción del MapServer dice febrero de 2013; el metadato 2026
(`c5580ab5-7277-4858-8d16-a982bd2cc23b`) declara actualización al 28 de octubre
de 2026 y escala 1:100 000. Es un inventario heterogéneo, no una capa homogénea
de susceptibilidad. El `1.729` anterior no es el conteo de la cuenca.

## 7. ZEE Piura

### 7.1 Estudio

- Título: *La Zonificación Ecológica Económica (ZEE) de la Región Piura.
  Memoria Final*.
- Autor: Gobierno Regional de Piura, Gerencia Regional de Recursos Naturales y
  Gestión del Medio Ambiente; apoyo del MINAM. **No es una capa de ANA.**
- Fecha: noviembre de 2012; proceso 2008–2012.
- Extensión: 255 páginas.
- Escala: **1:100 000** (mesozonificación).
- Metadatos: `https://sinia.minam.gob.pe/metadatos/295867`.
- PDF: `https://sinia.minam.gob.pe/sites/default/files/sinia/archivos/public/docs/estudio_de_la_propuesta_de_zee_7.pdf`.
- SHA-256 del PDF descargado:
  `c5a68cc6b9ae3fab7cf1312c09be23620b8afb1144425d7c330a4e7cd92256e0`.
- Metodología: submodelos de valor productivo, bioecológico, histórico-cultural,
  peligros y vulnerabilidad, conflicto de uso y aptitud urbano-industrial. El
  submodelo de inundación combina geomorfología 40 %, fisiografía 40 %,
  pendiente 10 %, precipitación 5 % y cobertura vegetal 5 %. **No es una
  probabilidad hidrológica.**
- Licencia: no declarada ni en la Memoria ni en el servicio.

### 7.2 Capas del Geoservidor

Servicio de potencialidades:
`.../ZEE_VISOR/09_POTENCIALIDADES_Y_LIMITACIONES_PIURA/MapServer`.
Servicio de dimensión:
`.../ZEE_VISOR/09_DIMENSIÓN_DE_EVALUACIÓN_TERRITORIAL_PIURA/MapServer`.

| Capa | Polígonos | Clases |
|---|---:|---|
| Peligro Inundación | 78 | Muy Alta 38, Alta 30, Media 6, Baja 4 |
| Vulnerabilidad frente a Inundaciones | 19 | Alta 9, Media 4, Muy Alta 3, Baja 3 |

- El campo de ambas capas se llama **`Nivel_Vuln`**. La capa «Peligro
  Inundación» no usa un campo de peligro.
- La Memoria describe un submodelo de peligro y otro de vulnerabilidad; el texto
  de vulnerabilidad habla de tres niveles, pero las capas usan cuatro clases.
- No se puede asignar la semántica por intuición. **No se usa como peligro,
  probabilidad ni vulnerabilidad publicada** hasta que el autor confirme qué
  representa `Nivel_Vuln` y qué capa corresponde a cada submodelo.
- CRS del servicio: **EPSG:32717**. No declara fecha, escala, método ni licencia.
- La capa de geología de la ZEE (1.155 polígonos) y la de geomorfología (70) no
  se auditaron en detalle porque el servicio no declara metadatos; se mantienen
  como referencia documental.

## 8. Catálogo IDEP y licencia

- El catálogo de metadatos de INGEMMET está en
  `https://metadatos.ingemmet.gob.pe:8443/geonetwork`.
- `https://idep.ingemmet.gob.pe/` **no resolvió** en esta red.
- La búsqueda de `SERV_GEOLOGIA_100K_INTEGRADA` devolvió **0 registros**. El
  registro más cercano es `0cc58287-29e0-415c-bf19-63bb1f51c59a` («GEOCATMIN —
  Geología integrada de proyectos geológicos»), con escala 1:100 000 en el
  metadato, pero **sin enlaces WFS/WMTS**.
- La consulta CSW con `AnyText` produjo un error interno de GeoNetwork; la
  búsqueda se hizo con la API JSON.
- Los servicios WFS/WMTS se verificaron directamente en GEOCATMIN, no a través
  de un registro del catálogo.
- Licencia de descarga (`https://geocatminapp.ingemmet.gob.pe/descarga?id=8&str=GEO_INGEEX`):
  **«Licencia para Uso No Comercial»**. El texto autoriza la utilización,
  traducción y creación de obras derivadas de los datos «a condición de que se
  cite al INGEMMET»; prohíbe la reproducción del software y no autoriza uso
  comercial. La aplicación de esta licencia a WFS/WMTS no está declarada.
- El atlas es CC BY 4.0 (permite uso comercial). **No se puede publicar una capa
  derivada de INGEMMET bajo la licencia actual del atlas sin una decisión de
  licencia separada.** Ver `docs/17-licencias-y-reutilizacion.md`.

## 9. Qué se puede decir que está validado

| Estado | Geología | Geomorfología | Susceptibilidad | Peligros | ZEE |
|---|---|---|---|---|---|
| Localizado | sí | sí | sí | sí | sí |
| Descargado | subconjunto de la cuenca | metadatos y conteos | metadatos y conteos | metadatos y conteos | Memoria y conteos |
| Procesado | 576 features, validez y área | conteos por clase | conteos por clase | conteos por capa | conteos por clase |
| Validado | geometría y conteo; 1 inválida | conteo; escala contradictoria | conteo; leyenda incompleta | conteo; fechas heterogéneas | fecha, escala y método; semántica no |
| Autorizado para publicación | **no** | **no** | **no** | **no** | **no** |

## 10. Reproducción

```bash
python3 etl/audit_geoservicios.py --insecure
```

La opción `--insecure` es explícita por el certificado TLS; no se usa en CI. El
script no descarga la capa nacional completa: solo el subconjunto de la cuenca
para geología. Las salidas quedan en `data/processed/geoservicios/`:

- `auditoria.json`
- `hojas_geologia_cuenca.csv`
- `clases_susceptibilidad.csv`
- `zee_piura_clases.csv`
- `geologia_cuenca.geojson` (23 MB, local, no publicado)

## 11. Limitaciones y siguientes comprobaciones

- Confirmar con INGEMMET la licencia aplicable a WFS/WMTS y la compatibilidad con
  un atlas CC BY 4.0.
- Pedir el registro ISO 19115 del servicio `SERV_GEOLOGIA_100K_INTEGRADA`.
- Confirmar la escala efectiva de geomorfología.
- Resolver la leyenda vectorial de susceptibilidad (tres clases frente a cuatro).
- Confirmar con el Gobierno Regional de Piura / MINAM el significado de
  `Nivel_Vuln` y la relación entre la Memoria 2012 y las capas del Geoservidor.
- Decidir si la geología se publica como capa no comercial separada o queda como
  documentación. En esta fase no se publica.
