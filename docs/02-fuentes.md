# 02 · Catálogo de fuentes

Registro humano de las fuentes. La versión legible por máquina está en
[`../data/sources.yml`](../data/sources.yml).

Estados: ✅ disponible · ⚠️ disponible con reservas · ❗ hay que solicitarlo · ❓ por verificar

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
| SENAMHI — estaciones del valle (Puente Sánchez Cerro, Tambogrande, Chulucanas, entre otras) | caudales y niveles históricos | ❗ |
| SENAMHI — PISCO v2.1 | precipitación grillada | ❗ registro |
| PECHP — operación de Poechos y trasvase | caudales derivados, reglas de operación | ❗ |
| PECHP — fichas públicas de Poechos y canal | dique, longitud y capacidad del canal | ✅ |
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
| ANA / ARCC — Plan de Control de Inundaciones Río Piura (2018) | obras y diagnóstico | ❗ |

## Estudios de referencia

| Fuente | Uso | Estado |
|---|---|---|
| INGEMMET — Estudio geodinámico de la cuenca del río Piura (1994) | geomorfología, procesos | ✅ |
| SIAR Piura — Apéndice D, hidrología (2000) | cuenca, pendientes, caudales de 1983/1998 | ✅ |
| SIAR Piura — evaluación hidrológica y erosión-sedimentación | fechas y niveles de 1983/1998; discrepancia 12/16 mar | ✅ |
| SIAR Piura — cambios de la embocadura | 1891 y 1983; diapositivas 5, 7 y 8 | ✅ |
| PUCP — tesis de modelamiento hidrológico | contraste para 1891 | ✅ |
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
