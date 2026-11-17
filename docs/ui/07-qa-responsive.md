# 07 · QA responsive y rendimiento

**Proyecto:** Río Piura Atlas  
**Fase:** UI-02, posterior al rediseño UI-01  
**Fecha:** 2026-11-17  
**Versión:** 0.2.3  
**Método:** Chrome headless con Playwright, build estático servido localmente, cinco resoluciones y pantalla horizontal corta. Capturas reales en `docs/ui/evidencia/ui02-*`.

---

## 1. Matriz revisada

| Resolución | Referencia | Inicio | Mapa | Escenarios | Fuentes | Maqueta |
|---|---|---|---|---|---|---|
| 1440 × 900 | Escritorio | ✅ | ✅ | ✅ | ✅ | ✅ |
| 1024 × 768 | Portátil/tablet | ✅ | ✅ | ✅ | ✅ | ✅ |
| 768 × 1024 | Tablet vertical | ✅ | ✅ | ✅ | ✅ | ✅ |
| 390 × 844 | Móvil | ✅ | ✅ | ✅ | ✅ | ✅ |
| 360 × 800 | Móvil compacto | ✅ | ✅ | ✅ | ✅ | ✅ |
| 844 × 390 | Horizontal corto (extra) | — | ✅ | — | — | ✅ |

En las 25 combinaciones de página × resolución:

- `documentElement.scrollWidth ≤ clientWidth + 1`.
- Sin errores JavaScript de página.
- Controles del mapa dentro del viewport.
- Canvas del mapa y de la maqueta con dimensiones válidas y coincidentes con su contenedor.
- Panel de capas plegado dentro de la ventana; panel expandido como diálogo modal.

---

## 2. Correcciones responsive

### 2.1. Escenarios a 1024 × 768

**Antes:** el documento medía **1029 px** con viewport de 1024. Las píldoras `.status` con `white-space:nowrap` desbordaban la columna de margen de 151 px; el enlace y el texto de fuente quedaban cortados.

**Después:** el documento mide **1024 px**. Se aplicó:

- `min-width:0` en `.chapter-margin`.
- `white-space:normal` en las píldoras de estado.
- `overflow-wrap:anywhere` en las notas de margen.

Comparación: `evidencia/ui02-escenarios-1024-antes.jpg` y `evidencia/ui02-escenarios-1024-despues.jpg`. La captura «antes» reproduce el CSS previo sobre el build actual.

### 2.2. Panel de capas móvil

**Antes:** el panel plegado medía 390 px con `left:16px`; su borde derecho llegaba a 406 px. El botón «Mostrar capas» quedaba 3 px fuera a 390, 13 px fuera a 360 y 16 px fuera a 768.

**Después:**

| Viewport | Panel plegado (izquierda → derecha) | Botón |
|---|---|---|
| 390 | 16 → 374 | Dentro |
| 360 | 16 → 344 | Dentro |
| 768 | 16 → 752 | Dentro |
| 844 × 390 | 12 → 271 (compacto) | Dentro |

El panel expandido ocupa `inset:0` y se comporta como diálogo modal; no deja franjas del mapa ni controles accesibles por error.

### 2.3. Horizontal corto 844 × 390

**Antes:** el mapa conservaba `min-height:480px`, el botón de leyenda quedaba en `y=433` (fuera de un viewport de 390) y la leyenda abierta se cruzaba con el panel plegado.

**Después:**

- El mapa mide `100dvh - cabecera - 1px` y cabe en la ventana (324 px de alto).
- El panel plegado se compacta a una fila de 64 px.
- La leyenda se ancla a la izquierda, debajo del panel; los controles quedan a la derecha.
- La leyenda puede desplazarse internamente; no tapa los controles.
- El perfil de corte oculta controles y leyenda mientras está abierto.

Captura: `evidencia/ui02-mapa-leyenda-844x390.jpg`.

### 2.4. Ficha móvil

- La ficha entra desde abajo, con `max-height:74dvh`, botón de cierre visible y `visibility:hidden` cuando está cerrada.
- El foco va al encabezado y `Escape` devuelve el foco al disparador o al canvas.
- No produce scroll horizontal ni saltos de scroll del documento.

Captura: `evidencia/ui02-mapa-ficha-390.jpg`.

### 2.5. Leyenda y perfil

- La leyenda abierta a 390 px queda por debajo de los controles y por encima del botón; no se solapan.
- El botón cambia a «Cerrar leyenda» y `Escape` cierra.
- El perfil se mantiene por encima del borde inferior y no tapa el botón de leyenda.
- En horizontal corto, controles y leyenda se ocultan mientras el perfil está abierto.

Capturas: `evidencia/ui02-mapa-leyenda-390.jpg`, `evidencia/ui02-mapa-corte-390.jpg`.

---

## 3. Dimensiones de canvas

### Mapa

| Viewport | Canvas CSS | Contenedor |
|---|---|---|
| 1440 × 900 | 1114 × 834 | 1114 × 834 |
| 1024 × 768 | 698 × 702 | 698 × 702 |
| 768 × 1024 | 768 × 966 | 768 × 966 |
| 390 × 844 | 390 × 786 | 390 × 786 |
| 360 × 800 | 360 × 742 | 360 × 742 |
| 844 × 390 | 844 × 324 | 844 × 324 |

MapLibre actualiza su canvas con su propio observador de contenedor. No se añadió un listener de resize nuevo; el existente solo recalcula etiquetas de ciudades y regla de longitudes.

### Maqueta

| Viewport | Canvas CSS | Contenedor |
|---|---|---|
| 1440 × 900 | 1130 × 834 | 1130 × 834 |
| 1024 × 768 | 714 × 702 | 714 × 702 |
| 768 × 1024 | 768 × 471 | 768 × 471 |
| 390 × 844 | 390 × 388 | 390 × 388 |
| 360 × 800 | 360 × 368 | 360 × 368 |
| 844 × 390 | 844 × 330 | 844 × 330 |

Three.js usa `ResizeObserver` sobre `#scene` y vuelve a encuadrar el modelo cuando cambia el tamaño. La prueba de orientación 390×844 → 844×390 confirma que ambos canvas se actualizan.

---

## 4. Capturas

Las 25 capturas base están en `docs/ui/evidencia/`:

| Página | 1440 | 1024 | 768 | 390 | 360 |
|---|---|---|---|---|---|
| Inicio | `ui02-inicio-1440.jpg` | `ui02-inicio-1024.jpg` | `ui02-inicio-768.jpg` | `ui02-inicio-390.jpg` | `ui02-inicio-360.jpg` |
| Mapa | `ui02-mapa-1440.jpg` | `ui02-mapa-1024.jpg` | `ui02-mapa-768.jpg` | `ui02-mapa-390.jpg` | `ui02-mapa-360.jpg` |
| Escenarios | `ui02-escenarios-1440.jpg` | `ui02-escenarios-1024.jpg` | `ui02-escenarios-768.jpg` | `ui02-escenarios-390.jpg` | `ui02-escenarios-360.jpg` |
| Fuentes | `ui02-fuentes-1440.jpg` | `ui02-fuentes-1024.jpg` | `ui02-fuentes-768.jpg` | `ui02-fuentes-390.jpg` | `ui02-fuentes-360.jpg` |
| Maqueta | `ui02-maqueta-1440.jpg` | `ui02-maqueta-1024.jpg` | `ui02-maqueta-768.jpg` | `ui02-maqueta-390.jpg` | `ui02-maqueta-360.jpg` |

Estados adicionales:

- `ui02-mapa-panel-390.jpg`: panel modal abierto.
- `ui02-mapa-ficha-390.jpg`: ficha de la cuenca.
- `ui02-mapa-leyenda-390.jpg`: leyenda abierta.
- `ui02-mapa-corte-390.jpg`: perfil de corte.
- `ui02-mapa-leyenda-844x390.jpg`: horizontal corto.
- `ui02-escenarios-1024-antes.jpg` / `...-despues.jpg`: comparación del ajuste.

---

## 5. Rendimiento

Medición local con `serve-dist`, sin compresión HTTP. Los tamaños de transferencia local son mayores que en producción; los tamaños gzip del build se indican aparte. Una sola pasada, Chrome headless; no es un benchmark estadístico.

### Antes / después

| Página | Antes | Después | Cambio |
|---|---:|---:|---:|
| Inicio | 703 KB | 703 KB | 0 |
| Mapa | 1 468 KB | 1 475 KB | +7 KB |
| Maqueta | 2 921 KB | 2 922 KB | +1 KB |
| Escenarios | 367 KB | 367 KB | 0 |
| Fuentes | 199 KB | 199 KB | 0 |

El mapa creció por el código de foco, el panel modal y el resumen textual. No hay dependencias nuevas.

### Build comprimido

| Recurso | Bruto | Gzip |
|---|---:|---:|
| JS del mapa | 828 327 B | 225 664 B |
| JS de la maqueta | 593 608 B | 151 487 B |
| CSS del mapa | 65 440 B | 9 301 B |
| CSS de la maqueta | 5 685 B | 1 738 B |
| GLB | 1 643 980 B | — (binario ya comprimido con Draco) |

### Tiempos y memoria observados

| Medición | Resultado |
|---|---|
| Mapa listo, 1440×900 | 257 ms |
| Mapa listo, 390×844 | 151 ms |
| Maqueta lista, 1440×900 | 866 ms |
| Maqueta lista, 390×844 | 872 ms |
| Heap del mapa tras carga | 8–10 MB |
| Heap de la maqueta | 31 MB |
| Carga de inundación en móvil | 85 ms; +1 MB |
| Perfil de corte en móvil | 66 ms; +2 MB |

### Recursos

- El mapa carga ~146 KB de GeoJSON base y 216 KB de relieve; la inundación (510 KB) y el DEM (433 KB) se cargan bajo demanda.
- La maqueta carga el GLB (1,6 MB), el póster (183–238 KB), Three.js (653 KB brutos) y el wasm de Draco (193 KB).
- No se implementaron optimizaciones de imágenes en esta fase. Las imágenes de portada y maqueta se sirven a tamaño completo en móvil; queda como P2 añadir `srcset` y variantes.

**Conclusión de rendimiento:** no hay regresión significativa con los cambios de accesibilidad. La deuda principal sigue siendo el GLB de 1,6 MB y las imágenes sin variantes responsive, no el código nuevo.

---

## 6. Pendientes

- **P2:** objetivos táctiles de 32–38 px; cumplen AA (24 px), no la recomendación de 44 px.
- **P2:** variantes responsive de `hero-maqueta.webp`, `maqueta-key.webp`, `mapa-crop.jpg`, `flood-plate.jpg` y `relieve-propuesta.jpg`.
- **P2:** prueba en Safari/Firefox y en dispositivos físicos.
- **P2:** prueba de memoria en sesión larga con capas, inundación y cortes repetidos.
- **P2:** el mapa en horizontal corto reduce el área cartográfica; es usable, pero conviene una prueba con usuarios.
