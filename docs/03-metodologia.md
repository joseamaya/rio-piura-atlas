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
Copernicus DEM 30 m. El relieve se muestra con **exageración vertical declarada**
(×7 en la maqueta). La exageración no es un dato: se dice en la leyenda y en la ficha.
En la maqueta, el color del terreno es una **rampa hipsométrica**: indica altitud, no
cobertura vegetal.

### Red hídrica
HydroRIVERS, filtrada por área aportante y recortada a la cuenca. En la llanura el
DEM no resuelve el cauce: el trazo procede del vector, no del ráster. En la maqueta
la red se eleva 45 m sobre el terreno para que se lea; no es una cota real.

### Cortes transversales
Implementados en `etl/build_cortes.py` y visibles en `/mapa`.

- **Cortes de referencia**: cinco transectos perpendiculares a la red hídrica (Bajo
  Piura, Piura, Catacaos, Chulucanas y Tambogrande), recortados a la cuenca oficial.
  El perfil se muestrea del DEM de 30 m.
- **Corte dibujado por el visitante**: dos clics sobre el mapa. El perfil se calcula
  sobre una malla `Int16` derivada del DEM (resolución aproximada de 467 m) que se
  descarga solo al dibujar; así no se envía el ráster completo al navegador.
- La ficha declara resolución, longitud del transecto y cota mínima y máxima.
- **Límite**: un corte de DEM no sirve para dimensionar obras; sirve para explicar la
  forma del valle. Cuando exista batimetría, se superpondrá y se distinguirá por estilo.

### Escenarios de inundación
No se simulan. Se digitalizan de fuentes documentales:

1. fuente (mapa oficial, imagen satelital, informe);
2. fecha del evento;
3. método de extracción (digitalización manual, umbral sobre Sentinel-1);
4. control de calidad (comparación con relatos o mapas oficiales).

Cada escenario muestra un rótulo permanente: **«escenario documentado, no pronóstico»**.

## Control de calidad

- Toda capa pasa por revisión de otra persona antes de publicarse.
- Se comprueba: cierre de polígonos, geometrías válidas, coherencia con el relieve,
  y que el área calculada coincida con la declarada por la fuente.
- Los desacuerdos entre fuentes se dejan visibles en la ficha, no se promedian.
- `etl/check_data.py` valida procedencia, cierres de anillos, perfiles de corte y
  presupuesto de datos. CI lo ejecuta junto con las pruebas de geometría.

## Reproducibilidad

`etl/` debe poder reconstruir `data/processed/` desde `data/raw/` con un comando.
Si un paso depende de una decisión manual, se documenta en el propio script.
