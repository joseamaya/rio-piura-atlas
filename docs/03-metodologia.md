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
fecha**, no una mancha simultánea: AOI10 suma 80,8 km² del 26/03 y 73,0 km² del
30/03, con una unión simplificada de 96,5 km²; AOI11 pasa de 457,4 km² originales a
459,0 km² simplificados. El total publicado es ≈555 km². La capa cubre la llanura
baja y el desierto adyacente, **no toda la cuenca**: en la sierra el evento se expresó
como crecidas y deslizamientos, no como una mancha continua. No es un modelo
hidráulico ni una predicción. No se publica una clase `Potential Flooded Area`
porque el vector no la trae; la extensión total del evento no se publica.

El PDF v2 de AOI10 declara Sentinel-1A, pero el DBF del mismo producto declara
Radarsat y Cosmo-SkyMed. El atlas usa los atributos del vector y deja la
discrepancia visible. El AOI12 Piura North se descartó porque sus registros no
traen fecha ni sensor.

### Escenarios históricos
Cada afirmación se clasifica como dato medido, documento, interpretación o pendiente:

- **1891.** SIAR registra la salida al mar antes de 1891, el cambio a la laguna San
  Ramón desde ese año y la reocupación del cauce antiguo en 1983 (p. 5 y 7). Una tesis
  de la PUCP, que cita a Huertas (1999) y Rocha (2014), respalda el mecanismo de
  crecidas y avulsión. El detalle del mecanismo se marca como interpretación histórica.
- **1983.** 3 200 m³/s el 21 de abril de 1983 en Puente Sánchez Cerro (SIAR 200 p. 15;
  SIAR 204 p. 49). La duración diaria del episodio no se localizó; no se afirma.
- **1998.** 4 424 m³/s (SIAR 204 p. 27 y 49). SIAR 200 consigna el 12 de marzo en la
  introducción (p. 1) y el 16 de marzo en el análisis de niveles (p. 15); la fecha
  exacta queda como discrepancia. El evento duró 161 días. La laguna La Niña se formó
  en 1998; IMARPE estima 2 326 km² en 1998 y 2 172 km² en 2017 con MODIS-Aqua de
  500 m (Escudero & Xu, 2019).
- **2017.** La geometría es el vector oficial EMSR199, no una reconstrucción propia.
- **2023.** La laguna La Niña volvió a desbordar en marzo; lo documentan Andina y
  Landsat 9. No hay informe hidrológico de SENAMHI/ANA en el catálogo, así que no se
  publica una cifra de área o volumen para 2023.

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
  geodésicas y correspondencia entre perfil y resolución efectiva del DEM. La suma de
  áreas es solo una comprobación secundaria; no sustituye la topología.
- Los desacuerdos entre fuentes se dejan visibles en la ficha, no se promedian.
- La mancha de 2017 conserva la clase `Flooded Area`, se revisa contra la máscara de
  mar y declara su cobertura; las obras se validan por su marca `esquematico: true`.
- `etl/check_data.py` valida procedencia, topología, perfiles, malla, GLB y
  presupuesto de datos. CI lo ejecuta junto con las pruebas de geometría.

## Reproducibilidad

`etl/` debe poder reconstruir `data/processed/` desde `data/raw/` con un comando.
Si un paso depende de una decisión manual, se documenta en el propio script.
