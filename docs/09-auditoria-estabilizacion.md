# 09 · Auditoría de estabilización

Fecha: 2026-11-16.
Alcance: topología de subcuencas, afirmaciones históricas, catálogo de fuentes,
pruebas funcionales y verificación del sitio.

## 1. Resumen ejecutivo

La intervención corrigió los defectos topológicos que la simplificación independiente
de las subcuencas había dejado: **15 solapamientos (0,7828 km²)**, **0,6747 km² fuera
de la cuenca** y **1,4725 km² de huecos**. La cuenca y las nueve subcuencas se
reconciliaron como una partición topológica en EPSG:32717; el resultado tiene
**0 solapamientos, 0 superficie fuera y 0 huecos por encima de 0,01 km²**, sin crear
superficie nueva. La suma de áreas sigue siendo 10 938,4 km².

También se corrigieron afirmaciones históricas y metadatos: la fecha del pico de 1998
es discrepante en la propia fuente (12 vs 16 de marzo), el vector de 2017 es una unión
de observaciones de dos fechas y no una mancha simultánea, el PDF de AOI10 declara un
sensor distinto al del DBF, y Bajo Piura estaba atribuido a ANA aunque es derivado por
el proyecto. Se añadieron fuentes verificables para 1891, 1983, 1998, 2017 y 2023.

Resultado: `check_data.py` en verde sin avisos, **38 pruebas Python** y **10 pruebas
Playwright** en verde, `npm run check` sin errores, build y enlaces correctos,
accesibilidad sin violaciones WCAG A/AA.

## 2. Problemas detectados

| Hallazgo | Evidencia | Severidad |
|---|---|---|
| 15 solapamientos entre subcuencas; 0,7839 km² medidos (0,7828 km² en la rejilla de reconciliación); máximo 0,1187 km² (Bajo Piura / Medio Bajo Piura) | Shapely en EPSG:32717 sobre `web/public/data/subcuencas.geojson` antes de la corrección | Alta |
| 0,6725 km² de subcuencas fuera de la cuenca medidos (0,6747 km² en la rejilla); máximo 0,2370 km² (Alto Piura) | Ibídem | Alta |
| Hueco de 1,4760 km² medido (1,4725 km² en la rejilla) en 176 fragmentos; máximo 0,0487 km² | Ibídem | Alta |
| Las ocho subcuencas ANA originales no se solapan; los slivers nacen de simplificar cada una por separado | Consulta directa al geoservidor ANA | Alta |
| Bajo Piura atribuido a `ana-subcuencas` aunque es derivado por el proyecto | `subcuencas.geojson` antes de la corrección | Alta |
| AOI10 de 2017 es la unión de 26/03 (Radarsat, 80,785 km²) y 30/03 (Cosmo-SkyMed, 73,040 km²); unión 97,053 km²; se publicaban 96,5 km² sin declarar la unión | Atributos `src_date` y `source_nam` del DBF de EMSR199 | Alta |
| El PDF v2 de AOI10 declara Sentinel-1A, pero el DBF declara Radarsat/Cosmo-SkyMed | PDF v2 vs DBF | Media |
| 1998: el pico de 4 424 m³/s aparece con fecha 12 de marzo en la introducción y 16 de marzo en el análisis de niveles | SIAR 200, p. 1 y p. 15 | Media |
| 1891: el cambio de embocadura está documentado, pero el mecanismo y el detalle “cerca de Sechura” requieren matiz | SIAR 1392 p. 5 y 7; tesis PUCP 2021 | Media |
| 2023: la reactivación de La Niña no tenía fuente en el catálogo | Andina 22/03/2023; NASA 10/04/2023 | Media |
| HydroRIVERS se citaba como “v10.0” y el mapa decía “HydroSHEDS” | Página oficial de HydroRIVERS: producto versión 1.0, archivos v10 | Media |
| Fechas marcador de posición (`2017-03-01`, `2018-01-01`) y enlaces genéricos (ENFEN) | `data/sources.yml` antes de la corrección | Media |
| La ficha de la cuenca no se abría al hacer clic en el relleno: `cuenca-fill` no estaba en `queryRenderedFeatures` | `mapa.astro` antes de la corrección | Media |
| WebGL sin soporte mostraba el mensaje pero sin enlace de salida | `maqueta.astro` antes de la corrección | Baja |
| Las pruebas Playwright no cubrían dibujo de perfil, capas, ficha, Escape ni WebGL ausente | `web/tests/e2e/atlas.spec.ts` antes de la corrección | Media |

## 3. Problemas corregidos

### 3.1 Topología

- `etl/topology.py` concentra la auditoría y la reconciliación.
- `etl/download_ana.py` simplifica la cuenca y las nueve subcuencas por separado,
  polygoniza el grafo de límites y asigna cada cara a la subcuenca con mayor
  solapamiento. Los huecos sin solapamiento se asignan a la más cercana.
- La cuenca y las subcuencas comparten una rejilla de 1e-6° (~0,11 m) antes de
  serializar, para que el redondeo no abra slivers en el borde.
- Si una subcuenca tuviera agujeros interiores, la reconciliación se detiene; no se
  rellena un cuerpo de agua o un enclave en silencio.
- `etl/check_data.py` audita `limits.json` y `subcuencas.geojson` con la misma
  función: solapamientos por par, superficie fuera por subcuenca, huecos por
  componente y agujeros interiores. La suma de áreas quedó como comprobación
  secundaria.
- Bajo Piura se publica con la fuente `bajo-piura-derivado`, institución
  «Río Piura Atlas (elaboración propia a partir de ANA)».

Resultado exacto de la reconciliación (`data/raw/limits.json → reconciliacion`):

| Métrica | Antes (rejilla 1e-6°) | Después |
|---|---:|---:|
| Solapamientos | 0,7828 km² | 0,0000 km² |
| Superficie fuera de la cuenca | 0,6747 km² | 0,0000 km² |
| Huecos | 1,4725 km² | 0,0000 km² |
| Caras del grafo | — | 374 |
| Caras de hueco asignadas | — | 209 |
| Suma de subcuencas | 10 938,4 km² | 10 938,4 km² |
| Bajo Piura | 4 752,9 km² | 4 752,9 km² |

La auditoría sin rejilla dio 0,7839 km² de solapamientos, 0,6725 km² fuera y
1,4760 km² de huecos; las diferencias con la tabla son de milésimas y provienen de
fijar la rejilla común de 1e-6° antes de reconciliar. No se ocultan: ambas medidas
están en los registros de la intervención.

Cambios de área por subcuenca (km², EPSG:32717): Bajo Piura +0,1080; Alto Piura
+0,0274; Medio Alto Piura +0,0385; Unidad Hidrográfica 13784 +0,0220; Medio Piura
+0,1611; Bigote +0,0196; Corrales +0,0074; Medio Bajo Piura −0,2433; San Francisco
−0,1258. Los cambios son de centésimas de km² y no crean superficie nueva.

### 3.2 Histórico y científico

- **1891.** Se cita SIAR 1392 p. 5 y 7 y la tesis PUCP 2021. El cambio de embocadura
  se marca como documentado; el mecanismo de crecidas/avulsión, como interpretación
  histórica.
- **1983.** Se añade la fecha del pico: 21 de abril de 1983, 3 200 m³/s (SIAR 200
  p. 15; SIAR 204 p. 49). La duración diaria no se localizó y se declara.
- **1998.** Se mantiene 4 424 m³/s, pero se retira la falsa precisión de una única
  fecha: SIAR 200 dice 12 de marzo en la introducción y 16 de marzo en el análisis de
  niveles. Se añaden los 161 días y la formación de La Niña con IMARPE 2019.
- **2017.** La ficha declara las observaciones por fecha y sensor, el área original y
  el área simplificada. Se distingue la unión de fechas de una mancha simultánea. Se
  declara que solo se publica `Flooded Area` y que no hay clase potencial en el
  vector. Se advierte la discrepancia PDF/DBF.
- **2023.** Se añade una nota separada: la laguna La Niña se reactivó y desbordó en
  marzo; Andina y NASA lo documentan. No se publica área ni volumen porque no hay
  informe hidrológico de SENAMHI/ANA en el catálogo.
- Se añadió una leyenda de certidumbre en `/escenarios` y en `/fuentes`: dato medido,
  derivado, documentado, interpretación y por verificar.

### 3.3 Catálogo de fuentes

- `data/sources.yml` incorpora `certeza` y `tipo`, y campos opcionales `documento`,
  `pagina` y `consultado`.
- HydroRIVERS se corrige a **v1.0 (archivos v10)** y se diferencia de HydroSHEDS.
- Se añaden: `bajo-piura-derivado`, `siar-evaluacion-200`, `pucp-1891`,
  `imarpe-la-nina-2019`, `andina-la-nina-2023` y `nasa-la-nina-2023`.
- ENFEN y UDEP quedan como `por_verificar`: no se localizó el documento exacto y no
  se usan para cifras concretas.
- Las fechas de consulta de OSM y PECHP pasan a `consultado`; las fechas de
  documento desconocidas quedan en `null`.
- `LICENSES/DATOS.md` incluye las fuentes nuevas y suaviza “sin restricciones” para
  ANA, que no estaba verificado.

### 3.4 Interfaz y accesibilidad

- La ficha de la cuenca se abre al hacer clic en el relleno (`cuenca-fill`) y
  desde el botón «Ver ficha de la cuenca», accesible con teclado.
- La ficha de subcuenca distingue ANA de Bajo Piura derivado.
- La ficha de 2017 muestra las observaciones por fecha y la advertencia de unión.
- `Escape` cierra el panel de corte y devuelve el foco al botón que lo abrió.
- La maqueta, si WebGL falla, muestra un enlace al mapa 2D.
- El mapa expone `data-ready="true"` después de cargar datos, registrar manejadores
  y completar el primer `idle` de MapLibre; las pruebas esperan ese estado
  observable en vez de un tiempo arbitrario.

## 4. Validaciones geoespaciales implementadas

`etl/topology.py` ofrece:

- `audit_partition(basin, named_geoms, tolerances, hole_notes)`.
- `pairwise_overlaps`, `outside_basin`, `gap_components`, `hole_findings`.
- `reconcile_partition(basin, named_geoms, precision=1e-6)`.

Tolerancias y justificación:

| Control | Error | Aviso | Justificación |
|---|---:|---:|---|
| Solapamiento por par | 0,01 km² | 0,001 km² | A 1:100 000, 1 mm² = 0,01 km²; 0,001 km² = 0,1 mm² |
| Hueco por componente | 0,01 km² | 0,001 km² | Ibídem |
| Hueco total | >0,01 % de la cuenca | >0,001 % | Evita que muchos slivers pequeños pasen inadvertidos |
| Fuera de cuenca por subcuenca | 0,01 km² | 0,001 km² | Ibídem |
| Suma de áreas | 0,5 % | — | Comprobación secundaria; no sustituye la geometría |

No se usa EPSG:32718 para medir: el servicio declara 32717 y el polígono está en la
zona 17S. 32718 es el CRS en el que ANA calculó `Shape_Area`; la capa declara
`sourceSpatialReference: 32718`. La medición en 32718 da 11 021,44 km², coherente con
el campo de ANA; la medición geodésica da 10 938,4 km².

## 5. Afirmaciones históricas verificadas

| Afirmación | Fuente | Evidencia | Estado |
|---|---|---|---|
| Antes de 1891 el río desembocaba en el mar; desde 1891 va a San Ramón; en 1983 vuelve al mar | SIAR 1392 p. 5 y 7 | «al mar (antes 1891 y en 1983); a laguna San Ramón (desde 1891)»; «reocupación del cauce antiguo» | Verificado |
| El mecanismo de 1891 incluye crecidas y avulsión | Tesis PUCP 2021, cita a Huertas (1999) y Rocha (2014) | El lecho principal cambió hacia el sureste por las crecidas de 1891 | Documentado con matiz de interpretación |
| 1983: 3 200 m³/s el 21/04/1983 | SIAR 200 p. 15; SIAR 204 p. 49 | Tabla 1983 = 3200,0; «21 de abril… 3200 m³/s» | Verificado |
| 1983 y 1998: descarga total hasta 12 veces la media anual | SIAR 204 p. 13 | «la descarga total supera en doce veces la media anual» | Verificado |
| 1998: 4 424 m³/s | SIAR 204 p. 27 y 49; SIAR 200 p. 1 y 15 | Serie de Puente Sánchez Cerro | Verificado |
| 1998: 12 o 16 de marzo | SIAR 200 p. 1 y p. 15 | «12 de marzo 1998» vs «16 de marzo de 1998» | Discrepancia declarada |
| 1998: 161 días de evento | SIAR 200 p. 1 | «durante un período de 161 días» | Verificado |
| 1998/2017: La Niña, 2 326 / 2 172 km² | IMARPE 2019, Escudero & Xu | MODIS-Aqua 500 m; área máxima | Verificado con límite de resolución |
| 2017: AOI10 Radarsat 26/03 y Cosmo-SkyMed 30/03; AOI11 Radarsat 26/03 | DBF de EMSR199 | `src_date` y `source_nam` de 1 378 + 413 registros | Verificado en el vector |
| 2017: PDF v2 declara Sentinel-1A | PDF EMSR199 10PIURA v2 | Texto del pie de mapa | Discrepancia declarada |
| 2023: La Niña se reactiva y desborda | Andina 22/03/2023; NASA 10/04/2023 | Nota de prensa y Landsat 9 | Documentado; sin informe hidrológico |

## 6. Afirmaciones pendientes de verificación

- **Fecha exacta del pico de 1998.** Se necesitan las series diarias de SENAMHI o
  una fuente que resuelva la discrepancia 12/16 de marzo de SIAR 200.
- **Duración del episodio de 1983.** No se localizó una serie diaria.
- **Área y volumen de La Niña en 2023.** Andina y NASA documentan el evento, pero no
  hay informe hidrológico de SENAMHI/ANA en el catálogo.
- **Documento ENFEN concreto.** La ficha actual es genérica; no se usa para cifras.
- **Documento UDEP concreto.** La URL es un handle; falta identificar la tesis o
  informe exacto.
- **Geometría oficial del vaso de Poechos y eje del canal Daniel Escobar.** Se
  mantiene el punto del dique y la recta de referencia.
- **Manchas de 1983 y 1998.** No hay geometría pública localizada.
- **Prueba manual de accesibilidad con personas.** La auditoría automática está
  limpia; falta teclado real, lector de pantalla y prueba con los tres públicos.

## 7. Fuentes documentales incorporadas

| id | Documento | Uso |
|---|---|---|
| `siar-piura` | Estudio para el Tratamiento Integral del Río Piura, Apéndice D (2000) | caudales 1983/1998, 12 veces la media |
| `siar-evaluacion-200` | Evaluación hidrológica y erosión-sedimentación del Río Piura | 21/04/1983; 12/16/03/1998; 161 días |
| `siar-cambios-cauce` | Cambios de la embocadura del río Piura | 1891 y 1983; p. 5, 7, 8 |
| `pucp-1891` | Tesis de modelamiento hidrológico e hidráulico | contraste para 1891 |
| `imarpe-la-nina-2019` | Escudero & Xu (2019), Bol. Inst. Mar Perú 34(1) | La Niña 1998/2017 |
| `andina-la-nina-2023` | Agencia Andina, 22/03/2023 | desborde de 2023 |
| `nasa-la-nina-2023` | NASA Earth Observatory, 10/04/2023 | Landsat 9 de 2023 |
| `bajo-piura-derivado` | Río Piura Atlas | subcuenca derivada, no ANA |

Las fuentes de 2017 ya existentes se conservaron; se corrigieron sus notas y se
añadieron los atributos del vector. `unosat-copernicus-ems` pasó a documento directo
de ReliefWeb y se mantiene como contraste, no como geometría.

## 8. Pruebas añadidas

### Python

`etl/tests/test_topology.py` (10 pruebas):

- dos subcuencas que se solapan;
- hueco entre dos subcuencas;
- subcuenca parcialmente fuera;
- subcuencas contiguas sin hallazgos;
- MultiPolygon sin falso hueco;
- agujero interior no justificado;
- agujero justificado como aviso;
- sliver pequeño como aviso vs solape grande como error;
- reconciliación que elimina solapamientos y huecos y conserva el área;
- reconciliación que rechaza agujeros interiores.

`etl/tests/test_published_contract.py` se amplió para comprobar la partición limpia,
la fuente derivada de Bajo Piura, las observaciones de 2017 y el total de la mancha.
Total: **38 pruebas**, todas OK.

### Playwright

`web/tests/e2e/atlas.spec.ts` (10 pruebas):

- carga, inundación y cierre de corte con retorno de foco;
- dibujo de un perfil con dos clics y nota de resolución;
- activación/desactivación de cuenca, subcuencas, ríos, agua, cortes, lugares,
  obras e inundación;
- consulta de la ficha de la cuenca desde el botón accesible;
- cierre con `Escape` y retorno de foco;
- fallo de una capa base;
- fallo de la capa de inundación;
- panel móvil plegado/abierto con `aria-expanded`;
- carga de la maqueta, reinicio y teclado;
- WebGL no disponible con enlace al mapa 2D.

## 9. Resultados de los comandos

| Comando | Resultado |
|---|---|
| `python3 etl/check_data.py` | OK; 0 errores, 0 avisos; 30 fuentes, 20 disponibles; topología 0/0/0 |
| `python3 -m unittest discover -s etl/tests -v` | 38 pruebas OK |
| `npm run check` | 0 errores, 0 warnings, 31 hints del Draco público |
| `npm run build` | 6 páginas, OK |
| `npm run check:links` | 94 enlaces internos, sin roturas |
| `npm run check:a11y` | 0 violaciones WCAG A/AA en 6 páginas + mapa/móvil + maqueta/móvil |
| `npm run test:e2e` | 10 pruebas OK |
| `BASE_PATH=/rio-piura-atlas npm run build` | OK |
| `BASE_PATH=/rio-piura-atlas npm run test:e2e` | 10 pruebas OK |

CI final: run **43981449273**, commit `7e52822`; jobs «Sitio web», «Datos y ETL» y
«GitHub Pages» en éxito. Sitio en vivo:
<https://joseamaya.github.io/rio-piura-atlas/> y `/mapa/`, `/escenarios/`, `/fuentes/`
responden 200. El GeoJSON desplegado conserva las observaciones por fecha.

Los dos primeros intentos de CI fallaron en la prueba de ficha por coordenadas:
el encuadre de MapLibre cambiaba entre entornos. Se corrigió la interfaz con un
botón accesible «Ver ficha de la cuenca» y se hizo que `data-ready` espere el primer
`idle` del mapa. No se relajó ninguna aserción; la prueba actual verifica el mismo
contenido por un camino estable.

Nota de entorno: el Python del sistema de esta máquina no tiene Shapely instalado;
las ejecuciones locales usaron `PYTHONPATH=/tmp/opencode/pylib`. CI instala
`etl/requirements.txt` y no necesita ese ajuste. No se alteró el resultado para
obtener un CI verde.

## 10. Limitaciones abiertas

- La reconciliación reparte slivers de simplificación; no sustituye una revisión
  cartográfica oficial de ANA. Los cambios de área son de centésimas de km².
- La mancha de 2017 es una unión de observaciones de dos fechas; no representa una
  extensión simultánea ni la extensión total del evento.
- La cifra de La Niña 1998/2017 es una estimación MODIS-Aqua de 500 m, no un
  levantamiento.
- La fecha de 1998 y la duración de 1983 siguen sin resolverse.
- No hay geometría oficial de Poechos, del canal ni de las manchas de 1983/1998.
- La prueba de accesibilidad con personas sigue pendiente.
- El GLB sigue siendo la excepción de peso (1,6 MB); no se tocó en esta fase.

## 11. Recomendaciones

1. Publicar una versión de parche (v0.2.1) con esta corrección topológica y de
   metadatos, sin cambiar la arquitectura.
2. Solicitar a SENAMHI las series diarias de 1983/1998 y a ANA/PECHP la geometría
   oficial de Poechos y del canal.
3. Incorporar el informe hidrológico de 2023 cuando esté disponible; no publicar
   cifras de área o volumen hasta entonces.
4. Identificar el informe ENFEN y la tesis UDEP exactos antes de usarlos para cifras.
5. Repetir la prueba manual de teclado, lector de pantalla y personas.
6. Si se añaden nuevas capas, mantener la auditoría de partición y las pruebas de
   regresión antes de publicar.

## Tabla de hallazgos

| Hallazgo | Severidad | Estado | Evidencia |
|---|---|---|---|
| 15 solapamientos, 0,7828 km² | Alta | Corregido y probado | `etl/topology.py`; `limits.json → reconciliacion`; 0 en `check_data` |
| 0,6747 km² fuera de la cuenca | Alta | Corregido y probado | Ibídem |
| 1,4725 km² de huecos | Alta | Corregido y probado | Ibídem |
| Bajo Piura atribuido a ANA | Alta | Corregido y probado | `bajo-piura-derivado`; test de contrato |
| 2017: unión de fechas no declarada | Alta | Corregido y probado | `observaciones` en `flood_2017.geojson`; test |
| 2017: discrepancia PDF/DBF de sensor | Media | Corregido y documentado | Nota en `sources.yml` y ficha |
| 1998: fecha 12 vs 16 de marzo | Media | Documentado; pendiente de fuente diaria | SIAR 200 p. 1 y 15 |
| 1983: fecha del pico | Media | Corregido y documentado | 21/04/1983; SIAR 200 p. 15 |
| 1891: mecanismo y detalle | Media | Documentado como interpretación | SIAR 1392 p. 5/7; tesis PUCP |
| 2023: La Niña sin fuente | Media | Corregido y documentado; sin cifra | Andina; NASA |
| HydroRIVERS v10.0 / HydroSHEDS | Media | Corregido | `sources.yml`; `mapa.astro` |
| Fechas y enlaces genéricos | Media | Corregido | `sources.yml`; `check_sources` |
| Ficha de cuenca no clickeable | Media | Corregido y probado | `cuenca-fill`; test Playwright |
| WebGL sin enlace de salida | Baja | Corregido y probado | `maqueta.astro`; test Playwright |
| Pruebas funcionales incompletas | Media | Corregido y probado | 10 pruebas Playwright |
| Agujeros interiores en datos actuales | — | No reproducido | 0 agujeros en las 9 subcuencas |
| Clase `Potential Flooded Area` | — | No reproducido | El DBF solo trae `Flooded Area` |
| Duración de 1983 | Baja | Pendiente de información externa | No localizada en SIAR |
| Geometría oficial de Poechos/canal | Media | Pendiente de información externa | PECHP/ANA no la publican |
| Manchas 1983/1998 | Alta | Pendiente de información externa | ANA/INDECI |
| Prueba con personas | Media | Pendiente | Auditoría automática limpia; falta prueba humana |
