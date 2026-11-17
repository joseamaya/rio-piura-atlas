# 02 · Dirección de arte

**Propuesta:** «Lámina y margen»  
**Proyecto:** Río Piura Atlas · UI-01  
**Fecha:** 2026-11-17

---

## 1. Concepto

Un atlas científico contemporáneo, no un dashboard. El mapa es una **lámina** que ocupa la página; los datos, las fuentes y las advertencias viven en el **margen**, con reglas finas, numeración de figura, pies de foto y tipografía editorial. La maqueta 3D se trata como un **espécimen** sobre papel, no como un visor de videojuego.

La metáfora guía las decisiones:

| Lámina | Margen |
|---|---|
| Mapa, maqueta, figura de inundación | Cifra, fuente, método, advertencia |
| Ocupa el espacio principal | Se lee en columna estrecha |
| Color y símbolos cartográficos | Tinta y reglas tipográficas |
| Se mira | Se cita |

**Atributos de marca:** sobria, cálida, precisa, material, paciente.  
**Lo que no es:** dashboard SaaS, plantilla de administración, infografía de noticias, mapa decorativo.

### Referencias conceptuales

- **Atlas editoriales:** la materialidad de la colección David Rumsey, la composición de *Atlas de los paisajes de España* y los suplementos cartográficos de *National Geographic*. Se toma la disciplina de la leyenda y el pie de figura, no su estética historicista.
- **Cartografía contemporánea:** la contención de Mapbox Studio y la claridad de las capas de OpenStreetMap. Se toma la jerarquía, no la interfaz.
- **Narrativa de datos:** Reuters Graphics y *The Pudding* para la secuencia lectura → cifra → fuente.
- **Publicación de naturaleza:** *Emergence Magazine* y revistas de ciencia para la tipografía y el ritmo de lectura.
- **Economía de tinta:** Edward Tufte para la relación dato/ornamento y los pequeños múltiples.
- **Anti-referencias:** dashboards con rejillas de tarjetas, gradientes decorativos, sombras difusas, iconos genéricos y semáforos rojo/verde.

---

## 2. Paleta

### 2.1. Marca y base

| Token | Hex | Uso | Contraste sobre papel |
|---|---|---|---:|
| `--paper` | `#F5F1E6` | Fondo principal, papel yeso | — |
| `--paper-2` | `#EAE3D3` | Superficies, tablas, láminas | — |
| `--paper-3` | `#FBF8F0` | Realce de fichas | — |
| `--ink` | `#16201E` | Texto principal, basalto | 14,8:1 |
| `--ink-2` | `#2B3733` | Texto de prosa | 12,0:1 |
| `--muted` | `#55605B` | Texto secundario | 5,8:1 |
| `--line` | `#D5CEBD` | Reglas de 1 px | — |
| `--line-strong` | `#B9B09C` | Reglas de énfasis | — |
| `--brand` | `#1C5B52` | Enlaces, acciones, selección | 7,0:1 |
| `--brand-strong` | `#123E38` | Hover y énfasis | 9,6:1 |
| `--clay` | `#A24E2E` | Acento editorial, interpretación | 5,1:1 |
| `--sand` | `#C9A36A` | Acento gráfico; nunca texto pequeño | 2,2:1 |

**Regla:** el algarrobo (`--brand`) es color de **interfaz**; no se usa para representar agua, cuenca ni ningún fenómeno. La arcilla (`--clay`) es acento editorial y color de **interpretación**; no es un color de error.

### 2.2. Colores semánticos del territorio

| Rol | Token | Hex | Tratamiento |
|---|---|---|---|
| Agua permanente / ríos | `--water` | `#1D6A86` | relleno sólido / línea de 1–3 px |
| Agua profunda / borde | `--water-deep` | `#134E63` | línea de costa y énfasis |
| Inundación 2017 | `--flood` | `#4C93A8` | relleno + **trama diagonal** `#17566B` |
| Límite de cuenca ANA | `--basin` | `#7A3A2B` | línea continua 2,5 px |
| Subcuencas | `--sub` | `#6F6555` | línea discontinua 1 px |
| Obras / interpretación | `--works` | `#B26A2C` | línea discontinua + rombo |
| Relieve | rampa `#D8C7A2 → #C9B88F → #A89A78 → #8B8A70 → #6F7664` | — | hipsométrica, no vegetación |
| Mar | `#AAC7CA` | — | tono apagado para que la tierra domine |

La **trama** es obligatoria en la inundación: permite distinguirla del agua permanente sin depender del tono. Se genera como patrón de 8×8 px con líneas diagonales; en impresión se mantiene.

### 2.3. Estados y certeza

No se usan semáforos. Se usan **forma + etiqueta**:

| Estado | Marca | Color |
|---|---|---|
| Dato medido | punto lleno | tinta |
| Derivado | medio punto | tinta |
| Documentado | círculo abierto | tinta |
| Interpretación | rombo | arcilla |
| Por verificar | cuadrado tramado | gris |
| Disponible | punto verde apagado | `#2F6248` |
| Por solicitar | punto ámbar | `#8A5A1F` |

La etiqueta textual acompaña siempre a la marca. El color por sí solo nunca comunica un estado.

---

## 3. Tipografía

### 3.1. Familias

| Rol | Familia | Licencia | Uso |
|---|---|---|---|
| Display y texto | **Newsreader** | OFL 1.1 | Titulares, prosa, cifras editoriales |
| Interfaz y cartografía | **Archivo** | OFL 1.1 | Navegación, paneles, tablas, rótulos |
| IDs y coordenadas | Mono del sistema | — | `ana-subcuencas`, coordenadas, figura |

**Por qué Newsreader.** Tiene opsz, itálicas y una cadencia literaria que sostiene la lectura larga sin volverse anticuada. **Archivo** aporta una grotesca con cifras tabulares y personalidad suficiente para la interfaz sin competir con la cartografía. Las dos son OFL y se pueden autoalojar.

**Implementación:** WOFF2 autoalojadas en `web/src/fonts/` (o `public/fonts/` con `withBase`), subset latino + español, `font-display: swap`, precarga solo de Newsreader. En el prototipo se usan tres archivos (Newsreader normal/itálica + Archivo, ~308 KB); en producción se debe subsetear a ~180 KB. Sin Google Fonts en runtime.

### 3.2. Escala

| Nivel | Tamaño | Line-height | Uso |
|---|---|---|---|
| Display | `clamp(3.05rem, 6.4vw, 6.2rem)` | 0.98 | Portada, año de escenario |
| H1 | `clamp(2.5rem, 4.8vw, 4.4rem)` | 1.06 | Título de página |
| H2 | `clamp(1.85rem, 3.1vw, 2.9rem)` | 1.08 | Sección |
| H3 | `clamp(1.2rem, 1.6vw, 1.45rem)` | 1.2 | Entrada, subtítulo |
| Lead | `clamp(1.1rem, 1.45vw, 1.35rem)` | 1.5 | Entradilla |
| Cuerpo | 17 px | 1.65 | Prosa |
| Pequeño | 14 px | 1.5 | Notas |
| Pie | 13 px | 1.45 | Pies de figura |
| Etiqueta | 11 px | 1.3 | Kickers, tablas, estados |

**Medida de lectura:** 68ch; titulares con `text-wrap: balance`; cifras con `font-variant-numeric: tabular-nums`. No se usa texto por debajo de 11 px en contenido; la cartografía puede bajar a 9,5 px solo en rótulos secundarios.

### 3.3. Voz

- Titulares en serif, con verbos y sin jerga: «El río que no llega al mar».
- Kickers en mayúsculas, 11 px, `letter-spacing: 0.15em`.
- Cifras siempre con unidad y fuente; nunca una cifra suelta.
- Notas al margen en sans, 12–13 px, con una regla superior.
- No se usan signos de admiración ni lenguaje publicitario.

---

## 4. Espaciado, rejilla y bordes

- **Base:** 4 px. Escala 4, 8, 12, 16, 24, 32, 48, 64, 96, 128.
- **Secciones:** 96–112 px en escritorio; 64 px en móvil.
- **Contenedor:** 1 240 px; prosa 720 px (68ch); mapas a sangre.
- **Rejilla:** 12 columnas, gutter 24 px; asimetría editorial (7/5, 8/4).
- **Radios:** 2 px en botones, campos y hojas; 0 en láminas y figuras.
- **Bordes:** 1 px `--line`; 2 px `--ink` para apertura de sección; 3 px de foco.
- **Sombras:** ninguna en tarjetas. Una sola sombra funcional para paneles flotantes del mapa y hojas móviles: `0 18px 48px rgba(22,32,30,.16)`.
- **Movimiento:** 180 ms `cubic-bezier(.2,.7,.2,1)` para paneles; nada de animaciones de scroll; respeta `prefers-reduced-motion`.

---

## 5. Tratamiento de imágenes

- **Láminas reales:** render del GLB existente, recorte del relieve Copernicus, figura de la inundación de Copernicus. Siempre con pie, fuente y escala.
- **Sin fotos de stock.** El atlas no necesita banco de imágenes; su material es cartográfico.
- **Formato:** AVIF/WebP con fallback JPEG; `<picture>` y dimensiones explícitas para evitar CLS; `loading="lazy"` salvo la lámina de portada.
- **Marco:** las láminas no llevan esquinas redondeadas; se apoyan en el papel con una regla fina o una sombra de objeto muy contenida.
- **Rotulación:** `Lámina 01`, `Fig. 03`; pie en Archivo 13 px; fuente en línea propia.
- **Lo conceptual se marca:** los esquemas de pendiente y trasvase llevan «Esquema conceptual; no es geometría». Las rutas históricas de la maqueta llevan «interpretación».
- **No se inventa geografía.** Si falta el polígono, no se dibuja una aproximación silenciosa.

---

## 6. Iconografía

- **Solo funciones:** capas, cerrar, más, menos, reiniciar, pantalla completa, información, flecha.
- **Trazo:** 1,5 px, 20/24 px, extremos redondeados; sin relleno decorativo.
- **Etiqueta textual** junto al icono cuando el espacio lo permite; en móvil, `aria-label`.
- **Iconos de mapa:** no son iconos de interfaz; son símbolos cartográficos (línea, trama, punto) y se dibujan con CSS/SVG, no con una librería.
- **Prohibido:** una cuadrícula de iconos genéricos para las secciones, iconos de “features” o emojis.

---

## 7. Componentes

### 7.1. Navegación y estructura

| Componente | Anatomía | Estados |
|---|---|---|
| `SiteHeader` | marca + nav + acción | actual, hover, foco, móvil con menú |
| `SiteFooter` | colofón, explorar, rigor, licencia | enlaces, aviso |
| `SectionHeader` | kicker + título + intro | — |
| `PageHero` | kicker, H1, lead, estados | — |

### 7.2. Editorial

| Componente | Anatomía | Uso |
|---|---|---|
| `Plate` | imagen + pie + fuente | Mapas, 3D, inundación |
| `MarginNote` | regla superior + estado + fuente | Capítulos, fichas |
| `DataFigure` | cifra + unidad + etiqueta + fuente | Portada, escenarios |
| `Note` | título + texto, borde superior | Reglas y advertencias |
| `SourceRecord` | id + título + meta + estados + detalle | Fuentes |
| `Timeline` | años + capítulos + estado activo | Escenarios |
| `EvidenceTable` | año × relato/caudal/geometría | Escenarios |

### 7.3. Mapa

| Componente | Anatomía | Estados |
|---|---|---|
| `LayerPanel` | grupos, filas, símbolo, estado, detalle | abierto, plegado, hoja móvil |
| `LayerRow` | checkbox + símbolo + nombre + tag + info | on/off, foco |
| `MapLegend` | título + símbolos + nota | contextual, colapsable |
| `FeaturePanel` | kicker + título + datos + método + fuente + cierre | cerrado, abierto, hoja |
| `ProfilePanel` | título + metadatos + SVG + nota | cerrado, abierto |
| `MapControls` | zoom, reset, fullscreen | hover, foco |
| `MapTitle` | título + subtítulo + fuente | — |
| `GeoRuler` | longitudes + marcas | — |

### 7.4. Estados

- **Vacío:** el mapa no muestra una tarjeta vacía permanente; una pista discreta desaparece al primer uso.
- **Carga:** `skeleton` en la ficha y en la leyenda; progreso textual en la maqueta.
- **Error:** mensaje en el panel, sin dejar el mapa en blanco; enlace a fuentes.
- **Selección:** el elemento se resalta en el mapa; la ficha se abre con foco gestionado.

---

## 8. Comportamiento responsive

| Breakpoint | Comportamiento |
|---|---|
| ≥ 1024 px | Rejilla 12 col; mapa con panel lateral de 320 px; ficha lateral; portada a dos columnas |
| 820–1023 px | Panel de 296 px; portada a dos columnas más estrecha; fuentes a una columna con índice superior |
| 640–819 px | Navegación en menú; mapa a pantalla completa con hojas; portada a una columna |
| < 640 px | Móvil: tipografía fluida; botones a ancho completo cuando corresponde; mapa con hoja inferior; maqueta modelo primero |

**Reglas móviles:**
- El mapa ocupa `100dvh - header`; el encuadre inicial prioriza el Bajo Piura y ofrece «ver toda la cuenca».
- La ficha empieza como «peek» de 64 px y se expande a hoja de 74dvh.
- El panel de capas es una hoja a pantalla completa, con cierre y foco atrapado.
- Las tablas se convierten en registros; nunca scroll horizontal.
- Objetivos táctiles ≥44 px; `env(safe-area-inset-bottom)` en hojas.
- La maqueta muestra el modelo primero (58dvh) y la ficha después.

---

## 9. Accesibilidad

- **WCAG 2.2 AA** como mínimo; contraste 4,5:1 en texto y 3:1 en elementos no textuales.
- **Foco visible:** 3 px `--brand` con offset 3 px; nunca `outline: none` sin sustituto.
- **Teclado:** capas, ficha, perfil, hojas y maqueta; `Escape` cierra y devuelve el foco.
- **Semántica:** un `h1` por página; orden `h1 → h2 → h3`; `main`, `nav`, `aside`, `footer`; listas reales.
- **Mapa:** `role="region"` con instrucciones y lista de capas alternativa; evitar `role="application"` como única estrategia.
- **Color:** nunca solo color; patrones, formas y etiquetas.
- **Movimiento:** `prefers-reduced-motion`; sin parallax ni scroll animado.
- **Tablas:** `caption`, `th` con `scope`, alternativa de registros en móvil.
- **Textos alternativos:** cada lámina describe qué se ve y qué no es; el resumen del mapa se mantiene.
- **Prueba manual:** teclado real, lector de pantalla y personas de los tres públicos siguen pendientes.

---

## 10. Tokens

Los tokens viven en `design-proposal/styles/tokens.css` y se trasladarán a `web/src/styles/tokens.css` en la implementación. Extracto:

```css
:root {
  --paper: #f5f1e6;
  --paper-2: #eae3d3;
  --ink: #16201e;
  --muted: #55605b;
  --brand: #1c5b52;
  --clay: #a24e2e;
  --water: #1d6a86;
  --flood: #4c93a8;
  --flood-deep: #17566b;
  --basin: #7a3a2b;
  --sub: #6f6555;
  --font-display: "Newsreader", Georgia, serif;
  --font-ui: "Archivo", ui-sans-serif, system-ui, sans-serif;
  --fs-body: 1.0625rem;
  --text: 68ch;
  --container: 1240px;
  --section: clamp(64px, 8vw, 112px);
  --radius: 2px;
  --shadow-panel: 0 18px 48px rgba(22, 32, 30, .16);
}
```

**Gobernanza:** un token nuevo requiere un uso documentado; no se añaden colores “porque quedan bien”. Los colores semánticos no se reutilizan en la interfaz. Los componentes nuevos se documentan en `sistema.html` antes de production.

---

## 11. Qué se conserva de la versión actual

- La paleta papel/tinta y el contraste AA.
- La voz editorial y las advertencias.
- El catálogo de fuentes y sus campos.
- La carga diferida de la inundación y el DEM.
- El bloque 3D y su declaración de exageración.
- El foco visible, el skip link y la reducción de movimiento.

## 12. Qué se elimina

- Las cuatro tarjetas iguales de la portada.
- El `.note` amarillo como recurso universal.
- Los badges de colores como decoración.
- El panel de capas como lista de documentación.
- La ficha vacía siempre visible.
- Los radios de 10 px y las sombras en tarjetas.
- La tipografía dependiente del sistema.
- La tabla de Fuentes en móvil.
