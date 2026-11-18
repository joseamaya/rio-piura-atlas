# 15 · Validación de las series históricas de SENAMHI

Actualizado: 2026-11-18.

Este documento audita la API histórica por estación de SENAMHI y el ETL del
atlas. **No publica las series**: la licencia de reutilización no está
confirmada. Las tablas completas viven en `data/raw/senamhi/` y
`data/processed/senamhi/`, ignorados por Git; aquí queda el resumen verificable y
los hashes de los archivos crudos.

## 1. Qué se consultó

- Catálogo: `https://servicios.senamhi.gob.pe/api/researchers/historical-download/stations`.
- Serie: `https://servicios.senamhi.gob.pe/api/researchers/historical-download/stations/{id}/series`.
- Fecha de consulta: **2026-11-18T01:57:45Z**.
- Catálogo completo: **293 estaciones**; **20** pertenecen al departamento de
  Piura y son las seleccionadas.
- La selección está fijada en `etl/senamhi_estaciones_piura.txt` para que un
  cambio del catálogo no altere la muestra sin revisión.
- Cada respuesta se guardó como **bytes crudos**, con SHA-256, tamaño, código
  HTTP, tipo de contenido y fecha en `data/raw/senamhi/manifest.json`.
- El build verifica el hash antes de procesar. No interpola, no rellena fechas y
  no elimina valores: conserva nulos y aplica banderas de calidad.

## 2. Cobertura por estación

La envolvente conjunta es **1961-01-01 a 2015-10-31**, pero no es la cobertura
de cada estación. Todas las series descargadas tienen **0 días faltantes dentro
de su intervalo** y **0 duplicados**: los huecos de dato se expresan como nulos,
no como filas ausentes. La tabla siguiente es la cobertura real.

| ID | Estación | Desde | Hasta | Días | Faltan | Precip. nula | Tmax nula | Tmin nula | Estado | Relación | Dist. borde km |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|---:|
| 000207 | MIRAFLORES | 1971-04-02 | 2013-12-31 | 15615 | 0 | 5.81 % | 5.56 % | 5.56 % | ok | dentro_cuenca | 16.77 |
| 000208 | MALLARES | 1961-01-01 | 2014-06-30 | 19539 | 0 | 21.86 % | 20.98 % | 21.02 % | ok | fuera_cuenca_contexto_regional | 10.14 |
| 000230 | LA ESPERANZA | 1966-07-01 | 2015-10-31 | 18020 | 0 | 4.82 % | 1.89 % | 2.85 % | ok | fuera_cuenca_contexto_regional | 31.39 |
| 000231 | CHUSIS | 1963-11-04 | 2014-04-30 | 18441 | 0 | 14.07 % | 6.1 % | 7.06 % | ok | dentro_cuenca | 3.88 |
| 000235 | MORROPON | 1963-10-01 | 2014-06-30 | 18536 | 0 | 4.06 % | 3.4 % | 3.32 % | ok | dentro_cuenca | 27.16 |
| 000237 | AYABACA | 1963-01-01 | 2014-06-30 | 18809 | 0 | 3.58 % | 0.77 % | 0.76 % | ok | fuera_cuenca_contexto_regional | 34.17 |
| 000238 | SAUSAL DE CULUCAN | 1963-01-01 | 2014-06-30 | 18809 | 0 | 4.88 % | 2.49 % | 2.59 % | ok | fuera_cuenca_contexto_regional | 21.56 |
| 000247 | SAN MIGUEL | 1973-01-01 | 2015-10-31 | 15644 | 0 | 3.89 % | 3.22 % | 2.89 % | ok | dentro_cuenca | 15.16 |
| 000248 | HUARMACA | 1963-10-19 | 2015-10-31 | 19006 | 0 | 3.71 % | 19.77 % | 21.06 % | ok | dentro_cuenca | 0.08 |
| 000255 | CHULUCANAS | 1972-01-02 | 2014-06-30 | 15521 | 0 | 18.51 % | 16.35 % | 18.03 % | ok | dentro_cuenca | 32.02 |
| 150001 | SAN PEDRO | 1975-01-01 | 2013-12-31 | 14245 | 0 | 5.1 % | 100 % | 100 % | sin_temperatura | dentro_cuenca | 20.93 |
| 152100 | BERNAL | 1963-11-01 | 2014-06-30 | 18505 | 0 | 5.95 % | 81.43 % | 81.53 % | temperatura_parcial | dentro_cuenca | 13.58 |
| 152101 | PANANGA | 1963-11-01 | 2013-12-31 | 18324 | 0 | 0.17 % | 100 % | 100 % | sin_temperatura | fuera_cuenca_contexto_regional | 42.2 |
| 152103 | LANCONES | 1963-09-01 | 2014-06-30 | 18566 | 0 | 2.63 % | 77.78 % | 77.64 % | temperatura_parcial | fuera_cuenca_contexto_regional | 19.87 |
| 152106 | SAPILLICA | 1963-08-01 | 2013-12-31 | 18416 | 0 | 5.95 % | 100 % | 100 % | sin_temperatura | fuera_cuenca_contexto_regional | 8.83 |
| 152111 | HACIENDA BIGOTE | 1963-12-01 | 2013-12-31 | 18294 | 0 | 5.8 % | 100 % | 100 % | sin_temperatura | dentro_cuenca | 21.57 |
| 152126 | SONDORILLO | 1963-10-01 | 2014-06-30 | 18536 | 0 | 1.32 % | 77.3 % | 77.33 % | temperatura_parcial | fuera_cuenca_contexto_regional | 10.66 |
| 152127 | TULUCE | 1963-10-01 | 2013-12-31 | 18355 | 0 | 2.66 % | 100 % | 100 % | sin_temperatura | fuera_cuenca_contexto_regional | 12.11 |
| 152128 | HACIENDA SHUMAYA | 1963-11-01 | 2013-12-31 | 18324 | 0 | 2.14 % | 100 % | 100 % | sin_temperatura | fuera_cuenca_contexto_regional | 16.7 |
| 152132 | PORCULLA | 1965-03-01 | 2014-06-30 | 18019 | 0 | 2.48 % | 100 % | 100 % | sin_temperatura | fuera_cuenca_contexto_regional | 16.93 |

Resumen: **357.524 filas diarias**. Diez estaciones tienen temperatura
utilizable (más del 78 % de días no nulos), tres tienen temperatura parcial
(Bernal, Lancones y Sondorillo) y **siete no tienen ningún dato de
temperatura**. La precipitación existe en las 20 estaciones; los nulos van de
0,17 % (Pananga) a 21,86 % (Mallares). El estado `ok` significa que la
temperatura está presente en al menos la mitad de los días; **no** significa que
la serie esté completa: Mallares, por ejemplo, tiene 21 % de nulos de Tmax.

## 3. Controles de calidad

Se aplicaron estos controles, todos conservando el valor original:

| Control | Resultado en esta descarga |
|---|---|
| Fecha válida y formato ISO | 0 fechas inválidas |
| Duplicados | 0 |
| Orden temporal | 0 series desordenadas |
| Precipitación negativa | 0; si aparece, se conserva y se marca `precip_negativa` |
| Tmax < Tmin | 0; si aparece, se conserva y se marca `tmax_menor_tmin` |
| Tmax = Tmin | 0; se marca `tmax_igual_tmin` |
| Precipitación > 100 mm/día | 109 filas marcadas `precip_extrema`; no se eliminan |
| Temperatura fuera de rango plausible | 0 |
| Coordenadas inválidas | 0 en las 20 estaciones |
| Campos ausentes o tipo no numérico | 0; el build falla por estación si aparece |
| Respuesta vacía o `status:false` | 0 |
| Correspondencia ID/archivo | verificada por nombre, manifiesto y hash; la API no devuelve el ID dentro de la serie |

Los máximos de precipitación son extremos plausibles de El Niño, no errores
automáticos:

| Estación | Fecha | Precipitación |
|---|---|---:|
| HACIENDA BIGOTE | 1998-03-10 | 240,0 mm |
| CHULUCANAS | 1983-01-26 | 202,5 mm |
| MALLARES | 1998-03-22 | 201,0 mm |
| SAN PEDRO | 2002-04-06 | 199,3 mm |
| LANCONES | 1983-04-26 | 193,8 mm |

No se imputó ningún valor. Los nulos del CSV se escriben vacíos y las banderas
`qc_*` permiten excluirlos o revisarlos sin perder el original.

## 4. Clasificación geográfica

Se usó la cuenca ANA publicada en `web/public/data/cuenca.geojson` (SHA-256
`09e6d974969807a3d8c637503d4653276e74b5a0a603bcf47b0d4cddbd17fc43`) y las
subcuencas publicadas. La distancia se midió en EPSG:32717, en kilómetros al
borde.

- **9 estaciones dentro de la cuenca:** Miraflores, Chusis, Morropón, San
  Miguel, Huarmaca, Chulucanas, San Pedro, Bernal y Hacienda Bigote.
- **11 estaciones fuera, pero en Piura:** Mallares, La Esperanza, Ayabaca,
  Sausal de Culucán, Pananga, Lancones, Sapillica, Sondorillo, Tuluce, Hacienda
  Shumaya y Porculla. Se conservan como **contexto regional** y no se mezclan
  con las estaciones de la cuenca.
- **0 estaciones fuera del ámbito de estudio** en esta selección. La regla para
  futuras estaciones es explícita: si están fuera de Piura, se clasifican como
  `fuera_ambito_estudio`.
- **Huarmaca** está a 0,08 km del borde: se marca como caso límite y su
  clasificación puede cambiar con otra generalización del límite.

La distancia no se usa para decidir la relevancia con un umbral arbitrario; se
publica como información y la justificación es la pertenencia al departamento
de Piura. Una estación fuera de la cuenca no es representativa de la cuenca y no
debe usarse para una serie agregada de la cuenca sin declararlo.

## 5. Hashes de los archivos crudos

Los archivos están en `data/raw/senamhi/series/` (ignorados por Git). El
manifiesto incluye además el catálogo y el propio manifiesto. Estos son los
hashes de las 20 series:

| ID | Archivo | Bytes | SHA-256 |
|---|---|---:|---|
| 000207 | `series/000207.json` | 1468977 | `d03d13b2c7a3e495a7583ed02f23ced13f46a40ebfdb952edbf9ac6fc3464278` |
| 000208 | `series/000208.json` | 1841241 | `a03d448ceea444f233f0f7060773f24d535c83d26a5e639eb7c82f31d2f9c06b` |
| 000230 | `series/000230.json` | 1695877 | `47bfe45dfff620ea45ba8ee5ee10e1ffc57f3cf374d29a8ea5c3f2d3a5dd041d` |
| 000231 | `series/000231.json` | 1736275 | `cfbcc8f08eee44a8c8de6f09d819be065f0298b6a3f8f5a9accab83e2bba98f4` |
| 000235 | `series/000235.json` | 1743742 | `201b4f1b7bf85992fd1ae10c5fa8f29da6522c254d706f927198c9e2eedbefa9` |
| 000237 | `series/000237.json` | 1760110 | `0727c988fa666ec4a71013a19423dc53ee1015fa1cf8360c86cc6ec653f1a0ef` |
| 000238 | `series/000238.json` | 1769735 | `0e2022f5911e79c0e86bdaf3403619aa047f1e0039101ae6ff0a53a9b91933a9` |
| 000247 | `series/000247.json` | 1471848 | `8aa3a655b287756274efb188beb3ff13f19c20a61ca1c8a8dab8e4e97c5b09e1` |
| 000248 | `series/000248.json` | 1788394 | `c4a5169d8a3fea3754e3e7cbf89ac407f04b7db38a4655fcc999ff60c9915209` |
| 000255 | `series/000255.json` | 1462358 | `12adfe23fd03cf98568501e5ae14dfcc1b708fbbe5a3fda26a748839ee0dbf9b` |
| 150001 | `series/150001.json` | 1340367 | `99a66085e97c6ef4d7204f32688f57bfe5e33a7d28fed5d7f0c528a8080befb4` |
| 152100 | `series/152100.json` | 1741346 | `0437a98ca46aa8bfc0ec5fde865c0268a5c180f0f0037d5a96a1f944c98336a6` |
| 152101 | `series/152101.json` | 1723419 | `1e5badba26dbf057d632b2467699894d9051041fe04755bc1955fb166ac41158` |
| 152103 | `series/152103.json` | 1746254 | `163bddf7ed1aa9ee97e5ec7e4943de3f818ff55b220dc1aa46f82c5711c3c680` |
| 152106 | `series/152106.json` | 1733722 | `e7bf10ff20f1fc227795691758cdbfebeaccc7020bae14e8ef59b622cc0f9052` |
| 152111 | `series/152111.json` | 1722735 | `204af60a4fee38ac2fa3bd95284b6968f50b2745af138776ad074f84d5991e87` |
| 152126 | `series/152126.json` | 1743234 | `9d539306fe4b15519c9a577981b4ea6c7bc5a0dc5069d26ac2f9eabf5733f3e3` |
| 152127 | `series/152127.json` | 1728800 | `a0741294b3d896067f57ccedb801bdde01eb61c81b5f34d60e1ed662bc68e5f1` |
| 152128 | `series/152128.json` | 1725067 | `33896495d376072eba5c3e1716e39d81ad58c87dbb1f65c3063253cb20335b04` |
| 152132 | `series/152132.json` | 1696367 | `070add107baede5af678ed1c1e46363e28f029a40e52145856dc1bdda36a2cd7` |

SHA-256 del catálogo crudo:
`548508e2ab9726eb9f7f32c3005952a355716bc59b975fca31d716e210bd0174`.
El build deja además `data/processed/senamhi/hashes.sha256` con los hashes de
las salidas.

## 6. Salidas locales

En `data/processed/senamhi/` (ignorado por Git):

- `estaciones_piura.csv`: 357.524 filas diarias con nulos y banderas `qc_*`.
- `catalogo_estaciones.csv`: las 293 estaciones del catálogo, con marca de
  selección.
- `inventario_estaciones.csv`: las 20 seleccionadas, con archivo, bytes, hash y
  metadatos de descarga.
- `cobertura_estaciones.csv`: la tabla de la sección 2, más fechas por variable,
  extremos y clasificación geográfica.
- `huecos_estaciones.csv`: intervalos contiguos faltantes; en esta consulta no
  hay ninguno.
- `metadata.json`: resumen, hashes, método, licencia y `publicado: false`.
- `hashes.sha256`: hashes de crudos y salidas.

## 7. Reproducción

```bash
python3 etl/download_senamhi_historico.py
python3 etl/build_senamhi_historico.py
```

El download se niega a escribir en `web/public/`, conserva los bytes crudos y
no sobrescribe un archivo existente sin `--force`. El build no usa red y falla
si el hash no coincide con el manifiesto.

Pruebas:

```bash
python3 -m unittest discover -s etl/tests -v
```

Las pruebas de integración en vivo son opt-in (`RUN_LIVE_TESTS=1`) y no se
ejecutan en CI.

## 8. Licencia y estado

Los términos de SENAMHI (`https://www.senamhi.gob.pe/?p=terminos-condiciones`)
permiten el uso público con atribución, pero no son una licencia abierta. No
autorizan expresamente la redistribución del JSON crudo ni la publicación de
series derivadas. Por eso:

- `data/sources.yml` declara `publicacion: bloqueada`.
- No hay ningún archivo de SENAMHI en `web/public/`.
- Las series no se usan en el sitio ni en una capa publicada.
- Cualquier publicación futura requiere confirmación escrita y una decisión de
  licencia; ver `docs/17-licencias-y-reutilizacion.md`.
- La página `/fuentes` se revisó con una captura real:
  `docs/ui/evidencia/fase2-2-fuentes-desktop.png` y
  `docs/ui/evidencia/fase2-2-fuentes-senamhi.png`.

## 9. Límites conocidos

- La API no declara unidades en el JSON: se asumen mm y °C según la
  documentación de SENAMHI; no se convierten.
- La API no devuelve el ID de la estación dentro de la serie; la correspondencia
  se verifica por la URL, el nombre del archivo y el manifiesto.
- La cobertura termina en 2015-10-31; no cubre 2016–2026, 2017 ni 2023.
- No incluye caudales ni niveles.
- Siete estaciones no tienen temperatura; no deben presentarse como una red de
  temperatura completa.
- La clasificación de las estaciones exteriores es contexto regional, no una
  serie representativa de la cuenca.
- Los extremos marcados son plausibles; la bandera no es una afirmación de error.
