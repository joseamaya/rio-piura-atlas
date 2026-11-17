# 08 · Coherencia cromática del modelo 3D

**Proyecto:** Río Piura Atlas  
**Fase:** UI-02  
**Fecha:** 2026-11-17  
**Modelo:** `web/public/models/piura.glb`  
**Decisión de esta fase:** mantener el GLB y documentar la reexportación coordinada; no se aplicó tinte runtime ni se reexportó el modelo.

---

## 1. Qué hay hoy

### 1.1. Activo

| Dato | Valor |
|---|---|
| Archivo | `piura.glb` |
| Peso | 1 643 980 B (1,6 MB) |
| Nodos / mallas | 39 / 39 |
| Materiales | 11 |
| Compresión | Draco |
| Textura del terreno | JPEG embebido, 2048 × 1733, ~342 KB |
| Colores por vértice | No; el color viene de la textura |

Materiales principales:

- `MAT-Terreno`: `baseColorTexture` con la rampa hipsométrica.
- `MAT-Mar`, `MAT-Agua-Rio`, `MAT-Agua-Crecida`, `MAT-Agua-Laguna`, `MAT-Canal`.
- `MAT-Divisoria`, `MAT-Corte-Bloque`, `MAT-Corte-Suelo`.
- `MAT-Etiqueta-Placa`, `MAT-Etiqueta-Texto`.

### 1.2. Origen de la textura

El GLB se generó con un proyecto Blender externo, no versionado en este repositorio. La textura se hornea con el DEM y una rampa de elevación definida en `build_texture.py` del proyecto Blender:

```
0 m     #C6B28A
60 m    #CEB98F
180 m   #CFBD94
380 m   #C4B78B
650 m   #B0B07A
1000 m  #8F9E62
1500 m  #6E8A53
2100 m  #5C794A
2700 m  #7A7958
3200 m  #9C8D74
3700 m  #C4BAAC
4100 m  #E8E7E2
```

La muestra de la textura tiene ~11 % de píxeles claramente verdes, concentrados en la sierra oriental. El resto es arena, mar y tonos de transición.

### 1.3. Paleta 2D

La lámina 2D usa una rampa de papel/oliva:

```
#D8C7A2 → #C9B88F → #A89A78 → #8B8A70 → #6F7664
```

La leyenda 2D la rotula de 0 a 3 000 m. El DEM de la maqueta llega a ~3 996 m; la rampa 3D añade tonos claros por encima de 3 000 m.

### 1.4. Diferencia visible

La sierra del GLB se lee más verde y saturada que la lámina 2D, que es más mineral y seca. No es un error de datos: ambas rampas codifican altitud, pero la 3D conserva la rampa original del proyecto Blender y la 2D usa la tinta editorial de «Lámina y margen».

**Comparación visual disponible:**

- `docs/ui/evidencia/implementado-mapa-desktop.png`: relieve 2D en papel.
- `docs/ui/evidencia/implementado-maqueta-desktop.png`: render/visor 3D actual.
- `docs/ui/evidencia/ui02-maqueta-1440.jpg`: maqueta en la QA de UI-02.

No se generó una captura «después» porque no se modificó el activo.

---

## 2. Alternativas evaluadas

| Alternativa | Fidelidad | Rendimiento | Coherencia | Riesgo | Coste |
|---|---|---|---|---|---|
| 1. Tinte runtime con Three.js | Media: no cambia geometría ni elevación, pero aproxima el color | Muy bueno: un shader o un tinte de material | Parcial: el visor se acerca al papel, pero los pósteres y renders siguen verdes | Medio: desajuste al pasar del póster al modelo; la leyenda no coincide exactamente | Bajo |
| 2. Reexportar textura + GLB + pósteres | Alta: la rampa se recalcula desde el DEM con los nuevos stops | Similar: misma malla y Draco; la textura puede pesar distinto | Alta: visor, póster, portada y OG comparten paleta | Medio-alto: hay que verificar geometría, regenerar renders y actualizar varios activos | Alto |
| 3. Mantener el GLB actual | Alta: no se toca el activo aprobado | Sin cambios | Baja-media: persiste la diferencia cromática | Ninguno sobre los datos | Nulo |

### Por qué no se aplicó el tinte runtime

- El póster de carga y el render de portada seguirían verdes; al terminar la carga, el modelo cambiaría de color.
- Un tinte global no reproduce la rampa 3D original: reduce saturación, pero no garantiza que cada cota caiga en el color de la lámina 2D.
- La leyenda de la maqueta describe una rampa hipsométrica; cambiar solo el material sin cambiar el activo puede volver a introducir una discrepancia entre leyenda y modelo.
- Es reversible, pero no resuelve el sistema completo.

### Por qué no se reexportó

- El proyecto Blender que genera la textura y el GLB está fuera del repositorio; no se puede reproducir la exportación solo con este árbol.
- Una reexportación exige regenerar también `hero-maqueta.webp`, `maqueta-key.webp`, la imagen OG y las capturas de la portada.
- Hay que demostrar que la geometría, los nodos, las mallas y las elevaciones no cambian; el brief lo exige antes de sustituir el GLB.
- Es un trabajo mayor que el alcance de estabilización de UI-02.

---

## 3. Decisión de UI-02

**Se mantiene `piura.glb` sin cambios.**

- No se modificó la textura, la geometría, las elevaciones ni los materiales del activo.
- No se añadió un tinte runtime.
- Se documenta la diferencia y se deja preparada la reexportación para una fase aprobada específicamente.
- La ficha de la maqueta ya declara que el color indica altitud, no vegetación; la afirmación sigue siendo correcta.

Esta decisión prioriza **fidelidad y reversibilidad** sobre una corrección cromática parcial. La coherencia completa queda pendiente, no ocultada.

---

## 4. Propuesta para la siguiente fase

### Paso 1 · Preparar la textura candidata

- Copiar el proyecto Blender a un entorno de trabajo o versionar los scripts mínimos.
- Cambiar solo los `STOPS` de `build_texture.py` por una rampa de papel/oliva compatible con la 2D, extendida hasta ~4 100 m.
- Generar `terrain.jpg` y una vista previa.
- Comparar la textura actual y la candidata lado a lado, sin cambiar el DEM.

### Paso 2 · Reexportar el GLB

- Ejecutar el build de escena y `export_web.py` con la misma configuración Draco.
- Verificar antes/después:
  - 39 nodos, 39 mallas, 11 materiales.
  - mismos nombres de nodos y materiales;
  - bounding box y rango de elevación;
  - recuento de vértices/caras y acceso a posiciones;
  - peso final y tiempo de carga.
- Si la geometría cambia, detener y no publicar.

### Paso 3 · Regenerar los renders y pósteres

- `hero-maqueta.webp`, `maqueta-key.webp`, OG y capturas de portada/maqueta.
- Verificar que el póster y el visor coinciden al cargar.
- Actualizar `docs/ui/08-coherencia-3d.md` con la comparación final.

### Paso 4 · Validar

- Capturas antes/después en la misma cámara y viewport.
- Medir peso, tiempo hasta `is-loaded` y heap.
- Repetir las pruebas de maqueta y `npm run verify`.
- Revisar que no se alteró ninguna cifra ni geometría publicada.

---

## 5. Estado

| Elemento | Estado |
|---|---|
| Análisis del GLB y la textura | Hecho |
| Comparación de paletas | Hecho |
| Decisión de no tocar el GLB en UI-02 | Tomada |
| Tinte runtime | No implementado; descartado para esta fase |
| Reexportación | Pendiente de aprobación y de una fase propia |
| Pruebas de geometría tras reexportar | No aplica todavía |
| Datos/geometrías alterados | Ninguno |

**Recomendación:** aprobar la reexportación coordinada como fase separada, con comparación visual y verificación geométrica. No aplicarla como parte de una corrección de accesibilidad.
