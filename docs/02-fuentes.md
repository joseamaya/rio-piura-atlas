# 02 · Catálogo de fuentes

Registro humano de las fuentes. La versión legible por máquina está en
[`../data/sources.yml`](../data/sources.yml).

Estados: ✅ disponible · ⚠️ disponible con reservas · ❗ hay que solicitarlo · ❓ por verificar

Desde la fase 2, `data/sources.yml` distingue **disponibilidad** (`localizada`,
`descargable`, `procesada`, `validada`, `documental`, `pendiente`, `descartada`) y
**tipo de evidencia**. Esta tabla es un resumen humano y puede agrupar estados; la
ficha completa está en el catálogo y en [`11-auditoria-fuentes-ampliacion.md`](11-auditoria-fuentes-ampliacion.md).

## Límites, relieve y red

| Fuente | Uso | Escala | Estado | Licencia |
|---|---|---|---|---|
| ANA — Unidades Hidrográficas Pfafstetter (R.M. 033-2008-AG) | cuenca y subcuencas | 1:100 000 | ✅ | dato público |
| Río Piura Atlas — Bajo Piura derivado | resto de la cuenca ANA; no es subcuenca oficial | 1:100 000 | ✅ derivado | CC BY 4.0 |
| Copernicus DEM GLO-30 | relieve, sombreado, cortes | 30 m (producto); malla ~140 m | ✅ | libre con atribución |
| HydroRIVERS v1.0 (archivos v10), producto de HydroSHEDS | red hídrica, orden, área aportante | ~500 m | ✅ | CC BY 4.0 |
| IGN — cartas nacionales | contraste y toponimia | 1:100 000 / 1:25 000 | ⚠️ | uso con atribución |
| OpenStreetMap — ciudades | toponimia y ubicación aproximada | punto | ✅ | ODbL 1.0 |

## Agua

| Fuente | Uso | Estado |
|---|---|---|
| OpenStreetMap — cuerpos de agua | lagunas y salinas | ✅ |
| SENAMHI — estaciones del valle (Puente Sánchez Cerro, Tambogrande, Chulucanas, entre otras) | caudales y niveles históricos | ❗ series históricas; el monitoreo PHISIS es actual |
| SENAMHI — PISCOp v3.0 | precipitación grillada diaria/mensual 1981–2025, 0,1° | ⚠️ descargable; licencia por aclarar |
| PECHP — operación de Poechos y trasvase | caudales derivados, reglas de operación | ❗ |
| PECHP — fichas públicas de Poechos y canal | dique, longitud y capacidad del canal | ✅ documental |
| PECHP — reporte hidrometeorológico diario | caudales y precipitación observados 2015–2026 | ⚠️ descargable; términos por confirmar |
| PECHP / ANA / MIDAGRI / PSI — inspección de 2026 | registro de la cuenca baja; sin geometría | ✅ documental |
| PECHP — topobatimetría de 2026 | levantamiento anunciado, datos no publicados | ❗ pendiente |
| ANA — inventario de infraestructura hidráulica | diques, bocatomas, canal Daniel Escobar | ❗ |
| Río Piura Atlas — Poechos y canal Daniel Escobar | trazado esquemático para orientar; no es levantamiento | ⚠️ interpretación |

## Inundaciones y riesgo

| Fuente | Uso | Estado |
|---|---|---|
| CENEPRED / SIGRID | escenarios de riesgo, mapas de peligro | ⚠️ |
| ENFEN | informes técnicos 1982-83, 1997-98, 2017; edición concreta pendiente | ❓ |
| Copernicus EMS — activación EMSR199 (AOI10 y AOI11) | geometría oficial de la inundación de marzo 2017; unión de fechas | ✅ con atribución |
| UNOSAT / Copernicus EMS | contraste visual de la inundación de marzo 2017 | ❓ |
| Sentinel-1 y 2 (Copernicus) | contraste de la mancha 2017; no se usa para la geometría publicada | ✅ descarga libre |
| INDECI / OEA / PNUD — Mapa de peligros de Piura y Castilla (2009) | categorías de inundación, drenaje, cuencas ciegas, 1983/1998 | ✅ documental; sin shapefiles |
| ANA — Tratamiento del cauce del río Piura (2014) | tramos críticos, erosión, sedimentación, propuestas | ✅ documental; CC BY-NC-ND |
| ANA / ARCC — Plan de Control de Inundaciones Río Piura (2018) | obras y diagnóstico | ❗ |

## Estudios de referencia

| Fuente | Uso | Estado |
|---|---|---|
| INGEMMET — Estudio geodinámico de la cuenca del río Piura (1994) | geomorfología, procesos | ✅ documental |
| INGEMMET — Carta Geológica Nacional 1:100 000 | geología superficial; PDF/JPG, no vector | ⚠️ localizada; no es vector |
| INGEMMET — Geología Integrada 1:100 000 | geología/geomorfología; MapServer vectorial; 576 polígonos en la cuenca | ⚠️ evaluada; licencia no comercial; no publicar |
| INGEMMET — GEOCATMIN Peligros Geológicos | inventario de peligros geológicos; no es susceptibilidad a inundaciones | ⚠️ localizada |
| Lund University — Ladewig Piscoya (2024) | transporte de sedimentos con HEC-RAS; Virrilá vs Sechura | ✅ documental; modelamiento |
| Asociación Perú Verde / IUCN — expedición de 2002 | rutas San Pedro/Virrilá/Reventazón; Tres Bocas; sedimentación | ✅ documental; GPS en anexo |
| SIAR Piura — Apéndice D, hidrología (2000) | cuenca, pendientes, caudales de 1983/1998 | ✅ |
| SIAR Piura — evaluación hidrológica y erosión-sedimentación | fechas y niveles de 1983/1998; discrepancia 12/16 mar | ✅ |
| SIAR Piura — cambios de la embocadura | 1891 y 1983; diapositivas 5, 7 y 8 | ✅ |
| PUCP — tesis de modelamiento hidrológico | referencia secundaria para 1891; PDF no abierto (403/Anubis) | ❓ por verificar |
| IMARPE — Escudero & Xu (2019) | formación y área de la laguna La Niña 1998/2017 | ✅ |
| Andina — desborde de La Niña 2023 | reactivación y afectación de la carretera | ✅ prensa |
| NASA Earth Observatory — La Niña 2023 | observación Landsat 9 | ✅ |
| Universidad Nacional de Piura — tesis de hidrología e hidráulica | métodos y validación | ⚠️ |
| Universidad de Piura — estudios de agua e inundaciones | contraste técnico; documento pendiente | ❓ |
| SERNANP — Reserva Nacional Illescas | referencia de lugar, no límite | ✅ |
| Banco Mundial / GFDRR | análisis de la inundación de 2017 | ❓ |

## Criterios para aceptar una fuente

1. Tiene autor o institución identificable.
2. Tiene fecha o se declara explícitamente que no se conoce.
3. Declara escala o resolución.
4. Su licencia permite reutilizar el dato o, al menos, citarlo.
5. Se puede verificar por un tercero.
6. Declara su nivel de certidumbre: medido, derivado, documentado, interpretación o por verificar.

Si falla cualquiera de los cinco, la capa no entra al atlas: como mucho, se menciona
en una nota.

## Fase 2.1–2.2 — fuentes nuevas y auditoría

| Fuente | Uso | Estado | Licencia |
|---|---|---|---|
| SENAMHI — API histórica por estación | precipitación diaria y temperatura con cobertura variable; 20 estaciones de Piura; envolvente 1961–2015; 7 sin temperatura | ✅ descargable; publicación bloqueada | uso con atribución; sin licencia abierta |
| INGEMMET — Geología Integrada 1:100 000 | geología vectorial; 576 polígonos en la cuenca; 12 hojas | ⚠️ evaluada; publicación bloqueada | Licencia para Uso No Comercial de GEOCATMIN |
| INGEMMET — Geomorfología vectorial | geomorfología regional; 573 polígonos en la cuenca | ⚠️ evaluada; escala contradictoria | Licencia para Uso No Comercial de GEOCATMIN |
| INGEMMET — susceptibilidad a inundación fluvial | 16.341 polígonos en la cuenca; GRIDCODE 2/3/4; leyenda incompleta | ⚠️ evaluada; publicación bloqueada | Licencia para Uso No Comercial de GEOCATMIN |
| Gobierno Regional de Piura / MINAM — ZEE Piura | geología, geomorfología, peligro de inundación (78) y vulnerabilidad (19) | ⚠️ evaluada; semántica y licencia pendientes | servicio público; sin licencia declarada |
| SIGRID — Sullana 1983/1998 | mapas de áreas de inundación | ✅ documental | documento público; citar |
| SIGRID — Cura Mori 1998 | 34 mapas JPG de peligro, riesgo e infraestructura | ✅ documental | documento público; citar |
| PECHP — batimetría de Poechos | batimetría del reservorio, no del cauce | ❗ pendiente | datos no publicados |
