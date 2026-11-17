# 09 · Auditoría científica y geométrica

Fecha: 2026-11-16.
Rama local: `audit/cientifica-v0.2.2`.
Base auditada: `15c9b58` (`v0.2.1`). El commit `d2fae02` citado en el encargo es
anterior a la corrección del pie y al release; no se usó como base.
Alcance: cuatro correcciones limitadas —validación antes de reparar, cifras de 2017,
fidelidad de la reconciliación y auditoría documental— sin cambiar la arquitectura,
sin publicar y sin desplegar.

## 1. Resumen ejecutivo

La auditoría encontró que la estabilización anterior había limpiado la topología,
pero todavía ocultaba información en tres frentes:

1. **La validez se comprobaba después de reparar.** `make_valid()` se aplicaba antes
   de la auditoría; el error original no se reportaba. Un polígono bow-tie se
   convertía en MultiPolygon válido y la auditoría no lo veía. Además, una geometría
   vacía podía producir un hueco `nan`.
2. **Las cifras de 2017 no estaban reconciliadas.** 96,5 km² es correcto para la capa
   publicada, pero no se explicaba que la unión original mide 97,053 km² y que las
   dos fechas de AOI10 se solapan en 56,772 km². La suma 80,8 + 73,0 = 153,8 km² no
   es una superficie.
3. **La fidelidad de la reconciliación no estaba medida.** La topología quedaba en
   0/0/0, pero ocho de las nueve subcuencas cambian más de 0,01 km² entre la fuente
   ANA y la geometría reconciliada. Parte es simplificación; parte es reasignación.
   No se publicaba IoU, diferencia simétrica, Hausdorff ni distancia media/p95.

También se corrigieron afirmaciones históricas: se retiró «litoral de Sechura»
porque SIAR no lo dice; se suavizó «161 días»; se retiró la atribución específica a
la tesis PUCP porque no se pudo abrir; y se cambió «2023 no cambió la desembocadura»
por «no se localizó evidencia de cambio».

Resultado: **52 pruebas Python** y **10 Playwright** en verde; `check_data.py` sin
errores y con **10 avisos** declarados; build, enlaces y accesibilidad
correctos. Los avisos no se ocultaron.

## 2. Problemas encontrados

| # | Hallazgo | Evidencia | Severidad |
|---|---|---|---|
| 1 | `make_valid()` se aplicaba antes de comprobar validez; la comprobación posterior era código muerto | `as_polygonal(bow-tie)` devolvía MultiPolygon válido; `audit_partition` no emitía `invalid` | Alta |
| 2 | Una geometría vacía podía generar un hueco `nan` | Prueba sintética: `gap nan` en `audit_partition` | Alta |
| 3 | `_geometry_from_record()` reparaba `limits.json` antes de validarlo | `check_raw_limits` no podía ver un anillo inválido | Alta |
| 4 | `geometry_record_from_geometry()` comprobaba validez después de `make_valid()` | La comprobación era tautológica | Media |
| 5 | El redondeo a 6 decimales de `limits.json` creó una autointersección en San Francisco | El registro era inválido y `check_data` lo reparaba en silencio | Alta |
| 6 | La unión de AOI10 no se explicaba: 97,053 km² originales frente a 96,507 km² publicados | Web y docs mostraban solo 96,5 km² | Alta |
| 7 | No se declaraba el solapamiento de 56,772 km² entre las dos fechas de AOI10 | Cálculo en EPSG:32717 | Alta |
| 8 | Un polígono de AOI10 traía autointersección de anillo | DBF/Shapefile EMSR199; reparado con registro | Media |
| 9 | La reconciliación no medía IoU, diferencia simétrica, Hausdorff ni distancia media/p95 | `limits.json` solo tenía cambios de área | Alta |
| 10 | No se registraba cuánta superficie se asignaba por proximidad | 209 caras, 1,4725 km² | Alta |
| 11 | Ocho de nueve subcuencas cambian más de 0,01 km² en la reconciliación | `cambios_area_km2` | Media |
| 12 | «Litoral de Sechura» no está en SIAR 1392 | La fuente dice «al mar»; p. 4 habla de una bahía al sur de Piura, no de Sechura | Media |
| 13 | «El evento duró 161 días» sobreinterpreta la fuente | SIAR 200 p. 1 dice «durante un período de 161 días» | Media |
| 14 | La tesis PUCP no se pudo abrir y se usaba para el mecanismo de 1891 | 403/Anubis; el resumen no menciona 1891 | Media |
| 15 | «2023 no cambió la desembocadura» no tiene fuente | Andina y NASA describen el desborde, no la desembocadura | Media |
| 16 | No se reabrió el PDF de Copernicus para la discrepancia Sentinel-1A | El DBF sí está verificado | Baja |

## 3. Correcciones implementadas

### 3.1 Validación antes de reparar

`etl/topology.py` ahora separa:

- `inspect_geometry(geom)`: comprueba validez, vacuidad, tipo y motivo sin tocar la
  geometría.
- `repair_to_polygonal(geom, allow_repair=False)`: normaliza solo cuando se le pide;
  devuelve un `GeometryAudit` con tipo original, tipo reparado, partes poligonales,
  componentes descartados y longitud descartada.
- `as_polygonal()`: no repara; falla ante geometría inválida o una GeometryCollection.
- `metric_area_km2()` y `geodesic_area_km2()`: no reparan; devuelven `0.0` para
  geometría vacía y nunca `nan`.
- `audit_partition()`: registra `invalid`, `empty` y `repair` antes de medir. Conserva
  el error original aunque la reparación sea posible.
- `reconcile_partition(..., allow_repair=False)`: se detiene ante una geometría
  inválida o compuesta. Solo repara si se autoriza y lo registra en `repairs`.
- `download_ana.py`: valida la fuente; si repara, escribe
  `reconciliacion.reparaciones`. Serializa con comprobación del registro y añade
  decimales si el redondeo crea una autointersección.
- `check_data.py`: valida los anillos crudos antes de reconstruir; reporta la
  reparación y no la usa para silenciar el error.
- `build_layers.py`: no repara `limits.json` ni `water.json`; si son inválidos, el
  build se detiene. En la mancha de 2017, cada reparación de origen queda en
  `reparaciones`.

La prueba clave: un bow-tie produce un hallazgo `invalid` de severidad error **antes**
de que `make_valid` lo convierta en MultiPolygon. La prueba falla con el código
anterior y pasa con el actual.

### 3.2 Cifras de 2017

`flood_2017.geojson` publica ahora, por AOI:

- `area_observaciones_sum_km2`
- `solapamiento_observaciones_km2`
- `area_union_original_km2`
- `area_filtrada_km2`
- `area_simplificada_km2`
- `area_publicada_utm_km2`
- `area_publicada_geodesica_km2`
- `area_original_km2` como alias de la unión original
- `reparaciones`

`area_km2` se calcula sobre el GeoJSON final reproyectado a EPSG:32717 y se guarda con
3 decimales. La web redondea a 1 decimal para mostrar 96,5 y 459,0. `check_data.py`
exige 0,01 km² de tolerancia, no el 1 % anterior, y comprueba las invariantes
suma − solapamiento = unión y unión ≥ mayor observación.

### 3.3 Fidelidad de la reconciliación

`data/raw/limits.json → reconciliacion.fidelidad` incluye, por subcuenca:

- área fuente, simplificada y reconciliada;
- Δ de simplificación, Δ de reconciliación, Δ total y porcentaje;
- IoU, diferencia simétrica;
- Hausdorff, distancia media y p95 entre límites;
- componentes de fuente y destino.

También se publica `reasignacion`: superficie asignada por solapamiento, por
proximidad, caras por proximidad, distancia máxima/media y superficies originales
solapada y fuera.

La distancia media y el p95 se muestrean cada 50 m en EPSG:32717. Hausdorff es el
máximo exacto entre límites y se publica como diagnóstico: un solo vértice aislado
puede dispararlo. Por eso se reportan también p95 y media.

Umbrales:

- Error topológico: 0,01 km² (1 mm² a 1:100 000).
- Aviso topológico: 0,001 km² (0,1 mm²).
- Aviso de fidelidad: |Δ reconciliación| > 0,01 km².
- Aviso de proximidad: superficie asignada por proximidad > 0,01 km².
- Aviso de p95: > 3 × 0,0006° ≈ 200 m. Es una regla derivada de la tolerancia de
  simplificación, no un estándar externo.
- IoU, diferencia simétrica y Hausdorff se publican como diagnóstico; no se usan
  solos para aprobar o rechazar.

### 3.4 Histórico

- **1891:** se retira «litoral de Sechura». Se mantiene el cambio de embocadura de
  SIAR 1392 p. 5 y 7. El mecanismo se apoya en la descripción general de avulsión de
  SIAR p. 9 y se marca como interpretación.
- **PUCP:** `pucp-1891` pasa a `por_verificar`; no se usa para una afirmación
  específica. El PDF no se pudo abrir.
- **1983:** se mantiene 3 200 m³/s del 21/04/1983; no se afirma una duración.
- **1998:** se mantiene 4 424 m³/s y la discrepancia 12/16 de marzo. «161 días» pasa
  a «SIAR 200 consigna un período de 161 días», con salvedad.
- **2017:** se publica la tabla completa; se distingue área delineada de superficie
  inundada; se declara el solapamiento y la reparación de AOI10.
- **2023:** se añaden los 120 m de Andina y la fecha de las imágenes de NASA. Se
  cambia «no cambió la desembocadura» por «no se localizó evidencia de cambio».
- Se crea `docs/10-contexto-historico.md` con el registro de afirmaciones, fuente,
  página, cita, acceso directo y estado.

## 4. Métricas topológicas y de fidelidad

Topología de la partición publicada:

| Métrica | Valor |
|---|---:|
| Cuenca | 10 938,4 km² |
| Suma de subcuencas | 10 938,4 km² |
| Solapamientos | 0,0000 km² |
| Superficie fuera de la cuenca | 0,0000 km² |
| Huecos por encima de 0,01 km² | 0,0000 km² |
| Caras del grafo | 374 |
| Caras de hueco | 209 |
| Superficie asignada por proximidad | 1,4725 km² |
| Superficie solapada original | 0,7828 km² |
| Superficie fuera original | 0,6747 km² |

Fidelidad fuente ANA → reconciliada, en EPSG:32717:

| Subcuenca | Fuente km² | Reconciliada km² | Δ total km² | Δ total % | IoU | Dif. sim. km² | Hausdorff m | Media m | p95 m | Δ reconciliación km² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bajo Piura | 4 749,485 | 4 749,354 | −0,1309 | −0,00276 | 0,998646 | 6,4343 | 513,9 | 17,9 | 49,6 | +0,1080 |
| Alto Piura | 1 158,217 | 1 158,219 | +0,0020 | +0,00017 | 0,997428 | 2,9825 | 1 565,9 | 22,4 | 46,5 | +0,0275 |
| Medio Alto Piura | 508,492 | 508,540 | +0,0487 | +0,00958 | 0,995750 | 2,1656 | 65,8 | 17,5 | 47,8 | +0,0385 |
| Unidad Hidrográfica 13784 | 917,912 | 917,949 | +0,0368 | +0,00401 | 0,997143 | 2,6261 | 66,0 | 17,3 | 48,5 | +0,0220 |
| Medio Piura | 73,700 | 73,662 | −0,0376 | −0,05100 | 0,989643 | 0,7670 | 156,4 | 18,1 | 48,4 | +0,1611 |
| Bigote | 678,462 | 678,489 | +0,0275 | +0,00405 | 0,996754 | 2,2062 | 66,5 | 17,6 | 47,5 | +0,0194 |
| Corrales | 589,712 | 589,888 | +0,1758 | +0,02981 | 0,996306 | 2,1828 | 314,5 | 18,7 | 50,7 | +0,0075 |
| Medio Bajo Piura | 1 798,650 | 1 798,438 | −0,2128 | −0,01183 | 0,997817 | 3,9309 | 65,4 | 17,6 | 50,1 | −0,2433 |
| San Francisco | 457,863 | 457,605 | −0,2583 | −0,05641 | 0,996224 | 1,7316 | 190,3 | 16,1 | 46,1 | −0,1258 |

Lectura:

- La topología es limpia, pero la fidelidad no es perfecta. La mayor diferencia de
  área total es San Francisco (−0,258 km², −0,056 %). La mayor diferencia simétrica
  es Bajo Piura (6,434 km², 0,135 % de su área).
- Hausdorff es un valor extremo: Bajo Piura tiene 513,9 m, pero su p95 es 49,6 m y su
  media 17,9 m. Usarlo solo describiría mal la transformación.
- Ocho de las nueve subcuencas tienen |Δ reconciliación| > 0,01 km². Se reportan como
  **ADVERTENCIA**, no como error: la reconciliación redistribuye slivers y conserva
  la superficie total. No se ocultan.
- La superficie asignada por proximidad es 1,4725 km² en 209 caras. La distancia
  máxima es 0 m porque las caras de hueco tocan el borde de la subcuenca asignada;
  «proximidad» aquí significa «sin solapamiento», no «lejos».

## 5. Comparación de superficies de 2017

| AOI | Paso | Área |
|---|---|---:|
| AOI10 | 26/03, Radarsat | 80,785 km² |
| AOI10 | 30/03, Cosmo-SkyMed | 73,040 km² |
| AOI10 | suma de observaciones | 153,825 km² |
| AOI10 | solapamiento entre fechas | 56,772 km² |
| AOI10 | unión original | 97,053 km² |
| AOI10 | tras filtro <0,5 ha | 96,347 km² |
| AOI10 | tras simplificación 25 m | 96,507 km² |
| AOI10 | GeoJSON publicado, UTM | 96,507 km² |
| AOI10 | área geodésica | 96,582 km² |
| AOI11 | 26/03, Radarsat | 457,408 km² |
| AOI11 | unión original | 457,408 km² |
| AOI11 | tras filtro | 457,213 km² |
| AOI11 | tras simplificación | 458,975 km² |
| AOI11 | GeoJSON publicado, UTM | 458,970 km² |
| AOI11 | área geodésica | 459,322 km² |

Total publicado: **555,477 km²** en EPSG:32717. La diferencia geodésica es +0,075 km²
en AOI10 y +0,352 km² en AOI11 (≈0,08 %). No se mezcla con el área geodésica de la
cuenca.

La suma 80,785 + 73,040 = 153,825 km² **no es una superficie**. La unión original es
97,053 km² porque 56,772 km² se observaron en ambas fechas. La diferencia hasta
96,507 km² viene del filtro de fragmentos menores de 0,5 ha y de la simplificación a
25 m. No se ajustó ninguna cifra a mano.

## 6. Afirmaciones históricas verificadas

| Afirmación | Fuente abierta | Evidencia | Estado |
|---|---|---|---|
| Antes de 1891 el río iba al mar; desde 1891 va a San Ramón; en 1983 vuelve al mar | SIAR 1392 p. 5 y 7 | Cita textual | VERIFICADO |
| El mecanismo general es avulsión | SIAR 1392 p. 9 | Cita textual | VERIFICADO como interpretación general |
| 1983: 3 200 m³/s el 21/04/1983 | SIAR 200 p. 15; SIAR 204 p. 49 | Texto y tabla | VERIFICADO |
| 1983 y 1998: hasta 12 veces la media anual | SIAR 204 p. 13 | Cita textual | VERIFICADO |
| 1998: 4 424 m³/s | SIAR 204 p. 27 y 49; SIAR 200 p. 1 y 15 | Texto y tabla | VERIFICADO |
| 1998: discrepancia 12 vs 16 de marzo | SIAR 200 p. 1 y 15 | Dos pasajes | VERIFICADO |
| 1998: «período de 161 días» | SIAR 200 p. 1 | Cita textual | VERIFICADO con salvedad |
| La Niña: 2 326 km² en 1997-98 y 2 172 km² el 5/04/2017 | IMARPE, resumen | Cita textual | VERIFICADO como estimación MODIS 500 m |
| 2017: sensores y fechas por AOI | DBF de EMSR199 | `src_date` y `source_nam` | VERIFICADO |
| 2017: áreas y solapamiento | Cálculo propio EPSG:32717 | Tabla | VERIFICADO |
| 2023: desborde y 120 m de carretera | Andina 22/03/2023 | Cita textual | VERIFICADO |
| 2023: imágenes del 24/02 y 12/03; desborde del 23/03 | NASA 10/04/2023 | Texto e imágenes | VERIFICADO |
| 1891: mecanismo específico con Huertas/Rocha | Tesis PUCP | No se pudo abrir | PENDIENTE / no verificado |
| 2017: la ficha del PDF v2 declara Sentinel-1A | PDF Copernicus | No se reabrió | PENDIENTE |
| 2023: no cambió la desembocadura | — | Sin fuente | PENDIENTE / sin evidencia |

## 7. Fuentes consultadas y evidencia documental

Se abrieron directamente:

- SIAR Piura, *Cambios de la embocadura del río Piura* (1392), p. 4–9.
- SIAR Piura, *Evaluación hidrológica y erosión-sedimentación del Río Piura* (200),
  p. 1 y 15.
- SIAR Piura, *Estudio para el Tratamiento Integral del Río Piura, Apéndice D* (204),
  p. 13, 27 y 49.
- IMARPE, Escudero & Xu (2019), página del artículo y resumen.
- Agencia Andina, 22/03/2023.
- NASA Earth Observatory, 10/04/2023.
- Shapefile DBF de Copernicus EMSR199, AOI10 y AOI11.

No se abrieron:

- Tesis PUCP: 403/Anubis; solo registro bibliográfico y resumen.
- PDF 10PIURA v2 de Copernicus: no se reabrió en esta auditoría. El DBF sí se
  verificó.

## 8. Pruebas ejecutadas y resultados

| Comando | Resultado |
|---|---|
| `python3 -m unittest discover -s etl/tests -v` | **52 pruebas OK** |
| `python3 etl/check_data.py` | **0 errores**, **10 avisos** de fidelidad/reparación |
| `npm run check` | 0 errores, 0 warnings, 31 hints del Draco público |
| `npm run build` | 6 páginas, OK |
| `npm run check:links` | 94 enlaces internos, sin roturas |
| `npm run check:a11y` | 0 violaciones WCAG A/AA |
| `npm run test:e2e` | **10 pruebas OK** |

Avisos de `check_data.py`:

- Ocho subcuencas con |Δ reconciliación| > 0,01 km²: Bajo Piura, Alto Piura,
  Medio Alto Piura, Unidad Hidrográfica 13784, Medio Piura, Bigote, Medio Bajo Piura
  y San Francisco.
- 1,4725 km² asignados por proximidad.
- AOI10 reparó un polígono con autointersección de anillo.

No se ocultaron para obtener un resultado verde.

## 9. Limitaciones pendientes

- La reconciliación sigue siendo una partición derivada, no una delimitación oficial
  nueva de ANA. Los cambios de área están medidos, no eliminados.
- La superficie asignada por proximidad (1,4725 km²) es una decisión metodológica
  documentada; no se puede justificar parcela por parcela sin cartografía oficial.
- Hausdorff es sensible a vértices aislados; por eso se publica con media y p95.
- La fecha del pico de 1998 y la duración de 1983 siguen sin serie diaria.
- El PDF de Copernicus y la tesis PUCP no se pudieron abrir.
- No hay informe hidrológico de La Niña 2023 ni geometría oficial de Poechos/canal.
- No hay manchas oficiales de 1983 y 1998.
- La prueba manual de accesibilidad con personas sigue pendiente.
- El GLB sigue en 1,6 MB.

## 10. Tabla final de severidad y estado

| Hallazgo | Severidad | Estado |
|---|---|---|
| `make_valid` ocultaba invalidez original | Alta | **CORREGIDO** |
| Geometría vacía producía `nan` | Alta | **CORREGIDO** |
| `limits.json` se reparaba antes de validar | Alta | **CORREGIDO** |
| Redondeo a 6 decimales creaba autointersección en San Francisco | Alta | **CORREGIDO** |
| AOI10 no explicaba 97,053 vs 96,507 km² | Alta | **CORREGIDO** |
| No se declaraba el solapamiento de 56,772 km² | Alta | **CORREGIDO** |
| No se medía IoU, diferencia simétrica, Hausdorff ni p95 | Alta | **CORREGIDO** |
| No se registraba la asignación por proximidad | Alta | **CORREGIDO** |
| Ocho subcuencas cambian > 0,01 km² en la reconciliación | Media | **ADVERTENCIA** declarada |
| Un polígono de AOI10 era inválido | Media | **CORREGIDO** y registrado |
| «Litoral de Sechura» sin respaldo | Media | **CORREGIDO** |
| «161 días» sobreinterpretado | Media | **CORREGIDO** con salvedad |
| Tesis PUCP usada sin abrir | Media | **PENDIENTE**; fuente degradada |
| «2023 no cambió la desembocadura» sin fuente | Media | **CORREGIDO**; ahora «sin evidencia» |
| PDF de Copernicus no reabierto | Baja | **PENDIENTE** |
| Fecha del pico de 1998 | Media | **PENDIENTE** |
| Duración de 1983 | Baja | **PENDIENTE** |
| Informe hidrológico de La Niña 2023 | Media | **PENDIENTE** |
| Geometría oficial de Poechos/canal | Media | **PENDIENTE** |
| Manchas de 1983 y 1998 | Alta | **PENDIENTE** |
| Prueba manual con personas | Media | **PENDIENTE** |

## 11. Estado de publicación

Los cambios están en la rama local `audit/cientifica-v0.2.2`. **No se hizo push, no
se hizo merge y no se desplegó nada.** La versión publicada sigue siendo `v0.2.1`;
`v0.2.2` es la etiqueta propuesta para este diff. No se cambió `package.json` ni
`CITATION.cff` para no simular una release que no fue autorizada.
