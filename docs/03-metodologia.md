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

- **AOI10 Piura**: Piura, Catacaos y La Unión. Radarsat-2 (26/03) y Cosmo-SkyMed
  (30/03).
- **AOI11 Parachique**: llanura baja y desierto adyacente. Radarsat-2 (26/03).

Se conserva la clase `Flooded Area`, se disuelve, se descartan fragmentos menores de
0,5 ha y se simplifica a 25 m. El área publicada es la del vector simplificado
(≈555 km² en total); la suma de los polígonos originales es ≈554 km². La capa cubre
la llanura baja y el desierto adyacente, **no toda la cuenca**: en la sierra el evento
se expresó como crecidas y deslizamientos, no como una mancha continua. No es un
modelo hidráulico ni una predicción. El AOI12 Piura North se descartó porque sus
registros no traen fecha ni sensor.

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
  solapamientos y huecos entre subcuencas, líneas fuera de cuenca, coherencia de
  áreas geodésicas y correspondencia entre perfil y resolución efectiva del DEM.
- Los desacuerdos entre fuentes se dejan visibles en la ficha, no se promedian.
- La mancha de 2017 conserva la clase `Flooded Area`, se revisa contra la máscara de
  mar y declara su cobertura; las obras se validan por su marca `esquematico: true`.
- `etl/check_data.py` valida procedencia, topología, perfiles, malla, GLB y
  presupuesto de datos. CI lo ejecuta junto con las pruebas de geometría.

## Reproducibilidad

`etl/` debe poder reconstruir `data/processed/` desde `data/raw/` con un comando.
Si un paso depende de una decisión manual, se documenta en el propio script.
