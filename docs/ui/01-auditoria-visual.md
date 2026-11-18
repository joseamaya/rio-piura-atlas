# 01 · Auditoría visual y de experiencia

**Proyecto:** Río Piura Atlas  
**Versión auditada:** 0.2.3 (`web/package.json`)  
**Fecha:** 2026-11-17  
**Alcance:** interfaz pública completa; no se modificó la aplicación.  
**Método:** lectura del repositorio, build de producción, navegación con Chrome/Playwright en escritorio (1440×900, 1280×800, 1024×768) y móvil (390×844, 360×800), medición de DOM, contraste y recursos, y revisión de estados del mapa (capas, inundación, ficha, corte) y de la maqueta 3D.

> **Nota de vigencia (UI-02, 2026-11-17).** Esta auditoría describe el estado previo al rediseño. El foco de fichas y paneles, la semántica de MapLibre, el panel móvil, el desbordamiento de Escenarios a 1024 y la orientación horizontal se actualizan en [06](06-estabilizacion-accesibilidad.md) y [07](07-qa-responsive.md). La diferencia cromática del GLB se documenta en [08](08-coherencia-3d.md). Las capturas `actual-*` siguen siendo evidencia histórica, no el estado actual.
>
> **Nota de fase 2.1 (2026-11-17).** El catálogo pasó de 30 a 48 fuentes y ahora distingue disponibilidad y tipo de evidencia. La fase 2.2 lo dejó en **49 fuentes** y añadió `publicacion` (`autorizada`/`bloqueada`). Las cifras de 30 fuentes de este documento son la línea base de UI-01; el estado actual está en [`../11-auditoria-fuentes-ampliacion.md`](../11-auditoria-fuentes-ampliacion.md) y [`../17-licencias-y-reutilizacion.md`](../17-licencias-y-reutilizacion.md).

---

## 1. Resumen ejecutivo

El atlas tiene una base científica y editorial sólida: el relato «El río que no llega al mar» funciona, las advertencias son honestas y la trazabilidad es real. La interfaz, en cambio, está todavía en un estado de **documento técnico con un mapa incrustado**, no de atlas digital.

El problema no es la falta de adornos. Es la **jerarquía**, la **legibilidad cartográfica**, la **tipografía dependiente del sistema** y la ausencia de un **sistema visual**. La portada no muestra el territorio; el mapa móvil desperdicia la pantalla; la inundación comparte la misma familia azul que el agua permanente; Fuentes se rompe en móvil; Escenarios es un muro de prosa; y la maqueta 3D queda desconectada de la página.

La oportunidad es clara: convertir el rigor existente en una experiencia editorial propia, sin convertirlo en un dashboard.

**Veredicto:** la arquitectura y el contenido están listos para un rediseño visual; no hace falta migrar de framework ni añadir dependencias de producción.

---

## 2. Inventario auditado

| Ruta | Contenido | Estado |
|---|---|---|
| `/` | Portada, qué es / qué no es, tres lecturas | Auditada en escritorio y móvil |
| `/mapa` | Mapa MapLibre, capas, ficha, cortes, enlaces `?capa=inundacion` y `?capa=obras` | Auditada con capas por defecto, inundación y perfil |
| `/maqueta` | Maqueta Three.js + Draco, panel, controles, teclado | Auditada en escritorio y móvil |
| `/escenarios` | 1891, 1983, 1998, 2017, 2023, tabla de estado | Auditada en escritorio y móvil |
| `/fuentes` | Catálogo generado desde `data/sources.yml` | Auditada en escritorio y móvil; 30 registros |
| `/404` | Página de error | Auditada |
| `Base.astro` | Cabecera, navegación, pie, metadatos | Inspeccionado |
| `global.css` | Todos los estilos del sitio (473 líneas) | Inspeccionado |
| `mapa.astro`, `maqueta.astro` | Lógica de MapLibre y Three.js | Inspeccionada |
| `data/sources.yml` | 30 fuentes, 19 disponibles, 5 por solicitar, 6 por verificar | Inspeccionado |
| ETL de relieve y figura 2017 | `etl/build_layers.py` | Inspeccionado como dependencia visual |

**Evidencia visual:** `docs/ui/evidencia/actual-*.png`.

---

## 3. Los diez problemas principales

### 3.1. La portada no muestra el atlas ni el territorio

**Qué se ve.** Una página de texto: titular, párrafo, cuatro tarjetas iguales y una caja de aviso. No hay una sola imagen ni una vista del mapa. El mapa es una tarjeta más, sin jerarquía sobre las otras tres.

**Evidencia.** Portada sin `<img>`; las cuatro tarjetas tienen el mismo peso y el mismo tratamiento. El primer píxel de mapa aparece después de un clic.

**Archivos.** `web/src/pages/index.astro:11-43`; `web/src/styles/global.css:136-156`.

**Impacto.** Un visitante nuevo no puede saber qué aspecto tiene el atlas ni por qué vale la pena explorarlo. La frase «El río que no llega al mar» es buena, pero no está acompañada por una prueba visual.

**Prioridad:** P0.

**Dirección.** Portada con una lámina real del territorio, una cifra editorial, una acción primaria clara y un índice asimétrico de las cuatro experiencias.

---

### 3.2. El mapa móvil desperdicia la pantalla y solapa controles

**Qué se ve.** El mapa ocupa el canvas, pero la geografía útil queda en una banda central de ~270 px dentro de un viewport de 739 px. Arriba y abajo quedan grandes franjas del fondo. El control de zoom aparece parcialmente detrás del panel de capas; la ficha tapa la atribución; los rótulos de Piura, Castilla, Catacaos y Chulucanas se pisan.

**Medición.** Canvas 390×739; panel plegado 358×92; ficha 358×111 en `y=693`; atribución 370×84 en `y=750`; zoom en `x=351`, `y=115`, solapado con el panel en `y=121-213`.

**Causa.** `mapPadding()` usa el panel y la ficha como padding del `fitBounds`; el encuadre resultante deja el bounding box de la cuenca en una banda pequeña y el resto es el fondo del mapa. En móvil se suma un panel que arranca plegado pero sigue ocupando espacio y una ficha siempre visible.

**Archivos.** `web/src/pages/mapa.astro:120-133`; `web/src/styles/global.css:423-441`.

**Impacto.** El mapa —la experiencia principal— se percibe pequeño, roto y difícil de tocar. Es el problema más grave para el público móvil.

**Prioridad:** P0.

**Dirección.** Mapa a pantalla completa; panel de capas en hoja; ficha en hoja inferior con estado de «peek»; controles fuera del panel; encuadre específico para el Bajo Piura en móvil y un botón «ver toda la cuenca».

---

### 3.3. La simbología cartográfica es ambigua

**Qué se ve.** Inundación, red hídrica y lagunas comparten la misma familia azul: `#0069a0` para la inundación, `#2f6f8a` para el agua y `#134f7a` para los ríos. La inundación puede leerse como agua permanente. Los swatches del panel son líneas cortas, no áreas ni tramas, y el mapa no tiene leyenda.

**Archivos.** `web/src/pages/mapa.astro:560-643`; `web/src/styles/global.css:285-303`.

**Impacto.** Un lector no especialista no puede distinguir qué es un río, qué es una laguna y qué es una mancha de inundación. Es un problema de rigor, no solo estético.

**Prioridad:** P0.

**Dirección.** Azul de agua para hidrografía; inundación en teal con **trama diagonal** y borde propio; límite de cuenca en arcilla; subcuencas en gris discontinuo; obras en ámbar discontinuo. Leyenda contextual con los símbolos reales.

---

### 3.4. Fuentes es ilegible en móvil y difícil de escanear en escritorio

**Qué se ve.** Una tabla de cinco columnas con descripciones largas en la primera celda. En móvil, la tabla mide 582 px dentro de un contenedor de 350 px; el documento completo mide 602 px y scrollea en horizontal. Las columnas de licencia y estado quedan fuera de pantalla. No hay búsqueda, filtros ni resumen.

**Medición.** 30 registros; 4 tablas de grupo; `body.scrollWidth = 602` en un viewport de 390 px.

**Archivos.** `web/src/pages/fuentes.astro:71-109`; `web/src/styles/global.css:186-201`.

**Impacto.** La página que debe transmitir confianza es la más difícil de leer en el dispositivo más usado. La información existe, pero no se puede consultar.

**Prioridad:** P0.

**Dirección.** Registros en una columna, no tablas; índice lateral de grupos; filtros por estado, certeza, tipo y texto; ficha desplegable; recuento real; nunca scroll horizontal. No inventar «primaria/secundaria»: usar `tipo` y `certeza`.

---

### 3.5. El panel de capas es un muro técnico

**Qué se ve.** Un panel de 290×804 px que mezcla checkboxes, método de la partición, fuentes, controles de corte y enlaces de atribución en tipografía de 0,72–0,85 rem. No hay grupos; el método de las subcuencas interrumpe la lista; la nota de fuentes queda al final, fuera de la vista.

**Archivos.** `web/src/pages/mapa.astro:26-82`; `web/src/styles/global.css:236-283`.

**Impacto.** El visitante tiene que leer documentación para activar una capa. La jerarquía entre «control» y «metodología» desaparece.

**Prioridad:** P1.

**Dirección.** Grupos Base / Agua / Evento / Análisis; cada fila con símbolo real, estado y un detalle de método plegable; «Fuentes y método» en un enlace separado; el panel no debe tapar el mapa en escritorio.

---

### 3.6. La ficha de información no es una ficha

**Qué se ve.** Una tarjeta de 360×111 px siempre visible que dice «Haz clic en el mapa», con un botón para la cuenca. Al seleccionar, reemplaza su contenido con HTML concatenado; no se cierra, no resalta el elemento seleccionado y puede crecer sin límite. En móvil tapa la atribución y parte del mapa.

**Archivos.** `web/src/pages/mapa.astro:84-90, 222-233, 516-849`.

**Impacto.** No hay una relación visual entre el elemento clicado y su ficha; el mapa queda cubierto por un panel vacío la mayor parte del tiempo.

**Prioridad:** P1.

**Dirección.** Ficha lateral que solo aparece al seleccionar; título, tipo, cifra, método, fuente y cierre; resaltado del elemento; en móvil, hoja inferior con «peek» y expansión.

---

### 3.7. Escenarios es un muro de prosa sin estructura temporal

**Qué se ve.** Cinco capítulos separados solo por `h2`, con badges incrustados en las frases, una tabla de 2017 densa, una figura estática de 900×1160 y una nota de 2023 dentro de un bloque `.note`. No hay línea de tiempo ni navegación por año; el lector no sabe dónde está ni qué puede comparar.

**Archivos.** `web/src/pages/escenarios.astro:28-235`.

**Impacto.** El contenido histórico más valioso se vuelve difícil de recorrer. La ausencia de geometrías de 1983/1998 no se convierte en una explicación visual; se convierte en un vacío.

**Prioridad:** P1.

**Dirección.** Línea de tiempo sticky; capítulos con año grande, estado y fuente en el margen; 2017 como lámina; matriz de evidencia que declare qué se puede comparar y qué no; 2023 como capítulo.

---

### 3.8. La maqueta 3D está desconectada y sufre en móvil

**Qué se ve.** Fondo gris plano, panel de texto de 460 px en móvil que deja ~250 px para el modelo, rótulos del GLB ilegibles y superpuestos, sin progreso de carga ni póster. En escritorio, el modelo está pegado al borde inferior y el panel es un muro de notas.

**Medición.** GLB 1 605 KB; panel móvil ~460 px de 739; el modelo queda en ~250 px.

**Archivos.** `web/src/pages/maqueta.astro:30-74, 189-221, 245-299`.

**Impacto.** La pieza más singular del atlas se percibe como un visor aparte, no como parte del atlas. En móvil es casi inutilizable.

**Prioridad:** P1.

**Dirección.** La maqueta como espécimen sobre papel; panel de margen; controles explícitos; póster y progreso; LOD de rótulos; en móvil, modelo primero y ficha en hoja.

---

### 3.9. No hay identidad tipográfica ni una escala de lectura

**Qué se ve.** No existe `@font-face`: el sitio cae en Georgia o en la serif del sistema y en `ui-sans-serif` para la interfaz. La identidad cambia según el sistema operativo. Solo hay tres tamaños de título; el cuerpo es de 16 px; los párrafos normales miden 1 040 px (~125 caracteres), aunque el `.lead` sí tiene 68ch.

**Archivos.** `web/src/styles/global.css:1-12, 58-65, 108-117`.

**Impacto.** La lectura larga cansa y la marca no tiene una voz estable. La página se ve como un documento por defecto, no como un atlas.

**Prioridad:** P1.

**Dirección.** Newsreader + Archivo autoalojadas; escala fluida; prosa a 68ch; cifras tabulares; jerarquía editorial.

---

### 3.10. No hay sistema de componentes ni estructura documental consistente

**Qué se ve.** 473 líneas de CSS global y nueve variables. Las superficies cambian entre `#fffdf7`, `#fff9ea` y `rgba(255,253,247,.97)`; los radios entre 4, 5, 6 y 10 px; las sombras aparecen en tarjetas y paneles sin un criterio. En la portada, los `h3` de las tarjetas van antes del primer `h2`. `/mapa` no tiene `h1`: su primer encabezado es `h2` («Capas»).

**Archivos.** `web/src/styles/global.css`; `web/src/layouts/Base.astro:56-75`; medido en las cinco páginas.

**Impacto.** Cada página se resuelve por separado; cualquier cambio visual es frágil. La estructura de encabezados afecta a lectores de pantalla y a la comprensión del documento.

**Prioridad:** P1/P2.

**Dirección.** Tokens + componentes Astro; superficies y radios únicos; jerarquía `h1 → h2 → h3`; `h1` visible o al menos presente en el mapa.

---

## 4. Hallazgos transversales

### 4.1. Color y contraste

El contraste de texto es bueno y se conserva: tinta/papel 14,8:1; gris/papel 5,8:1; algarrobo/papel 7,0:1; arcilla/papel 5,1:1; agua/papel 5,4:1. La auditoría axe no detecta violaciones WCAG A/AA.

El problema es **semántico**, no de contraste: el mismo azul se usa para agua, río e inundación; los estados usan badges de colores que no siempre coinciden con la certeza; el amarillo del `.note` se lee como advertencia genérica aunque a veces sea una regla editorial.

### 4.2. Tipografía y lectura

- Familia real medida: `"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif`; sin fuentes locales, el resultado depende del SO.
- `h1` 46,4 px; `h2` 21,6 px; `h3` 16,8 px; cuerpo 16 px/24,8.
- `.lead` 768 px (68ch); párrafos normales 1 040 px.
- La interfaz usa `ui-sans-serif` a 11,5–17 px; los paneles del mapa bajan a 11,5 px.
- Los badges de 0,72 rem se incrustan en el texto y rompen el ritmo de lectura.

### 4.3. Responsive

- La cabecera pasa de 59 px a 107 px en móvil porque la navegación envuelve; el `menu` no existe.
- El mapa móvil tiene el problema descrito en 3.2.
- La maqueta móvil tiene el panel antes del modelo y el modelo en ~250 px.
- Fuentes scrollea horizontalmente.
- Escenarios no scrollea horizontalmente, pero las tablas quedan al límite.
- No hay `safe-area-inset` para iPhone con notch.
- Los objetivos táctiles de los checkboxes (15 px) son menores de 44 px, aunque la fila completa es clicable.

### 4.4. Accesibilidad

**Lo que funciona:** skip link, foco visible, contraste AA, resumen `sr-only` del mapa y la maqueta, teclado en cortes, `Escape` devuelve el foco, `prefers-reduced-motion`, textos alternativos.

**Lo que falta o es frágil:**
- `/mapa` no tiene `h1`; el primer encabezado es «Capas».
- La ficha es `aria-live` pero no tiene cierre ni foco gestionado; el contenido se reemplaza sin anunciar el elemento seleccionado.
- El mapa usa `role="application"`, que puede atrapar al lector de pantalla; conviene un `region` con instrucciones y una lista de capas alternativa.
- Las hojas móviles propuestas necesitan foco atrapado y devuelto.
- La tabla de Fuentes no tiene alternativa móvil.
- La auditoría axe se ejecuta 500 ms después de `domcontentloaded`; no prueba estados dinámicos ni el foco de las hojas.
- No hay prueba manual con lector de pantalla ni con personas (ya declarado en `docs/09`).

### 4.5. Rendimiento y medios

| Recurso | Peso | Observación |
|---|---:|---|
| JS del mapa | 804 KB en bruto / 219 KB gzip | Dentro de lo esperable para MapLibre, pero es el mayor bloque |
| `relieve.jpg` | 480 KB | Ráster blando; candidato a WebP/AVIF y a una versión más pequeña |
| `flood_2017.geojson` | 512 KB / 133 KB gzip | Carga diferida; correcto |
| GLB de la maqueta | 1 605 KB | Se carga siempre al abrir `/maqueta`; sin póster ni progreso |
| JS de la maqueta | 580 KB en bruto / 148 KB gzip | Three.js + addons |
| Portada | ~10 KB | No hay imágenes; el presupuesto está libre para una lámina |
| Escenarios | ~131 KB | Incluye la figura de 2017 (121 KB) |

El mapa tarda en mostrar la geografía útil en móvil, pero el problema principal es de encuadre, no de peso. La maqueta necesita un póster y un estado de carga con progreso; el relieve necesita una versión web más eficiente.

### 4.6. Contenido y estructura

- La portada empieza con una cifra y una nota de método antes de contar la historia; el dato de `Shape_Area` es correcto, pero frena la entrada.
- Las cifras no tienen una jerarquía visual común: aparecen en prosa, en tablas y en fichas.
- La fecha del pico de 1998 (12 vs 16 de marzo) se declara, pero se pierde en un párrafo.
- La diferencia entre «dato medido», «derivado», «documentado», «interpretación» y «por verificar» se explica en dos páginas con badges distintos.
- No hay `og:image`; el sitio se comparte sin una lámina visual.
- No hay estilos de impresión; un atlas debería poder imprimirse.
- El pie no incluye navegación completa, cita ni enlace al repositorio.

---

## 5. Lo que funciona y debe conservarse

1. **La voz editorial.** «El río que no llega al mar» y «Cuándo el río sí llegó al mar» son titulares propios y memorables.
2. **La honestidad.** Las advertencias sobre 2017, la fecha de 1998, la ausencia de 1983/1998 y el carácter derivado de Bajo Piura están bien escritas.
3. **La trazabilidad.** El catálogo de 30 fuentes con institución, escala, licencia, método y certeza es el activo más valioso del proyecto.
4. **La paleta papel/tinta.** Es cálida y legible; el contraste AA está resuelto. No hace falta reemplazarla, sino ordenarla.
5. **La accesibilidad de base.** Skip link, foco, teclado, resumen del mapa y reducción de movimiento ya existen.
6. **La carga diferida.** La inundación y el DEM se descargan solo al activarlos; ese criterio debe mantenerse.
7. **El bloque 3D.** Es una pieza singular y real; el problema es su presentación, no el modelo.
8. **La ausencia de dependencias innecesarias.** Astro + MapLibre + Three.js es suficiente.

---

## 6. Tabla priorizada

| ID | Hallazgo | Prioridad | Impacto | Esfuerzo |
|---|---|---|---|---|
| A1 | Portada sin territorio ni jerarquía de entrada | P0 | Alto | M |
| A2 | Mapa móvil: encuadre, solapes, ficha y zoom | P0 | Alto | L |
| A3 | Simbología ambigua y sin leyenda | P0 | Alto | M |
| A4 | Fuentes: tabla rota en móvil, sin filtros | P0 | Alto | M |
| A5 | Panel de capas: muro técnico | P1 | Alto | M |
| A6 | Ficha sin cierre, sin resaltado y sin jerarquía | P1 | Alto | M |
| A7 | Escenarios: muro de prosa sin línea de tiempo | P1 | Medio | M |
| A8 | Maqueta 3D: móvil, rótulos, carga y encuadre | P1 | Medio | M |
| A9 | Tipografía sin identidad y lectura ancha | P1 | Medio | S |
| A10 | Falta de sistema de componentes y orden de encabezados | P1/P2 | Medio | M |
| B1 | Relieve de 480 KB y sin versión web | P2 | Medio | S |
| B2 | Sin `og:image`, sin impresión, pie sin colofón completo | P2 | Bajo | S |
| B3 | Estados de carga y error solo textuales | P2 | Medio | S |

---

## 7. Límites de esta auditoría

- No se probó con personas ni con un lector de pantalla real; la evaluación de accesibilidad es heurística y automática.
- No se probó en Safari/iOS ni en Firefox; las capturas y mediciones son de Chrome.
- No se midió con red 3G real; los pesos son de recursos y gzip locales.
- No se evaluó el contenido científico en sí: se auditó su presentación visual y su trazabilidad aparente. Las cifras se contrastaron con `data/sources.yml` y `docs/09`.
- Las propuestas de color y tipografía se evalúan en `design-proposal/`; no se aplicaron a producción.

---

## 8. Índice de evidencia

| Archivo | Qué muestra |
|---|---|
| `evidencia/actual-home-desktop.png` | Portada actual, escritorio |
| `evidencia/actual-home-mobile.png` | Portada actual, móvil |
| `evidencia/actual-mapa-desktop.png` | Mapa por defecto, escritorio |
| `evidencia/actual-mapa-mobile.png` | Mapa por defecto, móvil: franjas vacías y solapes |
| `evidencia/actual-mapa-inundacion.png` | Inundación 2017 y ficha, escritorio |
| `evidencia/actual-mapa-corte.png` | Perfil de corte, escritorio |
| `evidencia/actual-maqueta-desktop.png` | Maqueta 3D, escritorio |
| `evidencia/actual-maqueta-mobile.png` | Maqueta 3D, móvil: panel vs. modelo |
| `evidencia/actual-escenarios-desktop.png` | Escenarios, escritorio |
| `evidencia/actual-escenarios-mobile.png` | Escenarios, móvil |
| `evidencia/actual-fuentes-desktop.png` | Fuentes, escritorio |
| `evidencia/actual-fuentes-mobile.png` | Fuentes, móvil: tabla desbordada |
| `evidencia/actual-404.png` | Página 404 |

Las capturas actuales se tomaron sobre el build de producción `dist/` de la versión 0.2.3, sin la barra de desarrollo de Astro.

---

## 9. Comprobaciones de calidad sobre la versión auditada

| Comprobación | Resultado |
|---|---|
| `npm run build` | 6 páginas generadas correctamente |
| `npm run check` | 0 errores, 0 warnings, 31 hints del Draco público |
| `npm run check:links` | 95 enlaces internos, sin roturas |
| `npm run check:a11y` | 0 violaciones WCAG A/AA en 8 vistas (5 páginas, 404 y los dos visores en móvil) |
| `npm run test:e2e` | 11 pruebas Playwright en verde |
| Pruebas Python | 79 pruebas en verde |
| `python3 etl/check_data.py` | 0 errores y 10 avisos declarados (fidelidad de subcuencas, proximidad y reparación de AOI10) |
| Topología | cuenca 10 938,4 km² · subcuencas 10 938,4 km² · 0 solapamientos · 0 fuera · 0 huecos |
| Inundación publicada | 2 AOI · 555,477 km² · 522 kB |
| GLB | 39 nodos · 39 mallas · 1,6 MB |
| Datos publicados | 1 294 kB |
| Archivos versionados modificados | 0 |

La comprobación `check_data.py` se ejecutó en un entorno temporal con las dependencias de `etl/requirements.txt`; el sistema base no trae `shapely`. Los avisos no se ocultaron: son los mismos que documenta `docs/09-auditoria-estabilizacion.md`.

**Lectura:** el problema no es la validez de los datos ni el cumplimiento automático de WCAG; es la experiencia visual y la legibilidad. La auditoría automática no mide longitud de línea, tablas móviles, jerarquía de encabezados ni foco en hojas.

---

## 10. Evidencia de la entrega 1 implementada

La primera entrega del rediseño ya está aplicada en el árbol de trabajo: fundamentos visuales (tokens, Newsreader/Archivo, cabecera, pie y componentes) y portada nueva. Las capturas siguientes son del build estático real, sin la barra de desarrollo de Astro:

| Archivo | Qué muestra |
|---|---|
| `evidencia/implementado-home-desktop.png` | Portada nueva, escritorio |
| `evidencia/implementado-home-mobile.png` | Portada nueva, móvil |
| `evidencia/implementado-home-full.png` | Portada completa, escritorio |
| `evidencia/implementado-mapa-desktop.png` | Mapa nuevo por defecto, escritorio |
| `evidencia/implementado-mapa-mobile.png` | Mapa nuevo en móvil: lienzo completo, panel plegado y encuadre del Bajo Piura |
| `evidencia/implementado-mapa-inundacion.png` | Mapa nuevo con la capa de inundación y la trama |
| `evidencia/implementado-mapa-inundacion-mobile.png` | Inundación en móvil |
| `evidencia/implementado-escenarios-desktop.png` | Escenarios nuevo, escritorio |
| `evidencia/implementado-escenarios-mobile.png` | Escenarios nuevo en móvil |
| `evidencia/implementado-escenarios-2017.png` | Capítulo 2017 con lámina y cifras |
| `evidencia/implementado-fuentes-desktop.png` | Fuentes nuevo, registros y filtros |
| `evidencia/implementado-fuentes-mobile.png` | Fuentes en móvil, sin tabla horizontal |
| `evidencia/implementado-maqueta-desktop.png` | Maqueta 3D como espécimen, escritorio |
| `evidencia/implementado-maqueta-mobile.png` | Maqueta en móvil, modelo primero |

Todas las páginas comparten ya la dirección de arte y la estructura editorial; la revisión final queda en la fase de QA y publicación.
