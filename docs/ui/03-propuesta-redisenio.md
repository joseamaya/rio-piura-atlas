# 03 · Propuesta de rediseño

**Dirección:** «Lámina y margen»  
**Mockups:** `design-proposal/home.html`, `mapa.html`, `escenarios.html`, `fuentes.html`, `maqueta.html`, `sistema.html`  
**Galería:** [`design-proposal/index.html`](../../design-proposal/index.html)  
**Capturas:** `design-proposal/captures/`

---

## 1. Principios de la propuesta

1. **El mapa es la lámina.** En escritorio ocupa todo el espacio que no necesita el panel; en móvil, la pantalla completa.
2. **El margen explica.** Las cifras, los métodos y las fuentes no compiten con el mapa; lo acompañan en una columna estrecha.
3. **La ausencia también se diseña.** Si no hay mancha de 1983/1998, se declara con una matriz de evidencia, no con un hueco.
4. **La marca no es un color de dato.** El algarrobo es interfaz; el agua, la inundación y la cuenca tienen sus propios colores y símbolos.
5. **La lectura larga manda.** 68ch, 17 px, serif editorial, pie de figura con fuente.
6. **Nada de dashboard.** Sin rejillas de tarjetas, sin gradientes decorativos, sin sombras difusas, sin iconos por todas partes.

---

## 2. Inicio

**Objetivo:** que en menos de 10 segundos se entienda que es un atlas de la cuenca del río Piura y que se puede explorar.

### Estructura

1. **Portada lámina.** Titular «El río que no llega al mar», entradilla de dos frases, acciones «Explorar el mapa» y «Ver la maqueta 3D». A la derecha, render real del GLB existente como espécimen; en móvil, la lámina aparece después del titular, antes del texto largo.
2. **Franja de cifras.** 10 938 km²; 8 + 1 unidades; 0,4 ‰ en los últimos 130 km; 4 424 m³/s en 1998. Cada cifra con unidad, fecha y fuente.
3. **Índice asimétrico.** Mapa (7 columnas, imagen real), Maqueta (5 columnas), Escenarios (6 columnas, detalle de la inundación), Fuentes (6 columnas, ficha de muestra). No cuatro tarjetas iguales.
4. **Qué es / qué no es.** Dos columnas con una regla fuerte; la advertencia de «no es alerta» forma parte del relato, no es una caja amarilla.
5. **Tres lecturas.** Cuenca y unidades (mini mapa real), pendiente que se desploma (barras 8,7 ‰ vs 0,4 ‰), trasvase (esquema conceptual rotulado).
6. **Método y fuentes.** Contadores reales 30/19/5/6, ficha de ejemplo de Copernicus, acciones a Fuentes y metodología.
7. **Pie.** Colofón con versión, licencias, datos, repositorio y aviso.

### Decisiones

- **Una sola acción primaria.** El mapa es la entrada; la maqueta es la segunda.
- **La cifra no es un adorno.** Cada cifra tiene su límite: la superficie medida frente a `Shape_Area`; la pendiente calculada; la fecha discrepante de 1998.
- **La lámina 3D no es decorativa.** Es el modelo real; el pie declara ×7 y «color = altitud, no vegetación».
- **El índice no es una rejilla de features.** Usa tamaños distintos y una ficha de fuente como imagen editorial.

### Diferencias con la versión actual

| Actual | Propuesta |
|---|---|
| Cuatro tarjetas iguales | Índice asimétrico 7/5 y 6/6 |
| Sin imágenes | Lámina 3D y recortes reales del mapa |
| Cifras en prosa | Franja de cifras con fuente |
| «Tres cosas» en párrafos | Tres lecturas con visuales |
| Nota amarilla | Regla y cita editorial |
| Sin CTA primaria | «Explorar el mapa» como acción principal |

---

## 3. Mapa

**Objetivo:** que la cartografía sea el centro, con una jerarquía clara entre mapa, navegación, capas, leyenda, ficha y perfil.

### Distribución

**Escritorio (≥ 1024 px):**

```
┌─────────────────────────────────────────────────────────────┐
│ Cabecera 64 px: marca · navegación · mapa actual             │
├──────────────┬──────────────────────────────────────────────┤
│ Panel 326 px │ Mapa a pantalla completa                      │
│ Base         │  título + regla de longitudes                 │
│ Agua         │  controles arriba derecha                     │
│ Evento       │  leyenda abajo izquierda                      │
│ Análisis     │  ficha lateral derecha (solo al seleccionar)  │
│ Herramientas │  perfil de corte abajo (solo al abrir)         │
│ Fuentes      │  atribución compacta                          │
└──────────────┴──────────────────────────────────────────────┘
```

**Móvil (< 900 px):** mapa a `100dvh - header`; botón «Capas» que abre una hoja; ficha en hoja inferior con «peek»; leyenda en hoja; controles fuera del panel; atribución como botón «i».

### Panel de capas

- **Grupos:** Base (relieve, cuenca, subcuencas), Agua (red, lagunas), Evento documentado (inundación 2017), Análisis y contexto (obras, cortes, ciudades).
- **Cada fila:** checkbox de 15 px, símbolo real de 22 px, nombre, etiqueta de certeza solo cuando aporta (`derivado`, `interpretación`, `medido`).
- **Método:** en un `<details>` por capa, no en el flujo principal.
- **Fuentes:** enlace «Fuentes y método de cada capa» y contador 30/19.
- **Herramientas:** «Dibujar un corte» y «Abrir corte de ejemplo»; lista de cortes de referencia en un desplegable.

### Leyenda

- Contextual: solo las capas activas.
- Símbolos reales: línea, discontinua, trama, punto.
- Nota: «La trama distingue la inundación del agua permanente».
- En móvil, hoja de leyenda; no se muestra permanentemente sobre el mapa.

### Ficha

- Se abre al seleccionar; no hay tarjeta vacía permanente.
- Contenido: kicker, título, subtítulo, dos cifras, observaciones, «qué mide», advertencia, fuente y acciones.
- El elemento seleccionado se resalta en el mapa (en la implementación: `setFilter`/capa de énfasis).
- En móvil: «peek» de 64 px con título y cifra; al tocar, hoja de 74dvh; cierre con × y gesto.
- Foco gestionado: al abrir, foco al título; al cerrar, foco al control que la abrió.

### Perfil de corte

- Lámina inferior de 360 px en escritorio; hoja en móvil.
- Ejes, unidades, longitud, cota mínima/máxima, resolución y fuente.
- Nota: «No sirve para dimensionar obras».
- Se conserva el dibujo por dos clics y los cinco cortes de referencia.

### Encuadre

- **Escritorio:** cuenca completa con padding de 24 px; el panel no tapa el oeste porque está en el layout, no flotando.
- **Móvil:** vista inicial del Bajo Piura (Paita, Sechura, Piura, Catacaos, La Unión) para que la geografía llene la pantalla. Botón «Ver toda la cuenca» que reencuadra al bounding box completo.
- **Rótulos:** colisión resuelta en cliente; jerarquía 3 oculta a zoom bajo y en móvil; etiquetas sin caja, con halo de papel; los que se salen del viewport se ocultan.
- **Regla de longitudes:** marcas de 81°O, 80°O, 79°O; en móvil solo las visibles. Refuerza la identidad de atlas sin agregar datos.

### Estados

- Carga de la inundación: «Cargando la mancha de 2017…» y luego «2 AOI · 555 477 km² publicados (no simultáneos)».
- Error: mensaje en el panel; el mapa sigue operativo.
- Sin selección: pista discreta; no tarjeta vacía.
- Enlace `?capa=inundacion`: activa la capa y abre la ficha/peek.

### Diferencias con la versión actual

| Actual | Propuesta |
|---|---|
| Panel flotante de 290 px | Panel en el layout, 326 px, plegable |
| Ficha siempre visible | Ficha contextual con cierre y resaltado |
| Sin leyenda en el mapa | Leyenda contextual con trama |
| Azules ambiguos | Agua azul, inundación teal + trama |
| Móvil con franjas vacías | Mapa a pantalla completa, hoja y encuadre del Bajo Piura |
| Fuentes y método en el panel | Enlace y disclosure separados |
| Sin regla de longitudes | Regla discreta de 81°O–79°O |

---

## 4. Escenarios

**Objetivo:** convertir cinco capítulos de prosa en una lectura temporal clara, sin inventar comparaciones.

### Estructura

- **Cabecera editorial:** título, entradilla, clave de estados y nota «Escenario documentado ≠ pronóstico».
- **Línea de tiempo sticky** (escritorio) o chips horizontales (móvil): 1891, 1983, 1998, 2017, 2023.
- **Capítulos:** año grande en cifras tabulares, kicker, título, prosa a 66ch y margen con estado, fuente y límite. Cada capítulo tiene:
  - 1891: cambio de desembocadura; sin geometría.
  - 1983: 3 200 m³/s; sin duración diaria; sin mancha.
  - 1998: 4 424 m³/s; fecha 12/16; La Niña 2 326 km²; 161 días con salvedad.
  - 2017: lámina real, tres cifras (96 507 / 458 970 / 555 477), tabla de AOI plegable, advertencia de suma vs. unión.
  - 2023: 120 m de carretera; sin área ni volumen; sin evidencia de cambio de desembocadura.
- **Matriz «Qué se puede comparar»:** año × relato, caudal, geometría. Declara la ausencia. No se simula un slider 1983/1998.
- **Cierre:** enlace a Fuentes y al mapa.

### Decisiones

- **El año es el ancla visual.** No se usan tarjetas por evento; se usa una secuencia editorial.
- **El estado va al margen.** Los badges dejan de interrumpir las frases.
- **La cifra se lee con su límite.** El bloque de 2017 muestra la unión simplificada y el total, y explica el solapamiento de 56 772 km².
- **La ausencia es información.** La matriz evita que el lector crea que hay una comparación que no existe.
- **2023 es un capítulo**, no una nota dentro de un `.note`.

### Diferencias con la versión actual

| Actual | Propuesta |
|---|---|
| Sin navegación temporal | Línea de tiempo sticky / chips |
| Badges dentro de las frases | Estado y fuente en el margen |
| Tabla de 2017 como bloque | Cifras + tabla plegable |
| Figura pequeña | Lámina real a dos columnas |
| 2023 en un `.note` | Capítulo completo |
| Sin matriz de evidencia | Matriz año × relato/caudal/geometría |

---

## 5. Fuentes

**Objetivo:** transmitir confianza y permitir encontrar una fuente concreta en pocos segundos.

### Estructura

- **Cabecera:** título, entradilla y contadores reales 30/19/5/6.
- **Clave de certeza:** cinco clases con su definición, en una fila de cinco columnas.
- **Nota de método:** no se usan «primarias/secundarias»; se usan `tipo` y `certeza` del YAML.
- **Índice lateral de grupos** con conteos: Límites/relieve/red 6, Agua 7, Inundaciones/riesgo 6, Estudios 11.
- **Filtros:** grupo, estado, certeza y búsqueda por título, institución o id. Implementados en JS sin dependencias; si se consideran fuera de alcance, la navegación por grupos ya mejora la página.
- **Registros:** una columna, con `id` mono, tipo, título enlazado, institución, fecha, escala, licencia, estado, certeza, método y notas en un desplegable.
- **Anclas:** cada registro conserva su `id`; los enlaces desde el mapa (`/fuentes#ana-subcuencas`) siguen funcionando.
- **Aviso:** «Las fuentes pendientes no se dibujan» + enlace a solicitudes.

### Decisiones

- **No tabla.** La tabla es el formato equivocado para textos largos y para móvil.
- **No categorías inventadas.** La clasificación «primaria/secundaria» no está definida en el proyecto; se evita.
- **La certeza es una marca, no un color.** Punto lleno, medio punto, círculo, rombo, trama.
- **El filtro no oculta la escala.** Los contadores y la clave quedan siempre visibles.
- **La ficha de fuente es citable.** El `id` y el título son el ancla; el método y las notas quedan a un clic.

### Diferencias con la versión actual

| Actual | Propuesta |
|---|---|
| Tabla de 5 columnas | Registros de una columna |
| 582 px en móvil | 100% del ancho, sin scroll horizontal |
| Sin resumen | Contadores 30/19/5/6 |
| Sin búsqueda | Filtros por grupo, estado, certeza y texto |
| Badges en la última celda | Estados y certeza bajo el título |
| `tipo` sin usar | Tipo visible en cada registro |

---

## 6. Maqueta 3D

**Objetivo:** integrar la pieza en el atlas y hacerla usable en móvil.

### Estructura

- **Espécimen sobre papel.** El modelo flota sobre el fondo de la página, con una sombra contenida y una regla de lámina.
- **Panel de margen de 310 px:** título, dos párrafos, sello «Exageración vertical ×7», leyenda hipsométrica, símbolos y «Ficha técnica y límites».
- **Controles explícitos:** +, −, reiniciar, pantalla completa; en la implementación, teclado y gestos.
- **Póster y progreso:** antes de cargar el GLB de 1,6 MB, mostrar un render estático y un porcentaje; en móvil, evaluar «tocar para cargar».
- **LOD de rótulos:** pocos a distancia; más al acercarse; sin placas ilegibles.
- **Móvil:** modelo primero (58dvh), panel después; leyenda en una hoja.
- **Advertencias persistentes:** ×7, color = altitud, agua narrativa, rutas interpretadas.

### Decisiones

- **No se cambia el GLB ni Draco en esta fase.** El mockup usa el render existente; la implementación puede reexportar el color si se aprueba.
- **No se añade un motor nuevo.** Three.js sigue siendo la herramienta de esta pieza.
- **La maqueta no es el mapa.** Se enlaza al mapa 2D para capas consultables y se declara que no dibuja la inundación de 2017.

### Diferencias con la versión actual

| Actual | Propuesta |
|---|---|
| Fondo gris plano | Papel y sombra de espécimen |
| Panel de 460 px en móvil | Modelo primero, panel después |
| Rótulos ilegibles | LOD y pocos rótulos |
| Carga sin progreso | Póster + progreso |
| Botón «Reiniciar» como CTA | Controles agrupados |
| Leyenda sin rampa | Rampa hipsométrica + símbolos |

---

## 7. Cabecera y pie

- **Cabecera:** 64 px, marca serif + «ATLAS» en Archivo, navegación de 13 px con subrayado de 1 px, acción primaria opcional. En móvil, 56 px y menú en hoja; no se envuelve la navegación.
- **Pie:** colofón en cuatro columnas: marca/descripción, explorar, rigor, licencias y cita. Aviso «No es un sistema de alerta» en tinta, no en rojo. Enlace al repositorio y a la versión.

---

## 8. Responsive

| Página | Escritorio | Móvil |
|---|---|---|
| Inicio | Dos columnas; índice 7/5 y 6/6 | Una columna; lámina después del titular; cifras 2×2 |
| Mapa | Panel 326 + mapa; ficha lateral | Mapa completo; hojas; ficha peek; encuadre Bajo Piura |
| Escenarios | Rail 210 + capítulos | Chips horizontales; capítulos a una columna |
| Fuentes | Índice 200 + registros | Índice horizontal; filtros apilados; registros |
| Maqueta | Panel 310 + espécimen | Modelo 58dvh + panel |
| Sistema | Tres columnas | Una columna |

**Regla:** ninguna página debe producir scroll horizontal; las tablas se convierten en registros; los controles tienen 44 px; las hojas respetan `safe-area-inset`.

---

## 9. Lo que no cambia

- Las rutas públicas: `/`, `/mapa`, `/maqueta`, `/escenarios`, `/fuentes`.
- Los datos, geometrías, cifras y textos científicos.
- La fuente de verdad `data/sources.yml`.
- Los enlaces `?capa=inundacion` y `?capa=obras`.
- El catálogo de fuentes y sus anclas.
- La carga diferida de la inundación y el DEM.
- La licencia CC BY 4.0 y el aviso de «no es alerta».
- La arquitectura Astro + MapLibre + Three.js.

No se añaden capas nuevas, no se inventan manchas de 1983/1998 y no se cambia el ETL en esta fase.

---

## 10. Decisiones abiertas para aprobar

1. **Dirección de arte:** «Lámina y margen» (recomendada).
2. **Tipografía:** autoalojar Newsreader + Archivo (recomendado) o mantener fuentes del sistema.
3. **Imágenes:** regenerar el relieve y la figura de 2017 con la paleta propuesta (solo estilo) o conservar los actuales.
4. **Portada:** render del GLB (recomendado) o recorte del relieve.
5. **Alcance funcional:** mantener las funcionalidades actuales o aprobar los filtros de Fuentes, el estado de URL del mapa y la carga diferida de la maqueta en móvil.
6. **Maqueta:** conservar el GLB actual o reexportar el color del terreno para alinearlo con la rampa 2D.

---

## 11. Cómo revisar los mockups

```bash
cd /home/jamaya/Projects/rio-piura-atlas
python3 -m http.server 4330
# abrir http://127.0.0.1:4330/design-proposal/index.html
```

- `home.html`: portada responsive.
- `mapa.html?capa=inundacion`: mapa con capa y ficha; probar el botón «Capas» en móvil.
- `escenarios.html`: línea de tiempo y lámina 2017.
- `fuentes.html`: catálogo con filtros; probar un ancho de 390 px.
- `maqueta.html`: espécimen 3D.
- `sistema.html`: tokens, tipos, símbolos y componentes.

Las capturas en `design-proposal/captures/` permiten revisar sin servidor. El mapa vivo requiere el servidor porque carga los GeoJSON reales.
