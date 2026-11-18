# 13 · Plan de integración geoespacial

Actualizado: 2026-11-18.

Este documento decide qué capas pueden incorporarse, cuáles requieren
procesamiento y cuáles no deben incorporarse todavía. La regla es anterior a la
tecnología: **si la escala, la cobertura, la fecha o la licencia no se pueden
justificar, la capa no entra**.

## 1. Principios

1. Primero la fuente; después la capa. No se dibuja para llenar un vacío.
2. Una capa publicada debe ser reproducible desde `data/raw/` o desde una fuente
   descargable, con transformaciones registradas.
3. El sitio es estático: no se agregan dependencias de servicios externos en
   runtime si eso rompe la reproducibilidad.
4. Lo que es interpretación se marca con estilo propio y aviso visible.
5. No se mezclan categorías distintas de inundación en una sola capa.
6. No se convierte una propuesta en obra ejecutada.
7. No se confunde susceptibilidad geológica con probabilidad hidrológica.

## 2. Evaluación de capas candidatas

| Candidata | Fuente | ¿Hay geometría? | ¿Escala compatible? | ¿Licencia? | Decisión |
|---|---|---|---|---|---|
| Precipitación por subcuenca | PISCOp v3.0 | No; es una serie derivada | 0,1° (~10 km); suficiente para contexto, no para detalle | **En disputa** (GPL 3.0+ vs CC BY 4.0) | **Diferir**; diseñar ETL, no publicar |
| Precipitación por estación | SENAMHI API histórica | No; serie puntual | 20 estaciones de Piura; envolvente 1961–2015; 7 sin temperatura | Términos por confirmar | **ETL validado localmente**; no publicar |
| Precipitación como ráster | PISCOp v3.0 | Sí, NetCDF | 0,1°; no resuelve el valle | En disputa | **No** publicar como capa decorativa |
| Geología superficial | INGEMMET Geología Integrada 1:100 000 | **Sí, MapServer vectorial** | 1:100 000; 576 polígonos en la cuenca; 12 hojas | Licencia no comercial | **Evaluada**; no publicar bajo CC BY 4.0 |
| Geomorfología / depósitos aluviales | INGEMMET Geomorfología | **Sí, MapServer vectorial** | 573 polígonos en la cuenca; escala contradictoria | Licencia no comercial | **Evaluada**; no publicar |
| Susceptibilidad a inundaciones | INGEMMET + ZEE Piura | **Sí, vector** | INGEMMET 16.341 polígonos; ZEE 78/19 | INGEMMET 1:1 000 000; ZEE 1:100 000; licencias pendientes | **Evaluada**; no publicar |
| Ejes de canales y diques | ANA / PECHP | No hay geometría pública | — | — | **No**; solicitar |
| Bocatomas y defensas | ANA / PECHP | No hay geometría pública | — | — | **No**; solicitar |
| Ruta documentada 2002 | Perú Verde / IUCN | 178 puntos GPS en anexo | Track de navegación, no eje | Documento público; sin licencia explícita | **Diferir** a fase 3; no dibujar ahora |
| Registros de eventos | PECHP 2026, Lund 2024 | No hay geometría | — | Documental | **Sí**, como fichas en `/escenarios` |
| Inundación 1983/1998 | ANA / INDECI / SIGRID | Mapas PDF/JPG; sin vector de cuenca | Local: Sullana y Cura Mori | Documento público | **Documental**; no digitalizar |
| Inundación 2017 | Copernicus EMSR199 | Sí, vector oficial | 1:76 000–1:80 000 | Reutilización con atribución | **Ya incorporada** |

## 3. Prioridad 1 — Precipitación y contexto hidrológico

### 3.1 Qué se puede hacer

Una serie de precipitación media o acumulada por subcuenca, no un ráster
decorativo. La serie permite comparar:

- cuenca alta, media y Bajo Piura;
- fechas de máximos de precipitación;
- caudales observados del PECHP para 2015–2026;
- cifras históricas de 1983/1998 de SIAR/INDECI, con las salvedades del caso.

Hay dos vías complementarias:

1. **SENAMHI histórico por estación** (fase 2.1–2.2): 20 estaciones de Piura,
   precipitación diaria y temperatura con cobertura variable; la envolvente es
   1961–2015, pero siete estaciones no tienen temperatura y tres la tienen
   parcial. Es la vía inmediata para 1983/1998; no cubre 2017/2023 y no incluye
   caudales.
2. **PISCOp v3.0**: grilla 0,1° 1981–2025; permite una serie por subcuenca, pero
   su licencia sigue en disputa y el archivo diario pesa 1,5 GB.

### 3.2 ETL de SENAMHI histórico (fases 2.1–2.2)

- `etl/download_senamhi_historico.py`: descarga catálogo y series por estación en
  `data/raw/senamhi/`, con bytes crudos y SHA-256.
- `etl/build_senamhi_historico.py`: aplana a
  `data/processed/senamhi/estaciones_piura.csv`, `cobertura_estaciones.csv`,
  `catalogo_estaciones.csv`, `inventario_estaciones.csv`,
  `huecos_estaciones.csv` y `metadata.json`.
- No interpola, no rellena y conserva los nulos. Añade banderas de calidad sin
  eliminar valores.
- La tabla no se publica en `web/public/` hasta confirmar términos.
- Pruebas: 20 estaciones seleccionadas, fechas válidas, sin duplicados, nulos
  conservados, banderas de precipitación negativa/extremos/temperatura, cobertura
  y huecos, clasificación dentro/fuera de la cuenca y CSV con unidades.

### 3.3 Diseño del ETL de PISCO (si se autoriza la licencia)

1. `etl/download_pisco.py`
   - Descarga el NetCDF mensual (54 MB) y, si se autoriza, el diario (1,5 GB).
   - Verifica tamaño, fecha y hash.
   - Guarda en `data/raw/pisco/` (ignorado por Git).
2. `etl/build_pisco.py`
   - Abre el NetCDF con `xarray`/`netCDF4` (dependencia solo de ETL).
   - Recorta al bounding box de la cuenca.
   - Calcula la media por subcuenca con una regla explícita:
     - opción A: celdas cuyo centro cae dentro del polígono;
     - opción B: peso por área de intersección celda–polígono.
   - Declara cuántas celdas usa cada subcuenca.
   - Conserva la resolución original; no interpola.
   - Genera `web/public/data/pisco_subcuencas.csv` y un JSON de metadatos.
3. Pruebas
   - Cobertura temporal 1981–2025.
   - Sin `NaN` en la serie publicada.
   - Identificadores de subcuenca correctos.
   - Suma de pesos = 1 por subcuenca.
   - Valores de control para 1983, 1998 y 2017.
   - Comparación con caudales del PECHP donde exista solapamiento.
4. Documentación
   - Método, resolución, número de celdas, limitaciones y licencia.
   - Aviso: «estimación grillada, no medición directa».

### 3.4 Compuerta de licencia

El artículo es CC BY 4.0, pero el conjunto de datos en Figshare declara GPL 3.0+.
Antes de publicar una serie derivada se debe:

- obtener confirmación escrita de SENAMHI sobre la licencia de los datos; o
- aceptar explícitamente una licencia GPL 3.0+ para la serie derivada, con aviso
  separado; o
- no publicar la serie y dejar solo la ficha y el método.

La recomendación es la primera. Mientras no se resuelva, el ETL puede existir en
una rama de trabajo, pero no se publica el resultado.

## 4. Prioridad 2 — Geología y geomorfología

### 4.1 Qué existe

- Carta Geológica Nacional 1:100 000: 501 hojas, PDF/JPG, 1960–1999.
- **Geología Integrada 1:100 000:** MapServer vectorial con 7 capas; **576
  polígonos que intersectan la cuenca ANA**, en 12 hojas (10b, 10c, 10d, 11a,
  11b, 11c, 11d, 11e, 12b, 12c, 12d y 12e). La descripción oficial enumera 27
  hojas y no coincide con la capa; 13d no intersecta la cuenca.
- **Geomorfología:** MapServer vectorial; **573 polígonos en la cuenca**; el
  metadato declara 1:3 000 000, el abstract 1:100 000 de trabajo y 1:250 000 de
  presentación.
- **Susceptibilidad a inundación fluvial:** MapServer vectorial; **16.341
  polígonos en la cuenca**, con GRIDCODE 2/3/4. La leyenda oficial 2018 tiene
  cuatro clases; la capa vectorial no contiene «Muy bajo o nulo». Es
  1:1 000 000, no una probabilidad hidrológica.
- **Gobierno Regional de Piura / MINAM ZEE Piura:** geología (1.155 polígonos),
  geomorfología (70), peligro de inundación (78) y vulnerabilidad (19). La
  Memoria Final 2012, de 255 páginas, fija escala 1:100 000 y metodología; el
  servicio no declara fecha/escala/licencia y el campo `Nivel_Vuln` es ambiguo.
- **GEOCATMIN Peligros Geológicos:** **230 puntos** en la cuenca (capa 0), más
  63 «otros», 12 zonas críticas y 37 polígonos de cartografía. Es un inventario
  heterogéneo, no una susceptibilidad.
- Estudio geodinámico de la cuenca del río Piura (1994), ya catalogado como
  documento.

### 4.2 Qué falta

- Confirmar la licencia aplicable a WFS/WMTS de INGEMMET y su compatibilidad con
  CC BY 4.0; la licencia de descarga es no comercial.
- Resolver la escala efectiva de geomorfología y la leyenda vectorial incompleta
  de susceptibilidad (tres clases frente a cuatro).
- Confirmar con el Gobierno Regional de Piura / MINAM el significado de
  `Nivel_Vuln` y la relación entre la Memoria 2012 y las capas del Geoservidor.
- Confirmar la fecha de los registros de peligros geológicos y su heterogeneidad.
- Decidir si la geología se publica como capa no comercial separada o queda como
  documento.

### 4.3 Decisión

No incorporar capas en esta fase. Las tres fuentes quedan con
`publicacion: bloqueada`. Si se autorizan, priorizar:

1. geología superficial;
2. geomorfología;
3. depósitos aluviales;
4. llanuras de inundación;
5. zonas de erosión y procesos geodinámicos.

No usar la susceptibilidad geológica o de INGEMMET como probabilidad hidrológica.
No usar capas de Ancash o Apurímac como sustituto. No mezclar la susceptibilidad
con la mancha observada de 2017.

## 5. Prioridad 3 — Infraestructura hidráulica

### 5.1 Qué existe

- Poechos: punto en el dique documentado por el PECHP; no hay geometría del vaso.
- Canal Daniel Escobar: recta de referencia; no hay eje oficial.
- Diques, bocatomas, drenes y canal Chutuque: menciones documentales, sin
  geometría pública.
- Inspección de 2026: registro de campo sin coordenadas.
- Topobatimetría de 2026: anunciada, sin datos publicados.
- Cura Mori 1998: mapas JPG de riesgo de canales de riego e infraestructura
  agrícola; son imágenes, no ejes oficiales.
- Poechos: notas de batimetría del reservorio, no del cauce del río.

### 5.2 Decisión

Mantener las obras esquemáticas actuales. No dibujar canales, diques ni bocatomas
sin geometría oficial. Distinguir siempre:

- geometría oficial;
- geometría derivada;
- ubicación aproximada;
- referencia documental;
- obra proyectada;
- obra ejecutada;
- estado desconocido.

Solicitar a ANA/PECHP los ejes y polígonos con metadatos, escala y fecha de
levantamiento.

## 6. Prioridad 4 — Registros de eventos y rutas históricas

### 6.1 Modelo de datos propuesto

Un registro documental podría tener:

```yaml
- id: registro-2002-expedicion
  tipo: expedicion
  fecha: "2002-06-22/24"
  sector: "Puente Independencia–Puente Virrilá"
  ruta: "San Pedro / Virrilá / Reventazón"
  condicion_hidrologica: "estiaje; 50–60 cm en tramos someros"
  fuente: peruverde-expedicion-2002
  evidencia_cartografica: "178 puntos GPS; mapas 1–2"
  geometria: null
  certeza: documentado
```

Este modelo permite representar cambios históricos sin mezclar situaciones
distintas. La geometría es opcional y, si existe, debe declarar método y
transformación.

### 6.2 Decisión

Implementar solo fichas documentales en `/escenarios`, sin geometría. La ruta de
2002 queda como candidata para fase 3, con reconstrucción explícita. Los mapas de
Sullana (1983/1998) y Cura Mori (1998) son evidencia documental; no se digitalizan
sin georreferenciación, escala y método.

## 7. Futuro módulo «El recorrido del agua: de la cuenca al mar»

### 7.1 Qué debería explicar

1. Aportes de la cuenca alta.
2. Concentración de caudales en la cuenca media.
3. Paso por Piura y Castilla.
4. Dinámica del Bajo Piura.
5. Lagunas y estuarios.
6. Rutas hacia el litoral.
7. Papel de la infraestructura y la sedimentación.

### 7.2 Qué datos faltan

- Serie oficial de caudales diarios de SENAMHI.
- Precipitación PISCO con licencia clara.
- Confirmación de términos de la API histórica por estación.
- Batimetría y secciones transversales del cauce.
- Ejes oficiales de canales, diques y bocatomas.
- Cartografía vectorial de 1983 y 1998.
- Informe hidrológico de 2023.
- Coordenadas de la inspección de 2026.
- Metadatos y licencia de INGEMMET y de la ZEE Piura.

### 7.3 Arquitectura posible

- Una página estática nueva, sin nuevas dependencias de producción.
- Un mapa pequeño con capas conmutables y un panel de texto.
- Fichas de fuente reutilizadas desde `sources.yml`.
- Estilo «Lámina y margen»; no un dashboard.
- No implementar hasta que los datos anteriores estén disponibles o se decida
  contar el relato solo con texto y fuentes.

## 8. Dependencias

- **Fase 2.1:** ninguna dependencia nueva; el ETL de SENAMHI usa `requests`, ya
  presente. No se agrega PISCO al sitio.
- **PISCO (si se autoriza):** `xarray` y `netCDF4` solo en `etl/requirements.txt`;
  no se envían al navegador.
- **Ruta 2002 (si se autoriza):** `pyproj` y `shapely`, ya presentes.
- **Geología (si se autoriza):** `pyproj`/`shapely` para reproyectar y recortar;
  no se agrega `geopandas` si no es necesario.

## 9. Complejidad y riesgos

| Tarea | Complejidad | Riesgo principal |
|---|---|---|
| Catálogo y documentación | Media | Duplicar fuentes o perder trazabilidad |
| SENAMHI histórico por estación | Baja | Términos de reutilización y temperatura incompleta |
| PISCO por subcuenca | Alta | Licencia y resolución insuficiente |
| Geología vectorial | Media | Licencia no comercial incompatible con CC BY 4.0 |
| Susceptibilidad de INGEMMET/ZEE | Alta | Escala, leyenda y semántica no resueltas |
| Infraestructura | Alta | No hay geometría oficial |
| Ruta 2002 | Media | Track de estación seca mal interpretado como cauce actual |
| Módulo «El recorrido del agua» | Alta | Mezclar rutas históricas y estado actual |

## 10. Puertas de decisión

1. **SENAMHI histórico:** sin confirmación de términos, la tabla queda en
   `data/processed/`, no en el sitio.
2. **PISCO:** sin licencia clara, no se publica.
3. **Geología:** la licencia es no comercial; sin una decisión de licencia
   compatible, no se publica bajo CC BY 4.0.
4. **Geomorfología:** sin escala efectiva resuelta, no se publica.
5. **Susceptibilidad INGEMMET:** sin leyenda completa y sin decisión de licencia,
   no se publica.
6. **ZEE Piura:** sin semántica de `Nivel_Vuln` y sin licencia, no se publica.
7. **Infraestructura:** sin ejes oficiales, no se dibuja.
8. **Ruta 2002:** sin método de reconstrucción y aviso, no se dibuja.
9. **Inundaciones 1983/1998:** sin cartografía vectorial, los mapas quedan como
   documentos.
10. **Módulo de la cuenca baja:** sin datos nuevos, solo documentación.

## 11. Recomendación de fase

Cerrar la fase 2.2 con la auditoría de SENAMHI, INGEMMET y ZEE, la documentación
de licencias y las pruebas. No agregar capas. Dejar PISCO, la ruta de 2002, la
geología vectorial, la susceptibilidad y la infraestructura como candidatas de
fase 3, cada una con su compuerta. La geología vectorial solo entra si INGEMMET
confirma la compatibilidad de su licencia no comercial con el atlas CC BY 4.0; la
ZEE sigue como referencia documental hasta que el autor confirme qué representa
`Nivel_Vuln`.

## 12. Decisión de apertura de fase 3 (2026-11-18)

Se abre la fase 3 con la **ruta de 2002** como primera candidata. No se empieza por
la geología porque su licencia sigue bloqueada.

Condiciones de la ruta de 2002:

- transformar los 178 puntos GPS de PSAD56 a WGS84 con método documentado;
- documentar el orden del track, la escala y la incertidumbre;
- dibujarla como **interpretación**, no como eje oficial ni como cauce;
- mostrar una nota visible y enlazar a la fuente;
- no publicar si la transformación o el orden no se pueden explicar.

La segunda candidata es la **coherencia cromática 3D/2D**. Quedan diferidas la
geología, la susceptibilidad, la infraestructura y las manchas de 1983/1998 hasta
que lleguen licencias o geometrías oficiales.
