# 03 · Metodología

## Principio

El atlas no dibuja nada que no pueda justificar. Cada elemento visible tiene:

- **procedencia**: de dónde sale el dato;
- **método**: cómo se transformó;
- **incertidumbre**: qué margen tiene;
- **licencia**: qué se puede hacer con él.

## Clases de incertidumbre

| Clase | Significa | Cómo se muestra |
|---|---|---|
| **Dato** | proviene de una fuente oficial sin transformación geométrica | línea continua, ficha con la fuente |
| **Derivado** | calculado a partir de un dato (p. ej. pendiente desde un DEM) | línea continua, ficha con el método |
| **Interpretación** | reconstruido por el equipo (p. ej. traza aproximada de un canal) | línea punteada + aviso |
| **Sin dato** | no existe información pública | se declara, no se rellena |

## Capas y su producción

### Límites y subcuencas
Polígono oficial ANA 1:100 000, simplificado a ~1 000 puntos por anillo. Sin
reinterpretación. Si se compara con otra delimitación (HydroBASINS, estudios
hidrológicos), la diferencia se documenta en la ficha. En la maqueta 3D las
subcuencas aparecen solo como rótulos; sus límites se consultan en el mapa 2D.

La cuenca y las nueve subcuencas se simplifican por separado y después se
**reconcilian como una partición topológica**: se polygoniza el grafo de límites y
cada cara se asigna a la subcuenca con mayor solapamiento; los huecos sin
solapamiento se asignan a la más cercana. No se crea superficie nueva y el área
total se conserva. El método y los cambios de área quedan en
`data/raw/limits.json → reconciliacion`.

Umbrales de control, en EPSG:32717 (UTM 17S, el sistema de trabajo de ANA):

| Control | Error | Aviso | Justificación |
|---|---:|---:|---|
| Solapamiento por par | 0,01 km² | 0,001 km² | A 1:100 000, 1 mm² en el papel = 0,01 km² |
| Hueco por componente | 0,01 km² | 0,001 km² | Ibídem; 0,001 km² = 0,1 mm² |
| Hueco total | >0,01 % de la cuenca | >0,001 % | Evita que muchos slivers pequeños pasen inadvertidos |
| Fuera de cuenca por subcuenca | 0,01 km² | 0,001 km² | Ibídem |
| Suma de áreas | 0,5 % | — | Comprobación secundaria, no sustituye la geometría |

No se usa EPSG:32718 para medir: el servicio declara 32717 y el polígono está en
la zona 17S. 32718 es el sistema en el que ANA calculó `Shape_Area`, no el de la
geometría publicada. Si una subcuenca trae un agujero interior, la reconciliación
se detiene para revisión manual; no se rellena en silencio.

La **validez se comprueba antes de reparar**. `inspect_geometry()` registra el
motivo, el tipo y la vacuidad; `repair_to_polygonal()` solo actúa cuando se autoriza
y deja un registro con el tipo reparado y los componentes descartados. Una geometría
inválida produce un hallazgo de error aunque tenga una reparación posible.

La fidelidad de la reconciliación se mide en EPSG:32717: IoU, diferencia simétrica,
Hausdorff, distancia media y p95 entre límites. La distancia media y el p95 se
muestrean cada 50 m; Hausdorff es el máximo exacto y se publica como diagnóstico
porque un vértice aislado puede dispararlo. Los cambios de área se separan en
simplificación y reconciliación. La superficie asignada por proximidad (sin
solapamiento) se publica aparte. Los umbrales de aviso son 0,01 km² para el cambio de
área de reconciliación y para la superficie por proximidad, y p95 > 3 × 0,0006°
(≈200 m), derivado de la tolerancia de simplificación.

### Relieve
Copernicus DEM GLO-30 como producto de origen, remuestreado a una **malla de trabajo
de ~143 × 134 m**. El atlas no presenta perfiles a 30 m: la malla no tiene ese detalle.
El relieve se muestra con **exageración vertical declarada** (×7 en la maqueta). La
exageración no es un dato: se dice en la leyenda y en la ficha. En la maqueta, el color
del terreno es una **rampa hipsométrica**: indica altitud, no cobertura vegetal.

### Red hídrica
HydroRIVERS, filtrada por área aportante y **recortada con intersección geométrica
exacta** contra la cuenca ANA. En la llanura el DEM no resuelve el cauce: el trazo
procede del vector, no del ráster. En la maqueta la red se eleva 45 m sobre el terreno
para que se lea; no es una cota real.

### Cortes transversales
Implementados en `etl/build_cortes.py` y visibles en `/mapa`.

- **Cortes de referencia**: cinco transectos perpendiculares a la red hídrica (Bajo
  Piura, Piura, Catacaos, Chulucanas y Tambogrande), centrados en el punto más cercano
  del río y recortados a la cuenca oficial. El perfil se muestrea a la resolución
  efectiva del DEM de trabajo (~143 m), no a 30 m.
- **Corte dibujado por el visitante**: dos clics sobre el mapa. El perfil se calcula
  sobre una malla `Int16` derivada del DEM de trabajo (resolución aproximada de 467 m)
  que se descarga solo al dibujar; así no se envía el ráster completo al navegador.
- La ficha declara resolución, longitud del transecto y cota mínima y máxima.
- **Límite**: un corte de DEM no sirve para dimensionar obras; sirve para explicar la
  forma del valle. Cuando exista batimetría, se superpondrá y se distinguirá por estilo.

### Escenarios de inundación
No se simulan. Se digitalizan de fuentes documentales:

1. fuente (mapa oficial, imagen satelital, informe);
2. fecha del evento;
3. método de extracción (descarga de vector oficial, digitalización manual o umbral
   sobre radar; el umbral propio no se usa para 2017);
4. control de calidad (comparación con relatos o mapas oficiales).

Cada escenario muestra un rótulo permanente: **«escenario documentado, no pronóstico»**.

### Inundación de 2017
La mancha publicada es el **vector oficial de Copernicus EMSR199**, no una
reconstrucción propia. Se usan dos áreas de interés:

- **AOI10 Piura**: Piura, Catacaos y La Unión. Atributos del vector: Radarsat
  Ultra-Fine Beam (26/03/2017) y Cosmo-SkyMed 3-15m Stripmap (30/03/2017).
- **AOI11 Parachique**: llanura baja y desierto adyacente. Radarsat Ultra-Fine Beam
  (26/03/2017).

Se conserva la clase `Flooded Area`, se disuelve, se descartan fragmentos menores de
0,5 ha y se simplifica a 25 m. La capa publica la **unión de las observaciones por
fecha**, no una mancha simultánea. Todas las áreas se miden en EPSG:32717, que es el
CRS de los shapefiles de Copernicus:

| AOI | Paso | Área |
|---|---|---:|
| AOI10 | 26/03, Radarsat | 80,785 km² |
| AOI10 | 30/03, Cosmo-SkyMed | 73,040 km² |
| AOI10 | suma de observaciones | 153,825 km² |
| AOI10 | solapamiento entre fechas | 56,772 km² |
| AOI10 | unión original | 97,053 km² |
| AOI10 | tras filtro <0,5 ha | 96,347 km² |
| AOI10 | tras simplificación 25 m y publicación | 96,507 km² |
| AOI11 | 26/03, Radarsat | 457,408 km² |
| AOI11 | unión original | 457,408 km² |
| AOI11 | tras filtro | 457,213 km² |
| AOI11 | tras simplificación y publicación | 458,970 km² |

Total publicado: **555,477 km²**. La suma 80,785 + 73,040 = 153,825 km² **no es una
superficie**: 56,772 km² se observaron en ambas fechas. La diferencia entre la unión
original y la publicada (97,053 → 96,507 km²) se explica por el filtro de fragmentos
menores de 0,5 ha y por la simplificación a 25 m; no se ajustó manualmente. La
simplificación puede aumentar el área en algunas geometrías; se reporta el valor
medido, no el esperado.

La fidelidad entre la unión original, la geometría filtrada, la simplificada y la
publicada se mide en EPSG:32717: IoU, diferencia simétrica, Hausdorff, distancia
media y p95 entre límites. El informe reproducible está en
`web/public/data/flood_2017_audit.json`; el detalle de la auditoría, en `docs/09`.

La capa cubre la llanura baja y el desierto adyacente, **no toda la cuenca**: en la
sierra el evento se expresó como crecidas y deslizamientos, no como una mancha
continua. No es un modelo hidráulico ni una predicción. No se publica una clase
`Potential Flooded Area` porque el vector no la trae; la extensión total del evento
no se publica. «Área delineada» no es «superficie inundada»: la primera es lo que el
radar permitió delimitar en una fecha; la segunda requeriría un levantamiento o un
modelo, que el atlas no tiene.

La ficha del PDF v2 de AOI10 declara Sentinel-1A, pero el DBF del mismo producto
declara Radarsat y Cosmo-SkyMed. El atlas usa los atributos del vector. En la
auditoría de v0.2.2 no se reabrió el PDF: la discrepancia queda visible y pendiente
de confirmación documental. El AOI12 Piura North se descartó porque sus registros no
traen fecha ni sensor.

### Escenarios históricos
Cada afirmación se clasifica como dato medido, documento, interpretación o pendiente:

- **1891.** SIAR registra la salida al mar antes de 1891, el cambio a la laguna San
  Ramón desde ese año y la reocupación del cauce antiguo en 1983 (p. 5 y 7). SIAR
  describe el mecanismo general de avulsión (p. 9). La tesis de la PUCP queda como
  referencia secundaria: en esta auditoría el repositorio no permitió abrirla, así que
  no se usa para una afirmación específica. El detalle del mecanismo se marca como
  interpretación histórica.
- **1983.** 3 200 m³/s el 21 de abril de 1983 en Puente Sánchez Cerro (SIAR 200 p. 15;
  SIAR 204 p. 49). La duración diaria del episodio no se localizó; no se afirma.
- **1998.** 4 424 m³/s (SIAR 204 p. 27 y 49). SIAR 200 consigna el 12 de marzo en la
  introducción (p. 1) y el 16 de marzo en el análisis de niveles (p. 15); la fecha
  exacta queda como discrepancia. SIAR 200 consigna un período de 161 días; no se
  verificó con una serie diaria, así que no se afirma que el evento durara exactamente
  161 días. IMARPE estima 2 326 km² en 1997-98 y 2 172 km² el 5 de abril de 2017 con
  MODIS-Aqua de 500 m (Escudero & Xu, 2019).
- **2017.** La geometría es el vector oficial EMSR199, no una reconstrucción propia.
  Se publica la unión de observaciones, no una mancha simultánea.
- **2023.** La laguna La Niña volvió a desbordar en marzo; Andina documenta 120 m de
  carretera destruidos y NASA Landsat 9 documenta la laguna. No hay informe
  hidrológico de SENAMHI/ANA en el catálogo, así que no se publica una cifra de área o
  volumen. No se localizó una fuente que documente un cambio de desembocadura; no se
  afirma que lo haya habido ni que no lo haya.

### Obras hidráulicas
Poechos se dibuja como **punto en el dique** documentado por el PECHP, no como un
polígono de embalse inventado. El canal Daniel Escobar se dibuja como una **recta de
referencia** Poechos–Curumuy: el PECHP documenta 54 km y 70 m³/s, pero no publica el
eje. No son levantamientos ni provienen del inventario de ANA/PECHP. Las bocatomas y
los diques no se dibujan porque no hay geometría pública. El ancho de 420 m del canal
en el diorama es un recurso visual, no el ancho real.

## Control de calidad

- Toda capa pasa por revisión de otra persona antes de publicarse.
- Se comprueba: validez Shapely, autointersecciones, agujeros, MultiPolygon,
  **solapamientos por par**, **superficie fuera de la cuenca por subcuenca**,
  **huecos por componente** y su unión, líneas fuera de cuenca, coherencia de áreas
  geodésicas, **fidelidad (IoU, diferencia simétrica, Hausdorff, media y p95)** y
  correspondencia entre perfil y resolución efectiva del DEM. La suma de áreas es
  solo una comprobación secundaria; no sustituye la topología. Los avisos de
  fidelidad se publican aunque el resultado deje de ser «0 avisos».
- Los desacuerdos entre fuentes se dejan visibles en la ficha, no se promedian.
- La mancha de 2017 conserva la clase `Flooded Area`, se revisa contra la máscara de
  mar y declara su cobertura; las obras se validan por su marca `esquematico: true`.
- `etl/check_data.py` valida procedencia, topología, perfiles, malla, GLB y
  presupuesto de datos. CI lo ejecuta junto con las pruebas de geometría.

## Reproducibilidad

`etl/` debe poder reconstruir `data/processed/` desde `data/raw/` con un comando.
Si un paso depende de una decisión manual, se documenta en el propio script.

## Fuentes, disponibilidad y evidencia

Desde la fase 2, el catálogo distingue tres ejes que no se sustituyen entre sí:

- **disponibilidad:** `localizada`, `descargable`, `procesada`, `validada`,
  `documental`, `pendiente` o `descartada`;
- **certeza:** `medido`, `derivado`, `documentado`, `interpretacion` o
  `por_verificar`;
- **tipo de evidencia:** oficial, académica, científica, histórica, observación
  satelital, dato medido, reconstrucción cartográfica, modelamiento,
  prensa/documentación secundaria o colaborativa.

Una fuente `documental` puede sostener una afirmación o una ficha, pero no una
geometría publicada. Una capa publicada solo referencia fuentes `validada` o
`procesada`. Lo que está `pendiente` se declara y no se dibuja.

La fase 2 no incorporó capas geométricas nuevas. Las fuentes ANA 2014, INDECI 2009,
Lund 2024, INGEMMET, la inspección de 2026 y la expedición de 2002 quedan como
evidencia documental. PISCOp v3.0 queda condicionado a la aclaración de su licencia.

## Series históricas por estación (fase 2.1)

La API histórica de SENAMHI se procesa sin interpolar ni rellenar:

1. descarga del catálogo de estaciones y de cada serie diaria;
2. filtro de las 20 estaciones de Piura;
3. tabla plana con fecha, precipitación, temperatura máxima y mínima;
4. conservación de nulos y de la cobertura original (1961–2015);
5. salida local en `data/processed/senamhi/`, no publicada hasta confirmar
   términos.

No se usa como sustituto de caudales ni de PISCO: es una serie observada por
estación, con cobertura limitada a 2014/2015.
