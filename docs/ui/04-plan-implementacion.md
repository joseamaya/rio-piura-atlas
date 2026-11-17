# 04 · Plan de implementación

**Fase:** UI-01 · rediseño visual  
**Base:** Río Piura Atlas 0.2.3  
**Estrategia:** trabajar en una rama aislada, sin publicar en `main`, con entregas por etapa y validación visual en cada una. No se migra de framework ni se añaden dependencias de producción.

**Estado:** fases 0–5 completadas en el árbol de trabajo: propuesta, fundamentos + portada, mapa, páginas editoriales (Escenarios y Fuentes) y maqueta 3D. La fase 6 queda para la revisión final, la publicación por etapas y la prueba manual con personas.

---

## 1. Restricciones

- No cambiar datos, geometrías, cifras, textos científicos ni el ETL en esta fase.
- No añadir dependencias de runtime. Las fuentes y las imágenes son activos, no librerías.
- No publicar en GitHub Pages ni crear releases hasta la aprobación final.
- No romper las rutas, los anclas de fuentes ni los enlaces `?capa=inundacion`/`?capa=obras`.
- Mantener el presupuesto de rendimiento y la carga diferida de la inundación y el DEM.
- Mantener el aviso «No es un sistema de alerta ni un pronóstico» y la licencia CC BY 4.0.

---

## 2. Mapa de componentes

| Actual | Futuro | Acción |
|---|---|---|
| `Base.astro` | `layouts/Base.astro` + `SiteHeader.astro` + `SiteFooter.astro` + `SeoHead.astro` | Separar |
| `index.astro` | `pages/index.astro` + `Hero.astro`, `DataStrip.astro`, `EntryGrid.astro`, `Readings.astro`, `MethodBand.astro` | Reescribir |
| `mapa.astro` | `pages/mapa.astro` + `map/LayerPanel.astro`, `MapLegend.astro`, `FeaturePanel.astro`, `ProfilePanel.astro`, `MapControls.astro`, `MapTitle.astro` | Dividir |
| `maqueta.astro` | `pages/maqueta.astro` + `three/SceneShell.astro`, `ScenePanel.astro`, `SceneControls.astro` | Dividir |
| `escenarios.astro` | `pages/escenarios.astro` + `editorial/Timeline.astro`, `EventChapter.astro`, `FloodPlate.astro`, `EvidenceTable.astro` | Dividir |
| `fuentes.astro` | `pages/fuentes.astro` + `sources/SourceIndex.astro`, `SourceRecord.astro`, `SourceFilters.astro`, `StatusKey.astro` | Dividir |
| `global.css` | `styles/tokens.css`, `base.css`, `layout.css`, `components.css`, `pages/*.css`, `map.css` | Separar por capas |
| Scripts inline del mapa | `scripts/map/init.ts`, `layers.ts`, `interactions.ts`, `profile.ts`, `format.ts` | Extraer |
| Script inline de la maqueta | `scripts/scene.ts` | Extraer |
| Script de fuentes | `scripts/sources-filter.ts` | Extraer (si se aprueba) |

**No se sustituyen** MapLibre ni Three.js. **No se añade** un framework CSS, un sistema de iconos ni una librería de componentes.

---

## 3. Orden de trabajo

### Fase 0 · Cierre de la propuesta (esta entrega)

- `docs/ui/01-auditoria-visual.md`
- `docs/ui/02-direccion-de-arte.md`
- `docs/ui/03-propuesta-redisenio.md`
- `docs/ui/04-plan-implementacion.md`
- `design-proposal/` con mockups, capturas y sistema
- Evidencia del estado actual en `docs/ui/evidencia/`

**Criterio de aceptación:** propuesta revisable; `git status` sin cambios en `web/`; los mockups abren con servidor local y las capturas se ven sin servidor.

---

### Fase 1 · Fundamentos

**Trabajo:**
- Tokens en `web/src/styles/tokens.css`.
- Fuentes autoalojadas, subset y `@font-face`.
- `SiteHeader`, `SiteFooter`, `SkipLink`, `Button`, `StatusMark`, `DataFigure`, `Note`, `SourceLine`.
- Escala tipográfica, prosa 68ch, tablas base.
- Estilos de foco, `prefers-reduced-motion` y `prefers-contrast`.

**Archivos:** `web/src/layouts/Base.astro`, `web/src/components/*`, `web/src/styles/*`, `web/src/fonts/*`.

**Riesgo:** CLS por fuentes; mitigar con `font-display: swap`, métricas de fallback y precarga solo de Newsreader.

**Criterio:** las cinco páginas comparten cabecera, pie y tipografía; `npm run build` y `check:a11y` en verde; sin scroll horizontal.

**Tamaño:** S/M.

---

### Fase 2 · Mapa

Es la fase de mayor riesgo y la que define el sistema cartográfico.

**Trabajo:**
1. Layout de mapa a pantalla completa con panel en el layout (no flotante) y colapso a riel.
2. Nueva simbología: agua, inundación con trama, cuenca, subcuencas, obras, cortes.
3. Leyenda contextual con los símbolos reales.
4. Ficha lateral con cierre, resaltado y contenido por tipo.
5. Perfil de corte como lámina inferior.
6. Móvil: hoja de capas, ficha peek/sheet, controles fuera del panel, encuadre Bajo Piura y «ver toda la cuenca».
7. Regla de longitudes y colofón del mapa.
8. Colisiones de rótulos y jerarquía 3.
9. Patrón de inundación con `map.addImage` (sin dependencias).
10. Estados de carga, error, vacío y selección.

**Archivos:** `web/src/pages/mapa.astro`, `web/src/components/map/*`, `web/src/scripts/map/*`, `web/src/styles/map.css`.

**Riesgos:**
- Los tests E2E dependen de IDs (`#map`, `#ficha`, `#draw-corte`, `#corte-panel`, `.map-panel`). Conservarlos o actualizar los tests en el mismo commit.
- `fitBounds` y padding: probar 1440, 1024, 768 y 390; no usar el panel como padding en móvil.
- Rótulos HTML: la colisión se resuelve en cliente; probar zoom 6–12.
- Patrón: verificar en Chrome/Firefox/Safari y a 2× DPR.
- Foco de hojas: atrapar y devolver; no dejar el foco detrás del overlay.

**Criterio:** el mapa ocupa el espacio principal; la ficha solo aparece al seleccionar; la inundación se distingue del agua; en móvil no hay franjas vacías ni controles tapados; capas, ficha, cortes y deep links funcionan; `check:a11y` y E2E en verde.

**Tamaño:** L.

---

### Fase 3 · Inicio

**Trabajo:**
- Portada con lámina 3D, titular, entradilla, CTA y metadatos.
- Franja de cifras con fuente.
- Índice asimétrico con recortes reales del mapa, la maqueta y la inundación.
- Qué es / qué no es.
- Tres lecturas con mini mapa, barras y esquema de trasvase.
- Método y fuentes con contador real y ficha de ejemplo.
- Pie con colofón.

**Archivos:** `web/src/pages/index.astro`, `web/src/components/home/*`, `web/src/styles/home.css`, `web/public/img/*`.

**Criterio:** la portada comunica el atlas antes de hacer scroll y lleva al mapa en un clic; la lámina es un recurso real con pie y fuente; no se inventan cifras.

**Tamaño:** M.

---

### Fase 4 · Escenarios y Fuentes

**Trabajo:**
- Línea de tiempo sticky/chips y capítulos.
- Lámina 2017, cifras y tabla plegable.
- Matriz de evidencia.
- 2023 como capítulo.
- Registros de fuentes con índice, filtros y búsqueda (si se aprueba).
- Clave de certeza y estados unificada.
- Alternativa móvil de tablas.

**Archivos:** `web/src/pages/escenarios.astro`, `web/src/pages/fuentes.astro`, `web/src/components/editorial/*`, `web/src/components/sources/*`, `web/src/styles/editorial.css`.

**Criterio:** no hay scroll horizontal en 390 px; cada fuente conserva su ancla; la página declara lo que no se puede comparar; no se introducen categorías que el proyecto no define.

**Tamaño:** M/L.

---

### Fase 5 · Maqueta 3D

**Trabajo:**
- Póster y progreso de carga.
- Panel de margen, leyenda hipsométrica y ficha técnica.
- Controles agrupados y fullscreen.
- LOD de rótulos.
- Móvil: modelo primero, panel después, hoja de leyenda.
- Evaluar `prefers-reduced-data` o «tocar para cargar» en móvil (decisión aparte).

**Archivos:** `web/src/pages/maqueta.astro`, `web/src/components/three/*`, `web/src/scripts/scene.ts`, `web/src/styles/maqueta.css`.

**Criterio:** el modelo es legible en 390 px; la carga se entiende; las advertencias ×7/altitud/agua narrativa son visibles; no hay regresión >5 % en el peso; el teclado y el reset siguen funcionando.

**Tamaño:** M.

---

### Fase 6 · QA, rendimiento y documentación

**Trabajo:**
- `check_data.py`, pruebas Python, `npm run verify`.
- Capturas finales a 1440, 1024 y 390.
- Prueba de teclado real y revisión con axe en estados dinámicos.
- Simulación de daltonismo y revisión de contraste.
- Build con `BASE_PATH=/rio-piura-atlas`.
- Actualizar `web/README.md`, `docs/ui/*` y capturas.
- Revisión de contenido científico contra `data/sources.yml`.

**Criterio:** todo en verde; capturas reales; presupuesto cumplido; sin cambios de datos; documentación actualizada.

**Tamaño:** M.

---

## 4. Dependencias y activos

| Activo | Origen | Licencia | Estado |
|---|---|---|---|
| Newsreader | Production Type / Google Fonts | OFL 1.1 | Incluida en `design-proposal/assets/fonts/` |
| Archivo | Omnibus-Type / Google Fonts | OFL 1.1 | Incluida |
| Render 3D | GLB existente `web/public/models/piura.glb` | proyecto | Generado para el mockup |
| Relieve propuesto | DEM existente + `design-proposal/tools/build_relief.py` | Copernicus DEM / proyecto | Solo cambio de paleta |
| Recorte del mapa | MapLibre + GeoJSON reales | ANA, Copernicus, HydroRIVERS, OSM | Captura del prototipo |
| Figura 2017 | `flood_2017.geojson` real | Copernicus EMSR199 | Captura del prototipo |
| Mini mapa | GeoJSON reales | ANA / HydroRIVERS / OSM | SVG editorial |

**No se añaden** paquetes npm. Las fuentes se importan desde CSS para que Vite resuelva `BASE_PATH`; las imágenes pasan por `withBase` o por imports de Vite.

---

## 5. Riesgos técnicos y mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Regresión de tests E2E por cambio de DOM | Alta | Medio | Conservar IDs clave; actualizar tests en el mismo commit; correr `npm run test:e2e` en cada fase |
| Encuadre móvil incorrecto | Alta | Alto | Probar 390/360/768; separar bbox móvil; botón «ver toda la cuenca» |
| Rótulos solapados | Media | Medio | Colisión en cliente + jerarquía + ocultar fuera del viewport |
| Patrón de inundación no renderiza en Safari | Media | Medio | Probar `ImageData` y fallback a relleno + línea; no depender solo de la trama |
| Fuentes: CLS o base path | Media | Medio | Subset, `swap`, métricas de fallback, import CSS, probar `BASE_PATH` |
| Relieve regenerado cambia el hash visual | Media | Bajo | Cambio solo de paleta; conservar geometría y `relieve_info.json`; comparar |
| Foco atrapado en hojas | Media | Alto | Implementar focus trap, `Escape`, retorno al disparador; probar teclado |
| `role="application"` en el mapa | Media | Medio | Cambiar a `region` + instrucciones + lista de capas |
| Filtros de fuentes añaden JS | Baja | Bajo | 30 registros; JS vanilla; sin dependencia; si se aprueba |
| Pérdida de carga diferida | Baja | Alto | Mantener `loadFlood()` y `loadGrid()` bajo demanda; medir |
| Deriva de alcance | Media | Medio | Aprobar las decisiones abiertas antes de la fase 2 |

---

## 6. Presupuesto de rendimiento

| Página | Inicial actual | Objetivo | Techo |
|---|---:|---:|---:|
| Inicio | ~10 KB | ≤500 KB críticos (hero + fuentes); ≤1,0 MB total | 1,2 MB |
| Mapa | ~1,5 MB sin comprimir; ~1,1 MB comprimidos con fuentes | ≤1,2 MB iniciales comprimidos | 1,4 MB |
| Escenarios | ~131 KB | ≤500 KB | 700 KB |
| Fuentes | ~35 KB | ≤300 KB | 400 KB |
| Maqueta | ~2,4 MB | Sin regresión >5 %; póster antes del GLB | 2,6 MB |

Medidas: Lighthouse/DevTools en 4G simulada, `transferSize` de recursos, LCP y CLS. Los valores «críticos» excluyen imágenes bajo el pliegue cargadas con `loading="lazy"`. No se promete un LCP de laboratorio como si fuera campo.

---

## 7. Validación

### Comandos

```bash
python3 etl/check_data.py
python3 -m unittest discover -s etl/tests -v
cd web
npm run check
npm run build
npm run check:links
npm run check:a11y
npm run test:e2e
SITE_URL=https://joseamaya.github.io BASE_PATH=/rio-piura-atlas npm run build
BASE_PATH=/rio-piura-atlas node scripts/serve-dist.mjs
```

### Matriz visual

| Página | 1440 | 1024 | 768 | 390 |
|---|---|---|---|---|
| Inicio | ✓ | ✓ | ✓ | ✓ |
| Mapa | ✓ | ✓ | ✓ | ✓ |
| Escenarios | ✓ | ✓ | ✓ | ✓ |
| Fuentes | ✓ | ✓ | ✓ | ✓ |
| Maqueta | ✓ | ✓ | ✓ | ✓ |
| Sistema | ✓ | ✓ | — | ✓ |

### Pruebas manuales

- Teclado: tabular por cabecera, capas, ficha, perfil, hojas y maqueta; `Escape`; foco devuelto.
- Lector de pantalla: al menos VoiceOver o NVDA en inicio, mapa y fuentes.
- Contraste: tokens y estados; comprobar foco sobre mapa y papel.
- Daltonismo: deuteranopia/protanopia simulada; la inundación debe seguir distinguiéndose por trama.
- Impresión: portada, escenarios y fuentes; evitar cortes de tabla y figuras.
- Red lenta: mapa y maqueta; comprobar estados de carga.

---

## 8. Criterios de aceptación globales

1. **Identidad:** las cinco páginas comparten tokens, tipografía, cabecera, pie y lenguaje de figuras.
2. **Mapa protagonista:** en escritorio, el mapa ocupa el espacio principal; en móvil, la pantalla completa.
3. **Legibilidad cartográfica:** agua, inundación, cuenca, subcuencas y obras se distinguen sin depender solo del color.
4. **Rigor:** no se añade ninguna cifra o geometría sin fuente; las ausencias se declaran.
5. **Móvil:** sin scroll horizontal; hojas utilizables; objetivos de 44 px; sin controles tapados.
6. **Accesibilidad:** axe 0; foco visible; jerarquía de encabezados; alternativa textual del mapa; hojas con foco gestionado.
7. **Rendimiento:** presupuesto cumplido; carga diferida intacta.
8. **Compatibilidad:** build con `BASE_PATH`; enlaces y anclas sin roturas.
9. **Pruebas:** `check_data.py`, Python, `check`, `build`, `check:links`, `check:a11y` y `test:e2e` en verde.
10. **Evidencia:** capturas reales de las páginas afectadas y revisión visual contra los mockups.

---

## 9. Entrega y rollback

- Rama de trabajo: `design/ui-01` (no `main`).
- Un commit lógico por fase, en imperativo y en español.
- No se publica en GitHub Pages hasta la aprobación.
- Si una fase no cumple, se revierte el commit de esa fase; las anteriores quedan.
- Al cerrar, se actualizan `web/README.md`, `docs/ui/*` y las capturas; se propone el merge, no se ejecuta sin aprobación.

---

## 10. Decisiones que bloquean el inicio de la fase 2

1. Aprobar «Lámina y margen».
2. Aprobar las fuentes autoalojadas.
3. Decidir si se regenera el relieve y la figura de 2017 solo en estilo.
4. Decidir si se incluyen filtros de Fuentes, estado de URL del mapa y carga diferida de la maqueta.
5. Decidir si la maqueta conserva el GLB actual o se reexporta el color del terreno.

Sin esas decisiones se puede avanzar en fundamentos y mapa, pero no cerrar la dirección visual ni el presupuesto final.
