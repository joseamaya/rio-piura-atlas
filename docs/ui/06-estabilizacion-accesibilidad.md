# 06 · Estabilización funcional y accesibilidad

**Proyecto:** Río Piura Atlas  
**Fase:** UI-02, sobre el rediseño UI-01 «Lámina y margen»  
**Fecha:** 2026-11-17  
**Versión:** 0.2.3  
**Rama:** `main`  
**Base:** `64709c4` (merge de `feat/ui-01-lamina-y-margen`)  
**Alcance:** foco, teclado, semántica del mapa, panel móvil, leyenda y perfil. No se modificaron datos, geometrías, ETL, fuentes ni rutas públicas.

---

## 1. Estado inicial comprobado

| Dato | Valor |
|---|---|
| Git | Árbol limpio; sin cambios locales ni archivos sin seguimiento |
| Node / npm | `22.23.2` / `10.9.8` |
| Producción | Astro 5.6, MapLibre GL 4.7, Three 0.170, js-yaml, sitemap |
| Desarrollo | Playwright 1.65, axe-core, puppeteer-core, TypeScript |
| Pruebas iniciales | 11 Playwright, 79 Python, `check_data.py` con 0 errores y 10 avisos; axe sin violaciones en 8 vistas |
| `npm run check` | 0 errores, 33 hints |
| `check:links` | 148 enlaces internos, sin roturas |

El Python del sistema no incluye `shapely`; las comprobaciones de datos se ejecutaron en un venv temporal con `etl/requirements.txt`.

**Método:** lectura del código, build estático, Chrome headless con Playwright, medición de `activeElement`, secuencias de Tab, `aria-expanded`, `inert`, `role`, overflow de documento y capturas reales en las cinco resoluciones.

---

## 2. Hallazgos

### P0 · Bloqueantes

| # | Hallazgo | Comprobación | Estado |
|---|---|---|---|
| 1 | La ficha no movía el foco al abrirse ni lo devolvía al cerrarse | `activeElement` seguía en el botón o en el canvas; Escape cerraba sin devolver el foco | Corregido y probado |
| 2 | El panel móvil perdía el foco al abrirse | `#toggle-panel` quedaba `display:none` y el foco caía en `BODY` | Corregido y probado |
| 3 | El panel móvil no cerraba con Escape, no atrapaba el foco y dejaba tabular al mapa del fondo | 30 Tabs llegaban al canvas y a los controles detrás del panel | Corregido y probado |
| 4 | El panel plegado era más ancho que la ventana | A 390 px llegaba a 406 px; el botón quedaba 3 px fuera. A 360 px, 13 px; a 768 px, 16 px | Corregido y probado |
| 5 | El mapa no tenía una alternativa textual real y usaba `role="application"` sin necesidad | El canvas quedaba como `region` con nombre «Map», en inglés; el resumen no permitía consultar capas ni cifras | Corregido y probado |

### P1 · Importantes

| # | Hallazgo | Estado |
|---|---|---|
| 6 | El perfil de corte no recibía el foco al abrirse | Corregido y probado |
| 7 | La leyenda móvil no se cerraba con Escape ni devolvía el foco | Corregido y probado |
| 8 | Desbordamiento horizontal en Escenarios a 1024×768 (1029 px) | Corregido y probado |
| 9 | En horizontal corto (844×390) el mapa no cabía, la leyenda chocaba con el panel y el botón de leyenda quedaba fuera de pantalla | Corregido y probado |
| 10 | Los errores de carga podían quedar sin anunciar si el panel estaba plegado | Corregido con una región de estado global |
| 11 | No había fallback visible si MapLibre no podía iniciar WebGL | Corregido; el fallback enlaza al resumen y a Fuentes |
| 12 | La selección de elementos geográficos con teclado no existe en MapLibre | Mitigado con resumen textual, ficha de cuenca y cortes; no se declara equivalencia completa |

### Ya estaba resuelto

- El cierre del corte devolvía el foco al enlace.
- La ficha ya usaba `inert` y `aria-hidden` al cerrarse.
- MapLibre y Three.js ya actualizaban sus canvas al cambiar el tamaño del contenedor.
- La maqueta ya tenía póster, progreso, fallback de WebGL y enlace al mapa 2D si el GLB falla.
- El mapa ya manejaba el fallo de capas base y de la inundación sin dejar el lienzo en blanco.
- No había desbordamiento horizontal en 1440, 768, 390 ni 360 px.

---

## 3. Correcciones implementadas

### 3.1. Ficha del mapa

Archivos: `web/src/pages/mapa.astro`, `web/src/styles/map.css`.

- Se guarda el disparador al abrir: botón, canvas o enlace de corte.
- Al abrir, el foco va al primer `h3` de la ficha con `tabindex="-1"` y `focus({preventScroll:true})`; el panel vuelve a `scrollTop=0`.
- Al cerrar, el foco se mueve **antes** de aplicar `aria-hidden` e `inert`: vuelve al disparador si sigue visible; si no, al canvas del mapa.
- `Escape` cierra con una prioridad única: ficha → corte → panel modal → leyenda.
- Se retiró `aria-live` de la ficha; el foco en el encabezado evita anuncios duplicados.
- La ficha es un `role="dialog"` no modal, con nombre accesible.
- En móvil se añadió `visibility:hidden` a la ficha cerrada, además de `inert`, para que ningún navegador antiguo permita enfocar elementos fuera de pantalla.

Casos cubiertos por pruebas: ficha de la cuenca, selección geográfica (incluido «Sin elemento»), apertura por teclado, cierre por botón, cierre por Escape y retorno al canvas.

### 3.2. Panel de capas móvil

**Patrón elegido:** diálogo modal en `max-width:900px`; `aside` complementario no modal en escritorio. No se convirtió el panel de escritorio en modal.

- `#toggle-panel` mantiene `aria-expanded`; al abrir, el foco entra en el `h2` del panel.
- El panel recibe `role="dialog"`, `aria-modal="true"` y nombre accesible.
- Trampa de foco con `Tab`/`Shift+Tab`, recalculando los elementos visibles cada vez (incluye checkboxes, enlaces, `<details>` y enlaces de cortes).
- `Escape` cierra, devuelve el foco a `#toggle-panel` y retira el modo modal.
- Fondo inerte: cabecera, pie, menú móvil, skip link y escenario del mapa.
- `body.panel-open { overflow:hidden; }` bloquea el scroll del documento; el panel conserva su propio scroll.
- El panel expandido ocupa `inset:0` y cubre la cabecera; así no queda una cabecera visible pero inerte.
- El panel plegado usa `width:auto` con `left/right:16px`; ya no desborda a 360, 390 ni 768 px.
- Al cambiar de breakpoint se sincroniza el estado: desktop→móvil pliega y recoloca el foco; móvil→desktop retira el modo modal y muestra el panel.
- Abrir el panel cierra la ficha, el corte y la leyenda para no apilar capas de interfaz.
- «Dibujar un corte» cierra el panel y devuelve el foco al mapa, porque en móvil el panel modal impide interactuar con el lienzo.

### 3.3. MapLibre: semántica, teclado y alternativa textual

- Se eliminó `role="application"` del contenedor. El canvas de MapLibre conserva `role="region"`, `tabindex="0"` y ahora tiene nombre en español y `aria-describedby="map-summary map-instructions"`.
- Se configuró el `locale` de MapLibre en español para el título del mapa, la atribución y los marcadores.
- Los marcadores de ciudad y obra tienen `role="img"` y etiquetas como «Ciudad de Piura» u «Obra de referencia: Represa de Poechos».
- Se añadió `#map-status` fuera del panel (`role="status"`, `aria-live="polite"`, `aria-atomic="true"`). Anuncia carga, mapa listo, errores, inundación y modo corte.
- `#layer-status` se mantiene como mensaje visible, sin `aria-live`, para no duplicar anuncios.
- El canvas usa `aria-busy` hasta que termina la carga.
- Se añadió un bloque `<details id="map-alt">` «Leer el mapa en texto» con cuenca, subcuencas, red hídrica, inundación de 2017, obras, cortes y ciudades, con enlaces a las fuentes.
- Se añadió `#map-instructions` con las teclas de MapLibre: flechas, Mayús+flechas, `+` y `−`.
- Se añadió un fallback visible si MapLibre no puede iniciar WebGL: oculta el lienzo vacío, deshabilita «Dibujar un corte» y enlaza al resumen y a Fuentes.

**Límite declarado:** MapLibre no ofrece selección de features con teclado. El atlas no promete accesibilidad completa del lienzo; ofrece una alternativa textual y fichas accesibles. La interacción cartográfica con ratón y táctil se conserva.

### 3.4. Perfil de corte y leyenda

- `#corte-title` recibe el foco al abrir el perfil y el cierre devuelve el foco al disparador o al canvas.
- Abrir un corte cierra la leyenda y la ficha; abrir una ficha cierra el corte.
- La leyenda se cierra con Escape y devuelve el foco a `#legend-toggle`; el texto del botón cambia entre «Leyenda» y «Cerrar leyenda», con `aria-expanded`.
- En móvil, el botón de leyenda se oculta mientras el perfil está abierto para no quedar tapado.
- La leyenda mantiene códigos no cromáticos: línea continua, discontinua, trama diagonal y punto.

---

## 4. Pruebas

| Comprobación | Resultado |
|---|---|
| Playwright | **53 pruebas en verde** (11 existentes + 42 nuevas) |
| Foco de ficha | Abre en `h3`; cierra en disparador o canvas |
| Panel móvil | `dialog`, `aria-modal`, `inert`, trampa de foco, Escape, retorno y scroll bloqueado |
| Escritorio | Panel no modal; mapa enfocable |
| Leyenda | Escape y retorno; sin solape con controles en 390 |
| Corte | Foco en `#corte-title`; retorno al enlace |
| MapLibre | Sin `role=application`; canvas con nombre/descripción; estado listo; fallback WebGL |
| Resumen textual | 7 grupos de datos y enlaces a Fuentes |
| Responsive | 25 combinaciones página × resolución sin overflow horizontal |
| Canvas | Mapa y maqueta coinciden con su contenedor en las cinco resoluciones |
| Orientación | 390×844 → 844×390 con canvas redimensionado |
| Maqueta | Carga, error de GLB, render, controles, teclado y resize |
| axe-core | 0 violaciones WCAG A/AA en 8 vistas |
| `check_data.py` | 0 errores, 10 avisos declarados |
| Pruebas Python | 79 en verde |
| `npm run check` final | 0 errores, 0 warnings, 32 hints |
| `check:links` final | 157 enlaces internos, sin roturas |

**No verificable en este entorno:** lector de pantalla real (NVDA/VoiceOver), Safari/Firefox, teclado de MapLibre con un dispositivo físico y fullscreen en móvil real.

---

## 5. Archivos modificados

- `web/src/pages/mapa.astro`
- `web/src/styles/map.css`
- `web/src/styles/editorial.css`
- `web/src/pages/maqueta.astro`
- `web/tests/e2e/atlas.spec.ts` (se añadió la comprobación del estado global de error)
- `web/tests/e2e/helpers.ts` (nuevo)
- `web/tests/e2e/mapa-a11y.spec.ts` (nuevo)
- `web/tests/e2e/responsive.spec.ts` (nuevo)
- `web/tests/e2e/maqueta.spec.ts` (nuevo)
- `docs/ui/06-estabilizacion-accesibilidad.md`
- `docs/ui/07-qa-responsive.md`
- `docs/ui/08-coherencia-3d.md`
- `docs/ui/evidencia/` (capturas `ui02-*`)
- `docs/ui/README.md`
- `docs/ui/01-auditoria-visual.md` (nota de vigencia)
- `docs/08-pendientes.md` (nota de color 3D)

No se modificaron `data/`, `etl/`, `data/sources.yml`, geometrías ni rutas públicas.

---

## 6. Evidencia

| Archivo | Estado |
|---|---|
| `evidencia/ui02-mapa-390.jpg` | Mapa móvil con panel plegado dentro de la ventana |
| `evidencia/ui02-mapa-panel-390.jpg` | Panel modal abierto, foco en el título |
| `evidencia/ui02-mapa-ficha-390.jpg` | Ficha de la cuenca abierta |
| `evidencia/ui02-mapa-leyenda-390.jpg` | Leyenda abierta con «Cerrar leyenda» |
| `evidencia/ui02-mapa-corte-390.jpg` | Perfil de corte abierto |
| `evidencia/ui02-mapa-leyenda-844x390.jpg` | Leyenda en horizontal corto, sin tapar controles |
| `evidencia/ui02-escenarios-1024-antes.jpg` | Simulación del CSS anterior: borde derecho cortado |
| `evidencia/ui02-escenarios-1024-despues.jpg` | Estado corregido: píldoras y fuentes envueltas |

**Nota sobre la captura «antes»:** se reproduce inyectando el CSS anterior en el build actual, porque el árbol ya está corregido. El contenido y los datos son los mismos; solo cambia la regla de ajuste.

---

## 7. Pendientes y riesgos

- **P2:** objetivos táctiles de 32–38 px; cumplen el mínimo AA de 24 px, no los 44 px recomendados.
- **P2:** MapLibre no permite seleccionar features con teclado; el resumen textual es una alternativa, no una equivalencia completa.
- **P2:** falta prueba con lector de pantalla real y con Safari/Firefox.
- **P2:** el fallback de WebGL del mapa registra un error de consola (`Failed to initialize WebGL`) antes de mostrar la alternativa; la UI queda operativa y anunciada.
- **Riesgo:** `inert` es la base del bloqueo de fondo. En navegadores sin soporte se establece `aria-hidden` como respaldo y la trampa de foco sigue activa; no se probó en navegadores antiguos.
- **Riesgo:** el panel modal cubre la cabecera en móvil. Es una decisión de patrón para no dejar una cabecera visible pero inerte; se validó visualmente.
